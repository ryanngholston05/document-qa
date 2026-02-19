import streamlit as st
from openai import OpenAI
import requests

import requests

api_key = api_key = st.secrets["WEATHER_KEY"]

def get_current_weather(location, api_key, units='imperial'):
    url = (
        f'https://api.openweathermap.org/data/2.5/weather'
        f'?q={location}&appid={api_key}&units={units}'
    )
    
    response = requests.get(url)

    if response.status_code == 401:
        raise Exception('Invalid API key')
    if response.status_code == 404:
        raise Exception('Location not found')

    data = response.json()

    return {
        "location": location,
        "temperature": round(data['main']['temp'], 2),
        "feels_like": round(data['main']['feels_like'], 2),
        "temp_min": round(data['main']['temp_min'], 2),
        "temp_max": round(data['main']['temp_max'], 2),
        "humidity": data['main']['humidity'],
        "description": data['weather'][0]['description']
    }

print(get_current_weather("Syracuse, NY, US", api_key))
print(get_current_weather("Lima, Peru", api_key))



