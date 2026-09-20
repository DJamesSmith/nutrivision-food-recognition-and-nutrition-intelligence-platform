import logging
from pathlib import Path

from django.conf import settings
from django.utils import timezone

from accounts.decorators import log_execution_time
from audit.models import AuditLog
from audit.services import log_event

from .models import ModelVersion, TrainingJob
from .services import activate_model_version

logger = logging.getLogger(__name__)


class DatasetValidationError(Exception):
    """Raised when a dataset is not yet suitable for training."""
    pass


def validate_dataset_for_training(dataset):
    """
    Dataset Validation stage. Requires at least 2 classes (a classifier
    needs something to discriminate between) and a minimum number of
    images per class (settings.MIN_IMAGES_PER_CLASS_FOR_TRAINING), so a
    class with a handful of images doesn't silently produce a useless
    model. Returns the class distribution on success.
    """
    distribution = list(dataset.get_class_distribution())

    if len(distribution) < 2:
        raise DatasetValidationError(
            f"Dataset '{dataset.name}' needs at least 2 classes to train a classifier "
            f"(found {len(distribution)})."
        )

    insufficient = [
        row for row in distribution if row['count'] < settings.MIN_IMAGES_PER_CLASS_FOR_TRAINING
    ]
    if insufficient:
        labels = ", ".join(f"{row['class_label']} ({row['count']})" for row in insufficient)
        raise DatasetValidationError(
            f"Every class needs at least {settings.MIN_IMAGES_PER_CLASS_FOR_TRAINING} images. "
            f"Below threshold: {labels}."
        )

    return distribution


def _gather_filepaths_and_labels(dataset):
    """
    Dataset Loading stage. Reads every DatasetImage row for the dataset
    and builds parallel (filepath, label_index) lists, plus the ordered
    class_labels list that fixes the output-neuron ordering — this is
    what makes the number of output classes fully dynamic.
    """
    class_labels = sorted(dataset.images.order_by().values_list('class_label', flat=True).distinct())
    label_to_index = {label: index for index, label in enumerate(class_labels)}

    filepaths, labels = [], []
    for image in dataset.images.all().only('image', 'class_label'):
        filepaths.append(image.image.path)
        labels.append(label_to_index[image.class_label])

    return filepaths, labels, class_labels


