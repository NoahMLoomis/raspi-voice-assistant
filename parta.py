import pyaudio
from time import sleep
import wave
from os import listdir
import board
from digitalio import DigitalInOut, Direction, Pull
from PIL import Image, ImageDraw
from adafruit_rgb_display import st7789
from io import BytesIO
from picamera import PiCamera

# Set up pins
cs_pin = DigitalInOut(board.CE0)
dc_pin = DigitalInOut(board.D25)
reset_pin = DigitalInOut(board.D24)
BAUDRATE = 24000000
BUTTON_PIN = board.D17
LED_CLOCK = board.D6
LED_DATA = board.D5
JOY_UP = board.D23
JOY_DOWN = board.D27
JOY_LEFT = board.D22
JOY_RIGHT = board.D24
JOY_SELECT = board.D16
buttons = [BUTTON_PIN,JOY_DOWN, JOY_LEFT, JOY_UP, JOY_RIGHT, JOY_SELECT]

spi = board.SPI()
camera = PiCamera()
FORMAT = pyaudio.paInt16
CHANNELS = 2
BITRATE = 44100
CHUNK_SIZE = 512
RECORDING_DIR_PATH = "/home/pi/Documents/Pi/Labs/fmG50L07/recordings"
IMAGES_DIR_PATH = "/home/pi/Documents/Pi/Labs/fmG50L07/images"

for i, pin in enumerate(buttons):
    buttons[i] = DigitalInOut(pin)
    buttons[i].direction = Direction.INPUT
    buttons[i].pull = Pull.UP
    
button, joydown, joyleft, joyup, joyright, joyselect = buttons
disp = st7789.ST7789(spi, dc_pin, cs_pin, rst=reset_pin, height=240, y_offset=80, rotation=180, baudrate=BAUDRATE)
backlight = DigitalInOut(board.D26)
backlight.switch_to_output()
backlight.value = True
width = disp.width
height = disp.width


image = Image.new("RGBA", (width, height))
draw = ImageDraw.Draw(image)
draw.rectangle((0, 0, width, height), outline=0, fill=0)

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

def get_next_recording_count():
    recordings = listdir(RECORDING_DIR_PATH)
    recording_nums = [int(recording.split("-")[1].split(".")[0]) for recording in listdir(RECORDING_DIR_PATH)]
    recording_nums.sort()
    if len(recordings) <= 0:
        latest_count = 0
    else:
        latest_count = recording_nums[-1]
    return latest_count + 1

def get_next_img_count():
    imgs = listdir(IMAGES_DIR_PATH)
    img_nums = [int(img.split("-")[1].split(".")[0]) for img in listdir(IMAGES_DIR_PATH)]
    img_nums.sort()
    if len(imgs) <= 0:
        latest_count = 0
    else:
        latest_count = img_nums[-1]
    return latest_count + 1

def record_and_save(record_len):
    audio = pyaudio.PyAudio()
    print(f'Record lenght is {record_len}')
    for i in range(3):
        diff = 3-i
        print(f'Starting in {diff} seconds')
        sleep(1)
        
    print("Starting")

    stream = audio.open(format=FORMAT, channels=CHANNELS, rate=BITRATE, input=True,input_device_index=2, frames_per_buffer=CHUNK_SIZE)

    frames = []

    for i in range(int((BITRATE/CHUNK_SIZE) * record_len)):
        data = stream.read(CHUNK_SIZE)
        frames.append(data)
        
    stream.stop_stream()
    stream.close()
    audio.terminate()
    
    next_recording_count = get_next_recording_count()
    if (next_recording_count < 10):
        output_file = f'recording-0{str(next_recording_count)}.wav'
    else:
        output_file = f'recording-{str(next_recording_count)}.wav'
    wave_file = wave.open(f'{RECORDING_DIR_PATH}/' + output_file, "wb")
    wave_file.setnchannels(CHANNELS)
    wave_file.setsampwidth(audio.get_sample_size(FORMAT))
    wave_file.setframerate(BITRATE)
    wave_file.writeframes(b"".join(frames))

    wave_file.close()
    print("Wave file written")
    
if __name__ == "__main__":
    print("Press the button to start recording")
    while True:
        try:
            if not button.value:
                img = take_picture()
                save_img(img)
                print("Displaying image")
                disp.image(img)
                
                print("""Select a joystick value
                         top: 5 sec
                         right: 10 sec
                         bottom: 15 sec
                         left: 20 sec
                      """)
                while True:
                    if not joyup.value:
                        record_and_save(5)
                        break
                    if not joyright.value:
                        record_and_save(10)
                        break
                    if not joydown.value:
                        record_and_save(15)
                        break
                    if not joyleft.value:
                        record_and_save(20)
                        break
                    sleep(0.01)
                sleep(0.01)
        except KeyboardInterrupt:
            print("Program exited by keyboard press")
            break
        