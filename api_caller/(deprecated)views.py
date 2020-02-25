#import speech_recognition as sr

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

     
    for word in range(len(query)):

        # is a letter
        if query[word] in alphabet:
            result += query[word].upper()
            result +='-Line'
            break

        #if the word is a key word, grab the first word before the key if it
        elif query[word] in key_words:
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

        # is a number
        else:
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
        # print('inWhile; closest_direction: ', closest_direction)
        for i in range(len(bus_stops)):
            # print('index, direction: ', i, bus_stops[i]['direction'])
            if bus_stops[i]['direction'] != closest_direction:
                next_closest = abs(user_lat - bus_stops[i]['lat'])
                next_closest_stop_id = bus_stops[i]['id']
                next_closest_stop_lat = bus_stops[i]['lat']
                next_closest_stop_lon = bus_stops[i]['lon']
                name_of_next_closest = bus_stops[i]['name']
                next_closest_direction = bus_stops[i]['direction']
                index = i

                # print('breaking! index, direction: ', index, next_closest_direction)
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

