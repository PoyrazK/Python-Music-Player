from enum import Enum, auto

class PlayerStatus(Enum):
    PLAYING = auto()
    PAUSED = auto()
    STOPPED = auto()
