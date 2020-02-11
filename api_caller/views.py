from django.shortcuts import render
from django.http import HttpResponse
import requests
import time
import json

with open('bus_routes/finalRoutesAndIds.json') as all_routes:
    route_data = json.load(all_routes)

alphabet = ['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z']
special_cases = ['link', 'sounder south','amtrak','sounder north','tlink','swift blue','swift green','duvall monroe shuttle','trailhead direct mt. si','trailhead direct mailbox peak','trailhead direct cougar mt.','trailhead direct issaquah alps']

def find_closest_stops(request, lat, lon, bus_route):

    # Clean input
    bus_route = bus_route.lower()
    user_lat = float(lat) or 47.9365944 
    user_lon = float(lon) or -122.219628

    # Check for non-integer route numbers. Format them to be "<capitol letter> -Line"
    if bus_route[0] in alphabet and bus_route not in special_cases:
        temp = bus_route[0].upper()
        temp += '-Line'
        bus_route = temp

    # Check our dictionary of Puget Sound Area Routes
    if bus_route not in route_data:
        return HttpResponse(f'ERROR! {bus_route} is not a valid route.')
    # elif bus_route+'o' in route_data:
        # TODO: handle 20 cases where there are repeated routes (Northern)

    bus_id = route_data[bus_route]
     
    response = requests.get(f'http://api.pugetsound.onebusaway.org/api/where/stops-for-route/{bus_id}.json?key=TEST&version=2')
    bus_data = response.json()
    bus_stops = bus_data['data']['references']['stops']

    closest, next_closest = 1, 1
    closest_stop_id, next_closest_stop_id = 0, 0
    name_of_closest, name_of_next_closest = 'a', 'b'
    closest_direction, next_closest_direction = 'n', 's'

    for stop in bus_stops:

        difference_lat = abs(user_lat - stop['lat'])
        difference_lon = abs(user_lon - stop['lon'])
        difference = difference_lat + difference_lon

        if difference < closest:
            #change next closest
            next_closest = closest
            name_of_next_closest = name_of_closest
            next_closest_direction = closest_direction
            next_closest_stop_id = closest_stop_id

            #updating closest
            closest = difference
            name_of_closest = stop['name']
            closest_direction = stop['direction']
            closest_stop_id = stop['id']

    # Sequential API calls - Finding estimated Arrival Time of: the specific_bus at the nearest_stop
    closest_arrival = find_estimated_arrival(closest_stop_id, bus_id)
    next_closest_arrival = find_estimated_arrival(next_closest_stop_id, bus_id)

    # Check that a valid time was returned from find_estimated_arrival
    if closest_arrival or next_closest_arrival:
        return HttpResponse(f'<h1>Success!\n User_lat: {lat}\n User_lon: {lon}\n name_of_closest: {name_of_closest}\n direction: {closest_direction}\n closest_stop_id: {closest_stop_id} closest_minutes: {closest_arrival} name_of_next_closest: {name_of_next_closest}\n direction: {next_closest_direction} next_closest_stop_id: {next_closest_stop_id} next_closest_minutes: {next_closest_arrival}</h1>')

    return HttpResponse(f'ERROR! We\'re sorry, route {bus_route} is not available at this time.')


def find_estimated_arrival(stop_id, bus_id):

    url = f'http://api.pugetsound.onebusaway.org/api/where/arrivals-and-departures-for-stop/{stop_id}.json?key=TEST'

    response = requests.get(url)
    stop_data = response.json()
    list_of_arrivals = stop_data['data']['entry']['arrivalsAndDepartures']

    arrival_time = 0
    current_time = ((time.time()) *1000) # convert to epoch time

    for arrival in list_of_arrivals: #check all arrivals
        if arrival['routeId'] == bus_id: # find the correct arrival listing
            if arrival['predictedArrivalTime'] != 0: # predicted time is available (it is not always)
                arrival_time = arrival['predictedArrivalTime']
            else: # predicted time is not available
                arrival_time = arrival['scheduledArrivalTime']

        # make sure to only show busses that have NOT arrived yet. (arriving in the future)(Arrivaltime > current_time -- i.e in the future)    
        if arrival_time > current_time:
            return ((arrival_time - current_time)//60000)

    return None


