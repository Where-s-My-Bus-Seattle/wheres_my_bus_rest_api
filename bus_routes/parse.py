import json

with open('bus_routes/kingCountyMetro.json') as kc_metro:
    kc_data = json.load(kc_metro)
with open('bus_routes/communityTransit.json') as c_transit:
    ct_data = json.load(c_transit)
with open('bus_routes/everettTransit.json') as e_transit:
    et_data = json.load(e_transit)
with open('bus_routes/soundTransit.json') as s_transit:
    st_data = json.load(s_transit)
with open('bus_routes/seattleMonorail.json') as sea_mono:
    sm_data = json.load(sea_mono)
with open('bus_routes/seattleStreetCar.json') as street_car:
    sc_data = json.load(street_car)

with open('bus_routes/rawAgencies.json') as ag_obj:
    agencies = json.load(ag_obj)

def hash_routes():

    kc_list = kc_data['data']['list']
    ct_list = ct_data['data']['list']
    et_list = et_data['data']['list']
    st_list = st_data['data']['list']

    def add_unique_keys(dictionary, lst):
        bus_dict = dictionary
        for route in lst:
            route_name = route['shortName']
            route_id = route['id']

            if route_name not in bus_dict:
                bus_dict[route_name] = route_id
            else:
                route_name += 'o'
                bus_dict[route_name] = route_id
                print('already in there + "o": ', route_name)
        return bus_dict

    kc_added = add_unique_keys({}, kc_list)
    ct_added = add_unique_keys(kc_added, ct_list)
    et_added = add_unique_keys(ct_added, et_list)
    st_added = add_unique_keys(et_added, st_list)

    print(st_added)



def hash_agency():
    agency_list = agencies['data']['list']
    agency_ref = agencies['data']['references']['agencies']

    def combine_agency_name_number(dictionary, lst):
        agency_dict = dictionary
        for agency in lst:
            agency_number = agency['id']
            agency_name = agency['name']

            agency_dict[agency_number] = {"name": agency_name}
        return agency_dict

    def combine_agency_coordinates(dictionary, lst):
        agency_dict = dictionary
        for agency in lst:
            agency_number = agency['agencyId']
            agency_lat = agency['lat']
            agency_lon = agency['lon']

            agency_dict[agency_number]["lat"] = agency_lat
            agency_dict[agency_number]["lon"] = agency_lon
        return agency_dict

    names_for_ids = combine_agency_name_number({},agency_ref)
    coords_for_ids = combine_agency_coordinates(names_for_ids, agency_list)
    
    print(coords_for_ids)

if __name__ == "__main__":
    # hash_routes()
    hash_agency()