from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import User


def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('confirm_password')
        role = request.POST.get('role', 'student')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')

        if password != password_confirm:
            messages.error(request, 'Passwords do not match!')
            return redirect('register')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists!')
            return redirect('register')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists!')
            return redirect('register')

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            role=role,
            first_name=first_name,
            last_name=last_name
        )
        messages.success(request, 'Account created successfully! Please login.')
        return redirect('login')

    return render(request, 'accounts/register.html')


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password!')

    return render(request, 'accounts/login.html')


def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully!')
    return redirect('home')


@login_required(login_url='login')
def profile_view(request):
    return render(request, 'accounts/profile.html')


@login_required(login_url='login')
def edit_profile_view(request):
    user = request.user
    if request.method == 'POST':
        # Basic info
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name  = request.POST.get('last_name', user.last_name)
        user.email      = request.POST.get('email', user.email)
        user.phone      = request.POST.get('phone', user.phone or '')
        user.bio        = request.POST.get('bio', user.bio or '')

        # Avatar upload
        if request.FILES.get('avatar'):
            # Delete old avatar if exists
            if user.avatar:
                try:
                    import os
                    if os.path.isfile(user.avatar.path):
                        os.remove(user.avatar.path)
                except Exception:
                    pass
            user.avatar = request.FILES['avatar']

        user.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')

    return render(request, 'accounts/edit_profile.html')


@login_required(login_url='login')
def change_password_view(request):
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if not request.user.check_password(current_password):
            messages.error(request, 'Current password is incorrect.')
            return redirect('change_password')

        if new_password != confirm_password:
            messages.error(request, 'New passwords do not match.')
            return redirect('change_password')

        if len(new_password) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
            return redirect('change_password')

        request.user.set_password(new_password)
        request.user.save()
        update_session_auth_hash(request, request.user)  # Keep user logged in
        messages.success(request, 'Password changed successfully!')
        return redirect('profile')

    return render(request, 'accounts/change_password.html')


@login_required(login_url='login')
def notification_settings_view(request):
    # Placeholder — extend with a NotificationSettings model if needed
    if request.method == 'POST':
        messages.success(request, 'Notification preferences saved!')
        return redirect('notification_settings')
    return render(request, 'accounts/notification_settings.html')


@login_required(login_url='login')
def delete_account_view(request):
    if request.method == 'POST':
        password = request.POST.get('password')
        if not request.user.check_password(password):
            messages.error(request, 'Incorrect password. Account not deleted.')
            return redirect('delete_account')
        user = request.user
        logout(request)
        user.delete()
        messages.success(request, 'Your account has been permanently deleted.')
        return redirect('home')
    return render(request, 'accounts/delete_account.html')
