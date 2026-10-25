from django.db import models
from django.core.validators import MinValueValidator
from accounts.models import User
from tutors.models import TutorSchedule


class Booking(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    )

    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='student_bookings')
    tutor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tutor_bookings')

    date     = models.DateField()
    months   = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    schedule = models.ForeignKey(
        TutorSchedule, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='bookings'
    )
    status   = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    meet_link = models.URLField(blank=True, default='', help_text='Google Meet / Zoom link set by tutor')
    tutor_message = models.TextField(blank=True, default='', help_text='Message from tutor to student')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.student.username} -> {self.tutor.username} ({self.months} month(s), {self.status})"

    # ── Helpers for templates ──────────────────────────────────────────────
    @property
    def payment(self):
        """Latest approved payment, or latest pending, or None."""
        approved = self.payments.filter(status='approved').order_by('-created_at').first()
        if approved:
            return approved
        return self.payments.filter(status='pending').order_by('-created_at').first()

    @property
    def total_paid(self):
        """Sum of all approved payments."""
        from django.db.models import Sum
        return self.payments.filter(status='approved').aggregate(s=Sum('amount'))['s'] or 0

    @property
    def total_commission(self):
        """Sum of commission from approved payments."""
        from django.db.models import Sum
        return self.payments.filter(status='approved').aggregate(s=Sum('commission'))['s'] or 0

    @property
    def total_amount(self):
        """Full booking cost: monthly_rate × months."""
        try:
            return float(self.tutor.tutor_profile.monthly_rate) * self.months
        except Exception:
            return 4000 * self.months

    @property
    def balance_due(self):
        return round(self.total_amount - float(self.total_paid), 2)

    @property
    def is_fully_paid(self):
        return self.balance_due <= 0

    @property
    def first_payment_made(self):
        """True if at least one approved or pending payment exists."""
        return self.payments.exists()
