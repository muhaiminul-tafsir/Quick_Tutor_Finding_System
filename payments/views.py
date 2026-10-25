from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Payment
from bookings.models import Booking


@login_required(login_url='login')
def payment_create_view(request):
    booking_id = request.GET.get('booking_id')
    booking = get_object_or_404(Booking, id=booking_id)

    if booking.student != request.user:
        messages.error(request, 'You do not have permission to pay for this booking!')
        return redirect('booking-list')

    if booking.is_fully_paid:
        messages.info(request, 'This booking is fully paid!')
        return redirect('booking-detail', pk=booking.id)

    try:
        monthly_rate = booking.tutor.tutor_profile.monthly_rate
    except Exception:
        monthly_rate = 4000

    total_amount = booking.total_amount
    total_paid   = float(booking.total_paid)
    balance_due  = booking.balance_due

    # first_month_covered = first month already fully paid and approved
    first_month_covered = booking.payments.filter(status='approved').exists()

    # For model field tracking: is this the very first payment transaction submitted?
    is_first_transaction = not booking.payments.exists()

    # Block new submission if a pending payment already exists
    pending_payment = booking.payments.filter(status='pending').first()

    # Commission preview values for template
    if not first_month_covered:
        preview_first_commission = round(float(monthly_rate) * 0.50, 2)
        preview_excess_rate = 10
        preview_note = f"50% on first ৳{monthly_rate}, then 10% on the rest"
    else:
        preview_first_commission = None
        preview_excess_rate = 10
        preview_note = "10% platform charge on full amount"

    if request.method == 'POST':
        # Block if a pending payment already exists
        if pending_payment:
            messages.error(request, 'You already have a pending payment awaiting review. Please wait for admin approval before submitting another.')
            return redirect('booking-detail', pk=booking.id)

        payment_method = request.POST.get('payment_method', 'bkash')
        sender_number  = request.POST.get('sender_number', '').strip()
        transaction_id = request.POST.get('transaction_id', '').strip()
        amount_str     = request.POST.get('amount', '').strip()

        if not sender_number or not transaction_id:
            messages.error(request, 'Please provide your sender number and transaction ID.')
        elif not amount_str:
            messages.error(request, 'Please enter the payment amount.')
        else:
            try:
                amount = float(amount_str)
                if amount <= 0:
                    raise ValueError
            except ValueError:
                messages.error(request, 'Invalid amount.')
                amount = None

            if amount:
                if amount > balance_due + 1:
                    messages.error(request, f'Amount exceeds balance due (৳{balance_due}).')
                else:
                    commission, tutor_income = Payment.calculate_commission(
                        amount, monthly_rate, first_month_covered
                    )
                    Payment.objects.create(
                        booking=booking,
                        amount=amount,
                        commission=commission,
                        tutor_income=tutor_income,
                        is_first_payment=is_first_transaction,
                        payment_method=payment_method,
                        sender_number=sender_number,
                        transaction_id=transaction_id,
                        status='pending',
                    )
                    messages.success(request, f'Payment of ৳{amount} submitted! Admin will review shortly.')
                    return redirect('booking-detail', pk=booking.id)

    all_payments = booking.payments.order_by('created_at')

    context = {
        'booking':                booking,
        'total_amount':           total_amount,
        'total_paid':             total_paid,
        'balance_due':            balance_due,
        'monthly_rate':           monthly_rate,
        'first_month_covered':    first_month_covered,
        'is_first_payment':       is_first_transaction,   # kept for JS
        'pending_payment':        pending_payment,
        'preview_first_commission': preview_first_commission,
        'preview_note':           preview_note,
        'payment_methods':        Payment.METHOD_CHOICES,
        'all_payments':           all_payments,
    }
    return render(request, 'payments/create.html', context)


@login_required(login_url='login')
def payment_list_view(request):
    if request.user.role == 'student':
        bookings = (
            request.user.student_bookings
            .prefetch_related('payments', 'tutor__tutor_profile')
            .order_by('-created_at')
        )
    else:
        bookings = (
            request.user.tutor_bookings
            .prefetch_related('payments', 'student')
            .order_by('-created_at')
        )

    booking_groups = []
    for booking in bookings:
        try:
            monthly_rate = booking.tutor.tutor_profile.monthly_rate
        except Exception:
            monthly_rate = 4000
        total_amount = float(monthly_rate) * booking.months
        payments = list(booking.payments.order_by('created_at'))
        has_pending = any(p.status == 'pending' for p in payments)
        booking_groups.append({
            'booking': booking,
            'payments': payments,
            'monthly_rate': monthly_rate,
            'total_amount': total_amount,
            'has_pending': has_pending,
        })

    return render(request, 'payments/list.html', {'booking_groups': booking_groups})


