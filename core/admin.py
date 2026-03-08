from django.contrib import admin
from .models import Problem, Scheme, Complaint,State,City

admin.site.register(Problem)
admin.site.register(Scheme)
admin.site.register(Complaint)
admin.site.register(State)
admin.site.register(City)
