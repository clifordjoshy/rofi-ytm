#! /usr/bin/env python

# ------------------------------------------------------------------
# This program takes a youtube video id as argument and allows
# the user to either pick one of 5 recommendations or play the top
# recommendation automatically.
# ------------------------------------------------------------------

from subprocess import Popen, PIPE, run
from requests import get
import config
import sys

VIDEO_ID = sys.argv[1]

autoplay_options = [
    "yes, play immediately",
    "yes, but I'll pick",
    "no, repeat the current song",
    "no, quit"
]

process = Popen(['rofi', '-dmenu', '-p', 'play next', '-l', str(len(autoplay_options))], stdout=PIPE, stdin=PIPE)
process.stdin.write('\n'.join(autoplay_options).encode("utf8"))
selected = process.communicate()[0].decode("utf8")

if autoplay_options[0] in selected:
    autoplay = True
elif autoplay_options[1] in selected:
    autoplay = False
elif autoplay_options[2] in selected:
    run(
        f"nohup {config.TERMINAL} -e bash -c \"\
        ascii-image-converter /tmp/ytm_thumbnail --color -H 20 && \
        echo '\n' && \
        mpv --no-video 'https://www.youtube.com/watch?v={VIDEO_ID}' &&\
        ./continue.py {VIDEO_ID} ||\
        read -n1 -p 'Error. Press any key to quit.'\
    \" &", shell=True
    )
    quit()
else:
    quit()

videos_json = get('https://www.googleapis.com/youtube/v3/search', params={
    'part': 'snippet',
    'relatedToVideoId': VIDEO_ID,
    'maxResults': config.RESULT_COUNT,
    'type': 'video',
    'key': config.API_KEY
}, timeout=1).json()['items']

videos = [{
    'id': v['id']['videoId'],
    'title': v['snippet']['title'].replace('&#39;', "").replace('&quot;', '').replace('&amp;', '&'),
    'channel': v['snippet']['channelTitle'],
    'url': f"https://www.youtube.com/watch?v={v['id']['videoId']}",
    'thumbnail': v['snippet']['thumbnails']['medium']['url']
} for v in videos_json if "snippet" in v]

if not autoplay:
    videos_formatted = "\n".join(
        f"{i+1}.    \
        {v['title'][:config.TITLE_LENGTH].ljust(config.TITLE_LENGTH)}    \
        {v['channel'][:config.CHANNEL_LENGTH].ljust(config.CHANNEL_LENGTH)}"
        for i, v in enumerate(videos)
    )
    process = Popen(['rofi', '-dmenu', '-p', 'pick video', '-l', str(config.RESULT_COUNT)], stdout=PIPE, stdin=PIPE)
    process.stdin.write(videos_formatted.encode("utf8"))
    # will run into IndexOutOfBoundsError and quit if nothing selected
    selected = process.communicate()[0][0] - 49

    video = videos[selected]
else:
    video = videos[0]

run(['wget', video['thumbnail'], '-O', '/tmp/ytm_thumbnail'])
run(
    f"nohup {config.TERMINAL} -e bash -c \"\
        echo '{video['title']}\n{video['url']}\n' && \
        ascii-image-converter /tmp/ytm_thumbnail --color -H 20 && \
        echo '\n' && \
        mpv --no-video '{video['url']}' &&\
        ./continue.py {video['id']} ||\
        read -n1 -p 'Error. Press any key to quit.'\
    \" &", shell=True
)
quit()
