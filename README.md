# wheres_my_bus_backend

When you pull down:

```
./manage.py collectstatic
Add a .env file 

agencies.json - http://developer.onebusaway.org/modules/onebusaway-application-modules/1.1.13/api/where/methods/agencies-with-coverage.html

(<agency_num>)<agency_name>.json - http://developer.onebusaway.org/modules/onebusaway-application-modules/1.1.13/api/where/methods/routes-for-agency.html

![agency_map](agency_map.png)

Repeated routes:
<-- Community Transit (North - "lat": 47.938764500000005, "lon": -121.99284) -->
('already in there: ', '101ct')
('already in there: ', '105ct')
('already in there: ', '106ct')
('already in there: ', '107ct')
('already in there: ', '230ct')
('already in there: ', '111ct')
('already in there: ', '113ct')
('already in there: ', '116ct')
('already in there: ', '119ct')
('already in there: ', '240ct')
('already in there: ', '120ct')
('already in there: ', '271ct')

<-- Everett Transit (North - "lat": 47.9488655, "lon": -122.2443695) -->
('already in there: ', '70et')
('already in there: ', '2et')
('already in there: ', '3et')
('already in there: ', '4et')
('already in there: ', '7et')
('already in there: ', '8et')
('already in there: ', '12et')
('already in there: ', '18et')
('already in there: ', '29et')

<-- Pierce Transit (South - "lat": 47.2308535, "lon": -122.418351) -->
('already in there: ', '1pt')
('already in there: ', '2pt')
('already in there: ', '3pt')
('already in there: ', '4pt')
('already in there: ', '402pt')
('already in there: ', '425pt')
('already in there: ', '202pt')
('already in there: ', '212pt')
('already in there: ', '214pt')
('already in there: ', '102pt')
('already in there: ', '10pt')
('already in there: ', '11pt')
('already in there: ', '13pt')
('already in there: ', '28pt')
('already in there: ', '41pt')
('already in there: ', '45pt')
('already in there: ', '48pt')
('already in there: ', '55pt')
('already in there: ', '57pt')
('already in there: ', '63pt')

<-- Intercity Transit (South - "lat": 47.086729000000005, "lon": -122.7009125) -->
('already in there: ', '47it')
('already in there: ', '48it')
('already in there: ', '60it')
('already in there: ', '64it')
('already in there: ', '67it')
('already in there: ', '42it')
('already in there: ', '12it')
('already in there: ', '13it')
('already in there: ', '21it')
('already in there: ', '41it')
('already in there: ', '45it')