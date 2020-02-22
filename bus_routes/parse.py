import json

with open('bus_routes/(1)kingCountyMetro.json') as kc_metro:
    kc_data = json.load(kc_metro)
with open('bus_routes/(3)pierceTransit.json') as pierce:
    pt_data = json.load(pierce)
with open('bus_routes/(19)intercityTransit.json') as intercity:
    it_data = json.load(intercity)
with open('bus_routes/(23)seattleStreetCar.json') as street_car:
    sc_data = json.load(street_car)
with open('bus_routes/(29)communityTransit.json') as c_transit:
    ct_data = json.load(c_transit)
with open('bus_routes/(40)soundTransit.json') as s_transit:
    st_data = json.load(s_transit)
with open('bus_routes/(95)washingtonStateFerries.json') as ferries:
    ferry_data = json.load(ferries)
with open('bus_routes/(96)seattleMonorail.json') as sea_mono:
    sm_data = json.load(sea_mono)
with open('bus_routes/(97)everettTransit.json') as e_transit:
    et_data = json.load(e_transit)
with open('bus_routes/(98)seattleChildrens.json') as childrens:
    child_data = json.load(childrens)
with open('bus_routes/(KMD)kingCountyMarine.json') as king_marine:
    kmd_data = json.load(king_marine)

with open('bus_routes/rawAgencies.json') as ag_obj:
    agencies = json.load(ag_obj)

def hash_routes():

    kc_list = kc_data['data']['list']
    ct_list = ct_data['data']['list']
    et_list = et_data['data']['list']
    st_list = st_data['data']['list']
    sm_list = sm_data['data']['list']
    sc_list = sc_data['data']['list']
    pt_list = pt_data['data']['list']
    it_list = it_data['data']['list']
    kmd_list = kmd_data['data']['list']
    ferry_list = ferry_data['data']['list']
    child_list = child_data['data']['list']

    def add_unique_keys(dictionary, lst, letter):
        bus_dict = dictionary
        for route in lst:
            route_name = route['shortName']
            route_id = route['id']
            if route["agencyId"] == "95":
                route_name = route['longName']

            if route_name not in bus_dict:
                bus_dict[route_name] = route_id
            else:
                route_name += letter
                bus_dict[route_name] = route_id
                print('already in there: ', route_name)
        return bus_dict

    kc_added = add_unique_keys({}, kc_list, 'kcm')
    ct_added = add_unique_keys(kc_added, ct_list, 'N')
    et_added = add_unique_keys(ct_added, et_list, 'N')
    st_added = add_unique_keys(et_added, st_list, 'st')
    sm_added = add_unique_keys(st_added, sm_list, 'sm')
    sc_added = add_unique_keys(sm_added, sc_list, 'sc')
    pt_added = add_unique_keys(sc_added, pt_list, 'pt')
    it_added = add_unique_keys(pt_added, it_list, 'it')
    kmd_added = add_unique_keys(it_added, kmd_list, 'kmd')
    ferry_added = add_unique_keys(kmd_added, ferry_list, 'ferry')
    child_added = add_unique_keys(ferry_added, child_list, 'child')

    print(child_added)



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
    hash_routes()
    # hash_agency()