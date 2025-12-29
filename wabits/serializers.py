from rest_framework import serializers
from .models import WAbits

class WAbitsSerializers(serializers.ModelSerializer):
    class Meta:
        model = WAbits
        fields = "__all__"