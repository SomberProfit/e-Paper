#!/usr/bin/python
# -*- coding:utf-8 -*-
import sys
import os
import time
import logging
import requests
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
        return r.json()['bitcoin']['usd']
    except Exception as e:
        logging.warning(f"Error fetching BTC price: {e}")
        return None

try:
    logging.info("BTC Price + Sparkline Display Starting")

    epd = epd2in13_V4.EPD()
    epd.init()
    epd.Clear(0xFF)

    font24 = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 24)

    # Partial update base image
    base_image = Image.new('1', (epd.height, epd.width), 255)
    epd.displayPartBaseImage(epd.getbuffer(base_image))

    UPDATE_INTERVAL = 2.0
    BAR_HEIGHT = 8
    BAR_Y = epd.width - BAR_HEIGHT

    sparkline_path = os.path.join(picdir, 'btc_sparkline.bmp')
    if os.path.exists(sparkline_path):
        sparkline = Image.open(sparkline_path).resize((epd.height, 30)).convert('1')
    else:
        sparkline = None

    while True:
        price = get_btc_price()

        for i in range(10):  # 10 slices per 2 seconds
            image = Image.new('1', (epd.height, epd.width), 255)
            draw = ImageDraw.Draw(image)

            # Text
            if price is not None:
                text = f"BTC: ${price:,.2f}"
            else:
                text = "BTC: ERROR"

            text_width, _ = draw.textsize(text, font=font24)
            x = (epd.height - text_width) // 2
            y = 0
            draw.text((x, y), text, font=font24, fill=0)

            # Sparkline (below text)
            if sparkline:
                image.paste(sparkline, (0, 30))

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