@log_execution_time
def train_efficientnet(job_id):
    """
    Full pipeline: Dataset Loading -> Dataset Validation -> Train/Val Split
    -> Preprocessing -> Data Augmentation -> EfficientNetB0 -> Training ->
    Validation -> Evaluation -> Model Saving -> Model Version Registration.

    TensorFlow, NumPy and scikit-learn are imported lazily, INSIDE this
    function, rather than at module level. That means:
      - The Django web process (runserver, gunicorn, manage.py check/
        migrate) never needs these heavy ML dependencies installed.
      - Only the Celery worker process — which actually calls this
        function — needs the full ML stack.
    This keeps `training/models.py`, `training/views.py`, etc. importable
    (and the whole project runnable/testable) without TensorFlow present.
    """
    job = TrainingJob.objects.select_related('dataset', 'created_by').get(pk=job_id)

    try:
        job.status = TrainingJob.Status.STARTED
        job.started_at = timezone.now()
        job.save(update_fields=['status', 'started_at'])

        distribution = validate_dataset_for_training(job.dataset)
        filepaths, labels, class_labels = _gather_filepaths_and_labels(job.dataset)
        num_classes = len(class_labels)

        logger.info(
            "Training job #%s: %s images across %s classes (%s).",
            job.id, len(filepaths), num_classes, distribution,
        )

        # ---- Lazy, worker-only imports ----
        import numpy as np
        import tensorflow as tf
        from sklearn.metrics import precision_recall_fscore_support
        from sklearn.model_selection import train_test_split
        from tensorflow.keras import layers
        from tensorflow.keras import models as keras_models
        from tensorflow.keras.applications import EfficientNetB0
        from tensorflow.keras.applications.efficientnet import preprocess_input
        from tensorflow.keras.optimizers import Adam

        img_size = settings.EFFICIENTNET_IMG_SIZE
        batch_size = settings.DEFAULT_TRAINING_BATCH_SIZE

        # ---- Train / Validation Split ----
        train_paths, val_paths, train_labels, val_labels = train_test_split(
            filepaths, labels,
            test_size=settings.DEFAULT_VALIDATION_SPLIT,
            random_state=42,
            stratify=labels,
        )

        # ---- Preprocessing ----
        def _load_and_resize(path, label):
            raw = tf.io.read_file(path)
            image = tf.image.decode_image(raw, channels=3, expand_animations=False)
            image.set_shape([None, None, 3])
            image = tf.image.resize(image, img_size)
            return image, label

        # ---- Data Augmentation (training split only) ----
        augmentation = keras_models.Sequential([
            layers.RandomFlip('horizontal'),
            layers.RandomRotation(0.1),
            layers.RandomZoom(0.1),
        ], name='augmentation')

        def _build_dataset(paths, lbls, training):
            ds = tf.data.Dataset.from_tensor_slices((paths, lbls))
            ds = ds.map(_load_and_resize, num_parallel_calls=tf.data.AUTOTUNE)
            if training:
                ds = ds.shuffle(buffer_size=min(len(paths), 1000), seed=42)
                ds = ds.map(
                    lambda img, lbl: (augmentation(img, training=True), lbl),
                    num_parallel_calls=tf.data.AUTOTUNE,
                )
            ds = ds.map(
                lambda img, lbl: (preprocess_input(img), lbl),
                num_parallel_calls=tf.data.AUTOTUNE,
            )
            return ds.batch(batch_size).prefetch(tf.data.AUTOTUNE)

        train_ds = _build_dataset(train_paths, train_labels, training=True)
        val_ds = _build_dataset(val_paths, val_labels, training=False)

        # ---- EfficientNetB0 backbone (ImageNet weights, frozen) ----
        backbone = EfficientNetB0(
            include_top=False,
            weights='imagenet',
            input_shape=settings.EFFICIENTNET_INPUT_SHAPE,
        )
        backbone.trainable = False

        inputs = layers.Input(shape=settings.EFFICIENTNET_INPUT_SHAPE)
        x = backbone(inputs, training=False)
        x = layers.GlobalAveragePooling2D()(x)
        x = layers.Dropout(0.3)(x)
        outputs = layers.Dense(num_classes, activation='softmax')(x)
        model = keras_models.Model(inputs, outputs, name='efficientnetb0_classifier')

        model.compile(
            optimizer=Adam(learning_rate=1e-3),
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy'],
        )

        # ---- Training (classification head only) ----
        epochs_head = job.epochs or settings.DEFAULT_TRAINING_EPOCHS_HEAD
        history = model.fit(train_ds, validation_data=val_ds, epochs=epochs_head, verbose=2)

        # ---- Optional fine-tuning: unfreeze the top of the backbone ----
        if settings.DEFAULT_TRAINING_EPOCHS_FINE_TUNE > 0:
            backbone.trainable = True
            for layer in backbone.layers[:-20]:
                layer.trainable = False

            model.compile(
                optimizer=Adam(learning_rate=1e-5),
                loss='sparse_categorical_crossentropy',
                metrics=['accuracy'],
            )
            history = model.fit(
                train_ds, validation_data=val_ds,
                epochs=settings.DEFAULT_TRAINING_EPOCHS_FINE_TUNE, verbose=2,
            )

        final_train_acc = float(history.history['accuracy'][-1])
        final_val_acc = float(history.history['val_accuracy'][-1])
        final_train_loss = float(history.history['loss'][-1])
        final_val_loss = float(history.history['val_loss'][-1])

        # ---- Evaluation ----
        # Macro-averaged precision/recall/F1: appropriate for a multiclass
        # problem where class sizes may differ (unlike micro-averaging,
        # it doesn't let a large class dominate the score).
        val_predictions = model.predict(val_ds)
        predicted_indices = np.argmax(val_predictions, axis=1)
        precision, recall, f1, _ = precision_recall_fscore_support(
            val_labels, predicted_indices, average='macro', zero_division=0,
        )

        # ---- Model Saving ----
        version_label = f"v{ModelVersion.objects.count() + 1}"
        model_dir = Path(settings.TRAINED_MODELS_DIR) / version_label
        model_dir.mkdir(parents=True, exist_ok=True)
        model_path = model_dir / "model.keras"
        model.save(model_path)

        # ---- TrainingJob completion ----
        job.status = TrainingJob.Status.COMPLETED
        job.completed_at = timezone.now()
        job.accuracy = final_train_acc
        job.validation_accuracy = final_val_acc
        job.loss = final_train_loss
        job.validation_loss = final_val_loss
        job.model_path = str(model_path)
        job.save()

        # ---- Model Version Registration ----
        model_version = ModelVersion.objects.create(
            version=version_label,
            architecture='EfficientNetB0',
            dataset=job.dataset,
            training_job=job,
            class_labels=class_labels,
            num_classes=num_classes,
            accuracy=final_train_acc,
            validation_accuracy=final_val_acc,
            precision=float(precision),
            recall=float(recall),
            f1_score=float(f1),
            model_path=str(model_path),
        )
        activate_model_version(model_version)

        log_event(
            AuditLog.EventType.TRAINING_COMPLETED, user=job.created_by,
            description=f"Training completed for job #{job.id} — val_accuracy={final_val_acc:.4f}.",
            reference_model='TrainingJob', reference_id=job.id,
            metadata={'validation_accuracy': final_val_acc, 'validation_loss': final_val_loss},
        )
        log_event(
            AuditLog.EventType.MODEL_UPDATED, user=job.created_by,
            description=f"Model version {version_label} trained and activated.",
            reference_model='ModelVersion', reference_id=model_version.id,
        )

        return model_version.id

    except Exception as exc:
        logger.exception("Training job #%s failed.", job_id)
        job.status = TrainingJob.Status.FAILED
        job.completed_at = timezone.now()
        job.error_message = str(exc)[:2000]
        job.save(update_fields=['status', 'completed_at', 'error_message'])

        log_event(
            AuditLog.EventType.TRAINING_FAILED, user=job.created_by,
            description=f"Training failed for job #{job.id}: {exc}",
            reference_model='TrainingJob', reference_id=job.id,
        )
        raise
