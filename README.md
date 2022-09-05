# Redis_Geospatial_App

![Redis-Streamlit2](https://user-images.githubusercontent.com/63010257/188336133-c8778ffc-5166-4055-98d6-bcf690101d96.png)


# Installation

## Docker Redis Setup

#### Pulling Redis Official Image from Docker Hub
**docker pull redis**

#### Converting Docker Image to Container and Start Redis
**docker run --rm -i -t -p 6379:6379 --name local-redis redis**


## Python Libraries
**pip install -r requirements.txt**

# Starting Streamlit

**streamlit run .\main.py**


You can reach the medium article on Redis geo commands and project details from the link below.
https://medium.com/@TugrulGokce/redis-geospatial-app-with-geocoding-api-streamlit-and-folium-3937029b5420


Application Demo
https://www.youtube.com/watch?v=KQ6OIbNBjpE
