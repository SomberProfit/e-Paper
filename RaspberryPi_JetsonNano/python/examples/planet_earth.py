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

def draw_wire_sphere(draw, center, radius, rotation_angle_deg):
    cx, cy = center
    steps = 20
    angle_rad = rotation_angle_deg * pi / 180

    for i in range(steps):
        theta = 2 * pi * i / steps + angle_rad
        x = int(cx + radius * cos(theta))
        draw.line((x, cy - radius, x, cy + radius), fill=0)

    for j in range(-2, 3):
        ry = int(radius * cos(j * pi / 6))
        draw.ellipse((cx - radius, cy - ry, cx + radius, cy + ry), outline=0)

try:
    logging.info("epd2in13_V4 Spinning Sphere Demo")

    epd = epd2in13_V4.EPD()
    logging.info("init and clear")
    epd.init()
    epd.Clear(0xFF)

    font15 = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 15)
    font24 = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 24)

    # Set stdin to raw mode
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    tty.setcbreak(fd)

    angle = 0
    logging.info("Spinning... Press any key to exit.")
    while True:
        if key_pressed():
            break

        image = Image.new('1', (epd.height, epd.width), 255)  # 255 = white
        draw = ImageDraw.Draw(image)

        draw_wire_sphere(draw, center=(epd.height // 2, epd.width // 2 - 10), radius=30, rotation_angle_deg=angle)
        draw.text((epd.height // 2 - 45, epd.width - 30), 'EARTH CORP.', font=font24, fill=0)

        epd.display(epd.getbuffer(image))
        time.sleep(0.3)
        angle = (angle + 15) % 360

    logging.info("Exiting...")

    # Restore terminal and shutdown display
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
