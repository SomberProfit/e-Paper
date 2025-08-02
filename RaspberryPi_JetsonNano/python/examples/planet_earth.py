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

def draw_rotated_triangle_with_eye(draw, center, size, angle_deg):
    """Draw a rotating triangle with a symbolic 'eye' in the middle."""
    cx, cy = center
    angle_rad = angle_deg * pi / 180
    points = []
    for i in range(3):
        theta = 2 * pi * i / 3 + angle_rad
        x = cx + size * cos(theta)
        y = cy + size * sin(theta)
        points.append((x, y))
    
    # Draw triangle
    draw.polygon(points, outline=0)

    # Draw simple "eye" inside (just a horizontal ellipse and pupil)
    eye_rx, eye_ry = size // 3, size // 6
    draw.ellipse((cx - eye_rx, cy - eye_ry, cx + eye_rx, cy + eye_ry), outline=0)
    draw.ellipse((cx - 2, cy - 2, cx + 2, cy + 2), fill=0)

try:
    logging.info("epd2in13_V4 Illuminati Eye Demo")

    epd = epd2in13_V4.EPD()
    epd.init()
    epd.Clear(0xFF)

    font24 = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 24)

    # Set stdin to raw mode to detect single keypresses
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    tty.setcbreak(fd)

    # Set base image for partial updates
    base_image = Image.new('1', (epd.height, epd.width), 255)
    epd.displayPartBaseImage(epd.getbuffer(base_image))

    angle = 0
    logging.info("Spinning Illuminati... Press any key to exit.")
    while True:
        if key_pressed():
            break

        image = Image.new('1', (epd.height, epd.width), 255)
        draw = ImageDraw.Draw(image)

        # Draw rotating triangle + eye
        draw_rotated_triangle_with_eye(draw, center=(epd.height // 2, epd.width // 2 - 10), size=30, angle_deg=angle)

        # Center and draw text
        text = 'ARIEL IS NOSY >:('
        text_width, _ = draw.textsize(text, font=font24)
        x_text = (epd.height - text_width) // 2
        y_text = epd.width - 30
        draw.text((x_text, y_text), text, font=font24, fill=0)

        epd.displayPartial(epd.getbuffer(image))
        time.sleep(0.3)
        angle = (angle + 10) % 360

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
