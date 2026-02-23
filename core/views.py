from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import RegisterForm, ComplaintForm
from .models import Scheme, Complaint
from django.db.models import Count
import json


def index(request):
    return render(request, 'index.html')


def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Registration successful!")
            return redirect('login')
    else:
        form = RegisterForm()

    return render(request, 'register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid credentials")

    return render(request, 'login.html')


@login_required
def dashboard(request):
    complaints = Complaint.objects.filter(user=request.user)

    # Only current user's category wise count
    category_data = (
        Complaint.objects
        .filter(user=request.user)
        .values('problem__category')
        .annotate(total=Count('id'))
    )

    labels = [item['problem__category'] for item in category_data]
    data = [item['total'] for item in category_data]

    context = {
        'complaints': complaints,
        'labels': json.dumps(labels),   # 🔥 VERY IMPORTANT
        'data': json.dumps(data),       # 🔥 VERY IMPORTANT
    }

    return render(request, 'dashboard.html', context)

@login_required
def complaint_view(request):
    if request.method == 'POST':
        form = ComplaintForm(request.POST)
        if form.is_valid():
            complaint = form.save(commit=False)
            complaint.user = request.user
            complaint.save()
            return redirect('dashboard')
    else:
        form = ComplaintForm()

    return render(request, 'complaint.html', {'form': form})


@login_required
def schemes_view(request):
    schemes = Scheme.objects.all()
    return render(request, 'schemes.html', {'schemes': schemes})


@login_required
def prediction_view(request):
    data = Complaint.objects.values('area') \
        .annotate(total=Count('id')) \
        .order_by('-total')

    return render(request, 'prediction.html', {'data': data})


def logout_view(request):
    logout(request)
    return redirect('index')
