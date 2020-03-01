from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from rest_framework.views import APIView
import urllib.parse
import requests
import time
import json

with open('bus_routes/finalRoutesAndIds.json') as all_routes:
    route_data = json.load(all_routes)

############################################################################################
## Post Route for Speech Recognition #######################################################
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
        decoded = urllib.parse.unquote(the_audio_file)
        print("the Audio file: ", decoded)

        theBusRoute = '8'
        return get_a_routes_closest_stop_and_arrival_time(request, lat, lon, theBusRoute)


############################################################################################
## Get Route for Form Submission ###########################################################    
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

# 3. Finding arrival times for: the specific_bus at the nearest_stops
    closest_arrival = find_estimated_arrival(closest_stops['closest_stop_id'], bus_id)
    next_closest_arrival = find_estimated_arrival(closest_stops['next_closest_stop_id'], bus_id)

# 4. Check that a valid time was returned from find_estimated_arrival    
    if closest_arrival or next_closest_arrival:
       
        return JsonResponse({
            'status': 'good',
            'route': bus_route,
            'closest_stop': { 
                'closest_name': closest_stops['name_of_closest'],
                'closest_direction': closest_stops['closest_direction'],
                'closest_stop_id': closest_stops['closest_stop_id'],
                'closest_minutes': closest_arrival,
                'closest_lat': closest_stops['closest_stop_lat'],
                'closest_lon': closest_stops['closest_stop_lon'],
            },
            'next_closest_stop': {
                'next_closest_name': closest_stops['name_of_next_closest'],
                'next_closest_direction': closest_stops['next_closest_direction'],
                'next_closest_stop_id': closest_stops['next_closest_stop_id'],
                'next_closest_minutes': next_closest_arrival,
                'next_closest_lat': closest_stops['next_closest_stop_lat'],
                'next_closest_lon': closest_stops['next_closest_stop_lon'],
            }
        })
    
    return JsonResponse({'status': 'bad', 'error': 'no arrival time'})


############################################################################################
############################################################################################
def clean_route_data(lat, lon, bus_route):
    """
    [Parameters]: (user's latitude, user's longitude, desired bus route)
        1. Creates query [list of words]
        2. Cleans up the letter 'a' that is not intended to represent 'A-Line'
        3. Checks all words in the query to find the intended route
        4. Checks if the route is valid and if the route is a "repeated route"
    [Returns]: Object: {'bus_id':[string], 'user_lat':[float], 'user_lon':[float], 'bus_route':[string]}
    """
    if not lat or not lon:
        return None        
    user_lat = float(lat) 
    user_lon = float(lon)

# 1. create query
    bus_route = bus_route.replace('-', ' ')
    query = bus_route.lower().split()

# 2. Clean up letter 'a'
    query = clean_up_letter_a(query)        

# 3. Check all words in query
    matched_route = check_all_words_in_query(query)    
    bus_route = matched_route
 
# 4. Check our dictionary of Puget Sound Area Routes
    if bus_route not in route_data:
        return None

# 4. Check if it is a repeated route
    matched_bus_route = check_if_repeated_route(bus_route, user_lat)
    
    try:
        return {'bus_id':route_data[matched_bus_route], 'user_lat':user_lat, 'user_lon':user_lon, 'bus_route': bus_route}
    except:
        return None


