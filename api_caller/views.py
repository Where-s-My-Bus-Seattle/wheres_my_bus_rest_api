from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from rest_framework.views import APIView
#import speech_recognition as sr
import requests
import time
import json



with open('bus_routes/finalRoutesAndIds.json') as all_routes:
    route_data = json.load(all_routes)
    print(route_data)

#def voice_to_text(path):
 #   sound = path
  #  r = sr.Recognizer()
   # with sr.AudioFile(sound) as source:
    #    r.adjust_for_ambient_noise(source)
     #   print("Converting Audio To Text ..... ")
      #  audio = r.listen(source)
  #  try:
   #     print("Converted Audio Is : \n" + r.recognize_google(audio))
    #except Exception as e:
     #   print("Error {} : ".format(e) )



class show_me_the_request(APIView):
    
    def post(self, request, lat, lon, format=None):
        theFile = request.body
        # 1st .wav to text
        theBusRoute = '8' # the ana-leo function (.wav to text)
        return get_a_routes_closest_stop_and_arrival_time(request, lat, lon, theBusRoute)
        
        #2. Gets the two closest stops (both directions)
        # 3. Finds the soonest arrival time of the requested bus at both stops
        # 4. Returns (for each direction): [bus_id, direction, stop_name, arrival time (in minutes)]

        # return HttpResponse()
    

def get_a_routes_closest_stop_and_arrival_time(request, lat, lon, bus_route):
    """
    1. Cleans Data
    2. Gets the two closest stops (both directions)
    3. Finds the soonest arrival time of the requested bus at both stops
    4. Returns (for each direction): [bus_id, direction, stop_name, arrival time (in minutes)]
    """
    # 1
    clean_data = clean_route_data(lat,lon,bus_route)

    if not clean_data:
        return JsonResponse({'status': 'bad'})
        # return HttpResponse(f'ERROR! {bus_route} is not a valid route.')

    bus_id = clean_data['bus_id']
    bus_route = clean_data['bus_route']
    user_lat = clean_data['user_lat']
    user_lon = clean_data['user_lon']
    
    # 2
    closest_stops = find_closest_stops(user_lat,user_lon,bus_id)
    print("closest_stops: ", closest_stops)

    # closest_stops:  {'closest_stop_id': '29_2876', 'next_closest_stop_id': 0, 'name_of_closest': 'Aurora Village Transit Center Bay 7', 'name_of_next_closest': 'b', 'closest_direction': 'E', 'next_closest_direction': 's', 'closest_stop_lon': -122.342007, 'closest_stop_lat': 47.77436, 'next_closest_stop_lat': 0, 'next_closest_stop_lon': 0}
    
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

    # 3
    # Sequential API calls - Finding estimated Arrival Time of: the specific_bus at the nearest_stop
    closest_arrival = find_estimated_arrival(closest_stops['closest_stop_id'], bus_id)
    print("closest_arrival: ", closest_arrival)
    next_closest_arrival = find_estimated_arrival(closest_stops['next_closest_stop_id'], bus_id)
    print("next_closest_arrival: ", next_closest_arrival)
    # 4
    # Check that a valid time was returned from find_estimated_arrival
   # print('NC: ', name_of_closest, 'cArrival: ', closest_arrival, 'NNC: ', name_of_next_closest, 'nCArrival', next_closest_arrival)
    
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
    
    return JsonResponse({'status': 'bad'})

    # return HttpResponse(f'ERROR! We\'re sorry, route {bus_route} is not available at this time.')

def clean_route_data(lat, lon, bus_route):
    query = bus_route.lower().split()
    user_lat = float(lat) or 47.9365944 
    user_lon = float(lon) or -122.219628
    result=''

    alphabet = set(['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z'])
    repeated_routes = ['101','105','106','107','230','111','113','116','119','240','120','271','70','2','3','4','7','8','12','18','29','1','2','3','4','402','425','202','212','214','102','10','11','13','28','41','45','48','55','57','63','47','48','60','64','67','42','12','13','21','41','45']
    num_chars = set('1234567890')
    key_words = set(['line', 'route', 'bus'])

    special_cases = {
    'link': ['link'], 
    'sounder':['sounder south', 'sounder north'],
    'amtrak':['amtrak'],
    'tlink': ['tlink'],
    'swift':['swift blue', 'swift green'],
    'duvall':['duvall monroe shuttle'],
    'trailhead': ['trailhead direct mt. si','trailhead direct mailbox peak','trailhead direct cougar mt.','trailhead direct issaquah alps']
    }

    for word in range(len(query)):

        if query[word] in alphabet:
            result += query[word].upper()
            result +='-Line'
            break

        # is a number or leter
        if query[word] in key_words:
            # print('found key word: ', query[word])
            #if the word is a key word, grab the first word before the key if it
            if query[word -1]: 
                if query[word-1] in alphabet:
                    result += query[word-1].upper()
                    result +='-Line'
                    break
                if any(char in query[word-1] for char in num_chars):
                    result += query[word-1]
                    break

            # grabs the first word after the key if it is a letter or number           
            if query[word +1]:
                if query[word+1] in alphabet:
                    result += query[word +1].upper()
                    result +='-Line'
                    break
                if any(char in query[word+1] for char in num_chars):   
                    result += query[word+1]
                    break
        else:
            # if no key words are found, grab the first number found
            if any(char in query[word] for char in num_chars):
                result += query[word]
                break
        
        # checks if word is a key in special case, and returns a value inside
        # that key's list
        if query[word] in special_cases:
            if len(special_cases[query[word]]) == 1:
                result += special_cases[query[word]][0]  
                break
            else:
                if query[word +1] in special_cases[query[word]][0]:
                    result += special_cases[query[word]][0]
                    break
                if query[word +1] in special_cases[query[word]][1]:
                    result += special_cases[query[word]][1]
                    break
    
    bus_route = result
   # print(bus_route)
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


