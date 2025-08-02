#!/usr/bin/python
# -*- coding:utf-8 -*-
import sys
import os
import time
import logging
import requests
import random
from PIL import Image, ImageDraw, ImageFont

# Setup paths
picdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'pic')
libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib')
if os.path.exists(libdir):
    sys.path.append(libdir)

from waveshare_epd import epd2in13_V4

logging.basicConfig(level=logging.INFO)

def get_btc_price():
    try:
        r = requests.get(
            'https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd',
            timeout=10
        )
        data = r.json()
        if 'bitcoin' in data and 'usd' in data['bitcoin']:
            return data['bitcoin']['usd']
        else:
            logging.warning(f"Unexpected API response: {data}")
            return None
    except Exception as e:
        logging.warning(f"Error fetching BTC price: {e}")
        return None

def draw_sparkline(draw, prices, x, y, width, height):
    if len(prices) < 2:
        return
    min_p = min(prices)
    max_p = max(prices)
    scale = (max_p - min_p) or 1
    step = width / (len(prices) - 1)
    points = []
    for i, p in enumerate(prices):
        px = x + i * step
        py = y + height - ((p - min_p) / scale) * height
        points.append((px, py))
    draw.line(points, fill=0, width=1)

try:
    logging.info("BTC Price + Drawn Sparkline Starting")

    epd = epd2in13_V4.EPD()
    epd.init()
    epd.Clear(0xFF)

    font24 = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 24)

    base_image = Image.new('1', (epd.height, epd.width), 255)
    epd.displayPartBaseImage(epd.getbuffer(base_image))

    UPDATE_INTERVAL = 2.0
    BAR_HEIGHT = 8
    BAR_Y = epd.width - BAR_HEIGHT

    # Initialize fake history
    price_history = [random.uniform(30000, 40000) for _ in range(40)]

    while True:
        price = get_btc_price()
        if price is not None:
            price_history.append(price)
            price_history = price_history[-40:]
        else:
            price_history.append(price_history[-1] if price_history else 35000)

        for i in range(10):
            image = Image.new('1', (epd.height, epd.width), 255)
            draw = ImageDraw.Draw(image)

            # Text
            if price is not None:
                text = f"BTC: ${price:,.2f}"
            else:
                text = "BTC: ERROR"

            bbox = draw.textbbox((0, 0), text, font=font24)
            text_width = bbox[2] - bbox[0]
            x_text = (epd.height - text_width) // 2
            draw.text((x_text, 0), text, font=font24, fill=0)

            # Sparkline
            draw_sparkline(draw, price_history, x=0, y=30, width=epd.height, height=30)

            # Status bar
            progress = (i + 1) / 10
            bar_fill_width = int(epd.height * progress)
            draw.rectangle((0, BAR_Y, bar_fill_width, BAR_Y + BAR_HEIGHT), fill=0)

            epd.displayPartial(epd.getbuffer(image))
            time.sleep(UPDATE_INTERVAL / 10)

except KeyboardInterrupt:
    logging.info("Interrupted by user")

finally:
    epd.init()
    epd.Clear(0xFF)
    epd.sleep()
    logging.info("Display cleared and sleeping")
