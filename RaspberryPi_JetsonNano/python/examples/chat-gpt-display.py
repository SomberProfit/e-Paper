#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import openai
import os
import sys
import tty
import termios
import select
import time
from PIL import Image, ImageDraw

# Setup paths
picdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'pic')
libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib')
if os.path.exists(libdir):
    sys.path.append(libdir)

from waveshare_epd import epd2in13_V4

# Configure OpenAI client
api_key = os.getenv("OPENAI_API_KEY") or "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"
client = openai.OpenAI(api_key=api_key)

# Prepare e-Paper
epd = epd2in13_V4.EPD()
epd.init()
epd.Clear(0xFF)

# Setup drawing
image = Image.new('1', (epd.height, epd.width), 255)
draw = ImageDraw.Draw(image)

# Terminal settings for keypress
fd = sys.stdin.fileno()
old_settings = termios.tcgetattr(fd)
tty.setcbreak(fd)

def draw_spinner(draw, frame):
    spinner = ['|', '/', '-', '\\']
    draw.rectangle((100, 60, 120, 80), fill=255)
    draw.text((105, 65), spinner[frame % 4], fill=0)

def get_keypress():
    dr, _, _ = select.select([sys.stdin], [], [], 0)
    if dr:
        return sys.stdin.read(1)
    return None

try:
    while True:
        print("Describe a scene to draw on the e-Paper display:")
        description = input("> ")

        # Show loading spinner
        frame = 0
        spinner_active = True

        import threading
        response_container = {}

        def fetch_code():
            return client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a Python assistant that generates minimal 1-bit image drawing code using PIL for a Waveshare e-Paper display. Return only valid Python code that uses ImageDraw to render the requested scene."},
                    {"role": "user", "content": f"Create a scene: {description}"}
                ]
            )

        def worker():
            try:
                response_container['response'] = fetch_code()
            except Exception as e:
                response_container['error'] = str(e)
            finally:
                global spinner_active
                spinner_active = False

        thread = threading.Thread(target=worker)
        thread.start()

        while spinner_active:
            image = Image.new('1', (epd.height, epd.width), 255)
            draw = ImageDraw.Draw(image)
            draw.text((10, 50), "Talking to ChatGPT...", fill=0)
            draw_spinner(draw, frame)
            epd.displayPartial(epd.getbuffer(image))
            frame += 1
            time.sleep(0.2)

        if 'error' in response_container:
            print("Error from OpenAI:", response_container['error'])
            continue

        response = response_container['response']

        # Extract and run generated code
        code = response.choices[0].message.content

        image = Image.new('1', (epd.height, epd.width), 255)
        draw = ImageDraw.Draw(image)

        namespace = {"ImageDraw": ImageDraw, "Image": Image, "draw": draw, "epd": epd}
        try:
            exec(code, namespace)
        except Exception as e:
            draw.text((10, 60), f"Error: {str(e)}", fill=0)

        epd.displayPartBaseImage(epd.getbuffer(image))
        with open("generated_scene.py", "w") as f:
            f.write(code)

        print("Scene drawn and saved to generated_scene.py\nPress any key to continue or Ctrl+C to exit.")
        while not get_keypress():
            time.sleep(0.1)

except KeyboardInterrupt:
    print("Exiting...")

finally:
    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    epd.init()
    epd.Clear(0xFF)
    epd.sleep()
    print("Display cleared and sleeping")

