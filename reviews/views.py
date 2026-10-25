from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Review
from .serializers import ReviewSerializer
from bookings.models import Booking

class ReviewCreateView(APIView):
    def post(self, request):
        if not request.user.is_authenticated:
            return Response({'error': 'Not authenticated'}, status=status.HTTP_401_UNAUTHORIZED)

        booking_id = request.data.get('booking')
        try:
            booking = Booking.objects.get(id=booking_id)
            if booking.student != request.user:
                return Response({'error': 'Only the student can review this booking'}, status=status.HTTP_403_FORBIDDEN)

            serializer = ReviewSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Booking.DoesNotExist:
            return Response({'error': 'Booking not found'}, status=status.HTTP_404_NOT_FOUND)

class ReviewListView(APIView):
    def get(self, request):
        reviews = Review.objects.all()
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class ReviewDetailView(APIView):
    def get(self, request, pk):
        try:
            review = Review.objects.get(pk=pk)
            serializer = ReviewSerializer(review)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Review.DoesNotExist:
            return Response({'error': 'Review not found'}, status=status.HTTP_404_NOT_FOUND)

@login_required(login_url='login')
def review_create_view(request):
    booking_id = request.GET.get('booking')
    booking = get_object_or_404(Booking, id=booking_id)

    # Check if user is the student
    if booking.student != request.user:
        messages.error(request, 'Only the student can review this booking!')
        return redirect('booking-list')

    # Check if review already exists
    if hasattr(booking, 'review'):
        messages.error(request, 'You have already reviewed this booking!')
        return redirect('booking-detail', pk=booking.id)

    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')

        Review.objects.create(
            booking=booking,
            rating=int(rating),
            comment=comment
        )

        # Update tutor rating
        tutor = booking.tutor
        reviews = Review.objects.filter(booking__tutor=tutor)
        if reviews.exists():
            avg_rating = sum(r.rating for r in reviews) / len(reviews)
            tutor.tutor_profile.rating = round(avg_rating, 1)
            tutor.tutor_profile.save()

        messages.success(request, 'Review submitted successfully!')
        return redirect('booking-detail', pk=booking.id)

    context = {
        'booking': booking,
        'tutor': booking.tutor,
    }
    return render(request, 'reviews/create.html', context)

def review_list_view(request):
    reviews = Review.objects.all().order_by('-created_at')
    context = {
        'reviews': reviews,
    }
    return render(request, 'reviews/list.html', context)

def review_detail_view(request, pk):
    review = get_object_or_404(Review, pk=pk)
    context = {
        'review': review,
    }
    return render(request, 'reviews/detail.html', context)
