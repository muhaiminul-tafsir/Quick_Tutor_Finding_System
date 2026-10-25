from rest_framework import serializers
from .models import Payment

class PaymentSerializer(serializers.ModelSerializer):
    booking_id = serializers.IntegerField(source='booking.id', read_only=True)

    class Meta:
        model = Payment
        fields = ('id', 'booking', 'booking_id', 'amount', 'status', 'created_at', 'updated_at')

