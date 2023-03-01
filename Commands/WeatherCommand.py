import json
from typing import Optional

import discord
from pyowm import OWM

class Weather:
    def __init__(self):
        self.owm = OWM("e8cb46219d5ddaca75ca1d604e8edbeb")
        self.mgr = self.owm.weather_manager()

    async def getWeather(self, interaction: discord.Interaction, city: str, country_code: Optional[str]=""):
        observation = self.mgr.weather_at_place(city+","+country_code)
        w = observation.weather 

        weatherDict = {
            "city": city,
            "detailed": w.detailed_status,
            "temp": w.temperature('celsius'),
            "rain": w.rain,
            "wind": w.wind('km_hour'),
            "humidity": w.humidity,
            "clouds": w.clouds
        }
        await interaction.response.send_message("Getting Weather-Data...")
        await interaction.channel.send(embed=self.buildWeatherEmbed(dictionary=weatherDict))

    def buildWeatherEmbed(self, dictionary: dict):
        current_temp = dictionary["temp"]["temp"]
        max_temp = dictionary["temp"]["temp_max"]
        min_temp = dictionary["temp"]["temp_min"]
        cloud_perc = dictionary["clouds"]
        humidity_perc = dictionary["humidity"]
        wind_speed = float(round(dictionary["wind"]["speed"], 2))
        wind_deg = dictionary["wind"]["deg"]

        temp_emoji = self.get_temp_emoji(current_temp)
        cloud_emoji = self.get_cloud_emoji(cloud_perc)
        humidity_emoji = self.get_humidity_emoji(humidity_perc)
        wind_speed_emoji = self.get_wind_speed_emoji(wind_speed)

        embed = discord.Embed(
            title=f"« ≈ Weather in {dictionary['city']} ≈ »",
        )
        embed.add_field(name="Status", value=f"Weather: {dictionary['detailed']} \nClouds: {cloud_perc}% {cloud_emoji} \nHumidity: {humidity_perc}%{humidity_emoji}", inline=False)
        embed.add_field(name="Temperature", value=f"Current Temperature: {current_temp}°C{temp_emoji} \nMax Temperature: {max_temp}°C \nMin Temperature: {min_temp}°C", inline=False)
        embed.add_field(name="Wind", value=f"Wind-Speed: {wind_speed}km/h{wind_speed_emoji} \nWind-Degree: {wind_deg}°", inline=False)
        return embed
  
    def get_temp_emoji(self, temp):
        if temp < 0:
            return "❄️"
        if temp < 15:
            return "🌡️"
        if temp < 25:
            return "🌞"
        if temp < 35:
            return "🥵"
        return "🔥"

    def get_cloud_emoji(self, perc):
        if perc < 20:
            return "☀️"
        if perc < 50:
            return "🌤️"
        if perc < 80:
            return "⛅"
        if perc < 100:
            return "🌥️"
        return "☁️"

    def get_humidity_emoji(self, perc):
        if perc < 50:
            return "💧"
        if perc < 80:
            return "💦"
        return "🌊"

    def get_wind_speed_emoji(self, speed):
        if speed < 38.5:
            return "🌬️"
        if speed < 60:
            return "💨"
        return "🌪️"