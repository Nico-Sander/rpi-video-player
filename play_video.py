# --- Imports ---
import RPi.GPIO as GPIO
import subprocess
import time

# --- Configuration ---
BUTTON_GPIO_PIN = 23                # The GPIO to which the button is connected according to BCM numbering (the other pin is connected to ground)
VIDEO_PATH = "final.mp4"            # File name of the video, needs to be in the same directory as this python file.
VOLUME = -3000                      # Default Volume


# --- Global variables for omxplayer (video player) process ---
omxplayer_process = None            # At the beginning the process doesn't exist, so this variable is None
is_paused = False                   # This variable tracks if the video is paused or playing
start_found = False                 # This variable tracks if the start of the video has been found


### ---Function to send a command to omxplayer via stdin
def send_omxplayer_command(command):                                # valid input commands can be found here under the section "Key Bindings": https://github.com/huceke/omxplayer
    global omxplayer_process
    if omxplayer_process and omxplayer_process.poll() is None:          # Ensures that the omxplayer process is running before sending a command
        try:
            omxplayer_process.stdin.write(command)                          # Write the command to the input of the process
            omxplayer_process.stdin.flush()                                 # Basically pressing the "Enter" key
            print(f"Sent command '{command}' to omxplayer.")                # Show the user that the command was sent successfully
            return True                                                     # Return True if command was send successfully

        except Exception as e:                                          # If something went wrong
            print(f"Error sending command '{command}' to omxplayer stdin: {e}")     # Show the user what went wrong
            return False                                                            # Return False to the caller of the function, to indicate that something didn't work

    else:                                                               # If the omxplayer process is not running
        print(f"Omxplayer process not running. Cannot send command '{command}'.")   # Tell the user that the process is not running
        return False                                                                # Return False to to the caller of the function, to indicate that something didn't work 



### --- Function to start the video on startup
def start_video_paused():
    global omxplayer_process, is_paused, start_found
    print(f"Starting video: {VIDEO_PATH}")                          # Tell the user that the video player is starting up
    try:
        omxplayer_process = subprocess.Popen(                       # Start the video player in another process, so that it can run concurrently to the process of this python file
            [                           # This list specifies the shell command to start the process
                "omxplayer",                # Name of the binary executable of the omxplayer video player
                "-o", "local",              # Audio output device: "local" -> 3.5mm Jack, "hdmi" ->  Audio over HDMI
                "-b",                       # Video background color set to black, not relevant in this usecase, since the video isn't transparent
                "-z",                       # do not adjust the display refresh rate to match the video (caused some issues with the testing monitor)
                '--no-osd',                 # Do not display status information on screen
                '--with-info',              # Write status information to stdout and stderr, this is needed in order to detect the start of the video
                "--vol", str(VOLUME),       # set the audio volume in millidecibles. -3000 was a good value in testing. User can change this when the program starts
                VIDEO_PATH                  # Path to the video file
            ],
            stdin=subprocess.PIPE,          # Reroute stdin to Pipe, so that the process can be controlled from this python file
            stdout=subprocess.PIPE,         # Reroute stdout to Pipe, so that the output can be read from this python file
            stderr=subprocess.PIPE,         # Reroute stderr to Pipe, so that any errors can be read from this python file.
            text=True,                      # Output should be encoded as text
            bufsize=1,                      # This is also needed to encode the output correctly, no idea what it actually does.
            universal_newlines=True         # Set universal newline characters that mark the start of new lines is the outputs.
        ) 

        # --- Some logic to find the start of the video, since the "start paused" option isn't working.
        for line in omxplayer_process.stderr:           # Analyse all lines of the stderr output.
            if line.lstrip().startswith("Metadata"):        # a line that starts with the word "Metadata" corresponds with the moment the video actually starts (This was a lot of Trial and Error...)
                start_found = True                          # Signal that the start of the video was found
                break                                       # Stop analysing the output and continue

        time.sleep(0.58)                                    # Wait for same random time (Found out with Trial and Error)
        send_omxplayer_command("p")                         # Then actually send the pause command to the video player process (Video can be paused by pressing 'p')
        is_paused = True                                    # Signal that the video is now paused
            

    # --- Error handling
    except FileNotFoundError:                           # If the specified video doesn't exist in the directory
        print(f"Error: omxplayer not found. Is it installed and in your PATH?")     # Tell the user about the error
        omxplayer_process = None                                                    # Signal that the video player process is not running
        is_paused = False                                                           # Reset value to the default (False)

    except Exception as e:                              # If any other error occurred:
        print(f"An unexpected error occurred during video start: {e}")              # Tell the user about the error
        omxplayer_process = None                                                    # Signal that the video player process is not running
        is_paused = False                                                           # Reset value to the default (False)

    print("Start of video found!")                      # Signal the user that the start of the video has been successfully found


