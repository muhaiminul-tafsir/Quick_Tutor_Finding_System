from rest_framework import serializers
from .models import Review

class ReviewSerializer(serializers.ModelSerializer):
    booking_id = serializers.IntegerField(source='booking.id', read_only=True)

    class Meta:
        model = Review
        fields = ('id', 'booking', 'booking_id', 'rating', 'comment', 'created_at')

