from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Booking
from .serializers import BookingSerializer
from accounts.models import User
from tutors.models import TutorProfile, TutorSchedule
import json

@login_required(login_url='login')
def booking_list_view(request):
    if request.user.role == 'student':
        bookings = Booking.objects.filter(student=request.user)
    else:
        bookings = Booking.objects.filter(tutor=request.user)

    context = {
        'bookings': bookings,
    }
    return render(request, 'bookings/list.html', context)

@login_required(login_url='login')
def booking_detail_view(request, pk):
    booking = get_object_or_404(Booking, pk=pk)

    # Check if user has permission to view this booking
    if booking.student != request.user and booking.tutor != request.user:
        messages.error(request, 'You do not have permission to view this booking!')
        return redirect('booking-list')

    context = {
        'booking': booking,
    }
    return render(request, 'bookings/detail.html', context)

@login_required(login_url='login')
def booking_create_view(request):
    if request.user.role != 'student':
        messages.error(request, 'Only students can create bookings!')
        return redirect('home')

    tutors = User.objects.filter(
        role='tutor', is_active=True, is_superuser=False, is_staff=False,
        tutor_profile__isnull=False
    ).select_related('tutor_profile')
    tutor_id = request.GET.get('tutor_id') or request.GET.get('tutor')

    # Build {tutor_user_id: [available slot dicts]} for JS
    booked_slot_ids = set(
        Booking.objects.filter(
            status__in=['pending', 'confirmed'],
            schedule__isnull=False
        ).values_list('schedule_id', flat=True)
    )
    schedule_map = {}
    for slot in TutorSchedule.objects.select_related('tutor').all():
        uid = str(slot.tutor_id)
        if uid not in schedule_map:
            schedule_map[uid] = []
        if slot.id not in booked_slot_ids:
            schedule_map[uid].append({'id': slot.id, 'label': slot.display, 'months': slot.months})

    if request.method == 'POST':
        tutor_id_post = request.POST.get('tutor')
        date = request.POST.get('date') or timezone.now().date()
        months = int(request.POST.get('months', 1))
        schedule_id = request.POST.get('schedule')

        if months < 1:
            messages.error(request, 'Minimum booking duration is 1 month!')
            return render(request, 'bookings/create.html', {
                'tutors': tutors, 'selected_tutor_id': tutor_id_post,
                'schedule_map_json': json.dumps(schedule_map),
            })

        tutor = get_object_or_404(User, id=tutor_id_post, role='tutor')
        schedule_obj = None
        if schedule_id:
            try:
                schedule_obj = TutorSchedule.objects.get(pk=schedule_id, tutor=tutor)
            except TutorSchedule.DoesNotExist:
                pass

        booking = Booking.objects.create(
            student=request.user,
            tutor=tutor,
            date=date,
            months=months,
            schedule=schedule_obj,
            status='pending'
        )

        messages.success(request, 'Booking created successfully! Please proceed to payment.')
        return redirect(f'/payments/create/?booking_id={booking.id}')

    # Build {tutor_user_id: monthly_rate} for JS cost preview
    rate_map = {}
    for t in tutors:
        if hasattr(t, 'tutor_profile') and t.tutor_profile:
            rate_map[str(t.id)] = float(t.tutor_profile.monthly_rate)

    context = {
        'tutors': tutors,
        'selected_tutor_id': tutor_id,
        'schedule_map_json': json.dumps(schedule_map),
        'tutor_rates_json': json.dumps(rate_map),
    }
    return render(request, 'bookings/create.html', context)

@login_required(login_url='login')
def booking_confirm_view(request, pk):
    booking = get_object_or_404(Booking, pk=pk)

    if booking.tutor != request.user:
        messages.error(request, 'Only the assigned tutor can confirm this booking!')
        return redirect('booking-list')

    booking.status = 'confirmed'
    booking.save()
    messages.success(request, 'Booking confirmed successfully!')
    return redirect('booking-detail', pk=pk)

@login_required(login_url='login')
def booking_reject_view(request, pk):
    booking = get_object_or_404(Booking, pk=pk)

    if booking.tutor != request.user:
        messages.error(request, 'Only the assigned tutor can reject this booking!')
        return redirect('booking-list')

    booking.status = 'rejected'
    booking.save()
    messages.success(request, 'Booking rejected!')
    return redirect('booking-list')


