from rest_framework import serializers
from .models import TutorProfile

class TutorProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = TutorProfile
        fields = ('id', 'user', 'username', 'subject', 'bio', 'rating', 'created_at', 'updated_at')

