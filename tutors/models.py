from django.db import models
from accounts.models import User

class TutorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='tutor_profile')
    subject = models.CharField(max_length=100)
    bio = models.TextField()
    rating = models.FloatField(default=0)
    monthly_rate = models.DecimalField(max_digits=10, decimal_places=2, default=4000)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.subject}"


class TutorSchedule(models.Model):
    DAY_CHOICES = [
        ('0', 'Sun'),
        ('1', 'Mon'),
        ('2', 'Tue'),
        ('3', 'Wed'),
        ('4', 'Thu'),
        ('5', 'Fri'),
        ('6', 'Sat'),
    ]

    tutor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='schedules')
    days   = models.CharField(max_length=50, help_text="Comma separated days like '0,2,4'")
    time   = models.TimeField()
    months = models.PositiveIntegerField(default=1, help_text="Course duration in months")

    class Meta:
        ordering = ['time']

    def __str__(self):
        return f"{self.display} — {self.tutor.username}"

    @property
    def display(self):
        day_map = {k: v for k, v in self.DAY_CHOICES}
        day_names = [day_map.get(d.strip(), '') for d in self.days.split(',') if d.strip()]
        days_str = ", ".join(filter(bool, day_names))
        return f"{days_str} at {self.time.strftime('%I:%M %p')} ({self.months} month{'s' if self.months != 1 else ''})"

    def is_booked(self):
        """True if an active booking already holds this slot."""
        return self.bookings.filter(status__in=['pending', 'confirmed']).exists()
