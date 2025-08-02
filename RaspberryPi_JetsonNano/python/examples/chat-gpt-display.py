#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import openai
import os
import sys
import tty
import termios
import select
import time
import json
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

# Constants
HISTORY_FILE = "chat_history.json"
SCROLL_STEP = 1

# Helpers
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

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    return []

def save_history(lines):
    with open(HISTORY_FILE, "w") as f:
        json.dump(lines, f)

def display_lines(epd, font, lines, scroll_offset, max_lines, max_width):
    image = Image.new('1', (epd.height, epd.width), 255)
    draw = ImageDraw.Draw(image)
    view = lines[scroll_offset:scroll_offset + max_lines]
    y = 0
    for line in view:
        draw.text((0, y), line.strip(), font=font, fill=0)
        y += line_height
    epd.displayPartBaseImage(epd.getbuffer(image))

# Setup e-Paper
epd = epd2in13_V4.EPD()
epd.init()
epd.Clear(0xFF)
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
max_width = epd.height - 5
line_height = 14
max_lines = epd.width // line_height

# Load history
screen_lines = load_history()
scroll_offset = max(0, len(screen_lines) - max_lines)
display_lines(epd, font, screen_lines, scroll_offset, max_lines, max_width)

# Run loop
try:
    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    while True:
        print("Ask ChatGPT:")
        prompt = input("> ")

        tty.setcbreak(fd)
        thinking_text = "Thinking..."
        screen_lines.append(thinking_text)
        scroll_offset = max(0, len(screen_lines) - max_lines)
        display_lines(epd, font, screen_lines, scroll_offset, max_lines, max_width)

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

            wrapped = wrap_text(answer, ImageDraw.Draw(Image.new('1', (epd.height, epd.width), 255)), font, max_width)
            new_lines = wrapped + ["----------"]
            screen_lines = screen_lines[:-1] + new_lines  # replace "Thinking..." with response
            save_history(screen_lines)
            scroll_offset = max(0, len(screen_lines) - max_lines)
            display_lines(epd, font, screen_lines, scroll_offset, max_lines, max_width)

        except Exception as e:
            print("Error from OpenAI:", str(e))

        print("\nUse arrow keys to scroll, or press Enter to continue.")

        while True:
            key = get_keypress()
            if key == '\x1b':  # escape sequence
                if select.select([sys.stdin], [], [], 0.1)[0]:
                    next1 = sys.stdin.read(1)
                    if next1 == '[':
                        next2 = sys.stdin.read(1)
                        if next2 == 'A':  # up
                            if scroll_offset > 0:
                                scroll_offset -= SCROLL_STEP
                                display_lines(epd, font, screen_lines, scroll_offset, max_lines, max_width)
                        elif next2 == 'B':  # down
                            if scroll_offset < max(0, len(screen_lines) - max_lines):
                                scroll_offset += SCROLL_STEP
                                display_lines(epd, font, screen_lines, scroll_offset, max_lines, max_width)
                        elif next2 == 'C':  # right arrow resets view
                            scroll_offset = max(0, len(screen_lines) - max_lines)
                            display_lines(epd, font, screen_lines, scroll_offset, max_lines, max_width)
            elif key == '\n':
                break
            time.sleep(0.1)

except KeyboardInterrupt:
    print("Exiting...")

finally:
    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    epd.init()
    epd.Clear(0xFF)
    epd.sleep()
    print("Goodbye!")

