from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
import requests
import time
import json
import speech_recognition as sr

with open('bus_routes/finalRoutesAndIds.json') as all_routes:
    route_data = json.load(all_routes)

def voice_get_a_routes_closest_stop_and_arrival_time(request, lat, lon):


    """
    
    1. Convert audio to text
    2. Extract bus number from the text
    3. Gets the two closest stops (both directions)
    4. Finds the soonest arrival time of the requested bus at both stops
    5. Returns (for each direction): [bus_id, direction, stop_name, arrival time (in minutes)]
    """
    
    voice_to_text = voice_to_text(request)
    return get_aroutes_closest_stop_and_arrival_time(request, lat, lon, voice_to_text)



  
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
        return HttpResponse(f'ERROR! {bus_route} is not a valid route.')

    bus_id = clean_data['bus_id']
    bus_route = clean_data['bus_route']
    user_lat = clean_data['user_lat']
    user_lon = clean_data['user_lon']
    
    # 2
    closest_stops = find_closest_stops(user_lat,user_lon,bus_id)
    
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
    next_closest_arrival = find_estimated_arrival(closest_stops['next_closest_stop_id'], bus_id)

    # 4
    # Check that a valid time was returned from find_estimated_arrival
    if closest_arrival or next_closest_arrival:
        # return HttpResponse(f'<h1>Success!\n User_lat: {user_lat}\n User_lon: {user_lon}\n name_of_closest: {name_of_closest}\n direction: {closest_direction}\n closest_stop_id: {closest_stop_id} closest_minutes: {closest_arrival} closest_lat: {closest_lat} closest_lon: {closest_lon} name_of_next_closest: {name_of_next_closest}\n direction: {next_closest_direction} next_closest_stop_id: {next_closest_stop_id} next_closest_minutes: {next_closest_arrival} next_closest_lat: {next_closest_lat} next_closest_lon {next_closest_lon}</h1>')
        return JsonResponse({
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

    return HttpResponse(f'ERROR! We\'re sorry, route {bus_route} is not available at this time.')



def clean_route_data(lat, lon, bus_route):
    # Clean input
    bus_route = bus_route.lower()
    user_lat = float(lat) or 47.9365944 
    user_lon = float(lon) or -122.219628

    alphabet = ['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z']
    special_cases = ['link', 'sounder south','amtrak','sounder north','tlink','swift blue','swift green','duvall monroe shuttle','trailhead direct mt. si','trailhead direct mailbox peak','trailhead direct cougar mt.','trailhead direct issaquah alps']
    number_words = {
        'o': '0',
        'oh': '0',
        'zero': '0',
        'one': '1',
        'two': '2',
        'three': '3',
        'four': '4',
        'five': '5',
        'six': '6',
        'seven': '7',
        'eight': '8',
        'nine': '9',
        'ten': '10',
        'eleven': '11',
        'twelve': '12',
        'thirteen': '13',
        'fourteen': '14',
        'fifteen': '15',
        'sixteen': '16',
        'seventeen': '17',
        'eighteen': '18',
        'nineteen': '19',
        'twenty': '20',
        'thirty': '30',
        'forty': '40',
        'fifty': '50',
        'sixty': '60',
        'seventy': '70',
        'eighty': '80',
        'ninety': '90',
        'hundred': '0',
    }
    'When does the c line arrive'
    'when does sea line arrive'
    'when does see line arrive'
    'when does bus twenty get to fourth and pike'
    'how long until route 512'
    'how long until line d gets here'
    'I really love long walks on the beach d line when the sun is shining'
    'The Patriots are a terrible organization and we should revoke all six of their championships'
    'when does one o one get here'
    'when does one oh one get here'
    'when does one hundred and one get here'
    'how long until the five twelve arrives' #'512'




        
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

    closest, next_closest = None, None
    closest_stop_id, next_closest_stop_id = 0,0
    closest_stop_lat, next_closest_stop_lat = 0,0
    closest_stop_lon, next_closest_stop_lon = 0,0
    name_of_closest, name_of_next_closest = 'a', 'b'
    closest_direction, next_closest_direction = 'n', 's'

    for stop in bus_stops:

        difference_lat = abs(user_lat - stop['lat'])
        difference_lon = abs(user_lon - stop['lon'])
        difference = difference_lat + difference_lon

        if not closest:
            closest = difference
            name_of_closest = stop['name']
            closest_direction = stop['direction']
            closest_stop_id = stop['id']
            closest_stop_lat = stop['lat']
            closest_stop_lon = stop['lon']

        if difference < closest:
            #change next closest
            next_closest = closest
            name_of_next_closest = name_of_closest
            next_closest_direction = closest_direction
            next_closest_stop_id = closest_stop_id
            next_closest_stop_lat = closest_stop_lat
            next_closest_stop_lon = next_closest_stop_lat

            #updating closest
            closest = difference
            name_of_closest = stop['name']
            closest_direction = stop['direction']
            closest_stop_id = stop['id']
            closest_stop_lat = stop['lat']
            closest_stop_lon = stop['lon']
    
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
            return ((arrival_time - current_time)//60000) # time in minutes (rounded)

    return None

if __name__ == "__main__":
    bus_route = "when does the five twelve arrive"
    number_words = {
    'o': '0',
    'oh': '0',
    'zero': '0',
    'one': '1',
    'two': '2',
    'three': '3',
    'four': '4',
    'five': '5',
    'six': '6',
    'seven': '7',
    'eight': '8',
    'nine': '9',
    'ten': '10',
    'eleven': '11',
    'twelve': '12',
    'thirteen': '13',
    'fourteen': '14',
    'fifteen': '15',
    'sixteen': '16',
    'seventeen': '17',
    'eighteen': '18',
    'nineteen': '19',
    'twenty': '20',
    'thirty': '30',
    'forty': '40',
    'fifty': '50',
    'sixty': '60',
    'seventy': '70',
    'eighty': '80',
    'ninety': '90',
    'hundred': '0'
}

    for i, word in enumerate(bus_route.split()):
        if word in number_words:
            temp = word
            if word[i + 1] in number_words:
                temp += word[i +1]
            print(temp)
    print('word not found')


def voice_to_text(path):
     sound = path
    r = sr.Recognizer()
    with sr.AudioFile(sound) as source:
        r.adjust_for_ambient_noise(source)
        print("Converting Audio To Text ..... ")
        audio = r.listen(source)
    try:
        print("Converted Audio Is : \n" + r.recognize_google(audio))
    except Exception as e:
        print("Error {} : ".format(e) )