def clean_route_data_deprecated(lat, lon, bus_route):
    # Clean input
    bus_route = bus_route.lower()
    user_lat = float(lat) or 47.9365944 
    user_lon = float(lon) or -122.219628

    alphabet = set(['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z'])
    special_cases = ['link', 'sounder south','amtrak','sounder north','tlink','swift blue','swift green','duvall monroe shuttle','trailhead direct mt. si','trailhead direct mailbox peak','trailhead direct cougar mt.','trailhead direct issaquah alps']
    
    
    # Check for non-integer route numbers. Format them to be "<capitol letter> -Line"
    if bus_route[0] in alphabet and bus_route not in special_cases:
        temp = bus_route[0].upper()
        temp += '-Line'
        bus_route = temp

    # Check our dictionary of Puget Sound Area Routes
    if bus_route not in route_data:
        return None
    # TODO: elif bus_route+'o' in route_data:
        # handle 20 cases where there are repeated routes (Northern)

    return {'bus_id':route_data[bus_route], 'user_lat':user_lat, 'user_lon':user_lon, 'bus_route': bus_route}

def find_closest_stops(user_lat, user_lon, bus_id):
    response = requests.get(f'http://api.pugetsound.onebusaway.org/api/where/stops-for-route/{bus_id}.json?key=TEST&version=2')
    bus_data = response.json()
    bus_stops = bus_data['data']['references']['stops']

# Get every difference and save every index
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

# Get the closest stops

    # Closest
    closest = differences[0]
    index = indices[closest]

    closest_stop_id = bus_stops[index]['id']
    closest_stop_lat = bus_stops[index]['lat']
    closest_stop_lon = bus_stops[index]['lon']
    closest_direction = bus_stops[index]['direction']
    name_of_closest = bus_stops[index]['name']

    print('closest: ', closest_direction, closest_stop_id)

    # Find Next Closest in the list. Different Direction.
    for diff in differences[1:]:
        index = indices[diff]
        current_direction = bus_stops[index]['direction']

        if current_direction != closest_direction:
            # next_closest = diff
            next_closest_stop_id = bus_stops[index]['id']
            next_closest_stop_lat = bus_stops[index]['lat']
            next_closest_stop_lon = bus_stops[index]['lon']
            name_of_next_closest = bus_stops[index]['name']
            next_closest_direction = bus_stops[index]['direction']
            print('not the same direction!!!!!!!!!!!!!!!!!!!!!!!')
            print('next closest: ', next_closest_direction, next_closest_stop_id)
            break

# Return closest and next closest as an object.
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


def depracated_find_closest_stops(user_lat, user_lon, bus_id):
     
    response = requests.get(f'http://api.pugetsound.onebusaway.org/api/where/stops-for-route/{bus_id}.json?key=TEST&version=2')
    bus_data = response.json()
    bus_stops = bus_data['data']['references']['stops']


#### Setting First Two Stops. The First two in the list, going different directions ########################
    closest, next_closest = abs(user_lat - bus_stops[0]['lat']), abs(user_lat - bus_stops[0]['lat'])
    closest_stop_id, next_closest_stop_id = bus_stops[0]['id'], bus_stops[0]['id']
    closest_stop_lat, next_closest_stop_lat = bus_stops[0]['lat'], bus_stops[0]['lat']
    closest_stop_lon, next_closest_stop_lon = bus_stops[0]['lon'], bus_stops[0]['lon']
    name_of_closest, name_of_next_closest = bus_stops[0]['name'], bus_stops[0]['name']
    closest_direction, next_closest_direction = bus_stops[0]['direction'], bus_stops[0]['direction']
    index = 0

    while closest_direction == next_closest_direction:
        print('inWhile; closest_direction: ', closest_direction)
        for i in range(len(bus_stops)):
            print('index, direction: ', i, bus_stops[i]['direction'])
            if bus_stops[i]['direction'] != closest_direction:
                next_closest = abs(user_lat - bus_stops[i]['lat'])
                next_closest_stop_id = bus_stops[i]['id']
                next_closest_stop_lat = bus_stops[i]['lat']
                next_closest_stop_lon = bus_stops[i]['lon']
                name_of_next_closest = bus_stops[i]['name']
                next_closest_direction = bus_stops[i]['direction']
                index = i

                print('breaking! index, direction: ', index, next_closest_direction)
                break
        break
############################################################################################################


#### Updating 'closest' stops after the first two ##########################################################
    for stop in bus_stops[index:]:

        difference_lat = abs(user_lat - stop['lat'])
        difference_lon = abs(user_lon - stop['lon'])
        difference = difference_lat + difference_lon

        if difference < closest:

            # updating closest
            closest = difference
            name_of_closest = stop['name']
            closest_direction = stop['direction']
            closest_stop_id = stop['id']
            closest_stop_lat = stop['lat']
            closest_stop_lon = stop['lon']

        if difference < next_closest and difference != closest:
            #change next closest
            next_closest = difference
            name_of_next_closest = stop['name']
            next_closest_direction = stop['direction']
            next_closest_stop_id = stop['id']
            next_closest_stop_lat = stop['lat']
            next_closest_stop_lon = stop['lon']
############################################################################################################

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


