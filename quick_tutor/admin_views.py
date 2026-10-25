"""
Custom Admin Dashboard Views
Replaces Django's built-in /admin/ panel with a Luminary-styled dashboard.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.http import JsonResponse

from accounts.models import User
from bookings.models import Booking
from tutors.models import TutorProfile
from reviews.models import Review
from payments.models import Payment


def superuser_required(view_fn):
    """Decorator: only superusers/staff can access."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not (request.user.is_superuser or request.user.is_staff):
            messages.error(request, 'Access denied. Admin only.')
            return redirect('home')
        return view_fn(request, *args, **kwargs)
    wrapper.__name__ = view_fn.__name__
    return wrapper


# ─────────────────────────────────────────────
#  OVERVIEW
# ─────────────────────────────────────────────
@superuser_required
def admin_overview(request):
    total_users    = User.objects.count()
    total_students = User.objects.filter(role='student').count()
    total_tutors   = User.objects.filter(role='tutor').count()
    total_bookings = Booking.objects.count()
    total_payments = Payment.objects.filter(status='approved').count()
    total_revenue  = Payment.objects.filter(status='approved').aggregate(s=Sum('amount'))['s'] or 0
    total_commission = Payment.objects.filter(status='approved').aggregate(s=Sum('commission'))['s'] or 0
    total_reviews  = Review.objects.count()
    pending_payments = Payment.objects.filter(status='pending').count()
    pending_bookings = Booking.objects.filter(status='pending').count()

    recent_users    = User.objects.order_by('-date_joined')[:5]
    recent_bookings = Booking.objects.select_related('student', 'tutor').order_by('-created_at')[:5]
    recent_payments = Payment.objects.select_related('booking__student', 'booking__tutor').order_by('-created_at')[:5]

    context = {
        'total_users': total_users,
        'total_students': total_students,
        'total_tutors': total_tutors,
        'total_bookings': total_bookings,
        'total_payments': total_payments,
        'total_revenue': total_revenue,
        'total_commission': total_commission,
        'total_reviews': total_reviews,
        'pending_payments': pending_payments,
        'pending_bookings': pending_bookings,
        'recent_users': recent_users,
        'recent_bookings': recent_bookings,
        'recent_payments': recent_payments,
    }
    return render(request, 'admin_panel/overview.html', context)


# ─────────────────────────────────────────────
#  USER MANAGEMENT
# ─────────────────────────────────────────────
@superuser_required
def admin_users(request):
    role_filter = request.GET.get('role', '')
    search      = request.GET.get('q', '')
    users = User.objects.select_related('tutor_profile').order_by('-date_joined')
    if role_filter:
        users = users.filter(role=role_filter)
    if search:
        users = users.filter(Q(username__icontains=search) | Q(email__icontains=search) | Q(first_name__icontains=search))
    context = {'users': users, 'role_filter': role_filter, 'search': search}
    return render(request, 'admin_panel/users.html', context)


@superuser_required
def admin_user_detail(request, pk):
    user = get_object_or_404(User, pk=pk)
    bookings = []
    if user.role == 'student':
        bookings = Booking.objects.filter(student=user).select_related('tutor').order_by('-created_at')
    elif user.role == 'tutor':
        bookings = Booking.objects.filter(tutor=user).select_related('student').order_by('-created_at')
    payments = Payment.objects.filter(booking__in=bookings).order_by('-created_at')
    context = {'target_user': user, 'bookings': bookings, 'payments': payments}
    return render(request, 'admin_panel/user_detail.html', context)


