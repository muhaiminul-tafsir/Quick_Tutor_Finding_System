from django.urls import path
from . import views

urlpatterns = [
    path('', views.tutor_list_view, name='tutor-list'),
    path('<int:pk>/', views.tutor_detail_view, name='tutor-detail'),
    path('create-profile/', views.tutor_create_profile_view, name='tutor-create-profile'),
    path('edit-profile/', views.tutor_edit_profile_view, name='edit-profile'),
    path('schedule/add/', views.schedule_add_view, name='schedule-add'),
    path('schedule/<int:pk>/delete/', views.schedule_delete_view, name='schedule-delete'),
]
