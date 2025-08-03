#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import os
import sys
import json
import time
import math
import requests
from datetime import datetime, timezone, timedelta
from PIL import Image, ImageDraw, ImageFont

# Setup paths
picdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'pic')
libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib')
if os.path.exists(libdir):
    sys.path.append(libdir)

from waveshare_epd import epd2in13_V4

# Constants
WEATHER_API_URL = "https://api.weather.gov/stations/KDCA/observations/latest"  # Replace with your nearest station
REFRESH_INTERVAL = 60  # seconds
BAR_WIDTH = 122

# Helper to fetch weather data
def fetch_weather():
    try:
        response = requests.get(WEATHER_API_URL, timeout=10)
        data = response.json()
        props = data['properties']

        temp = props.get('temperature', {}).get('value')
        dewpoint = props.get('dewpoint', {}).get('value')
        humidity = props.get('relativeHumidity', {}).get('value')

        if temp is not None:
            temp = round(temp * 9/5 + 32, 1)  # Celsius to Fahrenheit
        else:
            temp = 'N/A'

        if dewpoint is not None:
            dewpoint = round(dewpoint * 9/5 + 32, 1)
        else:
            dewpoint = 'N/A'

        if humidity is not None:
            humidity = round(humidity, 1)
        else:
            humidity = 'N/A'

        # Estimate wet bulb temperature (approximate formula)
        if isinstance(temp, float) and isinstance(dewpoint, float):
            wbt = temp * math.atan(0.151977 * (dewpoint + 8.313659)**0.5) + math.atan(temp + dewpoint) - math.atan(dewpoint - 1.676331) + 0.00391838 * (dewpoint)**1.5 * math.atan(0.023101 * dewpoint) - 4.686035
            wbt = round(wbt, 1)
        else:
            wbt = 'N/A'

        timestamp = props.get('timestamp')
        if timestamp:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            est = dt.astimezone(timezone(timedelta(hours=-5)))
            updated_time = est.strftime("%Y-%m-%d %I:%M:%S %p EST")
        else:
            updated_time = 'N/A'

        return temp, dewpoint, humidity, wbt, updated_time

    except Exception as e:
        print(f"Weather fetch error: {e}")
        return 'N/A', 'N/A', 'N/A', 'N/A', 'N/A'

# Setup e-Paper
epd = epd2in13_V4.EPD()
epd.init()
epd.Clear(0xFF)
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 14)  # Use monospace for alignment

try:
    while True:
        start_time = time.time()
        temp, dew, rh, wbt, updated = fetch_weather()

        full_image = Image.new('1', (epd.height, epd.width), 255)
        draw = ImageDraw.Draw(full_image)

        draw.text((5, 0),  f"Temp:      {temp:>6} °F", font=font, fill=0)
        draw.text((5, 20), f"Dew Point: {dew:>6} °F", font=font, fill=0)
        draw.text((5, 40), f"Humidity:  {rh:>6} %",  font=font, fill=0)
        draw.text((5, 60), f"Wet Bulb:  {wbt:>6} °F", font=font, fill=0)
        draw.text((5, 80), f"Updated:   {updated}",  font=font, fill=0)

        epd.display(epd.getbuffer(full_image))

        for i in range(REFRESH_INTERVAL):
            bar_img = full_image.copy()
            draw_bar = ImageDraw.Draw(bar_img)
            bar_width = int((i + 1) / REFRESH_INTERVAL * BAR_WIDTH)
            draw_bar.rectangle((0, epd.width - 5, bar_width, epd.width), fill=0)
            epd.displayPartial(epd.getbuffer(bar_img))
            time.sleep(1)

except KeyboardInterrupt:
    print("Exiting...")

finally:
    epd.init()
    epd.Clear(0xFF)
    epd.sleep()
    print("Goodbye!")

