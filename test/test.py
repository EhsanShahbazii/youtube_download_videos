import requests
from urllib.parse import urlparse, parse_qs
from threading import Thread
import threading
import time
from moviepy.editor import VideoFileClip, AudioFileClip
import re
import os
import math

TOKEN = "977468:6329ac21c52466.23581203"
CHANNEL_URL = None
CHANNEL_ID = None


def sanitize_filename(filename):
    cleaned_filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    cleaned_filename = re.sub(r'[\s-]+', '_', cleaned_filename)
    cleaned_filename = cleaned_filename.strip('_')

    return cleaned_filename


def get_video_id(url):
    parsed_url = urlparse(url)
    video_id = parse_qs(parsed_url.query).get('v')
    return video_id[0] if video_id else None


def get_download_ids(video_id):
    response = requests.get(
        f"https://youtube.one-api.ir/?token={TOKEN}&action=fullvideo&id={video_id}").json()
    dat = response['result']['formats']
    if "Compilation" not in response['result']['title']:
        audio_detail = next(
            (x for x in dat if x['format_note'] == 'medium'),
            next(
                (x for x in dat if x['format_note'] == 'medium, DRC'),
                next(
                    (x for x in dat if x['format_note'] == 'low'),
                    None
                )
            )
        )
        video_detail = next(
            (x for x in dat if x['format_note'] == '720p60'),
            next(
                (x for x in dat if x['format_note'] == '720p'),
                next(
                    (x for x in dat if x['format_note'] == '480p'),
                    next(
                        (x for x in dat if x['format_note'] == '360p'),
                        None
                    )
                )
            )
        )

        return {
            'type': 'video_audio_download_id',
            # 'title': sanitize_filename(response['result']['title']),
            'title': str(math.floor(time.time())) + '-' + video_detail['format_note'],
            'audio': {
                'id': audio_detail['id'],
                'format': audio_detail['ext'],
            },
            'video': {
                'id': video_detail['id'],
                'format': video_detail['ext'],
            },
        }
    else:
        return False


def get_download_link(file_id):
    response = requests.get(
        f"https://youtube.one-api.ir/?token={TOKEN}&action=download&id={file_id}")
    return response.json()['result']['link']


def download(url, name, type):
    file_name = name + '.' + type
    chunk_size = 1024 * 1024

    def download_chunk(start, end, file):
        headers = {'Range': f'bytes={start}-{end}'}
        response = requests.get(url, headers=headers, stream=True)
        with open('./assets/' + file, "r+b") as f:
            f.seek(start)
            f.write(response.content)

    def get_file_size(url):
        response = requests.get(url, stream=True)
        return int(response.headers.get('content-length', 0))

    file_size = get_file_size(url)
    with open('./assets/' + file_name, "wb") as f:
        f.truncate(file_size)

    threads = []
    for i in range(0, file_size, chunk_size):
        start = i
        end = min(i + chunk_size - 1, file_size - 1)
        thread = Thread(target=download_chunk, args=(start, end, file_name))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    print(f"+ file download as ---> {file_name}")


def main(video_url):
    try:
        download_ids = get_download_ids(get_video_id(video_url))
        if download_ids:
            print(f"+ get download links ---> {download_ids['title']}")
            download_url_sound = get_download_link(download_ids['audio']['id'])
            download(download_url_sound,
                 download_ids['title'], download_ids['audio']['format'])

            download_url_video = get_download_link(download_ids['video']['id'])
            download(download_url_video,
                 download_ids['title'], download_ids['video']['format'])
    except:
        print("error during the download ...")


with open('video_links.txt', 'r') as f:
    print("+ Running the script ...")
    links = f.readlines()
    total_index = len(links)

    for idx, vid in enumerate(links):
        main(vid)
        print(f"+ reading the link ---> {vid}")
        print(f"progress status: %{round((idx+1)/total_index, 2) * 100}")
