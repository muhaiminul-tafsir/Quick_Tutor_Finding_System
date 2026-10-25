from django.urls import path
from . import views

urlpatterns = [
    path('', views.review_list_view, name='review-list'),
    path('<int:pk>/', views.review_detail_view, name='review-detail'),
    path('create/', views.review_create_view, name='review-create'),
]