@superuser_required
def admin_user_edit(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        user.first_name  = request.POST.get('first_name', user.first_name)
        user.last_name   = request.POST.get('last_name', user.last_name)
        user.email       = request.POST.get('email', user.email)
        user.phone       = request.POST.get('phone', user.phone)
        user.bio         = request.POST.get('bio', user.bio)
        user.is_active   = request.POST.get('is_active') == 'on'
        user.is_staff    = request.POST.get('is_staff') == 'on'
        user.save()
        messages.success(request, f'User {user.username} updated.')
        return redirect('admin-user-detail', pk=pk)
    return render(request, 'admin_panel/user_edit.html', {'target_user': user})


@superuser_required
def admin_user_toggle_active(request, pk):
    user = get_object_or_404(User, pk=pk)
    if user == request.user:
        messages.error(request, "You can't deactivate yourself.")
    else:
        user.is_active = not user.is_active
        user.save()
        state = 'activated' if user.is_active else 'deactivated'
        messages.success(request, f'User {user.username} {state}.')
    return redirect('admin-users')


@superuser_required
def admin_user_delete(request, pk):
    user = get_object_or_404(User, pk=pk)
    if user == request.user:
        messages.error(request, "You can't delete yourself.")
        return redirect('admin-users')
    if request.method == 'POST':
        username = user.username
        user.delete()
        messages.success(request, f'User {username} deleted.')
        return redirect('admin-users')
    return render(request, 'admin_panel/confirm_delete.html', {'obj': user, 'obj_type': 'User', 'cancel_url': '/admin-panel/users/'})


# ─────────────────────────────────────────────
#  BOOKING MANAGEMENT
# ─────────────────────────────────────────────
@superuser_required
def admin_bookings(request):
    status_filter = request.GET.get('status', '')
    search        = request.GET.get('q', '')
    bookings = Booking.objects.select_related('student', 'tutor', 'tutor__tutor_profile').order_by('-created_at')
    if status_filter:
        bookings = bookings.filter(status=status_filter)
    if search:
        bookings = bookings.filter(
            Q(student__username__icontains=search) | Q(tutor__username__icontains=search)
        )
    context = {'bookings': bookings, 'status_filter': status_filter, 'search': search,
               'STATUS_CHOICES': Booking.STATUS_CHOICES if hasattr(Booking, 'STATUS_CHOICES') else [
                   ('pending','Pending'), ('confirmed','Confirmed'), ('rejected','Rejected'), ('completed','Completed')
               ]}
    return render(request, 'admin_panel/bookings.html', context)


@superuser_required
def admin_booking_status(request, pk, new_status):
    booking = get_object_or_404(Booking, pk=pk)
    valid = ['pending', 'confirmed', 'rejected', 'completed']
    if new_status in valid:
        booking.status = new_status
        booking.save()
        messages.success(request, f'Booking #{pk} marked as {new_status}.')
    return redirect('admin-bookings')


@superuser_required
def admin_booking_delete(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    if request.method == 'POST':
        booking.delete()
        messages.success(request, f'Booking #{pk} deleted.')
        return redirect('admin-bookings')
    return render(request, 'admin_panel/confirm_delete.html', {
        'obj': booking, 'obj_type': 'Booking', 'cancel_url': '/admin-panel/bookings/'
    })


# ─────────────────────────────────────────────
#  TUTOR PROFILE MANAGEMENT
# ─────────────────────────────────────────────
@superuser_required
def admin_tutors(request):
    search = request.GET.get('q', '')
    profiles = TutorProfile.objects.select_related('user').order_by('-created_at')
    if search:
        profiles = profiles.filter(
            Q(user__username__icontains=search) | Q(subject__icontains=search)
        )
    context = {'profiles': profiles, 'search': search}
    return render(request, 'admin_panel/tutors.html', context)


@superuser_required
def admin_tutor_edit(request, pk):
    profile = get_object_or_404(TutorProfile, pk=pk)
    if request.method == 'POST':
        profile.subject      = request.POST.get('subject', profile.subject)
        profile.bio          = request.POST.get('bio', profile.bio)
        profile.monthly_rate = request.POST.get('monthly_rate', profile.monthly_rate)
        profile.rating       = request.POST.get('rating', profile.rating)
        profile.save()
        messages.success(request, f'Tutor profile for {profile.user.username} updated.')
        return redirect('admin-tutors')
    return render(request, 'admin_panel/tutor_edit.html', {'profile': profile})


@superuser_required
def admin_tutor_delete(request, pk):
    profile = get_object_or_404(TutorProfile, pk=pk)
    if request.method == 'POST':
        username = profile.user.username
        profile.delete()
        messages.success(request, f'Tutor profile for {username} deleted.')
        return redirect('admin-tutors')
    return render(request, 'admin_panel/confirm_delete.html', {
        'obj': profile, 'obj_type': 'Tutor Profile', 'cancel_url': '/admin-panel/tutors/'
    })


# ─────────────────────────────────────────────
#  REVIEW MANAGEMENT
# ─────────────────────────────────────────────
@superuser_required
def admin_reviews(request):
    rating_filter = request.GET.get('rating', '')
    reviews = Review.objects.select_related('booking__student', 'booking__tutor').order_by('-created_at')
    if rating_filter:
        reviews = reviews.filter(rating=rating_filter)
    context = {'reviews': reviews, 'rating_filter': rating_filter}
    return render(request, 'admin_panel/reviews.html', context)


@superuser_required
def admin_review_delete(request, pk):
    review = get_object_or_404(Review, pk=pk)
    if request.method == 'POST':
        review.delete()
        messages.success(request, f'Review #{pk} deleted.')
        return redirect('admin-reviews')
    return render(request, 'admin_panel/confirm_delete.html', {
        'obj': review, 'obj_type': 'Review', 'cancel_url': '/admin-panel/reviews/'
    })
