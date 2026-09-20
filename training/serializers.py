from rest_framework import serializers

from .models import ModelVersion, TrainingJob


class TrainingJobSerializer(serializers.ModelSerializer):
    dataset_name = serializers.CharField(source='dataset.name', read_only=True)

    class Meta:
        model = TrainingJob
        fields = [
            'id', 'dataset', 'dataset_name', 'status', 'task_id', 'epochs',
            'started_at', 'completed_at', 'accuracy', 'validation_accuracy',
            'loss', 'validation_loss', 'model_path', 'error_message',
            'created_by', 'created_at',
        ]
        read_only_fields = fields


class ModelVersionSerializer(serializers.ModelSerializer):
    dataset_name = serializers.CharField(source='dataset.name', read_only=True)

    class Meta:
        model = ModelVersion
        fields = [
            'id', 'version', 'architecture', 'dataset', 'dataset_name', 'training_job',
            'class_labels', 'num_classes', 'accuracy', 'validation_accuracy',
            'precision', 'recall', 'f1_score', 'model_path', 'is_active', 'created_at',
        ]
        read_only_fields = fields
