#!/usr/bin/python
# -*- coding:utf-8 -*-
import sys
import os
import tty
import termios
import time
import select
import logging
from PIL import Image, ImageDraw, ImageFont

# Setup paths
picdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'pic')
libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib')
if os.path.exists(libdir):
    sys.path.append(libdir)

from waveshare_epd import epd2in13_V4

logging.basicConfig(level=logging.DEBUG)

def get_char():
    """Read a single character without blocking."""
    if select.select([sys.stdin], [], [], 0)[0]:
        return sys.stdin.read(1)
    return None

try:
    logging.info("Live typing on e-Paper")

    epd = epd2in13_V4.EPD()
    epd.init()
    epd.Clear(0xFF)

    font = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 24)

    # Set terminal to raw mode
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    tty.setcbreak(fd)

    # Create empty display
    text = ""
    max_chars = 20  # Depends on font size
    line_height = 26

    base_image = Image.new('1', (epd.height, epd.width), 255)
    epd.displayPartBaseImage(epd.getbuffer(base_image))

    while True:
        char = get_char()
        if char:
            if char == '\x7f':  # Backspace
                text = text[:-1]
            elif char == '\n':
                text += '\n'
            elif char.isprintable():
                text += char

            # Redraw
            image = Image.new('1', (epd.height, epd.width), 255)
            draw = ImageDraw.Draw(image)

            # Break into lines
            lines = []
            line = ""
            for c in text:
                if c == '\n' or len(line) >= max_chars:
                    lines.append(line)
                    line = "" if c == '\n' else c
                else:
                    line += c
            if line:
                lines.append(line)

            # Trim to screen height
            lines = lines[-(epd.width // line_height):]

            # Draw lines
            for i, l in enumerate(lines):
                draw.text((0, i * line_height), l, font=font, fill=0)

            epd.displayPartial(epd.getbuffer(image))

        time.sleep(0.05)

except KeyboardInterrupt:
    logging.info("Interrupted by user")

finally:
    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    epd.init()
    epd.Clear(0xFF)
    epd.sleep()
    logging.info("Exited cleanly")
