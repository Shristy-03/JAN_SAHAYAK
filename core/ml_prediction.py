from datetime import datetime, timedelta
from django.db.models import Count
from .models import Complaint


def predict_next_5_days(category):

    today = datetime.today()

    last_7_days = today - timedelta(days=7)

    data = (
        Complaint.objects
        .filter(problem__category=category, created_at__gte=last_7_days)
        .extra({'day': "date(created_at)"})
        .values('day')
        .annotate(total=Count('id'))
        .order_by('day')
    )

    daily_counts = []

    for i in data:
        daily_counts.append(i['total'])

    if len(daily_counts) == 0:
        avg = 0
    else:
        avg = sum(daily_counts) / len(daily_counts)

    predictions = []

    for i in range(1, 6):
        predictions.append(round(avg))

    return predictions