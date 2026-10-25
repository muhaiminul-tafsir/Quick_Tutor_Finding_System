"""
Management command: fix_commissions
Backfills commission, tutor_income, and is_first_payment for all existing payments
that were created before the commission logic was implemented.

Usage:
    python manage.py fix_commissions
    python manage.py fix_commissions --dry-run
"""

from django.core.management.base import BaseCommand
from payments.models import Payment
from bookings.models import Booking


class Command(BaseCommand):
    help = 'Recalculate and backfill commission/tutor_income for all existing payments'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would change without saving to DB',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        updated = 0
        skipped = 0

        for booking in Booking.objects.prefetch_related('payments').all():
            # Sort payments by created_at to determine order
            payments = list(booking.payments.order_by('created_at'))
            if not payments:
                continue

            try:
                monthly_rate = booking.tutor.tutor_profile.monthly_rate
            except Exception:
                monthly_rate = 4000
                self.stdout.write(
                    self.style.WARNING(
                        f'  Booking #{booking.id}: tutor profile missing, using ৳4000 default'
                    )
                )

            for i, payment in enumerate(payments):
                is_first = (i == 0)
                # first_month_covered = True only for payments AFTER the first
                first_month_covered = (i > 0)
                commission, tutor_income = Payment.calculate_commission(
                    payment.amount, monthly_rate, first_month_covered
                )

                old = f'commission={payment.commission} tutor_income={payment.tutor_income} is_first={payment.is_first_payment}'
                new = f'commission={commission} tutor_income={tutor_income} is_first={is_first}'

                if (float(payment.commission) == float(commission)
                        and float(payment.tutor_income) == float(tutor_income)
                        and payment.is_first_payment == is_first):
                    skipped += 1
                    continue

                self.stdout.write(
                    f'Payment #{payment.id} (Booking #{booking.id})\n'
                    f'  BEFORE: {old}\n'
                    f'  AFTER : {new}'
                )

                if not dry_run:
                    payment.commission = commission
                    payment.tutor_income = tutor_income
                    payment.is_first_payment = is_first
                    payment.save(update_fields=['commission', 'tutor_income', 'is_first_payment'])

                updated += 1

        mode = '[DRY RUN] Would update' if dry_run else 'Updated'
        self.stdout.write(self.style.SUCCESS(
            f'\nOK: {mode} {updated} payment(s). {skipped} already correct.'
        ))
