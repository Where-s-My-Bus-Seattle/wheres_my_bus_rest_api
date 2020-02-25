from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from rest_framework.views import APIView
import requests
import time
import json

with open('bus_routes/finalRoutesAndIds.json') as all_routes:
    route_data = json.load(all_routes)
    # print(route_data)
############################################################################################

class show_me_the_request(APIView):
    """
    Post route for speech recognition.

    [Parameters]: (request, user's latitude, user's longitude)
        - /api/v1/lat/lon
        - audio file included in request.body
    [Return(for each direction)]: [bus_id, direction, stop_name, arrival time (in minutes)]
    """

    def post(self, request, lat, lon, format=None):
        the_audio_file = request.body
        print("the Audio file: ", the_audio_file)
        theBusRoute = '8'
        return get_a_routes_closest_stop_and_arrival_time(request, lat, lon, theBusRoute)

############################################################################################    

def get_a_routes_closest_stop_and_arrival_time(request, lat, lon, bus_route):
    """
    1. Cleans Data
    2. Gets the two closest stops (both directions)
    3. Finds the soonest arrival time of the requested bus at both stops
    4. Returns (for each direction): [bus_id, direction, stop_name, arrival time (in minutes)]
    """
# 1. Clean the data.
    clean_data = clean_route_data(lat,lon,bus_route)

    if not clean_data:
        return JsonResponse({'status': 'bad', 'error': 'not clean data'})

    bus_id = clean_data['bus_id']
    bus_route = clean_data['bus_route']
    user_lat = clean_data['user_lat']
    user_lon = clean_data['user_lon']
    
# 2. Find closest stops.
    closest_stops = find_closest_stops(user_lat,user_lon,bus_id)

## TODO: handle if only one stop comes back?? (sounder train? NORTH/SOUTH)
    if not closest_stops:
        return JsonResponse({'status': 'bad', 'error': 'no two stops available nearby'})
    
    name_of_closest = closest_stops['name_of_closest']
    name_of_next_closest = closest_stops['name_of_next_closest']
    
    closest_stop_id = closest_stops['closest_stop_id']
    next_closest_stop_id = closest_stops['next_closest_stop_id']
    
    closest_direction = closest_stops['closest_direction']
    next_closest_direction = closest_stops['next_closest_direction']

    closest_lat = closest_stops['closest_stop_lat']
    next_closest_lat = closest_stops['next_closest_stop_lat']

    closest_lon = closest_stops['closest_stop_lon']
    next_closest_lon = closest_stops['next_closest_stop_lon']


# 3. Finding arrival times for: the specific_bus at the nearest_stops
    closest_arrival = find_estimated_arrival(closest_stops['closest_stop_id'], bus_id)

    next_closest_arrival = find_estimated_arrival(closest_stops['next_closest_stop_id'], bus_id)


# 4. Check that a valid time was returned from find_estimated_arrival    
    if closest_arrival or next_closest_arrival:
       
        return JsonResponse({
            'status': 'good',
            'route': bus_route,
            'closest_stop': { 
                'closest_name': name_of_closest,
                'closest_direction': closest_direction,
                'closest_stop_id': closest_stop_id,
                'closest_minutes': closest_arrival,
                'closest_lat': closest_lat,
                'closest_lon': closest_lon,
            },
            'next_closest_stop': {
                'next_closest_name': name_of_next_closest,
                'next_closest_direction': next_closest_direction,
                'next_closest_stop_id': next_closest_stop_id,
                'next_closest_minutes': next_closest_arrival,
                'next_closest_lat': next_closest_lat,
                'next_closest_lon': next_closest_lon,
            }
        })
    
    return JsonResponse({'status': 'bad', 'error': 'no arrival time'})

############################################################################################

