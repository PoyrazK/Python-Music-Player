import os
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "hide"
import pygame
import sys
import select
import termios
import tty
import time
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.live import Live
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.layout import Layout
from rich import print as rprint
from enum import Enum, auto
from mutagen.mp3 import MP3

class PlayerStatus(Enum):
    PLAYING = auto()
    PAUSED = auto()
    STOPPED = auto()

class MusicPlayer:
    def __init__(self, folder="music"):
        self.folder = folder
        self.console = Console()
        self.mp3_files = []
        self.current_index = -1
        self.volume = 0.5
        self.status = PlayerStatus.STOPPED
        self.current_song_length = 0
        self.start_time = 0
        self.paused_time = 0
        self.total_paused_duration = 0
        
        try:
            pygame.mixer.init()
            pygame.mixer.music.set_volume(self.volume)
        except pygame.error as e:
            self.console.print(f"[bold red]Audio initialization failed![/bold red] {e}")
            raise

    def load_songs(self):
        if not os.path.isdir(self.folder):
            self.console.print(f"[bold red]Folder '{self.folder}' not found[/bold red]")
            return False
        
        self.mp3_files = sorted([f for f in os.listdir(self.folder) if f.endswith(".mp3")])
        if not self.mp3_files:
            self.console.print("[bold yellow]No .mp3 files found![/bold yellow]")
            return False
        return True

    def display_songs(self):
        table = Table(title="Song List", show_header=True, header_style="bold magenta")
        table.add_column("#", style="dim", width=4)
        table.add_column("Song Name")
        
        for idx, song in enumerate(self.mp3_files, 1):
            table.add_row(str(idx), song)
        
        self.console.print(table)

    def get_song_duration(self, file_path):
        try:
            audio = MP3(file_path)
            return audio.info.length
        except Exception:
            return 0

    def play_song(self, index):
        if 0 <= index < len(self.mp3_files):
            self.current_index = index
            song_name = self.mp3_files[index]
            file_path = os.path.join(self.folder, song_name)
            
            try:
                pygame.mixer.music.load(file_path)
                pygame.mixer.music.play()
                self.status = PlayerStatus.PLAYING
                self.current_song_length = self.get_song_duration(file_path)
                self.start_time = time.time()
                self.total_paused_duration = 0
            except pygame.error as e:
                self.console.print(f"[bold red]Error playing file:[/bold red] {e}")
        else:
            self.console.print("[bold red]Invalid song number[/bold red]")

    def get_progress_panel(self):
        if self.current_index == -1:
            return Panel("No song playing", title="Now Playing")

        song = self.mp3_files[self.current_index]
        
        if self.status == PlayerStatus.PLAYING:
            elapsed = time.time() - self.start_time - self.total_paused_duration
        elif self.status == PlayerStatus.PAUSED:
            elapsed = self.paused_time - self.start_time - self.total_paused_duration
        else:
            elapsed = 0

        # Clamp elapsed time
        elapsed = min(elapsed, self.current_song_length)
        
        # Create progress bar string manually or use rich's Progress
        # For simplicity in a panel, we can construct a visual bar
        width = 100
        if self.current_song_length > 0:
            percent = elapsed / self.current_song_length
            filled = int(width * percent)
            bar = f"[{'-' * filled}{' ' * (width - filled)}]"
            time_str = f"{int(elapsed)//60:02d}:{int(elapsed)%60:02d} / {int(self.current_song_length)//60:02d}:{int(self.current_song_length)%60:02d}"
        else:
            bar = f"[{' ' * width}]"
            time_str = "--:-- / --:--"

        content = f"[bold green]{song}[/bold green]\n\n"
        content += f"{bar} {time_str}\n\n"
        content += f"Status: {self.status.name.title()} | Volume: {int(self.volume * 100)}%\n"
        content += "[dim]Controls: [P]ause, [S]top, [N]ext, [B]ack, [+/-] Vol, [Q]uit[/dim]"

        return Panel(content, title="Now Playing", border_style="blue")

    def is_data_ready(self):
        return select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], [])

    def control_loop(self):
        # Set up non-blocking input
        old_settings = termios.tcgetattr(sys.stdin)
        try:
            tty.setcbreak(sys.stdin.fileno())
            
            with Live(self.get_progress_panel(), refresh_per_second=4) as live:
                while True:
                    if not pygame.mixer.music.get_busy() and self.status == PlayerStatus.PLAYING:
                        # Auto-play next song
                        next_index = (self.current_index + 1) % len(self.mp3_files)
                        self.play_song(next_index)
                        live.update(self.get_progress_panel())

                    if self.is_data_ready():
                        key = sys.stdin.read(1).upper()
                        
                        if key == "P":
                            if self.status == PlayerStatus.PAUSED:
                                pygame.mixer.music.unpause()
                                self.status = PlayerStatus.PLAYING
                                # Adjust total paused duration
                                self.total_paused_duration += time.time() - self.paused_time
                            elif self.status == PlayerStatus.PLAYING:
                                pygame.mixer.music.pause()
                                self.status = PlayerStatus.PAUSED
                                self.paused_time = time.time()
                        
                        elif key == "S":
                            pygame.mixer.music.stop()
                            self.status = PlayerStatus.STOPPED
                            return

                        elif key == "N":
                            next_index = (self.current_index + 1) % len(self.mp3_files)
                            self.play_song(next_index)

                        elif key == "B":
                            prev_index = (self.current_index - 1) % len(self.mp3_files)
                            self.play_song(prev_index)

                        elif key == "+":
                            self.volume = min(1.0, self.volume + 0.1)
                            pygame.mixer.music.set_volume(self.volume)

                        elif key == "-":
                            self.volume = max(0.0, self.volume - 0.1)
                            pygame.mixer.music.set_volume(self.volume)

                        elif key == "Q":
                            pygame.mixer.music.stop()
                            return "QUIT"
                    
                    live.update(self.get_progress_panel())
                    time.sleep(0.1)

        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

    def run(self):
        if not self.load_songs():
            return

        while True:
            self.console.clear()
            self.console.rule("[bold blue]MP3 PLAYER[/bold blue]")
            self.display_songs()
            
            choice = Prompt.ask("\nEnter song # to play (or 'Q' to quit)")
            
            if choice.upper() == 'Q':
                self.console.print("[bold blue]Bye![/bold blue]")
                break
            
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(self.mp3_files):
                    self.play_song(idx)
                    result = self.control_loop()
                    if result == "QUIT":
                        break
                else:
                    self.console.print("[bold red]Invalid choice[/bold red]")
            else:
                self.console.print("[bold red]Please enter a number[/bold red]")

if __name__ == "__main__":
    try:
        player = MusicPlayer()
        player.run()
    except KeyboardInterrupt:
        # Reset terminal settings if interrupted
        try:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, termios.tcgetattr(sys.stdin))
        except:
            pass
        print("\nBye!")
    except Exception as e:
        print(f"An error occurred: {e}")
