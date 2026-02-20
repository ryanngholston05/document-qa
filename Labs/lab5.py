import streamlit as st
from openai import OpenAI
import requests
import json

import requests


#TOOL
weather_tool = [
    {
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "Get current weather for a given location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City, State, Country"
                    }
                },
                "required": ["location"]
            }
        }
    }
]

#ASSIGNING API KEYS TO VARIABLES
client = OpenAI(api_key=st.secrets["OPENAI_KEY"])
api_key = st.secrets["WEATHER_KEY"]


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

#TESTING KEY
# print(get_current_weather("Syracuse, NY, US", api_key))
# print(get_current_weather("Lima, Peru", api_key))


#UI FOR BOT
st.title("What Should I Wear Today?")

client = OpenAI(api_key=st.secrets["OPENAI_KEY"])
weather_api_key = st.secrets["WEATHER_KEY"]

city = st.text_input("Enter a city:")


if city:
    messages = [
        {"role": "user", "content": f"What should I wear in {city} today?"}
    ]

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        tools=weather_tool,
        tool_choice="auto"
    )

    tool_calls = response.choices[0].message.tool_calls

    if tool_calls:
        location = json.loads(tool_calls[0].function.arguments)["location"]
        weather_data = get_current_weather(location, weather_api_key)
        final_response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": f"""
                        The current weather in {weather_data['location']} is:
                        Temperature: {weather_data['temperature']}°F
                        Feels like: {weather_data['feels_like']}°F
                        Description: {weather_data['description']}
                        Humidity: {weather_data['humidity']}%

                        What clothes should I wear today?
                        Suggest appropriate outdoor activities.
                        """
                    }
                ]
            )

    st.write(final_response.choices[0].message.content)

else:
    st.write("Enter a city to get clothing + activity suggestions.")


