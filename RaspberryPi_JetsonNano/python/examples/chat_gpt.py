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

# Configure OpenAI
openai.api_key = "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"

# Prepare e-Paper
epd = epd2in13_V4.EPD()
epd.init()
epd.Clear(0xFF)

# Setup drawing
image = Image.new('1', (epd.height, epd.width), 255)
draw = ImageDraw.Draw(image)

def draw_spinner(draw, frame):
    spinner = ['|', '/', '-', '\\']
    draw.rectangle((100, 60, 120, 80), fill=255)
    draw.text((105, 65), spinner[frame % 4], fill=0)

print("Describe a scene to draw on the e-Paper display:")
description = input("> ")

# Show loading spinner
frame = 0
start_time = time.time()
spinner_active = True

def fetch_code():
    return openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a Python assistant that generates minimal 1-bit image drawing code using PIL for a Waveshare e-Paper display. Return only valid Python code that uses ImageDraw to render the requested scene."},
            {"role": "user", "content": f"Create a scene: {description}"}
        ]
    )

import threading
response_container = {}
def worker():
    response_container['response'] = fetch_code()
    global spinner_active
    spinner_active = False

thread = threading.Thread(target=worker)
thread.start()

while spinner_active:
    draw.rectangle((0, 0, epd.height, epd.width), fill=255)
    draw.text((10, 50), "Talking to ChatGPT...", fill=0)
    draw_spinner(draw, frame)
    epd.displayPartial(epd.getbuffer(image))
    frame += 1
    time.sleep(0.2)

response = response_container['response']

# Extract generated Python code
code = response['choices'][0]['message']['content']

# Run the generated code in a sandboxed namespace
image = Image.new('1', (epd.height, epd.width), 255)
draw = ImageDraw.Draw(image)

namespace = {"ImageDraw": ImageDraw, "Image": Image, "draw": draw, "epd": epd}
exec(code, namespace)

# Display image
epd.displayPartBaseImage(epd.getbuffer(image))
time.sleep(2)
epd.sleep()

# Optionally log or save the script locally
with open("generated_scene.py", "w") as f:
    f.write(code)

print("Scene drawn and saved to generated_scene.py")

