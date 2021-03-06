#!/usr/bin/env -S python3 -u
# -u flag disables output buffering
# can also give sys.stdout.flush after all print statements

# ---------------------------------------------------------------------------
# This rofi-blocks script searches youtube and opens the audio in mpv
# Also prints the ascii representation of the thumbnail
# ---------------------------------------------------------------------------
# Dependencies:  wget, ascii-image-converter, rofi-blocks, mpv, pycurl
# ---------------------------------------------------------------------------


# imports take time. so do this first to immediately see prompt.
print({'input action': 'send', 'prompt': 'search youtube'})

from os.path import dirname
try:
    with open(f"{dirname(__file__)}/.search_history") as hist_file:
        hist_vals = hist_file.read().splitlines()
except FileNotFoundError:
    hist_vals = []

print({'lines': hist_vals, 'prompt': 'search youtube', 'input action': 'send'})

from json import loads as jsonify
from pycurl import Curl
from io import BytesIO
from requests import get
from re import findall
from subprocess import run
from urllib.parse import quote_plus as urlencode
import config

if not config.API_KEY:
    print(f'{{"message": "No api keys found in \'{config.API_KEY_PATH}\'", "prompt": "error"}}')
    input()
    quit()


def get_videos(song_query):
    videos_json = get('https://www.googleapis.com/youtube/v3/search', params={
        'part': 'snippet',
        'q': song_query,
        'maxResults': config.RESULT_COUNT,
        'regionCode': config.REGION,
        'type': 'video',
        'key': config.API_KEY
    }, timeout=1).json()['items']

    vid_ids = ",".join(v['id']['videoId'] for v in videos_json)

    details_json = get('https://www.googleapis.com/youtube/v3/videos', params={
        'part': 'contentDetails',
        'id': vid_ids,
        'key': config.API_KEY
    }, timeout=1).json()['items']

    videos = [{
        'id': v['id']['videoId'],
        'title': v['snippet']['title'].replace('&amp;', '&').replace('&#39;', '').replace('&quot;', ''),
        'channel': v['snippet']['channelTitle'],
        'duration': d['contentDetails']['duration'][2:],
        'url': f"https://www.youtube.com/watch?v={v['id']['videoId']}",
        'thumbnail': v['snippet']['thumbnails']['medium']['url']
    } for v, d in zip(videos_json, details_json) if "snippet" in v]

    return videos


crl = Curl()
# crl.setopt(crl.TIMEOUT_MS, 100)
suggestion_url = 'https://suggestqueries.google.com/complete/search?gl=us&ds=yt&client=youtube&q='


def search_query(query):
    b_obj = BytesIO()
    crl.setopt(crl.URL, suggestion_url + urlencode(query))
    crl.setopt(crl.WRITEDATA, b_obj)
    try:
        crl.perform()
        suggestions = findall(r"\[\"(.*?)\"", b_obj.getvalue().decode('unicode_escape'))
    except:
        suggestions = [query]
    return suggestions[:config.RESULT_COUNT]


def update_history(query):
    if query in hist_vals:
        hist_vals.remove(query)

    if len(hist_vals) >= 5:
        hist_vals.pop()

    hist_vals.insert(0, query)

    with open(f"{dirname(__file__)}/.search_history", "w") as hist_file:
        for val in hist_vals:
            hist_file.write(val + "\n")


stage = 0

while True:
    event = jsonify(input())

    if stage == 0 and event['name'] == "input change":
        print({'lines': search_query(event['value'])})

    elif event['name'] == "select entry":

        # query entered
        if stage == 0:
            stage = 1
            print({'prompt': 'searching', 'lines': [], 'value': ""})
            update_history(event['value'])
            videos = get_videos(event['value'])
            videos_strings = [
                f"{i+1}.    "
                f"{v['title'][:config.TITLE_LENGTH].ljust(config.TITLE_LENGTH)}    "
                f"{v['channel'][:config.CHANNEL_LENGTH].ljust(config.CHANNEL_LENGTH)}    "
                f"{v['duration'].ljust(config.DURATION_LENGTH)}"
                for i, v in enumerate(videos)
            ]
            print({'prompt': 'pick video', 'lines': videos_strings, 'active entry': 0})

        # video picked
        elif stage == 1:
            selected = int(event['value'][0]) - 1
            video = videos[selected]
            print({'prompt': 'fetching', 'lines': []})
            run(['wget', video['thumbnail'], '-O', '/tmp/ytm_thumbnail'])
            run(
                f"{config.TERMINAL} -e bash -c \""
                f"echo '{video['title']}\n{video['url']}\n' && "
                "ascii-image-converter /tmp/ytm_thumbnail --color -H 20 && "
                "echo '\n' && "
                f"mpv --no-video '{videos[selected]['url']}' && "
                f"cd {dirname(__file__)} && "
                f"./continue.py {video['id']} || "
                "read -n1 -p 'Error. Press any key to quit.'\" &", shell=True
            )
            quit()
