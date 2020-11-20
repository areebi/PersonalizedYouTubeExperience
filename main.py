from googleapiclient.discovery import build
from datetime import datetime, timedelta
import webbrowser
import math
import PySimpleGUI as sg
from PIL import Image
import requests
from io import BytesIO

API_KEY = ""                            # Enter API Key here
RESULTS_PER_CHANNEL = 20
VIDEOS_FROM_LAST_X_DAYS = 30
CHANNEL_IDS = [
        "UCBR8-60-B28hp2BmDPdntcQ"      # YouTube
        "UCStaiwu-FAgp_RC_tBiLh9A"      # YouTube Music
        "UCK8sQmJBp8GCxrOtXWBpyEA"      # Google
    ]


def find_playlist_id(youtube, channel_id):
    request = youtube.channels().list(part='contentDetails', id=channel_id)
    response = request.execute()
    playlist_id = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    return playlist_id


def find_videos(youtube, playlist_id):
    videos = []
    request = youtube.playlistItems().list(part='snippet', maxResults=RESULTS_PER_CHANNEL, playlistId=playlist_id)
    response = request.execute()
    for each in response['items']:
        current_video = Video(each)
        video_datetime = datetime.strptime(current_video.get_published_time(), '%Y-%m-%dT%H:%M:%SZ')
        if video_datetime > datetime.now() - timedelta(days=VIDEOS_FROM_LAST_X_DAYS):
            videos.append(current_video)
    return videos


class Video(object):
    def __init__(self, video_dict):
        self.published_time = video_dict['snippet']['publishedAt']
        self.channel_id = video_dict['snippet']['channelId']
        self.title = video_dict['snippet']['title']
        self.description = video_dict['snippet']['description']
        self.thumbnail = video_dict['snippet']['thumbnails']['medium']  # Dict of three keys: 'url', 'width', 'height'
        self.channel = video_dict['snippet']['channelTitle']
        self.id = video_dict['snippet']['resourceId']['videoId']

    def __str__(self):
        return "Title: " + self.title + ", Channel: " + self.channel

    def __lt__(self, other):
        return self.published_time > other.published_time  # Returns True if self was published more recently

    def get_published_time(self):
        return self.published_time

    def get_channel_id(self):
        return self.channel_id

    def get_video_id(self):
        return self.id

    def get_title(self):
        return self.title

    def get_channel(self):
        return self.channel

    def get_thumbnail(self):
        return self.thumbnail


def main():
    youtube = build('youtube', 'v3', developerKey=API_KEY)

    videos = []
    layout = []
    number_of_columns = 4

    for channel_id in CHANNEL_IDS:
        playlist_id = find_playlist_id(youtube, channel_id)
        videos.extend(find_videos(youtube, playlist_id))
    videos.sort()

    for i in range(int(math.ceil(len(videos) / number_of_columns))):
        layout.append([])
        for j in range(number_of_columns):
            video_index = number_of_columns * i + j
            if video_index < len(videos):
                response = requests.get(videos[video_index].get_thumbnail()['url'])
                img = Image.open(BytesIO(response.content))
                with BytesIO() as f:
                    img.save(f, format='png')
                    img_png = f.getvalue()
                sg.theme('Black')
                layout_col = [
                    [sg.Button(button_color=(sg.theme_background_color(), sg.theme_background_color()),
                               image_data=img_png, image_size=(videos[video_index].get_thumbnail()['width'],
                               videos[video_index].get_thumbnail()['height']), key='V' + str(video_index).zfill(2))],
                    [sg.Text(videos[video_index].get_title(), size=(29, 2), font='MSSansSerif', enable_events=True,
                             key='T' + str(video_index).zfill(2))],
                    [sg.Text(videos[video_index].get_channel() + '\n', font=('MSSansSerif', 11), size=(35, 1),
                             text_color="#AAAA99", enable_events=True, key='C' + str(video_index).zfill(2))]
                    ]
                layout[i] += [sg.Column(layout_col)]
    col = sg.Column(layout, scrollable=True, vertical_scroll_only=True)
    window = sg.Window('Personalized YouTube Experience', [[col]], size=(1420, 710))
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == 'Cancel':
            break
        elif event[0] == 'C':
            channel_url = "https://www.youtube.com/channel/" + videos[int(event[-2:])].get_channel_id()
            webbrowser.open_new_tab(channel_url)
        else:
            video_url = "https://www.youtube.com/watch?v=" + videos[int(event[-2:])].get_video_id()
            webbrowser.open_new_tab(video_url)
    window.close()


if __name__ == "__main__":
    main()
