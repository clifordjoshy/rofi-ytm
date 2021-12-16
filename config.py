
from os import getlogin as getusername

RESULT_COUNT = 5

# length of different elements in video list
TITLE_LENGTH = 40
DURATION_LENGTH = 6
CHANNEL_LENGTH = 15

# --class argument is specified so that the WM can apply my rules to map it to the music tag
TERMINAL = 'alacritty --class mpv-ytm'

API_KEY_PATH = f"/home/{getusername()}/.config/apikeys/youtube"

# ISO 3166-1 alpha-2 country code to only allow videos available in the country
REGION = "IN"

try:
    with open(API_KEY_PATH) as key:
        API_KEY = key.readline().strip()
except IndexError:
    API_KEY = None
