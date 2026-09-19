from rest_framework import serializers
from .models import Dataset, DatasetImage, UploadedImage


class DatasetImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = DatasetImage
        fields = ['id', 'dataset', 'image', 'class_label', 'uploaded_by', 'created_at']
        read_only_fields = ['id', 'dataset', 'uploaded_by', 'created_at']

    def validate_class_label(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("A class label is required.")
        return value


class DatasetSerializer(serializers.ModelSerializer):
    num_images = serializers.IntegerField(source='get_num_images', read_only=True)
    num_classes = serializers.IntegerField(source='get_num_classes', read_only=True)

    class Meta:
        model = Dataset
        fields = [
            'id', 'name', 'description', 'status',
            'num_images', 'num_classes', 'created_by', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'status', 'num_images', 'num_classes', 'created_by', 'created_at', 'updated_at']

    def validate_name(self, value):
        value = value.strip()
        qs = Dataset.objects.filter(name__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("A dataset with this name already exists.")
        return value


class UploadedImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadedImage
        fields = ['id', 'image', 'original_filename', 'content_type', 'file_size', 'created_at']
        read_only_fields = ['id', 'original_filename', 'content_type', 'file_size', 'created_at']
