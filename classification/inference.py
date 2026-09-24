import logging

logger = logging.getLogger(__name__)

# Keeps at most one Keras model resident in memory per process — the currently-active one. Avoids re-loading the model artifact from disk on
# every single prediction request, while never letting stale versions accumulate in memory after an admin activates a different one.
_MODEL_CACHE = {}


# Raised when the active model artifact cannot be loaded or run.
class InferenceError(Exception):
    pass


def _load_keras_model(model_version):
    cached = _MODEL_CACHE.get(model_version.id)
    if cached is not None:
        return cached
    try:
        import tensorflow as tf
    except ImportError as exc:
        raise InferenceError(f"TensorFlow is not available on this server: {exc}")
    try:
        model = tf.keras.models.load_model(model_version.model_path)
    except (OSError, ValueError) as exc:
        raise InferenceError(f"Could not load model artifact for version '{model_version.version}': {exc}")
    _MODEL_CACHE.clear()
    _MODEL_CACHE[model_version.id] = model
    return model


# Preprocessing -> Load Active Model -> Prediction -> Class Probabilities -> Highest Probability Class.

# TensorFlow/NumPy are imported lazily inside this function for the same reason as training.ml_pipeline: `manage.py check`/migrate and the rest
# of the Django project stay importable without the ML stack installed; only a request that actually reaches this function needs it. Any
# import failure is converted to InferenceError so the API always returns a clean JSON error instead of an unhandled 500.

# Returns (predicted_class: str, confidence: float, probabilities: dict).
def predict_image(image_path, model_version):
    from django.conf import settings

    if not model_version.class_labels:
        raise InferenceError("The active model version has no registered class labels.")

    model = _load_keras_model(model_version)

    try:
        import numpy as np
        import tensorflow as tf
        from tensorflow.keras.applications.efficientnet import preprocess_input
    except ImportError as exc:
        raise InferenceError(f"TensorFlow is not available on this server: {exc}")

    img_size = settings.EFFICIENTNET_IMG_SIZE
    try:
        raw = tf.io.read_file(image_path)
        image = tf.image.decode_image(raw, channels=3, expand_animations=False)
        image.set_shape([None, None, 3])
        image = tf.image.resize(image, img_size)
        image = preprocess_input(image)
        batch = tf.expand_dims(image, axis=0)
        raw_predictions = model.predict(batch, verbose=0)[0]
    except Exception as exc:
        logger.exception("Inference failed for image '%s'.", image_path)
        raise InferenceError(f"Failed to run prediction: {exc}")

    probabilities = {
        label: float(raw_predictions[index])
        for index, label in enumerate(model_version.class_labels)
    }
    predicted_index = int(np.argmax(raw_predictions))
    predicted_class = model_version.class_labels[predicted_index]
    confidence = float(raw_predictions[predicted_index])

    return predicted_class, confidence, probabilities