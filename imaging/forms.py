from django import forms
from .models import Dataset, DatasetImage


class DatasetForm(forms.ModelForm):
    class Meta:
        model = Dataset
        fields = ['name', 'description']


class DatasetImageUploadForm(forms.ModelForm):
    class Meta:
        model = DatasetImage
        fields = ['image', 'class_label']

    def clean_class_label(self):
        label = self.cleaned_data['class_label'].strip()
        if not label:
            raise forms.ValidationError("A class label is required.")
        return label
