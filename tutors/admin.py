from django.contrib import admin
from .models import TutorProfile

@admin.register(TutorProfile)
class TutorProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'subject', 'rating', 'created_at')
    list_filter = ('subject', 'rating')
    search_fields = ('user__username', 'subject')
