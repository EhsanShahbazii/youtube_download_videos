import requests
from urllib.parse import urlparse, parse_qs
from threading import Thread
import threading
from moviepy.editor import VideoFileClip, AudioFileClip
import re
import os

TOKEN = "paste your one-api.ir token"
CHANNEL_URL = None
CHANNEL_ID = None


def sanitize_filename(filename):
    cleaned_filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    cleaned_filename = re.sub(r'[\s-]+', '_', cleaned_filename)
    cleaned_filename = cleaned_filename.strip('_')

    return cleaned_filename


def extract_channel_id(url=CHANNEL_URL):
    return urlparse(url).path.split('/channel/')[-1]


def get_video_id(url):
    parsed_url = urlparse(url)
    video_id = parse_qs(parsed_url.query).get('v')
    return video_id[0] if video_id else None


def get_download_ids(video_id):
    response = requests.get(
        f"https://youtube.one-api.ir/?token={TOKEN}&action=fullvideo&id={video_id}").json()
    dat = response['result']['formats']
    audio_detail = next(
        (x for x in dat if x['format_note'] == 'medium'), None)
    video_detail = next(
        (x for x in dat if x['format_note'] == '1080p'), None)

    return {
        'type': 'video_audio_download_id',
        'title': sanitize_filename(response['result']['title']),
        'audio': {
            'id': audio_detail['id'],
            'format': audio_detail['ext'],
        },
        'video': {
            'id': video_detail['id'],
            'format': video_detail['ext'],
        },
    }


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

    print(f"File downloaded as {file_name}")


def merge_audio_and_video(name, format):
    video = VideoFileClip('./assets/' + name + '.' + format['video'])
    audio = AudioFileClip('./assets/' + name + '.' + format['audio'])
    final_video = video.set_audio(audio)
    final_video.write_videofile(
        './merge/' + name + '.' + format['video'], codec="libx264", audio_codec="aac")


def main(video_url):
    print(f"getting download ids ... ({video_url})")
    download_ids = get_download_ids(get_video_id(video_url))

    print(f'getting sound and video download links ... {video_url}')
    download_url_sound = get_download_link(download_ids['audio']['id'])
    download(download_url_sound,
             download_ids['title'], download_ids['audio']['format'])

    download_url_video = get_download_link(download_ids['video']['id'])
    download(download_url_video,
             download_ids['title'], download_ids['video']['format'])

    print(f'merging the video and sound ... {video_url}')
    merge_audio_and_video(download_ids['title'], {
                          'audio': download_ids['audio']['format'], 'video': download_ids['video']['format']})
    print(f'finish process ... {video_url}')

    file_path = 'path/to/your/file.txt'


    try:
        os.remove(
            f'./assets/{download_ids['title']}.{download_ids['video']['format']}')
        print(f"{file_path} has been deleted.")
    except:
        pass


with open('video_links.txt', 'r') as f:
    links = f.readlines()
    main(links[0])
