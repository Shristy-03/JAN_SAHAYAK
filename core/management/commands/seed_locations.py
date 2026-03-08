from django.core.management.base import BaseCommand
from core.models import State, City

class Command(BaseCommand):
    help = "Seed Indian states and cities"

    def handle(self, *args, **kwargs):

        data = {
            "Uttar Pradesh": ["Lucknow", "Kanpur", "Noida", "Varanasi"],
            "Maharashtra": ["Mumbai", "Pune", "Nagpur", "Nashik"],
            "Delhi": ["New Delhi"],
            "Karnataka": ["Bengaluru", "Mysuru", "Mangalore"],
            "Tamil Nadu": ["Chennai", "Coimbatore", "Madurai"],
            "Bihar": ["Patna", "Gaya"],
            "Rajasthan": ["Jaipur", "Udaipur", "Jodhpur"],
            "Madhya Pradesh": ["Bhopal", "Indore"],
            "Gujarat": ["Ahmedabad", "Surat", "Vadodara"],
            "West Bengal": ["Kolkata", "Siliguri"],
            "Haryana": ["Gurgaon", "Faridabad"],
            "Punjab": ["Chandigarh", "Ludhiana"],
            "Odisha": ["Bhubaneswar", "Cuttack"],
            "Kerala": ["Kochi", "Thiruvananthapuram"],
            "Assam": ["Guwahati"],
        }

        for state_name, cities in data.items():
            state, created = State.objects.get_or_create(name=state_name)

            for city_name in cities:
                City.objects.get_or_create(name=city_name, state=state)

        self.stdout.write(self.style.SUCCESS("Successfully seeded states and cities!"))