@login_required(login_url='login')
def payment_detail_view(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    if (payment.booking.student != request.user
            and payment.booking.tutor != request.user
            and not request.user.is_superuser):
        messages.error(request, 'You do not have permission to view this payment!')
        return redirect('payment-list')
    return render(request, 'payments/detail.html', {'payment': payment})


@login_required(login_url='login')
def admin_approve_payment(request, pk):
    if not request.user.is_superuser and not request.user.is_staff:
        return redirect('home')
    payment = get_object_or_404(Payment, pk=pk)
    payment.status = 'approved'
    payment.save()
    messages.success(request, f'Payment #{payment.id} approved!')
    return redirect('payment-admin')


@login_required(login_url='login')
def admin_reject_payment(request, pk):
    if not request.user.is_superuser and not request.user.is_staff:
        return redirect('home')
    payment = get_object_or_404(Payment, pk=pk)
    payment.status = 'rejected'
    payment.save()
    messages.success(request, f'Payment #{payment.id} rejected.')
    return redirect('payment-admin')


@login_required(login_url='login')
def payment_admin_view(request):
    if not request.user.is_superuser and not request.user.is_staff:
        messages.error(request, 'Access denied.')
        return redirect('home')

    status_filter = request.GET.get('status', '')
    payments = Payment.objects.all().select_related(
        'booking__student', 'booking__tutor', 'booking__tutor__tutor_profile'
    ).order_by('-created_at')
    if status_filter:
        payments = payments.filter(status=status_filter)

    from django.db.models import Sum
    import json

    total_revenue    = Payment.objects.filter(status='approved').aggregate(s=Sum('amount'))['s'] or 0
    total_commission = Payment.objects.filter(status='approved').aggregate(s=Sum('commission'))['s'] or 0
    total_tutor_pay  = Payment.objects.filter(status='approved').aggregate(s=Sum('tutor_income'))['s'] or 0

    stats = {
        'total':            Payment.objects.count(),
        'pending':          Payment.objects.filter(status='pending').count(),
        'approved':         Payment.objects.filter(status='approved').count(),
        'rejected':         Payment.objects.filter(status='rejected').count(),
        'total_amount':     total_revenue,
        'total_commission': total_commission,
        'total_tutor_pay':  total_tutor_pay,
    }

    # Monthly chart: last 6 months
    from datetime import date
    try:
        from dateutil.relativedelta import relativedelta
        chart_labels = []
        chart_revenue = []
        chart_commission = []
        chart_tutor = []
        for i in range(5, -1, -1):
            ms = date.today().replace(day=1) - relativedelta(months=i)
            me = ms + relativedelta(months=1)
            label = ms.strftime('%b %Y')
            rev  = Payment.objects.filter(status='approved', created_at__date__gte=ms, created_at__date__lt=me).aggregate(s=Sum('amount'))['s'] or 0
            comm = Payment.objects.filter(status='approved', created_at__date__gte=ms, created_at__date__lt=me).aggregate(s=Sum('commission'))['s'] or 0
            tut  = Payment.objects.filter(status='approved', created_at__date__gte=ms, created_at__date__lt=me).aggregate(s=Sum('tutor_income'))['s'] or 0
            chart_labels.append(label)
            chart_revenue.append(float(rev))
            chart_commission.append(float(comm))
            chart_tutor.append(float(tut))
    except ImportError:
        chart_labels = chart_revenue = chart_commission = chart_tutor = []

    method_data = {}
    for m_val, m_label in Payment.METHOD_CHOICES:
        count = Payment.objects.filter(payment_method=m_val, status='approved').count()
        if count:
            method_data[m_label] = count

    # ── Detailed commission breakdown ────────────────────────────────────────
    # Iterate approved payments to compute the correct broker vs platform split
    approved_payments = Payment.objects.filter(status='approved').select_related(
        'booking__tutor__tutor_profile'
    )

    total_first_month_commission = 0.0   # 50% on first ৳monthly_rate only
    total_broker_commission      = 0.0   # 40% of first month
    total_platform_commission    = 0.0   # 10% on everything (all months, all payments)
    total_recurring_commission   = 0.0   # 10% on months 2+ across all payments

    for p in approved_payments:
        try:
            mr = float(p.booking.tutor.tutor_profile.monthly_rate)
        except Exception:
            mr = 4000.0
        amt = float(p.amount)

        if p.is_first_payment:
            first_portion = min(amt, mr)
            excess        = max(0, amt - mr)
            fm_comm       = round(first_portion * 0.50, 2)
            ex_comm       = round(excess * 0.10, 2)
            total_first_month_commission += fm_comm
            total_broker_commission      += round(first_portion * 0.40, 2)
            total_platform_commission    += round(first_portion * 0.10, 2) + ex_comm
            total_recurring_commission   += ex_comm
        else:
            comm = round(amt * 0.10, 2)
            total_platform_commission  += comm
            total_recurring_commission += comm

    total_broker_commission      = round(total_broker_commission, 2)
    total_platform_commission    = round(total_platform_commission, 2)
    total_first_month_commission = round(total_first_month_commission, 2)
    total_recurring_commission   = round(total_recurring_commission, 2)

    context = {
        'payments': payments,
        'stats': stats,
        'status_filter': status_filter,
        'chart_labels':     json.dumps(chart_labels),
        'chart_revenue':    json.dumps(chart_revenue),
        'chart_commission': json.dumps(chart_commission),
        'chart_tutor':      json.dumps(chart_tutor),
        'method_labels':    json.dumps(list(method_data.keys())),
        'method_counts':    json.dumps(list(method_data.values())),
        # Breakdown stats
        'first_month_commission': total_first_month_commission,
        'recurring_commission':   total_recurring_commission,
        'broker_commission':      total_broker_commission,
        'platform_commission':    total_platform_commission,
        'filter_tabs': [
            ('', 'All', '#3525cd'),
            ('pending', 'Pending', '#d97706'),
            ('approved', 'Approved', '#16a34a'),
            ('rejected', 'Rejected', '#dc2626'),
        ],
    }
    return render(request, 'payments/admin.html', context)