def clean_route_data(lat, lon, bus_route):
    """
    [Parameters]: (user's latitude, user's longitude, desired bus route)

    [Returns]: Object: {'bus_id':[string], 'user_lat':[float], 'user_lon':[float], 'bus_route':[string]}
    """
    if not lat or not lon:
        return None
    bus_route = bus_route.replace('-', ' ')
    query = bus_route.lower().split()
    user_lat = float(lat) 
    user_lon = float(lon)
    result=''

    alphabet = ['a','b','c','d','e','f']
    repeated_routes = ['101','105','106','107','230','111','113','116','119','240','120','271','70','2','3','4','7','8','12','18','29','1','2','3','4','402','425','202','212','214','102','10','11','13','28','41','45','48','55','57','63','47','48','60','64','67','42','12','13','21','41','45']
    num_chars = set('1234567890')
    key_words = ['line', 'route', 'bus']
    special_cases = {
        'dash':['dash'],
        'nite':['nite'],
        'one':['one'],
        'link': ['link'], 
        'sounder':['sounder south', 'sounder north'],
        'monorail':['monorail sc', 'monorail wl'],
        'amtrak':['amtrak'],
        'tlink': ['tlink'],
        'swift':['swift blue', 'swift green'],
        'duvall':['duvall monroe shuttle'],
        'trailhead': ['trailhead direct mt. si','trailhead direct mailbox peak','trailhead direct cougar mt.','trailhead direct issaquah alps']
    }

    def clean_up_a(query):
        """Check that 'a' is preceded or followed by a keyword"""
        if len(query) == 1:
            return query

        for word in range(len(query)):
            if query[word] == 'a':
                # preceding
                if query[word-1] in key_words:
                    pass
                # following
                else:
                    try:
                        if query[word+1] in key_words:
                            pass
                        else:
                            query[word] = ''
                    except:
                        query[word] = ''
        return query

    query = clean_up_a(query)        

    for word in range(len(query)):
        # is a letter
        if query[word] in alphabet:
            result += query[word].upper()
            result += '-Line'
            break
        # is a special case
        elif query[word] in special_cases:
            if len(special_cases[query[word]]) == 1:
                result += special_cases[query[word]][0]
                break
            else:
                looking = True
                while looking:
                    for route in special_cases[query[word]]:
                        temp, i, temp_result = route.split(), 0, query[word]
                        isMatch = True
                        while isMatch:
                            try:
                                if temp[i+1] == query[word+1+i]:
                                    temp_result += ' '
                                    temp_result += temp[i+1]
                                    i += 1
                                else:
                                    isMatch = False
                            except:
                                if temp_result[:3] == 'tra':
                                    if len(temp_result.split()) > 2:
                                        result += temp_result
                                        looking = False
                                elif len(temp_result.split()) > 1:
                                    result += temp_result
                                    looking = False
                                isMatch = False
                        if not looking:
                            break
                    break
        # is a number
        elif any(char in query[word] for char in num_chars):
            result += query[word]
            break
    
    bus_route = result

    # Check our dictionary of Puget Sound Area Routes
    if bus_route not in route_data:
        return None

    if bus_route in repeated_routes:

        if user_lat > 47.7: # going to be community transit or everett transit (N)
            bus_route += 'N'
        elif user_lat > 47.33: # going to be king county metro
            bus_route = bus_route 
        elif user_lat > 47.08: # going to be pierce transit
            bus_route += 'pt'
        else: # going to be intercity transit
            bus_route += 'it'
    
    try:
        return {'bus_id':route_data[bus_route], 'user_lat':user_lat, 'user_lon':user_lon, 'bus_route': bus_route}
    except:
        return None

############################################################################################

def find_closest_stops(user_lat, user_lon, bus_id):
    """
    [Parameters]: (User's Latitude, User's Longitude, Bus Route Identification Number)
    
    [Return]: The closest stop's and next closest stop's details as a single object

    1. Get request to OneBusAway.
    2. Save and sort the differences in distance to the user.
    3. Assign closest stop variables. And find next closest - Different direction.
    4. Return object.
    """
# 1. Call to OneBusAway
    response = requests.get(f'http://api.pugetsound.onebusaway.org/api/where/stops-for-route/{bus_id}.json?key=TEST&version=2')
    bus_data = response.json()
    bus_stops = bus_data['data']['references']['stops']

    if not bus_stops:
        return None

# 2. Get every difference and save every index
    differences, indices, i = [], {}, 0

    for stop in bus_stops:
        difference_lat = abs(user_lat - stop['lat'])
        difference_lon = abs(user_lon - stop['lon'])
        difference = difference_lat + difference_lon

        differences.append(difference)
        indices[difference] = i

        i += 1

    # Sort the differences
    differences.sort()

# 3. Get the closest stops

    # Closest
    closest = differences[0]
    index = indices[closest]

    closest_stop_id = bus_stops[index]['id']
    closest_stop_lat = bus_stops[index]['lat']
    closest_stop_lon = bus_stops[index]['lon']
    closest_direction = bus_stops[index]['direction']
    name_of_closest = bus_stops[index]['name']

    # Find Next Closest in the list. Different Direction.
    for diff in differences[1:]:
        index = indices[diff]
        current_direction = bus_stops[index]['direction']

        if current_direction != closest_direction:
            next_closest_stop_id = bus_stops[index]['id']
            next_closest_stop_lat = bus_stops[index]['lat']
            next_closest_stop_lon = bus_stops[index]['lon']
            name_of_next_closest = bus_stops[index]['name']
            next_closest_direction = bus_stops[index]['direction']
            break

# 4. Return closest and next closest as an object.
    try:
        return {
            'closest_stop_id':closest_stop_id,
            'next_closest_stop_id':next_closest_stop_id,
            'name_of_closest':name_of_closest,
            'name_of_next_closest':name_of_next_closest,
            'closest_direction':closest_direction,
            'next_closest_direction':next_closest_direction,
            'closest_stop_lon':closest_stop_lon,
            'closest_stop_lat':closest_stop_lat,
            'next_closest_stop_lat':next_closest_stop_lat,
            'next_closest_stop_lon':next_closest_stop_lon
        }
    except:
        return None

############################################################################################

def find_estimated_arrival(stop_id, bus_id):

    response = requests.get(f'http://api.pugetsound.onebusaway.org/api/where/arrivals-and-departures-for-stop/{stop_id}.json?key=TEST')
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
            print('SUCCESS=====================', arrival_time)
            return ((arrival_time - current_time)//60000) # time in minutes (rounded)

    return None


