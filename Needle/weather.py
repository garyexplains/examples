# python3 -m venv needle-env
# source needle-env/bin/activate
# pip install cactus-needle
# pip install requests
import needle
import subprocess
#from pathlib import Path
import requests

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# Comprehensive mapping of WMO codes to Open-Meteo English descriptions
WMO_WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snowfall",
    73: "Moderate snowfall",
    75: "Heavy snowfall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail"
}
def get_weather_description(code: int) -> str:
    """Returns the English text description for a given WMO weather code."""
    return WMO_WEATHER_CODES.get(code, f"Unknown weather code ({code})")

def get_coordinates(city_name):
  """Turn a city name into latitude and longitude."""
  response = requests.get(GEOCODING_URL, params={"name": city_name, "count": 1})
  response.raise_for_status()
  results = response.json().get("results")
  if results:
    return results[0]["latitude"], results[0]["longitude"]
  return None, None


def get_weather_by_city(city_name):
  """Fetch current weather for a city name."""
  lat, lon = get_coordinates(city_name)
  if lat is None or lon is None:
    return f"City '{city_name}' not found."

  response = requests.get(
      FORECAST_URL,
      params={
          "latitude": lat,
          "longitude": lon,
          "current": "temperature_2m,weather_code",
          "timezone": "auto",
      },
  )
  response.raise_for_status()
  return response.json()


@needle.tool
def get_weather(city: str):
    "Get the current weather for a city."

    weather_data = get_weather_by_city(city)
    return {"city": city, "temp_c": weather_data["current"]["temperature_2m"], "sky": get_weather_description(weather_data["current"]["weather_code"])}

@needle.tool
def get_cpu_temperature():

    """Return the current CPU temperature of this Raspberry Pi in Celsius."""

    out = subprocess.check_output(["vcgencmd", "measure_temp"], text=True)

    return {"temperature_c": float(out.split("=")[1].split("'")[0])}



agent = needle.Needle(tools=[get_weather, get_cpu_temperature])
print(agent.run("what's it like in London right now?")["results"])
agent.reset()
print(agent.run("What is the CPU temp?")["results"])
