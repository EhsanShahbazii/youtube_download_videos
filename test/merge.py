import subprocess
from os import walk
from concurrent.futures import ThreadPoolExecutor

def merge_audio_and_video(name):
    print(f"Processing {name}...")
    command = [
        'ffmpeg', '-i', f'{name}.mp4', '-i', f'{name}.m4a', 
        '-c:v', 'copy', '-c:a', 'aac', f'./merge/{name}.mp4'
    ]
    subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)

filenames = next(walk('.'), (None, None, []))[2]
mp4_files = [file for file in filenames if file.endswith('.mp4')]
mp4_files_without_extension = [file.replace('.mp4', '') for file in mp4_files]

with ThreadPoolExecutor(max_workers=8) as executor:
    futures = [executor.submit(merge_audio_and_video, name)
               for name in mp4_files_without_extension]

    for future in futures:
        future.result()
print("All video files have been processed.")