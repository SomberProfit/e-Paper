#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import openai
import os
import sys
import tty
import termios
import select
import time
from PIL import Image, ImageDraw, ImageFont

# Setup paths
picdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'pic')
libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib')
if os.path.exists(libdir):
    sys.path.append(libdir)

from waveshare_epd import epd2in13_V4

# Configure OpenAI client
api_key = os.getenv("OPENAI_API_KEY") or "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"
client = openai.OpenAI(api_key=api_key)

# Terminal settings for keypress
fd = sys.stdin.fileno()
old_settings = termios.tcgetattr(fd)
tty.setcbreak(fd)

def get_keypress():
    dr, _, _ = select.select([sys.stdin], [], [], 0)
    if dr:
        return sys.stdin.read(1)
    return None

# Setup e-Paper
epd = epd2in13_V4.EPD()
epd.init()
epd.Clear(0xFF)
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)

try:
    while True:
        print("Ask ChatGPT:")
        prompt = input("> ")

        print("\nThinking...\n")

        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            answer = response.choices[0].message.content
            print("ChatGPT Response:\n")
            print(answer)

            # Display answer on e-Paper
            image = Image.new('1', (epd.height, epd.width), 255)
            draw = ImageDraw.Draw(image)
            y = 0
            for line in answer.split('\n'):
                draw.text((0, y), line.strip(), font=font, fill=0)
                y += 14
            epd.displayPartBaseImage(epd.getbuffer(image))

        except Exception as e:
            print("Error from OpenAI:", str(e))

        print("\nPress any key to continue or Ctrl+C to exit.")
        while not get_keypress():
            time.sleep(0.1)

except KeyboardInterrupt:
    print("Exiting...")

finally:
    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    epd.init()
    epd.Clear(0xFF)
    epd.sleep()
    print("Goodbye!")

