from rest_framework import serializers
from .models import Prediction


class PredictionSerializer(serializers.ModelSerializer):
    uploaded_image_url = serializers.SerializerMethodField()
    model_version_label = serializers.CharField(source='model_version.version', read_only=True)

    class Meta:
        model = Prediction
        fields = ['id', 'uploaded_image_url', 'predicted_class', 'confidence', 'class_probabilities', 'model_version', 'model_version_label', 'created_at']
        read_only_fields = fields

    def get_uploaded_image_url(self, obj):
        if not (obj.uploaded_image and obj.uploaded_image.image):
            return None
        url = obj.uploaded_image.image.url
        request = self.context.get('request')
        return request.build_absolute_uri(url) if request else url