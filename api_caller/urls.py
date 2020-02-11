from django.urls import path
from .views import find_closest_stops

urlpatterns=[
    path('v1/<lat>/<lon>/<bus_route>', find_closest_stops, name='bus_data')
]
