from tkinter import Button
from picamera import PiCamera
from turtle import position
import speech_recognition as sr
from digitalio import DigitalInOut, Direction, Pull
from adafruit_dotstar import DotStar
import board
from time import sleep
from PIL import Image, ImageDraw
from adafruit_rgb_display import st7789
from io import BytesIO
import pyaudio
from os import listdir

cs_pin = DigitalInOut(board.CE0)
dc_pin = DigitalInOut(board.D25)
reset_pin = DigitalInOut(board.D24)

BAUDRATE = 24000000
spi = board.SPI()
camera = PiCamera()
FORMAT = pyaudio.paInt16
CHANNELS = 2
BITRATE = 44100
CHUNK_SIZE = 512

LED_CLOCK = board.D6
LED_DATA = board.D5

JOYSELECT_PIN = board.D16
JOYDOWN_PIN = board.D22
JOYUP_PIN = board.D24
JOYLEFT_PIN = board.D23
JOYRIGHT_PIN = board.D27
BUTTON_PIN = board.D17

# Lists
COLORS = ['red', 'green', 'blue', 'yellow', 'orange', 'white']
COLOR_DICT = {'red': (0, 0, 255),'green': (255, 0, 0), 'blue': (0, 255, 0), 'yellow': (0, 255, 255), 'orange': (128, 0, 255), 'white': (255, 255, 255)}
LED_POSITIONS = ['left', 'middle', 'right', 'all']
POSITION_DICT = {'left': 2, 'middle': 1, 'right': 0, 'write': 0}
SECONDS_LIST = {'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5}


RECORDING_DIR_PATH = "/home/pi/Documents/Pi/Labs/fmG50L07/recordings"
IMAGES_DIR_PATH = "/home/pi/Documents/Pi/Labs/fmG50L07/images"

# Set HAT commandds
buttons = [BUTTON_PIN, JOYDOWN_PIN, JOYUP_PIN, JOYLEFT_PIN, JOYRIGHT_PIN, JOYSELECT_PIN]
for i,pin in enumerate(buttons):
    buttons[i] = DigitalInOut(pin)
    buttons[i].direction = Direction.INPUT
    buttons[i].pull = Pull.UP
    
button, joydown, joyup, joyleft, joyright, joyselect = buttons


# Turn on the backlight
backlight = DigitalInOut(board.D26)
backlight.switch_to_output()
disp = st7789.ST7789(spi, dc_pin, cs_pin, rst=reset_pin, height=240, y_offset=80, rotation=180, baudrate=BAUDRATE)
backlight.value = True
width = disp.width
height = disp.width
image = Image.new("RGBA", (width, height))
draw = ImageDraw.Draw(image)
draw.rectangle((0, 0, width, height), outline=0, fill=0)


dots = DotStar(LED_CLOCK, LED_DATA, 3, brightness=0.1)
dots.fill((0,0,0))

def turn_on(color, pos):
    if pos == 'all':
        dots.fill(COLOR_DICT[color])
    else:
        dots[POSITION_DICT[pos]] = COLOR_DICT[color]

def blink(seconds, color, pos):
    for key, value in SECONDS_LIST.items():
        if key == seconds:
            turn_on(color, pos)
            sleep(value)
            dots.fill((0, 0, 0))
        elif str(value) == seconds:
            turn_on(color, pos)
            sleep(value)
            dots.fill((0, 0, 0))

def light_up_command():
    for pos in LED_POSITIONS:
        for color in COLORS:
            if f'turn on {pos} LED colour {color}' in text:
                turn_on(color, pos)
            elif f'turn off {pos} LED' in text:
                if pos == 'all':
                    dots.fill((0, 0, 0))
                else:
                    dots[POSITION_DICT[pos]] = (0, 0, 0)
            elif f'blink {pos} LED colour {color} for' in text:
                split_text = text.split()
                seconds = split_text[-2]
                blink(seconds, color, pos)

def get_next_img_count():
    imgs = listdir(IMAGES_DIR_PATH)
    img_nums = [int(img.split("-")[1].split(".")[0]) for img in listdir(IMAGES_DIR_PATH)]
    img_nums.sort()
    if len(imgs) <= 0:
        latest_count = 0
    else:
        latest_count = img_nums[-1]
    return latest_count + 1

def take_picture():
    print("Taking picture")
    for i in range(3):
        diff = 3-i
        print(f"Taking picture in {diff} seconds")
        sleep(1)
    draw.rectangle((0, 0, width, height), outline=0, fill=0)
    stream = BytesIO()
    camera.capture(stream, format="png", resize="240x240")
    stream.seek(0)
    image = Image.open(stream)
    return image

def save_img(image):
    print("Saving image")
    sleep(2)
    count = get_next_img_count()
    if count < 10:
        image.save(f'{IMAGES_DIR_PATH}/image-0{count}.png')
    else:
        image.save(f'{IMAGES_DIR_PATH}/image-{count}.png')
    
def get_image(num):
    image = Image.open(f"{IMAGES_DIR_PATH}/image-{num}.png")

    image_ratio = image.width/image.height
    screen_ratio = width/height

    if screen_ratio < image_ratio:
        scaled_width = image.width * height // image.height
        scaled_height = height
    else:
        scaled_width = width
        scaled_height = image.height * width // image.width
        
    image = image.resize((scaled_width, scaled_height), Image.BICUBIC)

    x = scaled_width //2 - width //2
    y = scaled_height // 2 - height //2

    image = image.crop((x,y, x+width, y+height))
    return image


r = sr.Recognizer()
while True:
    if not button.value:
        with sr.Microphone() as sauce:
            print("Recording")
            audio_data = r.record(sauce, duration=5)
            print("Recording ended")
            text = r.recognize_google(audio_data)
            
            if 'turn on backlight' in text:
                backlight.value = True
                print('ON')
            elif 'turn off backlight' in text:
                backlight.value = False
                print('OFF')
            elif 'take a photo' in text:
                img = take_picture()
                save_img(img)
                print("Displaying image")
                disp.image(img)
            elif 'show image' in text:
                split_text = text.split()
                num = split_text[-1]
                img = get_image(num)
                disp.image(img)
            else:
                light_up_command()
                    
            
            print(f'Input: {text}')
    