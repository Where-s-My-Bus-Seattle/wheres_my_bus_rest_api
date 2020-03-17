from django.urls import path
from .views import get_a_routes_closest_stop_and_arrival_time, show_me_the_request,send_email

urlpatterns=[
    path('v1/<lat>/<lon>/<bus_route>', get_a_routes_closest_stop_and_arrival_time, name='bus_data'),
    path('v1/<lat>/<lon>', show_me_the_request.as_view(), name='print'),
    path('v1/email', send_email, name='email')
]