############################################################################################
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
############################################################################################
def find_estimated_arrival(stop_id, bus_id):
    """
    Finds estimated arrival time of a requested bus at a given stop.\n
    [Parameters]: (stop_id[string], bus_id[string])
    [Returns]: (time_in_minutes[integer])
    """
    response = requests.get(f'http://api.pugetsound.onebusaway.org/api/where/arrivals-and-departures-for-stop/{stop_id}.json?key=TEST')
    stop_data = response.json()
    list_of_arrivals = stop_data['data']['entry']['arrivalsAndDepartures']

    arrival_time = 0
    current_time = ((time.time()) *1000) # convert to epoch time
    
    #check all arrivals
    for arrival in list_of_arrivals:

        # find the correct arrival listing 
        if arrival['routeId'] == bus_id:

            # predicted time IS available (it is not always) 
            if arrival['predictedArrivalTime'] != 0: 
                arrival_time = arrival['predictedArrivalTime']
            
            # predicted time NOT available
            else: 
                arrival_time = arrival['scheduledArrivalTime']

        # make sure to only show busses that have NOT arrived yet. (arriving in the future)(Arrivaltime > current_time -- i.e in the future)    
        if arrival_time > current_time:
            print('SUCCESS=====================', arrival_time)
            return ((arrival_time - current_time)//60000) # time in minutes (rounded)

    return None


############################################################################################
## Helper Functions ########################################################################
############################################################################################

def clean_up_letter_a(query):
    """Check that 'a' is preceded or followed by a keyword"""
    key_words = ['line', 'route', 'bus']
    alphabet = ['b','c','d','e','f']
    num_chars = set('1234567890')
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
    override = False
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
        elif query[word] in alphabet or query[word] in special_cases or any(char in query[word] for char in num_chars):
            override = True

    if override:
        for word in range(len(query)):
            if query[word] is 'a':
                print('word is a')
                query[word] = ''   

    return query

def check_special_cases(query, idx):
    """
    [Parameters]: (query[list of strings], idx[integer])

    [Return]: A matched route[string] OR null string
    """
    result = ''
    special_cases = {'dash':['dash'],'nite':['nite'],'one':['one'],'link': ['link'], 'sounder':['sounder south', 'sounder north'],'monorail':['monorail sc', 'monorail wl'],'amtrak':['amtrak'],'tlink': ['tlink'],'swift':['swift blue', 'swift green'],'duvall':['duvall monroe shuttle'],'trailhead': ['trailhead direct mt. si','trailhead direct mailbox peak','trailhead direct cougar mt.','trailhead direct issaquah alps']}

    if len(special_cases[query[idx]]) == 1:
        result += special_cases[query[idx]][0]
    else:
        looking = True
        while looking:
            for route in special_cases[query[idx]]:
                temp, i, temp_result = route.split(), 0, query[idx]
                isMatch = True
                while isMatch:
                    try:
                        if temp[i+1] == query[idx+1+i]:
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
    return result

def check_all_words_in_query(query):
    """
    [Parameters]: query[list of strings]

    [Returns]: A matched route[string] OR null string
    """
    alphabet = ['a','b','c','d','e','f']
    num_chars = set('1234567890')
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
    result = ''

    for i in range(len(query)):

        # is a letter
        if query[i] in alphabet:
            result += query[i].upper()
            result += '-Line'
            break

        # is a special case
        elif query[i] in special_cases:
            matched_special_case = check_special_cases(query, i)
            if matched_special_case:
                result += matched_special_case
                break

        # is a number
        elif any(char in query[i] for char in num_chars):
            result += query[i]
            break

    return result

def check_if_repeated_route(route, user_lat):
    """
    Checks if route is a repeated route. Adds correct identifier to route number.

    [Parameters]: (route[string], user_lat[float])

    [Returns]: updated bus_route[string]
    """
    bus_route = route
    repeated_routes = {'101':'','105':'','106':'','107':'','230':'','111':'','113':'','116':'','119':'','240':'','120':'','271':'','70':'','2':'pt','7':'','8':'','18':'','29':'','1':'pt','3':'pt','4':'pt','402':'pt','425':'pt','202':'pt','212':'pt','214':'pt','102':'pt','10':'pt','11':'pt','13':'','28':'pt','41':'','45':'','55':'pt','57':'pt','63':'pt','47':'','48':'','60':'','64':'','67':'','42':'','12':'','21':''}
    intercity_transit = ['47','48','60','64','67','42','12','13','21','41','45']
    king_county_metro = ['917', 'A Line', '225', '231', '239', '230', '250', '37', '910', '628', '372', '373', '630', '218', '631', '63', '4', '36', '43', '986', '823', '44', '987', '212', '45', '988', 'Trailhead Direct Issaquah Alps', '989', '824', '214', '47', '180', '48', '635', '216', '5', '217', '982', '41', '21', '984', 'F Line', 'E Line', '342', '345', '346', '952', '347', '894', '348', '49', '248', '355', '895', '116', '243', '245', '893', '118', '246', '661', '931', '119', '67', '915', '12', '249', '120', '238', '62', '226', '111', '24', '64', '193', '113', '240', '65', '930', '241', '114', '255', '73', '128', '74', '257', '75', '13', '907', '121', '122', '7', '123', '252', '70', '124', '71', '125', '221', '244', 'Trailhead Direct Cougar Mt.', '55', '994', '50', '995', 'Trailhead Direct Mailbox Peak', '219', '981', 'Trailhead Direct Mt. Si', '22', '224', '157', '204', '101', '232', '102', '105', '57', '106', '234', '156', '107', '235', '236', '60', '980', '237', 'B Line', '11', '775', '56', '1', '10', '166', '167', '903', '158', '908', '159', '3', '906', '301', '913', '914', '303', '164', '304', '916', '901', '178', '169', '308', '17', '309', '31', '311', '312', '177', '168', '629', 'Duvall-Monroe Shuttle', '268', '14', '76', '77', '131', '26', '773', '29', '132', '78', '40', '8', '887', 'C Line', '277', '9', '153', '28', '154', '269', 'D Line', '27', '143', '271', '886', '148', '888', '889', '15', '150', '891', '892', '208', '200', '181', '32', '182', '33', '183', '330', '331', '186', '187', '316', '179', '18', '192', '197', '2', '19', '190']
    pierce_transit = ['1','2','3','4','402','425','202','212','214','102','10','11','13','28','41','45','48','55','57','63']
    north_routes = ['101','105','106','107','230','111','113','116','119','240','120','271','70','2','3','4','7','8','12','18','29']
    
    if bus_route in repeated_routes:
        if user_lat > 47.7:
            # going to be community transit or everett transit (N)
            if bus_route in north_routes: 
                bus_route += 'N'
            else:
                bus_route += repeated_routes[bus_route]  
        elif user_lat > 47.33:
            # going to be king county metro
            if bus_route in king_county_metro:
                bus_route = bus_route
            else:
                bus_route += repeated_routes[bus_route]
        elif user_lat > 47.08:
            # going to be pierce transit
            if bus_route in pierce_transit: 
                bus_route += 'pt'
            else:
                bus_route += repeated_routes[bus_route] 
        else:
            # going to be intercity transit
            if bus_route in intercity_transit: 
                bus_route += 'it'
            else:
                bus_route += repeated_routes[bus_route] 

    return bus_route
    