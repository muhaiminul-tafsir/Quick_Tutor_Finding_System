from django.contrib import admin
from .models import Booking

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('student', 'tutor', 'date', 'months', 'status', 'created_at')
    list_filter = ('status', 'date')
    search_fields = ('student__username', 'tutor__username')

# Register your models here.
