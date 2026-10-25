from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from bookings.models import Booking
from reviews.models import Review
from payments.models import Payment


def home(request):
    return render(request, 'home.html')


@login_required(login_url='login')
def dashboard_view(request):
    user = request.user

    # Superusers and staff see the Admin Overview at /dashboard/
    if user.is_superuser or user.is_staff:
        from .admin_views import admin_overview
        return admin_overview(request)

    if user.role == 'student':
        bookings = Booking.objects.filter(student=user).select_related(
            'tutor', 'tutor__tutor_profile'
        ).order_by('-date')

        total_bookings = bookings.count()
        completed_bookings = bookings.filter(status='completed').count()
        pending_bookings  = bookings.filter(status='pending').count()
        approved_bookings = bookings.filter(status='confirmed').count()

        total_spent = sum(
            b.payment.amount for b in bookings
            if hasattr(b, 'payment') and b.payment is not None and b.payment.status == 'approved'
        )
        average_rating = (
            sum(b.review.rating for b in bookings if hasattr(b, 'review') and b.review)
            / bookings.filter(review__isnull=False).count()
            if bookings.filter(review__isnull=False).count() > 0 else 0
        )

        # Recent 4 bookings for session cards
        recent_bookings = bookings[:4]

        # Unique tutors student has booked
        tutor_ids = bookings.values_list('tutor', flat=True).distinct()
        from accounts.models import User
        recent_tutors = User.objects.filter(
            id__in=tutor_ids, role='tutor'
        ).select_related('tutor_profile')[:6]

        context = {
            'total_bookings':    total_bookings,
            'completed_bookings': completed_bookings,
            'pending_bookings':  pending_bookings,
            'approved_bookings': approved_bookings,
            'total_spent':       round(total_spent, 2),
            'average_rating':    round(average_rating, 1),
            'recent_bookings':   recent_bookings,
            'recent_tutors':     recent_tutors,
        }

    else:  # tutor
        bookings = Booking.objects.filter(tutor=user).select_related(
            'student'
        ).order_by('-date')

        total_students   = bookings.values('student').distinct().count()
        pending_bookings = bookings.filter(status='pending').count()
        confirmed_bookings = bookings.filter(status='confirmed').count()
        total_earned = sum(
            b.payment.amount for b in bookings
            if hasattr(b, 'payment') and b.payment is not None and b.payment.status == 'approved'
        )

        tutor_profile = getattr(user, 'tutor_profile', None)
        rating = tutor_profile.rating if tutor_profile else 0

        recent_students = bookings.order_by('-date')[:6]

        context = {
            'total_students':    total_students,
            'pending_bookings':  pending_bookings,
            'confirmed_bookings': confirmed_bookings,
            'total_earned':      round(total_earned, 2),
            'rating':            rating,
            'recent_students':   recent_students,
        }

    return render(request, 'dashboard.html', context)
