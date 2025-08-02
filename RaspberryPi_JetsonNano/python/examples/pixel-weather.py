#!/usr/bin/python
# -*- coding:utf-8 -*-
import sys
import os
import time
import tty
import termios
import select
import logging
import random
from datetime import datetime
from PIL import Image, ImageDraw

# Setup paths
picdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'pic')
libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib')
if os.path.exists(libdir):
    sys.path.append(libdir)

from waveshare_epd import epd2in13_V4

logging.basicConfig(level=logging.INFO)

# Simulation constants
NUM_CLOUDS = 3
CLOUD_WIDTH = 40
NUM_PARTICLES = 25
PARTICLE_SPEED = 2
NUM_FIREFLIES = 15

clouds = [{'x': random.randint(0, 250), 'y': random.randint(0, 20)} for _ in range(NUM_CLOUDS)]
particles = [{'x': random.randint(0, 250), 'y': random.randint(30, 122)} for _ in range(NUM_PARTICLES)]
fireflies = [{'x': random.randint(0, 250), 'y': random.randint(30, 100), 'blink': False} for _ in range(NUM_FIREFLIES)]

def is_night_time():
    now = datetime.now()
    return now.hour > 20 or (now.hour == 20 and now.minute >= 30)

def get_keypress():
    dr, _, _ = select.select([sys.stdin], [], [], 0)
    if dr:
        return sys.stdin.read(1)
    return None

def draw_city(draw):
    draw.rectangle((0, 110, 250, 122), fill=0)
    for x in range(0, 250, 20):
        height = random.randint(5, 10)
        draw.rectangle((x + 2, 122 - height, x + 10, 122), fill=0)

def draw_cloud(draw, x, y):
    draw.ellipse((x, y, x + 20, y + 10), fill=0)
    draw.ellipse((x + 10, y - 5, x + 30, y + 7), fill=0)
    draw.ellipse((x + 20, y, x + 40, y + 10), fill=0)

def draw_sun(draw):
    draw.ellipse((200, 5, 220, 25), outline=0)

def draw_moon(draw):
    draw.ellipse((200, 5, 220, 25), fill=0)
    draw.ellipse((205, 5, 225, 25), fill=1)

def draw_house(draw, base_x, base_y):
    draw.rectangle((base_x, base_y - 20, base_x + 30, base_y), outline=0, fill=255)
    draw.polygon([(base_x - 2, base_y - 20), (base_x + 15, base_y - 35), (base_x + 32, base_y - 20)], outline=0)
    draw.rectangle((base_x + 12, base_y - 10, base_x + 18, base_y), outline=0)

def draw_person(draw, x, y, is_female=False):
    draw.ellipse((x - 2, y - 6, x + 2, y - 2), fill=0)
    draw.line((x, y - 2, x, y + 4), fill=0)
    draw.line((x, y, x - 2, y + 3), fill=0)
    draw.line((x, y, x + 2, y + 3), fill=0)
    if is_female:
        draw.line((x, y - 2, x - 3, y + 1), fill=0)
        draw.line((x, y - 2, x + 3, y + 1), fill=0)
    else:
        draw.line((x, y - 2, x - 3, y), fill=0)
        draw.line((x, y - 2, x + 3, y), fill=0)

def draw_dog(draw, x, y):
    draw.rectangle((x, y, x + 6, y + 3), fill=0)
    draw.point((x + 6, y), fill=0)
    draw.point((x + 1, y - 1), fill=0)
    draw.point((x + 2, y + 4), fill=0)

def draw_tree(draw, base_x, base_y):
    draw.rectangle((base_x + 4, base_y - 20, base_x + 6, base_y), fill=0)
    draw.polygon([(base_x - 10, base_y - 20), (base_x + 5, base_y - 35), (base_x + 20, base_y - 20)], outline=0)
    draw.polygon([(base_x - 8, base_y - 25), (base_x + 5, base_y - 40), (base_x + 18, base_y - 25)], outline=0)
    draw.polygon([(base_x - 6, base_y - 30), (base_x + 5, base_y - 45), (base_x + 16, base_y - 30)], outline=0)

def draw_fireflies(draw):
    for f in fireflies:
        f['blink'] = random.random() > 0.8
        if f['blink']:
            draw.point((f['x'], f['y']), fill=0)

try:
    logging.info("Pixel Weather Scene with Ctrl+T toggle")

    epd = epd2in13_V4.EPD()
    epd.init()
    epd.Clear(0xFF)

    base = Image.new('1', (epd.height, epd.width), 255)
    epd.displayPartBaseImage(epd.getbuffer(base))

    # Set terminal to raw mode for keypresses
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    tty.setcbreak(fd)

    # Start with real-time based mode
    night = is_night_time()

    while True:
        # Toggle manually with Ctrl+T
        key = get_keypress()
        if key == '\x14':  # Ctrl+T
            night = not night
            logging.info("Toggled night mode: %s", night)

        image = Image.new('1', (epd.height, epd.width), 255)
        draw = ImageDraw.Draw(image)

        draw_moon(draw) if night else draw_sun(draw)

        for cloud in clouds:
            draw_cloud(draw, cloud['x'], cloud['y'])
            cloud['x'] -= 1
            if cloud['x'] < -CLOUD_WIDTH:
                cloud['x'] = epd.height
                cloud['y'] = random.randint(0, 20)

        for p in particles:
            draw.point((p['x'], p['y']), fill=0)
            p['y'] += PARTICLE_SPEED
            if p['y'] > epd.width:
                p['x'] = random.randint(0, epd.height)
                p['y'] = random.randint(30, 40)

        draw_city(draw)
        draw_house(draw, 30, 110)
        draw_tree(draw, 160, 110)
        draw_person(draw, 90, 106, is_female=False)
        draw_person(draw, 100, 106, is_female=True)
        draw_dog(draw, 110, 108)

        if night:
            draw_fireflies(draw)

        epd.displayPartial(epd.getbuffer(image))
        time.sleep(0.1)

except KeyboardInterrupt:
    logging.info("Interrupted by user")

finally:
    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    epd.init()
    epd.Clear(0xFF)
    epd.sleep()
    logging.info("Display cleared and sleeping")
