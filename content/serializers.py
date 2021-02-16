from rest_framework import serializers
from .models import StaticContent


# This class is use for serialize the data of role
class StaticContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaticContent
        fields = ('terms_and_conditions', 'privacy_policy', 'about_us')

class NewsletterSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaticContent
        fields = '__all__'