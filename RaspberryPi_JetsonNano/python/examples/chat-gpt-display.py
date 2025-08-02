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

def wrap_text(text, draw, font, max_width):
    lines = []
    for paragraph in text.split('\n'):
        words = paragraph.split()
        line = ""
        for word in words:
            test_line = f"{line} {word}" if line else word
            if draw.textlength(test_line, font=font) <= max_width:
                line = test_line
            else:
                lines.append(line)
                line = word
        if line:
            lines.append(line)
    return lines

# Setup e-Paper
epd = epd2in13_V4.EPD()
epd.init()
epd.Clear(0xFF)
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
max_width = epd.height - 5
line_height = 14
max_lines = epd.width // line_height

# Track conversation text and y-position
screen_lines = []

try:
    while True:
        print("Ask ChatGPT:")
        prompt = input("> ")

        print("\nThinking...\n")
        thinking_img = Image.new('1', (epd.height, epd.width), 255)
        thinking_draw = ImageDraw.Draw(thinking_img)
        thinking_lines = screen_lines + wrap_text("Thinking...", thinking_draw, font, max_width)

        while len(thinking_lines) > max_lines:
            thinking_lines.pop(0)

        y = 0
        for line in thinking_lines:
            thinking_draw.text((0, y), line.strip(), font=font, fill=0)
            y += line_height
        epd.displayPartBaseImage(epd.getbuffer(thinking_img))

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

            # Wrap and format
            image = Image.new('1', (epd.height, epd.width), 255)
            draw = ImageDraw.Draw(image)
            wrapped = wrap_text(answer, draw, font, max_width)
            new_lines = wrapped + ["----------"]
            screen_lines.extend(new_lines)
            while len(screen_lines) > max_lines:
                screen_lines.pop(0)

            y = 0
            for line in screen_lines:
                draw.text((0, y), line.strip(), font=font, fill=0)
                y += line_height
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

