from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import TutorProfile, TutorSchedule
from .serializers import TutorProfileSerializer
from accounts.models import User

def tutor_list_view(request):
    search = request.GET.get('search', '')
    subject = request.GET.get('subject', '')
    rating = request.GET.get('rating', '')

    tutors = User.objects.filter(
        role='tutor', is_active=True, is_superuser=False, is_staff=False,
        tutor_profile__isnull=False
    ).select_related('tutor_profile').order_by('-tutor_profile__rating')

    if search:
        tutors = tutors.filter(
            username__icontains=search
        ) | User.objects.filter(
            role='tutor', is_active=True,
            tutor_profile__subject__icontains=search
        ).select_related('tutor_profile')

    if subject:
        tutors = tutors.filter(tutor_profile__subject__icontains=subject)

    if rating:
        tutors = tutors.filter(tutor_profile__rating__gte=float(rating))

    context = {
        'tutors': tutors,
        'search': search,
        'subject': subject,
        'rating': rating,
    }
    return render(request, 'tutors/list.html', context)

def tutor_detail_view(request, pk):
    profile = get_object_or_404(TutorProfile.objects.select_related('user'), user_id=pk)
    tutor = profile.user  # Template expects a User object
    reviews = tutor.tutor_bookings.filter(review__isnull=False).select_related('review')

    context = {
        'tutor': tutor,
        'reviews': [booking.review for booking in reviews if hasattr(booking, 'review')],
    }
    return render(request, 'tutors/detail.html', context)

@login_required(login_url='login')
def tutor_create_profile_view(request):
    if request.user.role != 'tutor':
        messages.error(request, 'Only tutors can create a profile!')
        return redirect('home')

    # Check if tutor profile already exists
    try:
        tutor_profile = request.user.tutor_profile
        messages.info(request, 'You already have a tutor profile. Redirecting to edit.')
        return redirect('edit-profile')
    except TutorProfile.DoesNotExist:
        pass

    if request.method == 'POST':
        subject = request.POST.get('subject')
        bio = request.POST.get('bio')
        monthly_rate = request.POST.get('monthly_rate', 4000)

        tutor_profile = TutorProfile.objects.create(
            user=request.user,
            subject=subject,
            bio=bio,
            monthly_rate=monthly_rate,
            rating=0
        )

        messages.success(request, 'Tutor profile created successfully!')
        return redirect('profile')

    context = {}
    return render(request, 'tutors/edit.html', context)

@login_required(login_url='login')
def tutor_edit_profile_view(request):
    if request.user.role != 'tutor':
        messages.error(request, 'Only tutors can access this page!')
        return redirect('home')

    # Try to get existing tutor profile, or create a new one
    tutor_profile, created = TutorProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        subject = request.POST.get('subject')
        bio = request.POST.get('bio')
        monthly_rate = request.POST.get('monthly_rate', 4000)

        tutor_profile.subject = subject
        tutor_profile.bio = bio
        tutor_profile.monthly_rate = monthly_rate
        tutor_profile.save()

        if created:
            messages.success(request, 'Tutor profile created successfully!')
        else:
            messages.success(request, 'Tutor profile updated successfully!')
        return redirect('profile')

    context = {
        'tutor_profile': tutor_profile,
        'is_new': created,
        'schedules': request.user.schedules.all() if request.user.role == 'tutor' else [],
    }
    return render(request, 'tutors/edit.html', context)


@login_required(login_url='login')
def schedule_add_view(request):
    if request.user.role != 'tutor':
        messages.error(request, 'Only tutors can manage schedules.')
        return redirect('home')
    if request.method == 'POST':
        days   = request.POST.getlist('days')
        time   = request.POST.get('time')
        months = int(request.POST.get('months', 1) or 1)
        if months < 1:
            months = 1
        if days and time:
            days_str = ",".join(days)
            TutorSchedule.objects.get_or_create(
                tutor=request.user, days=days_str, time=time,
                defaults={'months': months}
            )
            messages.success(request, 'Schedule slot added.')
        else:
            messages.error(request, 'Please select at least one day and a time.')
    return redirect('edit-profile')


@login_required(login_url='login')
def schedule_delete_view(request, pk):
    slot = get_object_or_404(TutorSchedule, pk=pk, tutor=request.user)
    slot.delete()
    messages.success(request, 'Schedule slot removed.')
    return redirect('edit-profile')

class TutorListView(APIView):
    def get(self, request):
        tutors = TutorProfile.objects.all()
        serializer = TutorProfileSerializer(tutors, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class TutorDetailView(APIView):
    def get(self, request, pk):
        try:
            tutor = TutorProfile.objects.get(pk=pk)
            serializer = TutorProfileSerializer(tutor)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except TutorProfile.DoesNotExist:
            return Response({'error': 'Tutor not found'}, status=status.HTTP_404_NOT_FOUND)

class TutorCreateView(APIView):
    def post(self, request):
        if not request.user.is_authenticated or request.user.role != 'tutor':
            return Response({'error': 'Only tutors can create a profile'}, status=status.HTTP_403_FORBIDDEN)

        serializer = TutorProfileSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
