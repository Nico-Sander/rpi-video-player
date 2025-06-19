import RPi.GPIO as GPIO
import subprocess
import time
import os

# --- Configuration ---
BUTTON_GPIO_PIN = 23
VIDEO_PATH = "test_video_3_min_converted.mp4" # Ensure this path is correct

# --- Global variables for omxplayer process ---
omxplayer_process = None
is_paused = False # Track the current playback state

# Function to start the video
def start_video_playing():
    global omxplayer_process, is_paused

    stop_video_clean() # Ensure any old process is stopped

    print(f"Starting omxplayer: {VIDEO_PATH}")
    try:
        omxplayer_process = subprocess.Popen(
            ['omxplayer', '-o', 'hdmi', '-b', '--no-osd', VIDEO_PATH],
            stdin=subprocess.PIPE,
            # Let stdout/stderr go to the console for any diagnostic messages
        )
        print("Omxplayer process started.")
        is_paused = False # Video starts playing by default
    except FileNotFoundError:
        print(f"Error: omxplayer not found. Is it installed and in your PATH?")
        omxplayer_process = None
    except Exception as e:
        print(f"An unexpected error occurred during video start: {e}")
        omxplayer_process = None

# Function to send a command to omxplayer via stdin
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

# Function to stop the video by sending 'q'
def stop_video_clean():
    global omxplayer_process, is_paused
    if omxplayer_process and omxplayer_process.poll() is None:
        print("Stopping omxplayer process by sending 'q'...")
        try:
            send_omxplayer_command('q') # Send 'q' to quit
            # Give it a moment to terminate gracefully
            omxplayer_process.wait(timeout=5)
            print("Omxplayer stopped.")
        except subprocess.TimeoutExpired:
            print("Omxplayer did not quit gracefully, terminating forcibly.")
            omxplayer_process.terminate()
            omxplayer_process.wait(timeout=5)
        except Exception as e:
            print(f"Error stopping omxplayer process: {e}")
            if omxplayer_process and omxplayer_process.poll() is None:
                omxplayer_process.terminate()
                print("Omxplayer forcibly terminated.")
        finally:
            omxplayer_process = None
            is_paused = False
    else:
        print("No omxplayer process to stop.")

# Button callback function
def button_callback(channel):
    global is_paused # Declare global to modify the variable
    if GPIO.input(channel) == GPIO.LOW: # Button pressed (assuming pull-up and button pulls low)
        print("\nButton pressed!")
        
        if omxplayer_process and omxplayer_process.poll() is None:
            # Omxplayer is running
            if not is_paused: # Video is currently playing
                print("Video is playing. Rewinding 600 secs and pausing...")
                # Send 'down arrow' key code (ESC [ B) once for 600 seconds rewind
                send_omxplayer_command('\x1b[B') # Send down arrow once
                time.sleep(0.1) # Small delay to ensure rewind is processed before pause

                # Now pause the video
                send_omxplayer_command('p')
                is_paused = True
                print("Video rewound and paused.")
            else: # Video is currently paused
                print("Video is paused. Starting playback...")
                send_omxplayer_command('p')
                is_paused = False
                print("Video started playing.")
        else:
            print("Omxplayer process is not running. Starting video.")
            start_video_playing()

# --- Main execution block ---
if __name__ == "__main__":
    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(BUTTON_GPIO_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(BUTTON_GPIO_PIN, GPIO.FALLING, callback=button_callback, bouncetime=300)
        print("GPIO setup complete. Button configured.")
    except Exception as e:
        print(f"GPIO setup failed (likely not on a Raspberry Pi or wiring issue): {e}")
        print("Running without button control. You will need to manually start/stop/Ctrl+C.")

    # Start the video immediately on script launch
    start_video_playing()
    time.sleep(4)
    send_omxplayer_command('p')

    print("\n--- Script running. Press the button for new rewind/pause/play logic. ---")
    print("Press Ctrl+C in terminal to exit.")

    try:
        # Keep the main thread alive to listen for GPIO events and monitor omxplayer
        while True:
            # Check if omxplayer process has terminated (e.g., video finished)
            if omxplayer_process is not None and omxplayer_process.poll() is not None:
                print(f"Omxplayer process has terminated (exit code {omxplayer_process.returncode}). Restarting...")
                start_video_playing() # Restart the video

            time.sleep(1) # Sleep to reduce CPU usage
    except KeyboardInterrupt:
        print("KeyboardInterrupt detected. Exiting.")
    finally:
        stop_video_clean() # Ensure omxplayer is cleanly stopped on script exit
        try:
            GPIO.cleanup() # Clean up GPIO settings
            print("GPIO cleaned up.")
        except Exception as e:
            print(f"GPIO cleanup skipped (likely not on a Raspberry Pi or no GPIO was used): {e}")
        print("Goodbye!")
