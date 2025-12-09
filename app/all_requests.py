import os
import requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import tzlocal
from flask import current_app
import asyncio
from .telegram_bot import telegram_bot_send_message


TOKEN = os.environ.get('ARTIFACTS_TOKEN')

headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {TOKEN}"
    }


def get_local_time(time_isoformat):
    time_utc = datetime.fromisoformat(time_isoformat)
    local_tz_name = tzlocal.get_localzone_name()
    local_time_zone = ZoneInfo(local_tz_name)
    time_local = time_utc.astimezone(local_time_zone)
    return time_local


def get_names():
    url = "https://api.artifactsmmo.com/my/characters"
    responce = requests.get(url, headers=headers)
    names = []
    responce = responce.json()
    for i in range(len(responce['data'])):
        names.append(responce['data'][i]['name'])
    return names


def get_data_for_db(action):
    data = []
    url = f"https://api.artifactsmmo.com/{action}"
    response = requests.get(url, headers=headers).json()
    if action == 'my/logs':
        return response['data']
    if response.get('total'):
        if response['total'] % response['size'] != 0:
            pages = response['total'] // response['size'] + 1
        else:
            pages = response['total'] // response['size']
        for page in range(1, pages + 1):
            querystring = {'page': page}
            response = requests.get(url, headers=headers, params=querystring)
            for d in response.json()['data']:
                data.append(d)
    else:
        data = response['data']
    return data


def download_map_images(skins):
    image_dir = os.path.join(os.getcwd(), 'app/static/images/maps')
    if not os.path.isdir(image_dir):
        os.makedirs(image_dir)
    for skin in skins:
        file_path = os.path.join(image_dir, f'{skin}.png')
        if os.path.exists(file_path):
            continue
        print(f"Downloading skin: {skin}")
        url = f'https://www.artifactsmmo.com/images/maps/{skin}.png'
        img_data = requests.get(url).content
        with open(os.path.join(image_dir, f'{skin}.png'), 'wb') as handler:
            handler.write(img_data)


def get_achievements():
    account_name = current_app.config['ARTIFACTS_ACCOUNT']
    url = f"https://api.artifactsmmo.com/accounts/{account_name}/achievements"
    querystring = {"size":"100"}
    responce = requests.get(url, headers=headers, params=querystring)
    responce = responce.json()['data']
    achievements = {}
    data = []
    all_points = 0
    my_points = 0
    for a in responce:
        all_points += a['points']
        if a['completed_at'] is not None:
            my_points += a['points']
            dt_object_local = get_local_time(a['completed_at'])
            dt_object_local = dt_object_local.strftime('%d-%m-%Y %H:%M')
            a['completed_at'] = dt_object_local
        data.append(a)
    achievements['my_points'] = my_points
    achievements['all_points'] = all_points
    achievements['data'] = data
    return achievements


def get_active_events():
    url = "https://api.artifactsmmo.com/events/active"
    responce = requests.get(url, headers=headers)
    responce = responce.json()['data']
    events = []
    for event in responce:
        duration = timedelta(minutes=event['duration'])
        event['duration'] = (datetime(1, 1, 1) + duration).strftime('%H:%M')
        local_tz_name = tzlocal.get_localzone_name()
        local_time_zone = ZoneInfo(local_tz_name)
        expiration_local = get_local_time(event['expiration'])
        created_local = get_local_time(event['created_at'])
        time_left = expiration_local - datetime.now(tz=local_time_zone)
        event['expiration'] = expiration_local.strftime('%H:%M')
        event['created_at'] = created_local.strftime('%H:%M')
        event['time_left'] = (datetime(1, 1, 1) + time_left).strftime('%H:%M')
        events.append(event)
    return events

def get_account_name():
    url = "https://api.artifactsmmo.com/my/details"
    responce = requests.get(url, headers=headers)
    responce = responce.json()['data']
    account_name = responce['username']
    return account_name

def create_character_request(name, skin):
    url = "https://api.artifactsmmo.com/characters/create"
    payload = {'name': name, 'skin': skin}
    responce = requests.post(url, headers=headers, json=payload)
    return responce.json()['data']

def delete_character_request(name):
    url = "https://api.artifactsmmo.com/characters/delete"
    payload = {'name': name}
    responce = requests.post(url, headers=headers, json=payload)
    return responce.status_code


def get_one_map(map_id):
    url = f"https://api.artifactsmmo.com/maps/id/{map_id}"
    response = requests.get(url, headers=headers)
    return response

