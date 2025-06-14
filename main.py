import RPi.GPIO as GPIO
import subprocess
import time
import os

# -- Config
BUTTON_GPIO_PIN = 23
VIDEO_PATH = "test_video_converted.mp4"

# -- GPIO Setup
GPIO.setmode(GPIO.BCM)      # Use BCM numbering for GPIO Pins
GPIO.setup(BUTTON_GPIO_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)      # Setup Button as Input
                                                                    # Button is connected to GPIO23 and GND
                                                                    # Use internal Pull Up resistor
                                                                    # -> default: HIGH, pressed: LOW
# -- Variabl to track the process of the video player
omxplayer_process = None


def play_video():
    global omxplayer_process

    if omxplayer_process and omxplayer_process.poll() is None:
        print("Video is already playing")
        return
   
    print(f"Starting video: {VIDEO_PATH}")
    try:
        # Start omxplayer as a subprocess
        # -o hdmi: directs audio to HDMI
        # -b: hides the black border around the video (useful for full screen)
        # --no-osd: hides on-screen display (like volume, progress bar)
        # We redirect stdin to PIPE so we can send 'q' to quit it later if needed.
        # We redirect stdout/stderr to devnull to avoid cluttering the console.
        omxplayer_process = subprocess.Popen(
            ['omxplayer', '-o', 'hdmi', '-b', '--no-osd', VIDEO_PATH],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL, # Discard omxplayer's stdout
            stderr=subprocess.DEVNULL  # Discard omxplayer's stderr
        )
        print("Video started.")
    except FileNotFoundError:
        print(f"Error: omxplayer not found. Is it installed and in your PATH?")
    except Exception as e:
        print(f"An error occurred while trying to play video: {e}")


def button_callback(channel):
    if GPIO.input(channel) == GPIO.LOW:
        print("Button pressed!")
        play_video()


if __name__ == "__main__":
    # play_video()
    GPIO.add_event_detect(BUTTON_GPIO_PIN, GPIO.FALLING, callback=button_callback, bouncetime=300)
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting")
    finally:
        GPIO.cleanup()
        print("GPIO cleaned up. Goodbye!")


