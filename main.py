import sys
import termios
from music_player import MusicPlayer

if __name__ == "__main__":
    try:
        player = MusicPlayer()
        player.run()
    except KeyboardInterrupt:
        # Reset terminal settings if interrupted
        try:
            # If terminal recieves weird input , its a retry
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, termios.tcgetattr(sys.stdin))
        except:
            pass
        print("\nBye!")
    except Exception as e:
        print(f"An error occurred: {e}")
