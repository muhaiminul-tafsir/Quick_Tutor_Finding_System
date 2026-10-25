from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from .views import home, dashboard_view
from .admin_views import (
    admin_users, admin_user_detail, admin_user_edit,
    admin_user_toggle_active, admin_user_delete,
    admin_bookings, admin_booking_status, admin_booking_delete,
    admin_tutors, admin_tutor_edit, admin_tutor_delete,
    admin_reviews, admin_review_delete,
)

urlpatterns = [
    path('', home, name='home'),
    path('dashboard/', dashboard_view, name='dashboard'),
    # Django admin DISABLED — replaced by custom panel
    # path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('tutors/', include('tutors.urls')),
    path('bookings/', include('bookings.urls')),
    path('reviews/', include('reviews.urls')),
    path('payments/', include('payments.urls')),

    # ── Custom Admin Panel ──────────────────────────────
    # Overview is served at /dashboard/ for admins (see quick_tutor/views.py)
    # path('admin-panel/', admin_overview, name='admin-overview'),
    path('admin-panel/users/',       admin_users,               name='admin-users'),
    path('admin-panel/users/<int:pk>/',        admin_user_detail,         name='admin-user-detail'),
    path('admin-panel/users/<int:pk>/edit/',   admin_user_edit,           name='admin-user-edit'),
    path('admin-panel/users/<int:pk>/toggle/', admin_user_toggle_active,  name='admin-user-toggle'),
    path('admin-panel/users/<int:pk>/delete/', admin_user_delete,         name='admin-user-delete'),
    path('admin-panel/bookings/',              admin_bookings,            name='admin-bookings'),
    path('admin-panel/bookings/<int:pk>/status/<str:new_status>/', admin_booking_status, name='admin-booking-status'),
    path('admin-panel/bookings/<int:pk>/delete/', admin_booking_delete,   name='admin-booking-delete'),
    path('admin-panel/tutors/',                admin_tutors,              name='admin-tutors'),
    path('admin-panel/tutors/<int:pk>/edit/',  admin_tutor_edit,          name='admin-tutor-edit'),
    path('admin-panel/tutors/<int:pk>/delete/',admin_tutor_delete,        name='admin-tutor-delete'),
    path('admin-panel/reviews/',               admin_reviews,             name='admin-reviews'),
    path('admin-panel/reviews/<int:pk>/delete/', admin_review_delete,     name='admin-review-delete'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
