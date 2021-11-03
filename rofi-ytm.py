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

from json import loads as jsonify
from pycurl import Curl
from io import BytesIO
from requests import get
from re import findall
from subprocess import run
from urllib.parse import quote_plus as urlencode

RESULT_COUNT = 5

# length of different elements in video list
TITLE_LENGTH = 40
DURATION_LENGTH = 6
CHANNEL_LENGTH = 15

TERMINAL = 'alacritty'

with open("/home/cliford/.config/apikeys/youtube") as key:
    API_KEY = key.read().strip()


def get_videos(song_query):
    videos_json = get('https://www.googleapis.com/youtube/v3/search', params={
        'part': 'snippet',
        'q': song_query,
        'maxResults': RESULT_COUNT,
        'type': 'video',
        'key': API_KEY
    }, timeout=1).json()['items']

    vid_ids = ",".join(v['id']['videoId'] for v in videos_json)

    details_json = get('https://www.googleapis.com/youtube/v3/videos', params={
        'part': 'contentDetails',
        'id': vid_ids,
        'key': API_KEY
    }, timeout=1).json()['items']

    videos = [{
        'title': v['snippet']['title'].replace('&#39;', "'").replace('&quot;', '"').replace('&amp;', '&'),
        'channel': v['snippet']['channelTitle'],
        'duration': d['contentDetails']['duration'][2:],
        'url': f"https://www.youtube.com/watch?v={v['id']['videoId']}",
        'thumbnail': v['snippet']['thumbnails']['medium']['url']
    } for v, d in zip(videos_json, details_json)]

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
        suggestions = findall(r"\[\"(.*?)\"", b_obj.getvalue().decode('utf8'))
    except:
        suggestions = [query]
    return suggestions[:RESULT_COUNT]


stage = 0

while True:
    event = jsonify(input())

    if stage == 0 and event['name'] == "input change":
        print({'lines': search_query(event['value'])})

    elif event['name'] == "select entry":

        # query entered
        if stage == 0:
            stage = 1
            print({'prompt': 'searching', 'lines': []})
            videos = get_videos(event['value'])
            videos_strings = [
                f"{i+1}.    \
                {v['title'][:TITLE_LENGTH].ljust(TITLE_LENGTH)}    \
                {v['channel'][:CHANNEL_LENGTH].ljust(CHANNEL_LENGTH)}    \
                {v['duration'].ljust(DURATION_LENGTH)}"
                for i, v in enumerate(videos)
            ]
            print({'prompt': 'pick video', 'lines': videos_strings, 'active entry': 0})

        # video picked
        elif stage == 1:
            selected = int(event['value'][0]) - 1
            video = videos[selected]
            print({'prompt': 'fetching', 'lines': []})
            run(['wget', video['thumbnail'], '-O', '/tmp/ytm_thumbnail'])
            run(f"{TERMINAL} -e bash -c \"\
                    echo '{video['title']}\n{video['url']}\n' && \
                    ascii-image-converter /tmp/ytm_thumbnail --color -H 20 && \
                    echo '\n' && \
                    mpv --no-video '{videos[selected]['url']}'\
                \"&", shell=True)
            quit()

# TODO add autoplay after song ends
