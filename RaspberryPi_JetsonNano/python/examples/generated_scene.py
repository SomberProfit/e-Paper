Sure, here's a basic Python script to create the scene with the text "Hello!". Please replace 'your_font_path.ttf' with the path of your actual .ttf file. 

```python
from PIL import Image, ImageDraw, ImageFont

# Create a blank image
image = Image.new('1', (250, 122), 255)  # 255: clear the frame
draw = ImageDraw.Draw(image)

# Add text
font = ImageFont.truetype('your_font_path.ttf', 15)
draw.text((10, 50), 'Hello!', font=font, fill=0)

# Save the image
image.save('hello_scene.bmp')
```

The script is creating a new image that is 250 pixels by 122 pixels. This is standard for Waveshare e-Paper displays, but you can adjust the size as needed for your specific display.