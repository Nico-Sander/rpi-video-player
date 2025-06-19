import RPi.GPIO as GPIO
import subprocess
import time
import os

# -- Config
BUTTON_GPIO_PIN = 23
VIDEO_PATH = "test_video_3_min_converted.mp4"

# -- GPIO Setup
GPIO.setmode(GPIO.BCM)      # Use BCM numbering for GPIO Pins
GPIO.setup(BUTTON_GPIO_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)      # Setup Button as Input
                                                                    # Button is connected to GPIO23 and GND
                                                                    # Use internal Pull Up resistor
                                                                    # -> default: HIGH, pressed: LOW

# -- Variable to track the process of the video player
omxplayer_process = None
is_video_playing = False # New state variable to track if video is actively playing

def start_video_and_pause():
    global omxplayer_process, is_video_playing

    # Stop any existing omxplayer process before starting a new one
    stop_video()
    
    print(f"Starting video and immediately pausing: {VIDEO_PATH}")
    try:
        omxplayer_process = subprocess.Popen(
            ['omxplayer', '-o', 'hdmi', '-b', '--no-osd', VIDEO_PATH],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        # Give omxplayer a moment to start and render the first frame
        time.sleep(0.1) # Experiment with this value: 0.1, 0.2, 0.5 seconds

        # Now, send the 'p' key to pause it
        if omxplayer_process.poll() is None: # Check if it's still running
            omxplayer_process.stdin.write(b'p')
            omxplayer_process.stdin.flush()
            is_video_playing = False # It's now paused
            print("Video started and sent pause command.")
        else:
            print("Omxplayer exited prematurely before pause command could be sent.")
            omxplayer_process = None # Reset if it crashed
            is_video_playing = False
            
    except FileNotFoundError:
        print(f"Error: omxplayer not found. Is it installed and in your PATH?")
    except Exception as e:
        print(f"An error occurred while trying to start video and pause: {e}")

def unpause_video():
    global omxplayer_process, is_video_playing
    if omxplayer_process and omxplayer_process.poll() is None:
        print("Unpausing video...")
        try:
            omxplayer_process.stdin.write(b'p') # 'p' toggles play/pause
            omxplayer_process.stdin.flush()
            is_video_playing = True # It's now playing
            print("Video unpaused.")
        except Exception as e:
            print(f"Error sending unpause command: {e}")
    else:
        print("No video process found to unpause. Starting video in paused state.")
        start_video_and_pause() # Fallback: if somehow not running, ensure it starts paused

def stop_video():
    global omxplayer_process, is_video_playing
    if omxplayer_process and omxplayer_process.poll() is None:
        print("Stopping video...")
        try:
            omxplayer_process.stdin.write(b'q')
            omxplayer_process.stdin.flush()
            omxplayer_process.wait(timeout=5) # Wait for the process to terminate
            print("Video stopped.")
        except Exception as e:
            print(f"Error sending quit command or waiting for process: {e}")
        finally:
            omxplayer_process = None
            is_video_playing = False # It's no longer playing or paused
    else:
        print("No video process to stop.")


def button_callback(channel):
    global is_video_playing
    if GPIO.input(channel) == GPIO.LOW:
        print("Button pressed!")
        
        # Check if omxplayer process is active
        if omxplayer_process and omxplayer_process.poll() is None:
            # If omxplayer is running
            if is_video_playing:
                # Scenario 1: Video is currently playing -> Restart and pause
                print("Video is playing. Restarting and pausing on first frame.")
                start_video_and_pause()
            else:
                # Scenario 2: Video is currently paused -> Unpause and play
                print("Video is paused. Unpausing.")
                unpause_video()
        else:
            # If omxplayer is not running (e.g., just started script, or video finished)
            print("Omxplayer not active. Starting video and pausing on first frame.")
            start_video_and_pause()


if __name__ == "__main__":
    # Start the video and immediately pause it at script launch (preload behavior)
    start_video_and_pause()

    GPIO.add_event_detect(BUTTON_GPIO_PIN, GPIO.FALLING, callback=button_callback, bouncetime=300)
    
    try:
        while True:
            # This loop checks if the video has finished playing.
            # If omxplayer_process is not None AND it has terminated (poll() is not None),
            # then restart it in the paused state to maintain preload.
            if omxplayer_process is not None and omxplayer_process.poll() is not None:
                print("Video finished playing or exited prematurely. Restarting in paused state...")
                omxplayer_process = None # Reset the process variable
                is_video_playing = False # Make sure state is reset
                start_video_and_pause() # Re-launch and pause
            
            time.sleep(1) # Keep the main thread alive
    except KeyboardInterrupt:
        print("Exiting")
    finally:
        stop_video() # Ensure omxplayer is cleanly stopped on exit
        GPIO.cleanup()
        print("GPIO cleaned up. Goodbye!")
