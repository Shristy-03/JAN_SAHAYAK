from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import RegisterForm, ComplaintForm
from .models import Scheme, Complaint
from django.db.models import Count
from django.contrib.auth.models import User
from .models import Complaint
from django.http import JsonResponse
from .models import City
from datetime import datetime, timedelta
from .ml_prediction import predict_next_5_days
from django.utils import timezone
from datetime import timedelta
from  google import genai
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import random
import json

# from .ml_model import predict_status

# def prediction_view(request):

#     result = None

#     if request.method == 'POST':
#         area = request.POST.get('area')
#         category = request.POST.get('category')

#         result = predict_status(area, category)

#     return render(request, 'prediction.html', {'result': result})

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
            action = request.POST.get("action")
            complaint = form.save(commit=False)
            complaint.user = request.user

            if action == "submit":
                complaint.save()
                return redirect('dashboard')

            elif action == "solution":
                category = complaint.problem.category
                return redirect(f'/solution/?category={category}')

    else:
        form = ComplaintForm()

    return render(request, 'complaint.html', {'form': form})

@login_required
def schemes_view(request):
    schemes = Scheme.objects.all()
    return render(request, 'schemes.html', {'schemes': schemes})


# @login_required
# def prediction_dashboard(request):

#     if not request.user.is_superuser:
#         return redirect('dashboard')

#     categories = ['Water', 'Electricity', 'Job', 'Health']

#     return render(request, 'prediction.html', {'categories': categories})
#     return render(request, 'prediction.html', {'data': data})


def logout_view(request):
    logout(request)
    return redirect('index')

@login_required
def status_view(request):
    complaints = Complaint.objects.filter(user=request.user)
    return render(request, 'status.html', {'complaints': complaints})

@login_required
def solution_view(request):
    category = request.GET.get('category')

    schemes = Scheme.objects.filter(category=category)

    return render(request, 'solution.html', {
        'schemes': schemes,
        'category': category
    })

def admin_dashboard(request):
    context = {
        'total_users': User.objects.count(),
        'total_complaints': Complaint.objects.count(),
        'pending_complaints': Complaint.objects.filter(status='Pending').count(),
    }
    return render(request, 'admin_dashboard.html', context)

def load_cities(request):
    state_id = request.GET.get('state_id')
    cities = City.objects.filter(state_id=state_id).values('id', 'name')
    return JsonResponse(list(cities), safe=False)

def get_prediction_data(request):

    category = request.GET.get("category")

    state_data = (
        Complaint.objects.filter(problem__category=category)
        .values('state__name')
        .annotate(total=Count('id'))
    )

    city_data = (
        Complaint.objects.filter(problem__category=category)
        .values('city__name')
        .annotate(total=Count('id'))
    )

    states = []
    state_totals = []

    for i in state_data:
        states.append(i['state__name'])
        state_totals.append(i['total'])

    cities = []
    city_totals = []

    for i in city_data:
        cities.append(i['city__name'])
        city_totals.append(i['total'])

    # next 5 days prediction
    days = []
    predictions = []

    for i in range(5):
        day = (datetime.now() + timedelta(days=i)).strftime("%d %b")
        days.append(day)
        predictions.append(random.randint(5,20))

    return JsonResponse({
        "states": states,
        "state_totals": state_totals,
        "cities": cities,
        "city_totals": city_totals,
        "days": days,
        "predictions": predictions
    })

def get_city_complaints(request):

    city = request.GET.get("city")
    category = request.GET.get("category")

    complaints = Complaint.objects.filter(
        city__name=city,
        problem__category=category
    )

    data = []

    for c in complaints:
        data.append({
            "id": c.id,
            "area": c.area,
            "pincode": c.pincode,
            "status": c.status,
            "date": c.created_at.strftime("%d-%m-%Y")
        })

    return JsonResponse(data, safe=False)

def get_alert():

    data = Complaint.objects.values(
        'state__name','city__name','area'
    ).annotate(total=Count('id')).filter(total__gt=10)

    alerts = []

    for i in data:

        alerts.append(
        f"{i['state__name']} - {i['city__name']} - {i['area']} needs attention!"
        )

    return alerts

from django.db.models import Count

@login_required
def prediction_dashboard(request):

    if not request.user.is_superuser:
        return redirect('dashboard')

    category = request.GET.get('category')
    predictions = []
    if category:
        predictions = predict_next_5_days(category)

    alerts = check_alerts()

    context = {
        'category': category,
        'predictions': predictions,
        'alerts': alerts
    }

    return render(request, 'prediction.html', context)

def check_alerts():

    last_24_hours = datetime.now() - timedelta(hours=24)

    data = (
        Complaint.objects
        .filter(created_at__gte=last_24_hours)
        .values('problem__category')
        .annotate(count=Count('id'))
    )

    alerts = []

    threshold = 2   
    for item in data:
        if item['count'] >= threshold:
            alerts.append({
                "category": item['problem__category'],
                "count": item['count']
            })

    return alerts

client = genai.Client(api_key=settings.GEMINI_API_KEY)


def chatbot_reply(message):

    msg = message.lower()

    if "road" in msg or "gaddha" in msg:
        return "Ye road department ki complaint lag rahi hai."

    elif "water" in msg or "pani" in msg:
        return "Ye water supply issue hai."

    elif "light" in msg or "electricity" in msg:
        return "Ye electricity department se related complaint hai."

    # complaint kaise kare
    elif "complaint" in msg or "complain" in msg:
        return "Complaint karne ke liye Dashboard par jaake 'Complaint' button par click kare aur form submit kare."

    # complaint status
    elif "status" in msg:
        return "Complaint status check karne ke liye Dashboard me 'My Complaints' section open kare."

    # schemes
    elif "scheme" in msg or "yojana" in msg:
        return "Abhi available schemes: Jal Jeevan Mission, Ujjwala Yojana, Saubhagya Yojana, Ayushman Bharat. Aap Schemes Section mei ja kr uplabdh yojanaaye dekh skte hai."

    # greeting
    elif "hello" in msg or "hi" in msg:
        return "Namaste! Mai Jan Sahayak AI assistant hoon. Mai aapki kya madad kar sakta hoon."

    # road complaint
    elif "road" in msg or "pothole" in msg:
        return "Ye road complaint lag rahi hai. Aap Complaint page par jaake 'Road Issue' select karke complaint submit kar sakte hain."

    # water complaint
    elif "water" in msg or "pani" in msg:
        return "Ye water supply issue ho sakta hai. Complaint page par jaake 'Water Department' select kare."

    # electricity complaint
    elif "light" in msg or "electricity" in msg:
        return "Electricity problem ke liye Complaint page par jaake 'Electricity Department' select kare."

    else:
        return "Kripya apni complaint detail me bataye."

@csrf_exempt
def chatbot_api(request):

    if request.method == "POST":
        data = json.loads(request.body)
        message = data.get("message")

        reply = chatbot_reply(message)

        return JsonResponse({
            "reply": reply
        })