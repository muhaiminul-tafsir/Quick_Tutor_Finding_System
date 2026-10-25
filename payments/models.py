from django.db import models
from bookings.models import Booking


class Payment(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    METHOD_CHOICES = (
        ('bkash', 'bKash'),
        ('nagad', 'Nagad'),
        ('rocket', 'Rocket'),
    )

    # ForeignKey to allow multiple partial payments per booking
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='payments')

    amount = models.DecimalField(max_digits=10, decimal_places=2)

    # Commission breakdown
    commission = models.DecimalField(max_digits=10, decimal_places=2, default=0,
        help_text='Platform commission deducted from this payment')
    tutor_income = models.DecimalField(max_digits=10, decimal_places=2, default=0,
        help_text='Net amount tutor receives from this payment')
    is_first_payment = models.BooleanField(default=False,
        help_text='True if this is the first payment for this booking (50% commission applies)')

    payment_method = models.CharField(max_length=10, choices=METHOD_CHOICES, default='bkash')
    sender_number = models.CharField(max_length=20, blank=True, default='')
    transaction_id = models.TextField(blank=True, default='')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @staticmethod
    def calculate_commission(amount, monthly_rate, first_month_covered=False):
        """
        Commission rules (applied within a single payment):

        If the first month is NOT yet covered (no approved payments exist):
          - First ৳monthly_rate: 50% commission  (broker 40% + platform 10%)
          - Any excess beyond monthly_rate: 10% commission  (platform only)

        If the first month IS already covered:
          - Full amount: 10% commission  (platform only)

        Example: Pay ৳10,000, monthly_rate = ৳4,000, first time paying
          → first ৳4,000 × 50% = ৳2,000
          → excess ৳6,000 × 10% = ৳600
          → total commission = ৳2,600, tutor gets ৳7,400

        Args:
            amount:               payment amount submitted
            monthly_rate:         tutor's monthly_rate
            first_month_covered:  True if first month already paid & approved
        """
        amount = float(amount)
        monthly_rate = float(monthly_rate)

        if not first_month_covered:
            first_portion     = min(amount, monthly_rate)
            first_commission  = first_portion * 0.50          # 50% on 1st month
            excess            = max(0, amount - monthly_rate)
            excess_commission = excess * 0.10                  # 10% on rest
            commission = first_commission + excess_commission
        else:
            commission = amount * 0.10                         # 10% only

        commission   = round(commission, 2)
        tutor_income = round(amount - commission, 2)
        return commission, tutor_income

    @property
    def breakdown(self):
        """Human-readable commission breakdown."""
        if self.is_first_payment:
            try:
                rate = self.booking.tutor.tutor_profile.monthly_rate
                broker = round(float(rate) * 0.40, 2)
                platform = round(float(rate) * 0.10, 2)
                advance = round(float(self.amount) - float(rate), 2)
                return {
                    'broker_charge': broker,
                    'platform_charge': platform,
                    'advance': max(0, advance),
                }
            except Exception:
                pass
        return {
            'broker_charge': 0,
            'platform_charge': round(float(self.commission), 2),
            'advance': 0,
        }

    def __str__(self):
        tag = '[1st]' if self.is_first_payment else '[+]'
        return f"{tag} Booking#{self.booking.id} ৳{self.amount} → commission ৳{self.commission} ({self.get_status_display()})"
