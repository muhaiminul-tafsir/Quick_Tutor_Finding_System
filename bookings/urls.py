from django.urls import path
from . import views

urlpatterns = [
    path('', views.booking_list_view, name='booking-list'),
    path('<int:pk>/', views.booking_detail_view, name='booking-detail'),
    path('create/', views.booking_create_view, name='booking-create'),
    path('<int:pk>/confirm/', views.booking_confirm_view, name='booking-confirm'),
    path('<int:pk>/reject/', views.booking_reject_view, name='booking-reject'),
    path('<int:pk>/cancel/', views.booking_cancel_view, name='booking-cancel'),
    path('<int:pk>/complete/', views.booking_complete_view, name='booking-complete'),
    path('<int:pk>/tutor-update/', views.booking_tutor_update_view, name='booking-tutor-update'),
]
