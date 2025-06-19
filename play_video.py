import RPi.GPIO as GPIO
import subprocess
import time

# --- Configuration ---
BUTTON_GPIO_PIN = 23
VIDEO_PATH = "test_video_3_min_converted.mp4" # Ensure this path is correct

# --- Global variables for omxplayer process ---
omxplayer_process = None
is_paused = False # Track the current playback state

### ---Function to send a command to omxplayer via stdin
def send_omxplayer_command(command): # No need for count/delay here if sending single key presses
    global omxplayer_process
    if omxplayer_process and omxplayer_process.poll() is None:
        try:
            # Ensure the command is bytes, not string, followed by newline for omxplayer
            omxplayer_process.stdin.write(command.encode('utf-8'))
            omxplayer_process.stdin.flush()
            print(f"Sent command '{command}' to omxplayer.")
            return True
        except Exception as e:
            print(f"Error sending command '{command}' to omxplayer stdin: {e}")
            return False
    else:
        print(f"Omxplayer process not running. Cannot send command '{command}'.")
        return False

### --- Function to start the video on startup
def start_video():
    global omxplayer_process, is_paused
    print(f"Starting video: {VIDEO_PATH}")
    try:
        omxplayer_process = subprocess.Popen(
            ["omxplayer", "-o", "hdmi", "-b", '--no-osd', VIDEO_PATH],
            stdin=subprocess.PIPE,
        )
        

    except FileNotFoundError:
        print(f"Error: omxplayer not found. Is it installed and in your PATH?")
        omxplayer_process = None
        is_paused = False # Ensure state is consistent if start fails
    except Exception as e:
        print(f"An unexpected error occurred during video start: {e}")
        omxplayer_process = None
        is_paused = False # Ensure state is consistent if start fails


def button_callback(channel):
    print("Button pressed")
    send_omxplayer_command("p")
    pass



if __name__ == "__main__":
    ### --- GPIO SETUP --- ###
    try: 
        GPIO.setmode(GPIO.BCM)     # Use BCM Pin numbering
        GPIO.setup(BUTTON_GPIO_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # setup the Button as Input with internal Pullup Resistor
        GPIO.add_event_detect(BUTTON_GPIO_PIN, GPIO.FALLING, callback=button_callback, bouncetime=300)  # Add a callback function that runs every time the button gets pressed. Add debouncing to prevent multiple calls from a single press
    except Exception as e:
        print(f"GPIO setup failed (likely not on a Raspberry Pi or wiring issue): {e}")
        print("Running without button control. You will need to manually start/stop/Ctrl+C.")

    ### --- START THE PROCESS --- ###
    start_video()

    while True:
        time.sleep(0.1)