@login_required(login_url='login')
def booking_complete_view(request, pk):
    """Tutor OR student marks the booking as completed — enables student to leave a review."""
    booking = get_object_or_404(Booking, pk=pk)

    # Both tutor and student can mark as completed
    if booking.tutor != request.user and booking.student != request.user:
        messages.error(request, 'You do not have permission to complete this booking!')
        return redirect('booking-list')

    if booking.status != 'confirmed':
        messages.error(request, 'Only confirmed bookings can be marked as completed.')
        return redirect('booking-detail', pk=pk)

    # ── Duration check ─────────────────────────────────────────────────────
    # Calculate end date: start date + booked months
    end_date = booking.date + relativedelta(months=booking.months)
    today = timezone.now().date()

    if today < end_date:
        remaining = (end_date.year - today.year) * 12 + (end_date.month - today.month)
        if end_date.day > today.day:
            pass  # same partial month, already counted
        messages.warning(
            request,
            f'You can give a review after completing the course. '
            f'Course ends on {end_date.strftime("%B %d, %Y")} '
            f'({remaining} month(s) remaining).'
        )
        return redirect('booking-detail', pk=pk)
    # ───────────────────────────────────────────────────────────────────────

    booking.status = 'completed'
    booking.save()
    messages.success(request, 'Booking marked as completed! You can now leave a review.')
    return redirect('booking-detail', pk=pk)

@login_required(login_url='login')
def booking_cancel_view(request, pk):
    booking = get_object_or_404(Booking, pk=pk)

    if booking.student != request.user:
        messages.error(request, 'Only the student can cancel this booking!')
        return redirect('booking-list')

    if booking.payments.exists():
        messages.error(request, 'Cannot cancel a booking that already has a payment.')
        return redirect('booking-detail', pk=pk)

    if booking.status in ('completed', 'cancelled'):
        messages.error(request, 'This booking cannot be cancelled.')
        return redirect('booking-detail', pk=pk)

    booking.status = 'cancelled'
    booking.save()
    messages.success(request, 'Booking cancelled successfully.')
    return redirect('booking-list')

@login_required(login_url='login')
def booking_tutor_update_view(request, pk):
    """Tutor sets meet link and sends message to student."""
    booking = get_object_or_404(Booking, pk=pk)

    if booking.tutor != request.user:
        messages.error(request, 'Only the assigned tutor can update this booking!')
        return redirect('booking-list')

    if request.method == 'POST':
        meet_link = request.POST.get('meet_link', '').strip()
        tutor_message = request.POST.get('tutor_message', '').strip()
        booking.meet_link = meet_link
        booking.tutor_message = tutor_message
        booking.save()
        messages.success(request, 'Meet link and message sent to student successfully!')

    return redirect('booking-detail', pk=pk)

class BookingListView(APIView):
    def get(self, request):
        if request.user.is_authenticated:
            if request.user.role == 'student':
                bookings = Booking.objects.filter(student=request.user)
            else:  # tutor
                bookings = Booking.objects.filter(tutor=request.user)
            serializer = BookingSerializer(bookings, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response({'error': 'Not authenticated'}, status=status.HTTP_401_UNAUTHORIZED)

class BookingCreateView(APIView):
    def post(self, request):
        if not request.user.is_authenticated or request.user.role != 'student':
            return Response({'error': 'Only students can create bookings'}, status=status.HTTP_403_FORBIDDEN)

        serializer = BookingSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(student=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class BookingUpdateView(APIView):
    def patch(self, request, pk):
        try:
            booking = Booking.objects.get(pk=pk)

            if request.user == booking.tutor:
                serializer = BookingSerializer(booking, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response(serializer.data, status=status.HTTP_200_OK)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            return Response({'error': 'Only the assigned tutor can update this booking'}, status=status.HTTP_403_FORBIDDEN)
        except Booking.DoesNotExist:
            return Response({'error': 'Booking not found'}, status=status.HTTP_404_NOT_FOUND)
