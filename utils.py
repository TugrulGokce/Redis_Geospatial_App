from folium import plugins
from pprint import pprint
from redis import Redis
import requests
import json
import folium

base_url = 'https://maps.googleapis.com/maps/api/geocode/json?'

attr = {'fill': '#007DEF', 'font-weight': 'bold', 'font-size': '22'}

r = Redis("127.0.0.1", 6379)


def location_info_from_geocoding_api(params: dict):
    """
    > This function takes a dictionary of parameters and
    returns a dictionary of location information
    
    :param params: dict
    :type params: dict
    """
    response = requests.get(base_url, params=params)
    response_json = json.loads(response.text)
    return response_json["results"][0]["geometry"]["location"]


def get_full_coordinates(city: str, district: str, api_key: str):
    """
    > This function takes a city and district name and returns the full coordinates of the district
    
    :param city: The name of the city you want to get the coordinates for
    :type city: str
    :param district: The district of the city you want to get the coordinates for
    :type district: str
    :param api_key: Your API key
    :type api_key: str
    """
    if not district:
        return {"longtitude": "null", "latitude": "null", "status": "Missing district"}

    params_full_address = {"key": api_key, "address": f"{district}, {city}"}
    params_city_address = {"key": api_key, "address": f"{city}"}

    location_full_address = location_info_from_geocoding_api(params_full_address)
    location_city_address = location_info_from_geocoding_api(params_city_address)

    # add district locations to redis with by key: city_name, member: district
    r.geoadd(city, (location_full_address['lng'], location_full_address['lat'], district))

    # add city locations to redis with by key: 'cities', member: city
    r.geoadd("Cities", (location_city_address['lng'], location_city_address['lat'], city))

    return {"longtitude": location_full_address['lng'], "latitude": location_full_address['lat'],
            "status": "OK"}


def get_member_cordinates_by_location(key: str):
    """
    > This function takes a location as a string and returns a list of tuples containing the latitude
    and longitude of each member in that location
    
    :param key: The key of the member you want to get the coordinates of
    :type key: str
    """
    all_members_by_key = [member.decode() for member in r.zrange(name=key, start=0, end=-1)]
    coordinates_of_members = [list((members,) + r.geopos(key, members)[0]) for members in all_members_by_key]
    return all_members_by_key, coordinates_of_members


def draw_map_with_circle(district_points: list, radius: str, coordinates_with_radius: list, distance_option: str,
                         distance: int):
    """
    This function takes in a list of district points, a radius, a list of coordinates with radius, a
    distance option, and a distance, and returns a map with a circle around the coordinates with radius

    :param district_points: list of points that make up the district
    :type district_points: list
    :param radius: the radius of the circle
    :type radius: str
    :param coordinates_with_radius: list of tuples of coordinates and radius
    :type coordinates_with_radius: list
    :param distance_option: This is the option that the user selects. It can be either 'nearest' or
    'furthest'
    :type distance_option: str
    :param distance: the distance in miles or kilometers that you want to draw the circle around the
    coordinates
    :type distance: int
    """

    _Map = folium.Map(location=district_points, zoom_start=13)

    for point in coordinates_with_radius:
        folium.Marker(location=[point[2][1], point[2][0]],
                      popup=f"{point[0].decode()}",
                      tooltip="Click and see district").add_to(_Map)

    circle = folium.Circle(radius=radius,
                           location=district_points,
                           color='red',
                           fill_color="yellow",
                           weight=3)

    _Map.add_child(circle)
    if distance_option == "The Nearest":
        line = folium.PolyLine([[coordinates_with_radius[0][2][1], coordinates_with_radius[0][2][0]],
                                [coordinates_with_radius[distance][2][1], coordinates_with_radius[distance][2][0]]],
                               color="red",
                               weight=2.5,
                               opacity=1)

        wind_textpath = plugins.PolyLineTextPath(line,
                                                 f"{coordinates_with_radius[distance][1]} m",
                                                 center=True,
                                                 offset=7,
                                                 attributes=attr)
    else:  # Furthest
        line = folium.PolyLine([[coordinates_with_radius[-1][2][1], coordinates_with_radius[-1][2][0]],
                                [coordinates_with_radius[distance - 1][2][1],
                                 coordinates_with_radius[distance - 1][2][0]]],
                               color="red",
                               weight=2.5,
                               opacity=1)

        wind_textpath = plugins.PolyLineTextPath(line,
                                                 f"{coordinates_with_radius[distance - 1][1]} m",
                                                 center=True,
                                                 offset=7,
                                                 attributes=attr)
    _Map.add_child(line)
    _Map.add_child(wind_textpath)
    return _Map


def draw_map_by_distance(locations: list, distances: float, zoom_start: int):
    """
    > This function takes a list of locations, a list of distances, and a zoom level, and returns a map
    of the locations with the distances between them
    
    :param locations: a list of tuples containing latitude and longitude values
    :type locations: list
    :param distances: a list of distances from the origin point
    :type distances: float
    :param zoom_start: The initial zoom level of the map
    :type zoom_start: int
    """
    _Map = folium.Map(location=[locations[0][2], locations[0][1]], zoom_start=zoom_start)

    for point in locations:
        folium.Marker(location=[point[2], point[1]],
                      popup=f"{point[0]}",
                      tooltip="Click and see location").add_to(_Map)

    line = folium.PolyLine([[locations[0][2], locations[0][1]], [locations[1][2], locations[1][1]]],
                           color="red",
                           weight=2.5,
                           opacity=1).add_to(_Map)

    plugins.PolyLineTextPath(line,
                             f"{distances} km",
                             center=True,
                             offset=7,
                             attributes=attr).add_to(_Map)

    return _Map


