import os
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "hide"
import pygame
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich import print as rprint

class MusicPlayer:
    def __init__(self, folder="music"):
        self.folder = folder
        self.console = Console()
        self.mp3_files = []
        self.current_index = -1
        self.volume = 0.5
        self.is_paused = False
        
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

    def play_song(self, index):
        if 0 <= index < len(self.mp3_files):
            self.current_index = index
            song_name = self.mp3_files[index]
            file_path = os.path.join(self.folder, song_name)
            
            try:
                pygame.mixer.music.load(file_path)
                pygame.mixer.music.play()
                self.is_paused = False
                self.show_now_playing()
            except pygame.error as e:
                self.console.print(f"[bold red]Error playing file:[/bold red] {e}")
        else:
            self.console.print("[bold red]Invalid song number[/bold red]")

    def show_now_playing(self):
        if self.current_index != -1:
            song = self.mp3_files[self.current_index]
            status = "Paused" if self.is_paused else "Playing"
            panel = Panel(
                f"[bold green]{song}[/bold green]\n"
                f"Status: {status} | Volume: {int(self.volume * 100)}%",
                title="Now Playing",
                border_style="blue"
            )
            self.console.print(panel)

    def control_loop(self):
        self.console.print("\n[bold cyan]Controls:[/bold cyan] [P]ause/Resume, [S]top, [N]ext, [B]ack, [V+] Vol Up, [V-] Vol Down, [Q]uit")
        
        while True:
            if not pygame.mixer.music.get_busy() and not self.is_paused:
                # Auto-play next song could go here, but for now we wait
                pass

            command = Prompt.ask("Command").upper()

            if command == "P":
                if self.is_paused:
                    pygame.mixer.music.unpause()
                    self.is_paused = False
                    self.console.print("[green]Resumed[/green]")
                else:
                    pygame.mixer.music.pause()
                    self.is_paused = True
                    self.console.print("[yellow]Paused[/yellow]")
                self.show_now_playing()

            elif command == "S":
                pygame.mixer.music.stop()
                self.console.print("[red]Stopped[/red]")
                return

            elif command == "N":
                next_index = (self.current_index + 1) % len(self.mp3_files)
                self.play_song(next_index)

            elif command == "B":
                prev_index = (self.current_index - 1) % len(self.mp3_files)
                self.play_song(prev_index)

            elif command == "V+":
                self.volume = min(1.0, self.volume + 0.1)
                pygame.mixer.music.set_volume(self.volume)
                self.console.print(f"Volume: {int(self.volume * 100)}%")

            elif command == "V-":
                self.volume = max(0.0, self.volume - 0.1)
                pygame.mixer.music.set_volume(self.volume)
                self.console.print(f"Volume: {int(self.volume * 100)}%")

            elif command == "Q":
                pygame.mixer.music.stop()
                return "QUIT"
            
            else:
                self.console.print("[red]Invalid command[/red]")

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
        print("\nBye!")
    except Exception as e:
        print(f"An error occurred: {e}")