# --- Function that restarts the video from the beginning and pauses it immediately ---
def rewind_video_pause():
    global omxplayer_process, is_paused, start_found
    print("Rewinding video")            # Tell the user that this function was called
    send_omxplayer_command("\x1b[B")    # Send the "Down Arrow" key to the process. This rewinds the video by 600 seconds (10 mins). Works as long as the video isn't longer than 10 mins
    time.sleep(0.5)                     # Wait for half a second, since the raspberry pi or the video player can't handle it when commands are sent to close to each other
    send_omxplayer_command("p")         # Send "p" to the process to pause the video
    is_paused = True                    # Signal that the video is now paused


# --- Function that runs every time that the physical push button is pressed. ---
def button_callback(_):
    global is_paused
    print("Button pressed")             # Signal the user that a button press was detected.
    if is_paused:                       # If the video is currently paused
        send_omxplayer_command("p")         # Send "p" to start playing the video
        is_paused = False                   # Signal that the video is now playing

    else:                               # If the video isn't paused, it is currently playing:
        print("Restarting and pausing video")   # Tell the user that that the video is restarting and and pausing
        rewind_video_pause()                    # Actually call the function that restarts and pauses the video


# --- Main Entry point to the programm. This is where the program starts. ---
if __name__ == "__main__":
    ### --- GPIO SETUP --- ###
    try: 
        GPIO.setmode(GPIO.BCM)                                                                              # Use BCM Pin numbering
        GPIO.setup(BUTTON_GPIO_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)                                      # setup the Button as Input with internal Pullup Resistor
        GPIO.add_event_detect(BUTTON_GPIO_PIN, GPIO.FALLING, callback=button_callback, bouncetime=1000)     # Add a callback function that runs every time the button gets pressed
                                                                                                            # Add debouncing to prevent multiple calls from a single press
    # --- Error handling
    except Exception as e:
        print(f"GPIO setup failed (likely not on a Raspberry Pi or wiring issue): {e}")                     # Tell the user that something went wrong and possible reasons
        print("Running without button control. You will need to manually start/stop/Ctrl+C.")               # Tell the user that the button is not working

    
    input_volume = input("Enter volume (default: -3000, very loud: 0, mute: -10000):    ")                  # Ask the user to input a desired audio volume
    try:
        VOLUME = int(input_volume)                                                                          # Check if an actuall number was entered, if yes, use it 
    except:
        pass                                                                                                # If the input was not a number, use the default value


    ### --- START THE PROCESS --- ###
    start_video_paused()                        # Start the video player process and pause at the beginning

    try:
        while True:                             # Do this forever
            time.sleep(0.1)                         # Small delay to not overuse the processor
            if omxplayer_process.poll() != None:    # Check if the video player process is currently running    
                start_video_paused()                    # If not, restart it
                
            
    # --- Error handling
    except Exception as e:
        print(f"Exiting because of {e}")        # If something went wrong, tell the user about it
    finally:
        GPIO.cleanup()                          # If the program is interrupted, clean up the GPIO configuration, so that it works again next time
        print("GPIO cleaned up. Goodbye!")      
