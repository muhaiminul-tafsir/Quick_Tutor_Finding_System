from rest_framework import serializers
from .models import Booking

class BookingSerializer(serializers.ModelSerializer):
    student_username = serializers.CharField(source='student.username', read_only=True)
    tutor_username = serializers.CharField(source='tutor.username', read_only=True)

    class Meta:
        model = Booking
        fields = ('id', 'student', 'student_username', 'tutor', 'tutor_username', 'date', 'months', 'status', 'created_at', 'updated_at')

