from django.urls import path
from . import views

urlpatterns = [
    path('', views.payment_list_view, name='payment-list'),
    path('<int:pk>/', views.payment_detail_view, name='payment-detail'),
    path('create/', views.payment_create_view, name='payment-create'),
    path('manage/', views.payment_admin_view, name='payment-admin'),
    path('approve/<int:pk>/', views.admin_approve_payment, name='admin_approve_payment'),
    path('reject/<int:pk>/', views.admin_reject_payment, name='admin_reject_payment'),
]
