import streamlit as st
from redis import Redis
from streamlit_folium import st_folium
from utils import get_full_coordinates, get_member_cordinates_by_location, r, draw_map_with_circle, \
    draw_map_by_distance

st.set_page_config(page_title="Redis Geospatial Application", page_icon="redis.png")
st.write("**This application uses redis geospatial data structures.**")


tab1, tab2, tab3 = st.tabs(["Create", "Circle Marker", "Distance"])

# Create
with tab1:
    st.subheader("Add new geospatial data with Geocoding API")
    api_key = st.text_input("API Key", placeholder="Type your Geolocation API Key")
    city = st.text_input("City", placeholder="Type city name.For better result don't use Non-English characters.")
    district = st.text_input("District", placeholder="Type the district name that matches the city."
                                                     "For better result don't use Non-English characters.")

    if button := st.button("Find Cordinates"):
        try:
            coordinates = get_full_coordinates(city, district, api_key)
            if not api_key or not city or not district:
                st.error("Some input missing or incorrect. Check it and try again!")
            if coordinates["status"] == "Missing district" and api_key and city:
                st.error("Please type district correctly.")
            if coordinates["status"] == "OK":
                st.success(f"**Added** ***{district}/{city}*** **coordinates to Redis with longtitude:** "
                           f"***{coordinates['longtitude']}***, **latitude :** ***{coordinates['latitude']}***")
        except IndexError:
            st.error("Some input missing or incorrect. Check it and try again!")

# Circle Marker
with tab2:
    circle_col1, circle_col2, circle_col3, circle_col4 = st.columns(4)

    if all_cities := [keys for keys in r.keys() if r.type(keys) == b'zset']:

        all_current_district_by_cities = [keys.decode() for keys in r.keys()
                                          if r.type(keys) == b'zset' and keys != b"Cities"]

        # First option : Select city
        city_by_circle = circle_col1.selectbox("City", all_current_district_by_cities)

        members, coordinates_of_members = get_member_cordinates_by_location(city_by_circle)

        # Second Option : Select District
        district_by_circle = circle_col2.selectbox("District", members)

        # Third Option : Type Radius
        radius_text_circle = circle_col3.text_input("Radius(m)", placeholder="Type Radius")
        # print("radius:", radius_text_circle)

        # Fourth Option : Select Distance Metric Selection
        distance_metric = circle_col4.radio("Distance Metric Selection", ("The Nearest", "Furthest"))

        # Get all district coordinates by selectbox
        district_coordinates = [[points[2], points[1]] for points in coordinates_of_members
                                if points[0] == district_by_circle][0]

        if radius_text_circle != "":
            if distance_metric == "The Nearest":
                # st.info(f"{district_coordinates[1]}, {district_coordinates[0]}")
                coordinates_with_radius = r.geosearch(name=city_by_circle,
                                                      longitude=district_coordinates[1],
                                                      latitude=district_coordinates[0],
                                                      radius=radius_text_circle, sort="ASC",
                                                      withcoord=True, withdist=True)
                if len(coordinates_with_radius) == 1:
                    st.info("**Can't find any nearest location. "
                            "Increase the radius or add new district and try again.**")
                elif len(coordinates_with_radius) == 2:
                    st.info(f"Currently, there is one location near **{district_by_circle}**.")
                    _map = draw_map_with_circle(district_coordinates, radius_text_circle, coordinates_with_radius,
                                                distance_metric,
                                                1)
                    st_folium(_map, width=750, height=500)
                else:
                    st.info(f"There seem to be {len(coordinates_with_radius) - 1} places nearby.")
                    nearest = st.select_slider("Select the nth ´nearest´ locations.",
                                               options=range(1, len(coordinates_with_radius)))
                    _map = draw_map_with_circle(district_coordinates, radius_text_circle, coordinates_with_radius,
                                                distance_metric,
                                                nearest)
                    st_folium(_map, width=750, height=500)

            else:  # Furthest
                coordinates_with_radius = r.geosearch(name=city_by_circle,
                                                      longitude=district_coordinates[1],
                                                      latitude=district_coordinates[0],
                                                      radius=radius_text_circle, sort="DESC",
                                                      withcoord=True, withdist=True)
                if len(coordinates_with_radius) == 1:
                    st.info("**The furthest location cannot be found. "
                            "Increase the radius or add new district and try again.**")
                elif len(coordinates_with_radius) == 2:
                    st.info(f"Currently, there is one location near **{district_by_circle}**.")
                    _map = draw_map_with_circle(district_coordinates, radius_text_circle, coordinates_with_radius,
                                                distance_metric, 1)
                    st_folium(_map, width=750, height=500)
                else:
                    st.info(f"There seem to be {len(coordinates_with_radius) - 1} places nearby.")
                    furthest = st.select_slider("Select the nth ´furthest´ locations.",
                                                options=range(1, len(coordinates_with_radius)))
                    _map = draw_map_with_circle(district_coordinates, radius_text_circle, coordinates_with_radius,
                                                distance_metric, furthest)
                    st_folium(_map, width=750, height=500)

    else:
        st.error("**Cannot find any geospatial data. Please fill the form and try again.**")

# Distance
with tab3:
    st.subheader("View the distance between two any locations.")
    if all_Cities := [keys for keys in r.keys() if r.type(keys) == b'zset']:

        st.write('<style>div.row-widget.stRadio > div{flex-direction:row;}</style>', unsafe_allow_html=True)
        distance_choice = st.radio("Select City distance or District distance", ("City", "District"))

        all_cities = get_member_cordinates_by_location("Cities")
        if distance_choice == "City":
            if len(r.zrange("Cities", 0, -1)) >= 2:
                city_col1, city_col2 = st.columns(2)
                first_city = city_col1.selectbox("First City", all_cities[0])
                second_city = city_col2.selectbox("Second City",
                                                  list(filter(lambda City: City != first_city, all_cities[0])))

                coordinates_of_first_city = list((first_city,) + r.geopos("Cities", first_city)[0])
                coordinates_of_second_city = list((second_city,) + r.geopos("Cities", second_city)[0])
                _map = draw_map_by_distance(locations=[coordinates_of_first_city, coordinates_of_second_city],
                                            distances=r.geodist("Cities", first_city, second_city, unit="km"),
                                            zoom_start=7)
                st_folium(_map, width=750, height=500)
            else:
                st.error("**At least two cities are needed to compare.**")
        else:  # District
            city_col1, city_col2, city_col3 = st.columns(3)
            city = city_col1.selectbox("Choose City", all_cities[0])

            if len(r.zrange(city, 0, -1)) >= 2:
                members, coordinates_of_members = get_member_cordinates_by_location(city)
                first_district = city_col2.selectbox("Select the first district of city.", members)
                coordinates_of_first_district = [points for points in coordinates_of_members
                                                 if points[0] == first_district][0]

                second_district = city_col3.selectbox("Select the second district of city.",
                                                      list(filter(lambda City: City != first_district, members)))

                coordinates_of_second_district = [points for points in coordinates_of_members
                                                  if points[0] == second_district][0]

                _map = draw_map_by_distance(locations=[coordinates_of_first_district, coordinates_of_second_district],
                                            distances=r.geodist(city, first_district, second_district, unit="km"),
                                            zoom_start=12)
                st_folium(_map, width=750, height=500)

            else:
                st.error(f"**To view the distance, you need at least two districts of {city}.**")

    else:
        st.error("**Cannot find any geospatial data. Please fill the form and try again.**")
