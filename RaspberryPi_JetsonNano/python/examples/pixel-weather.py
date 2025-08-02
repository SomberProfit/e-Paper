#!/usr/bin/python
# -*- coding:utf-8 -*-
import sys
import os
import time
import logging
import random
from PIL import Image, ImageDraw

# Setup e-paper paths
picdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'pic')
libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib')
if os.path.exists(libdir):
    sys.path.append(libdir)

from waveshare_epd import epd2in13_V4

logging.basicConfig(level=logging.INFO)

# Cloud parameters
NUM_CLOUDS = 3
CLOUD_WIDTH = 40
CLOUD_HEIGHT = 15

# Particle parameters
NUM_PARTICLES = 20
PARTICLE_SPEED = 2

# Initialize cloud and rain positions
clouds = [{'x': random.randint(0, 250), 'y': random.randint(0, 20)} for _ in range(NUM_CLOUDS)]
particles = [{'x': random.randint(0, 250), 'y': random.randint(30, 122)} for _ in range(NUM_PARTICLES)]

def draw_city(draw):
    draw.rectangle((0, 110, 250, 122), fill=0)  # solid ground
    # buildings
    for x in range(0, 250, 20):
        height = random.randint(5, 10)
        draw.rectangle((x + 2, 122 - height, x + 10, 122), fill=0)

def draw_cloud(draw, x, y):
    draw.ellipse((x, y, x + 20, y + 10), fill=0)
    draw.ellipse((x + 10, y - 5, x + 30, y + 7), fill=0)
    draw.ellipse((x + 20, y, x + 40, y + 10), fill=0)

def draw_sun(draw):
    draw.ellipse((200, 5, 220, 25), outline=0)

try:
    logging.info("Pixel Weather Display Starting")

    epd = epd2in13_V4.EPD()
    epd.init()
    epd.Clear(0xFF)

    base = Image.new('1', (epd.height, epd.width), 255)
    epd.displayPartBaseImage(epd.getbuffer(base))

    while True:
        image = Image.new('1', (epd.height, epd.width), 255)
        draw = ImageDraw.Draw(image)

        # Sun
        draw_sun(draw)

        # Clouds
        for cloud in clouds:
            draw_cloud(draw, cloud['x'], cloud['y'])
            cloud['x'] -= 1
            if cloud['x'] < -CLOUD_WIDTH:
                cloud['x'] = epd.height
                cloud['y'] = random.randint(0, 20)

        # Rain particles
        for p in particles:
            draw.point((p['x'], p['y']), fill=0)
            p['y'] += PARTICLE_SPEED
            if p['y'] > epd.width:
                p['x'] = random.randint(0, epd.height)
                p['y'] = random.randint(30, 40)

        # City silhouette
        draw_city(draw)

        epd.displayPartial(epd.getbuffer(image))
        time.sleep(0.3)

except KeyboardInterrupt:
    logging.info("Interrupted by user")

finally:
    epd.init()
    epd.Clear(0xFF)
    epd.sleep()
    logging.info("Display cleared and sleeping")
