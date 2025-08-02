#!/usr/bin/python
# -*- coding:utf-8 -*-
import sys
import os
import time
import logging
import traceback
from math import sin, cos, pi
import tty
import termios
import select
from PIL import Image, ImageDraw, ImageFont

# Setup paths for e-Paper library and assets
picdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'pic')
libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib')
if os.path.exists(libdir):
    sys.path.append(libdir)

from waveshare_epd import epd2in13_V4

logging.basicConfig(level=logging.DEBUG)

def key_pressed():
    dr, dw, de = select.select([sys.stdin], [], [], 0)
    return dr != []

def draw_zombie_elon(draw):
    # Head
    draw.rectangle((60, 20, 120, 80), outline=0)

    # Eyes (squares)
    draw.rectangle((70, 35, 78, 43), fill=0)
    draw.rectangle((102, 35, 110, 43), fill=0)

    # Jagged mouth
    draw.line([(75, 65), (80, 68), (85, 65), (90, 68), (95, 65)], fill=0)

    # Wild hair
    draw.line([(60, 20), (50, 10), (60, 10), (70, 20)], fill=0)
    draw.line([(120, 20), (130, 10), (120, 10), (110, 20)], fill=0)

    # Shoulders
    draw.arc((50, 75, 90, 110), 0, 180, fill=0)
    draw.arc((90, 75, 130, 110), 0, 180, fill=0)

    # Text
    draw.text((40, 100), "ZOMBIE ELON", font=font24, fill=0)

try:
    logging.info("epd2in13_V4 Zombie Elon Demo")

    epd = epd2in13_V4.EPD()
    epd.init()
    epd.Clear(0xFF)

    font24 = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 24)

    # Set terminal input to raw mode
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    tty.setcbreak(fd)

    # Prepare partial update base image
    base_image = Image.new('1', (epd.height, epd.width), 255)
    epd.displayPartBaseImage(epd.getbuffer(base_image))

    logging.info("Displaying zombie... Press any key to stop.")
    angle = 0
    while True:
        if key_pressed():
            break

        image = Image.new('1', (epd.height, epd.width), 255)
        draw = ImageDraw.Draw(image)

        # Slight rotation effect (head jitter)
        offset = int(3 * sin(angle * pi / 180))
        draw_zombie_elon(draw)

        epd.displayPartial(epd.getbuffer(image))
        time.sleep(0.3)
        angle = (angle + 15) % 360

    logging.info("Exiting...")

    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    epd.init()
    epd.Clear(0xFF)
    epd.sleep()

except IOError as e:
    logging.error(e)
    try:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    except:
        pass

except KeyboardInterrupt:
    logging.info("ctrl + c:")
    epd2in13_V4.epdconfig.module_exit(cleanup=True)
    try:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    except:
        pass
    exit()
