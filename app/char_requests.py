import requests
from datetime import datetime
from zoneinfo import ZoneInfo
import tzlocal
from .all_requests import headers
from .telegram_bot import telegram_bot_send_message
import asyncio
import time


def get_cooldown(dt_object):
    expiration_utc = datetime.fromisoformat(dt_object)
    local_tz_name = tzlocal.get_localzone_name()
    local_time_zone = ZoneInfo(local_tz_name)
    expiration_local = expiration_utc.astimezone(local_time_zone)
    time_now = datetime.now(tz=local_time_zone)
    time_left = expiration_local - time_now
    return time_left.total_seconds()


def char_equip_item(name, code, slot, quantity=1):
    url = f"https://api.artifactsmmo.com/my/{name}/action/equip"
    payload = {
            "code": code,
            "slot": slot,
            "quantity": quantity,
            }
    response = requests.post(url, json=payload, headers=headers)
    return response


def char_unequip_item(name, slot, quantity=1):
    url = f"https://api.artifactsmmo.com/my/{name}/action/unequip"
    payload = {"slot": slot, "quantity": quantity}
    response = requests.post(url, json=payload, headers=headers)
    return response

def char_move_request(name, map_id):
    url = f"https://api.artifactsmmo.com/my/{name}/action/move"
    payload = {"map_id": map_id}
    response = requests.post(url, json=payload, headers=headers)
    return response


def char_action_request(name, action, payload={}):
    url = f"https://api.artifactsmmo.com/my/{name}/action/{action}"
    try:
        response = requests.post(url, json=payload, headers=headers)
    except requests.exceptions.ConnectionError:
        message = f'ConnectionError occured, {name} waits 60 seconds.'
        asyncio.run(telegram_bot_send_message(f'❗️ <b>{name}</b>: {message}'))
        time.sleep(60)
        response = char_action_request(name, action, payload)
    return response
