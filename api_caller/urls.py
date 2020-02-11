from django.urls import path
from .views import get_a_routes_closest_stop_and_arrival_time

urlpatterns=[
    path('v1/<lat>/<lon>/<bus_route>', get_a_routes_closest_stop_and_arrival_time, name='bus_data')
]
