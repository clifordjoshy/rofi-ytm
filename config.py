
from os import getlogin as getusername

RESULT_COUNT = 5

# length of different elements in video list
TITLE_LENGTH = 40
DURATION_LENGTH = 6
CHANNEL_LENGTH = 15

TERMINAL = 'alacritty'

API_KEY_PATH = f"/home/{getusername()}/.config/apikeys/youtube"

try:
    with open(API_KEY_PATH) as key:
        API_KEY = key.readline().strip()
except IndexError:
    API_KEY = None
