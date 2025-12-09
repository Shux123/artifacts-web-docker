from .telegram_bot import telegram_bot_send_message
import asyncio
import time
import re
from datetime import datetime, timedelta, timezone
from celery import shared_task
from . import r
from .models import Character, BankItem, Map, Item
from .char_requests import char_action_request

FISH = [{1: 'cooked_gudgeon', 'hp': 75},
        {10: 'cooked_shrimp', 'hp': 150},
        {20: 'cooked_trout', 'hp': 225},
        {30: 'cooked_bass', 'hp': 300},
        {40: 'cooked_salmon', 'hp': 400},
        {50: 'cooked_swordfish', 'hp': 500}]

to_diff_layer = {'mithril_rocks': 571,
                  'bat': 571,
                  'lich': 655,
                  'cultist_alchemist': 934,
                  'rosenblood': 934,
                  'frost_slime': 1099,
                  'snowman': 1099,
                  'gingerbread': 1099,
                  'nutcracker': 1099,
                  }
from_diff_layer = {'mithril_rocks': 572,
                  'bat': 572,
                  'lich': 656,
                  'cultist_alchemist': 935,
                  'rosenblood': 935,
                  'frost_slime': 1216,
                  'snowman': 1216,
                  'gingerbread': 1216,
                  'nutcracker': 1216,
                  }


@shared_task
def bot(char_name, slot_number, action, target):
    character = Character.query.filter_by(name=char_name).first()   
    target_map = Map.query.filter_by(content_code=target).first()

    # Get nearest bank to target
    banks = Map.query.filter_by(content_code='bank').all()
    if action != 'craft':
        if target_map.name == 'Sandwhisper Isle':
            bank_map = banks[2]
        else:
            bank_map = banks[0]
        for bank in banks[:2]:
            nearest_bank_distance = abs(bank_map.x - target_map.x) + \
                abs(bank_map.y - target_map.y)
            bank_distance = abs(bank.x - target_map.x) + abs(bank.y - target_map.y)
            if bank_distance < nearest_bank_distance: 
                bank_map = bank

    status = ''
    status = f'{char_name} is {action}ing the '
    message = f"✅ {char_name} bot has been started."
    asyncio.run(telegram_bot_send_message(message))
    r.hset(char_name, 'char_status' , status)
    if action == 'gather':
        gathering_loop(character, target_map, bank_map, slot_number)
    elif action == 'fight':
        fighting_loop(character, target_map, bank_map, slot_number)
    elif action == 'craft':
        item = Item.query.filter_by(code=target).first()
        target_map = Map.query.filter_by(content_code=item.craft_skill).first()
        bank_map = banks[0]
        crafting_loop(character, target, target_map, bank_map, slot_number)
    

def precise_sleep(expiration):
    target_time = datetime.fromisoformat(expiration)
    target_time = target_time + timedelta(milliseconds=2200)
    remaining_time = (target_time - datetime.now(timezone.utc)).total_seconds()
    if remaining_time <= 0:
        return
    
    coarse_sleep_duration = remaining_time - 0.005
    if coarse_sleep_duration > 0:
        time.sleep(coarse_sleep_duration)

    while datetime.now(timezone.utc) < target_time:
        time.sleep(0.000001)


def response_200(response):
    response = response.json()['data']
    if 'character' in response:
        Character.update_character(response['character'])
    elif 'characters' in response:
        for char in response['characters']:
            Character.update_character(char)
    expiration = response['cooldown']['expiration']
    precise_sleep(expiration)
    return response


def error_in_responce(response, char_name):
    error_msg = response['error']['message']
    error_msg = error_msg.replace('The character', char_name)
    message = f"Code {response['error']['code']}: {error_msg}"
    asyncio.run(telegram_bot_send_message(f'<b>{char_name}</b>: {message}'))
    

def cooldown_in_response(response, char_name):
    text = response.json()['error']['message']
    seconds = re.findall(r'\d+.\d+', text)
    time_now = datetime.now(timezone.utc)
    message = f'<b>{char_name}</b> was on cooldown. He is waiting {seconds[0]} seconds.'
    asyncio.run(telegram_bot_send_message(message))
    time_for_sleep = time_now+timedelta(seconds=float(seconds[0]),milliseconds=300)
    precise_sleep(time_for_sleep.isoformat())


def move(character, map_id):
    payload = {"map_id": map_id}
    response = char_action_request(character.name, 'move', payload)
    if response.status_code == 200:
        if response.json()['data']['destination']['interactions']['content'] is not None:
            destination = response.json()['data']['destination']['interactions']['content']['code']
            message = f'<b>{character.name}</b> moved to {destination}'
            asyncio.run(telegram_bot_send_message(message))
        response = response_200(response)

    elif 'cooldown' in response.json()['error']['message']:
        cooldown_in_response(response, character.name)
        move(character, map_id)


def gathering_loop(character, target_map, bank_map, slot_number):
    char_name = character.name
    stop = False if r.hget(char_name, 'stop').decode('utf-8') == 'false' else True
    while not stop:
        if target_map.content_code in to_diff_layer:
            map_id = to_diff_layer[target_map.content_code]
            move_transition(character, 'to', map_id)
        move(character, target_map.map_id)
        if is_stop(char_name):
            break
        gathering(character)
        if is_stop(char_name):
            break
        if target_map.content_code in from_diff_layer:
            map_id = from_diff_layer.get(target_map.content_code)
            move_transition(character, 'from', map_id)
        move(character, bank_map.map_id)
        if is_stop(char_name):
            break
        deposit_items_in_bank(character, slot_number)
        if is_stop(char_name):
            break
       
def gathering(character):
    char_name = character.name
    message = f'<b>{char_name}</b> starts gathering resourses.'
    asyncio.run(telegram_bot_send_message(message))
    stop = False if r.hget(char_name, 'stop').decode('utf-8') == 'false' else True
    while not stop:
        response = char_action_request(char_name,'gathering')
        if response.status_code == 200:
            response = response_200(response)
        elif 'cooldown' in response.json()['error']['message']:
            cooldown_in_response(response, char_name)
            continue
        elif 'error' in response.json():
            if response.json()['error']['code'] == 598:
                asyncio.run(telegram_bot_send_message(f'❗️ Resource event has been ended.'))
                r.hset(char_name, 'stop', 'true')
            else:
                response = response.json()
                error_in_responce(response, char_name)
                break
        stop = False if r.hget(
                    char_name, 'stop').decode('utf-8') == 'false' else True


def fighting_loop(character, target_map, bank_map, slot_number):
    char_name = character.name
    food, food_hp = '', 0
    lvl = character.level
    food_level = 1 if not (lvl // 10 * 10) else lvl // 10 * 10
    for f in FISH:
        if f.get(food_level) is not None:
            food = f.get(food_level)
            food_hp = f.get('hp')
    stop = False if r.hget(char_name, 'stop').decode('utf-8') == 'false' else True

    while not stop:
        if character.map != bank_map:
            move(character, bank_map.map_id)
        if is_stop(char_name):
            break
        withdraw_food_from_bank(character, food)
        if is_stop(char_name):
            break
        if target_map.content_code in to_diff_layer:
            map_id = to_diff_layer[target_map.content_code]
            move_transition(character, 'to', map_id)
        move(character, target_map.map_id)
        if is_stop(char_name):
            break
        fight_use_rest(character, food, food_hp)
        if is_stop(char_name):
            break
        rest(char_name)
        if is_stop(char_name):
            break
        if target_map.content_code in from_diff_layer:
            map_id = from_diff_layer.get(target_map.content_code)
            move_transition(character, 'from', map_id)
        move(character, bank_map.map_id)
        if is_stop(char_name):
            break
        deposit_items_in_bank(character, slot_number)
        if is_stop(char_name):
            break


def fight_use_rest(character, food, food_hp):
    char_name = character.name
    message = f'<b>{char_name}</b> starts fighting.'
    asyncio.run(telegram_bot_send_message(message))
    if_rest = False
    stop = False if r.hget(char_name, 'stop').decode('utf-8') == 'false' else True

    while not stop:
        # Fight
        response = fight(character)
        char_hp, char_max_hp = 0, 0
        if 'error' in response:
            if response['error']['code'] == 598:
                asyncio.run(telegram_bot_send_message(f'❗️ Monster event has been ended.'))
                r.hset(char_name, 'stop', 'true')
            else:
                error_in_responce(response, char_name)
            break
        else:
            for char in response['characters']:
                if char['name'] == char_name:
                    char_hp = char['hp']
                    char_max_hp = char['max_hp']

        # Use food
        if char_max_hp - char_hp > food_hp * 0.7:
            use_food_number = (char_max_hp - char_hp) // (food_hp * 0.7)
            response = use_food(char_name, food, use_food_number)
            if 'error' in response:
                error_in_responce(response, char_name)
                response = rest(char_name)
                break
            else:
                char_hp = response['character']['hp']
                char_max_hp = response['character']['max_hp']
                if char_max_hp != char_hp:
                    if_rest = True
        
        # rest
        if if_rest and char_hp < char_max_hp:
            response = rest(char_name)
            if 'error' in response:
                error_in_responce(response, char_name)
                break
            else:
                if_rest = False
        stop = False if r.hget(
                        char_name, 'stop').decode('utf-8') == 'false' else True


def fight(character):
    char_name = character.name
    if character.map.monster.monster_type == 'boss':
        char_names = [char.name for char in character.map.characters]
        char_names.remove(char_name)
        payload = {'participants': char_names}
        response = char_action_request(char_name, 'fight', payload)
    else:
        response = char_action_request(char_name, 'fight')
    if response.status_code == 200:
        response = response_200(response)
        if response['fight']['result'] == 'loss':
            message = f'❗️ <b>{char_name}</b> lost the fight.'
            asyncio.run(telegram_bot_send_message(message))
            r.hset(char_name, 'stop', 'true')
    elif 'cooldown' in response.json()['error']['message']:
        cooldown_in_response(response, char_name)
        response = fight(character)
    elif 'error' in response.json():
        response = response.json()
    return response


def use_food(char_name, food, use_food_number):
    payload = {'code': food, 'quantity': use_food_number}
    response = char_action_request(char_name, 'use', payload)
    if response.status_code == 200:
        response = response_200(response)
    elif 'cooldown' in response.json()['error']['message']:
        cooldown_in_response(response, char_name)
        response = use_food(char_name, food, use_food_number)
    elif 'error' in response.json():
        response = response.json()
    return response


def rest(char_name):
    response = char_action_request(char_name, 'rest')
    if response.status_code == 200:
        response = response_200(response)
    elif 'cooldown' in response.json()['error']['message']:
        cooldown_in_response(response, char_name)
        response = rest(char_name)
    elif 'error' in response.json():
        response = response.json()
    return response


def deposit_items_in_bank(character, slot_number):
    payload = []
    update_bank_items = []
    item_text = ''
    for item in character.inventory_items:
        if item.slot > slot_number:
            if item.item:
                payload.append({'code': item.item.code, 'quantity': item.quantity})
                item_text += f'    {item.item.name}: {item.quantity}\n'
                update_bank_items.append((item.item.code, item.quantity))
    response = char_action_request(character.name, 'bank/deposit/item', payload=payload)
    if response.status_code == 200:
        message = f'<b>{character.name}</b> deposits:\n{item_text}'
        asyncio.run(telegram_bot_send_message(message))
        response = response_200(response)
        BankItem.update_bank('deposit', update_bank_items)
    elif 'cooldown' in response.json()['error']['message']:
        cooldown_in_response(response, character.name)
        deposit_items_in_bank(character, slot_number)
    

def withdraw_food_from_bank(character, food):
    char_name = character.name
    number_of_items = 0
    for i in character.inventory_items:
        number_of_items += i.quantity
    food_quantity = int((character.inventory_max_items - number_of_items) / 2)
    payload = [{'code': food, 'quantity': food_quantity}]
    response = char_action_request(char_name, 'bank/withdraw/item', payload)
    if response.status_code == 200:
        message = f'<b>{character.name}</b> withdraws {food_quantity} {food}'
        asyncio.run(telegram_bot_send_message(message))
        response = response_200(response)
        BankItem.update_bank('withdraw', [(food, food_quantity)])
    elif 'cooldown' in response.json()['error']['message']:
        cooldown_in_response(response, character.name)
        withdraw_food_from_bank(character, food)
    elif 'error' in response.json():
        if 'Missing required item' in response.json()['error']['message']:
            asyncio.run(telegram_bot_send_message(f'❗️ There are no food {food} in bank.'))
            r.hset(char_name, 'stop', 'true')
        else:
            asyncio.run(telegram_bot_send_message(f'<b>{char_name}</b>: {response.json()['error']['message']}'))


def crafting_loop(character, target_code, target_map, bank_map, slot_number):
    char_name = character.name
    if character.map != bank_map:
        move(character, bank_map.map_id)
    deposit_items_in_bank(character, slot_number)
    stop = is_stop(char_name)
    target_item = Item.query.filter_by(code=target_code).first()
    number_inv_items = 0
    withdraw_bank_payload = []
    for i in character.inventory_items:
        number_inv_items += i.quantity
    free_inv_space = character.inventory_max_items - number_inv_items
    target_ingridients_number = 0
    for item in target_item.craft_items:
        target_ingridients_number += item.quantity
    target_quantity = free_inv_space // target_ingridients_number
    msg_text = ''
    withdraw_from_bank = []
    for item in target_item.craft_items:
        withdraw_bank_payload.append({'code': item.craft_item.code,
                                    'quantity': item.quantity*target_quantity})
        msg_text += f'    {item.craft_item.name}: {item.quantity*target_quantity}\n'
        withdraw_from_bank.append((item.craft_item.code, item.quantity*target_quantity))
   
    stop = False if r.hget(char_name, 'stop').decode('utf-8') == 'false' else True

    while not stop:
        if character.map != bank_map:
            move(character, bank_map.map_id)
        if is_stop(char_name):
            break
        withdraw_ingridiends_from_bank(
                char_name, withdraw_bank_payload, msg_text, withdraw_from_bank)
        if is_stop(char_name):
            break
        move(character, target_map.map_id)
        if is_stop(char_name):
            break
        craft(char_name, target_code, target_quantity, target_item.name)
        if target_item.can_recycle:
            recycle(char_name, target_code, target_quantity, target_item.name)
        if is_stop(char_name):
            break
        move(character, bank_map.map_id)
        if is_stop(char_name):
            break
        deposit_items_in_bank(character, slot_number)
        if is_stop(char_name):
            break


def withdraw_ingridiends_from_bank(char_name, payload, msg_text, withdraw_from_bank):
    response = char_action_request(char_name, 'bank/withdraw/item', payload)
    if response.status_code == 200:
        message = f'<b>{char_name}</b> withdraws ingridients for craft:\n{msg_text}'
        asyncio.run(telegram_bot_send_message(message))
        response = response_200(response)
        BankItem.update_bank('withdraw', withdraw_from_bank)
    elif 'cooldown' in response.json()['error']['message']:
        cooldown_in_response(response, char_name)
        withdraw_ingridiends_from_bank(char_name, payload, msg_text, withdraw_from_bank)
    elif 'error' in response.json():
        if 'Missing required item' in response.json()['error']['message']:
            asyncio.run(telegram_bot_send_message(f'❗️ There are not enough ingredients in the bank.'))
            r.hset(char_name, 'stop', 'true')
        else:
            asyncio.run(telegram_bot_send_message(response.json()['error']['message']))


def craft(char_name, target_code, target_quantity, target_name):
    payload = {'code': target_code, 'quantity': target_quantity}
    response = char_action_request(char_name, 'crafting', payload)
    if response.status_code == 200:
        message = f'<b>{char_name}</b> crafts {target_quantity} {target_name}.'
        asyncio.run(telegram_bot_send_message(message))
        response = response_200(response)
    elif 'cooldown' in response.json()['error']['message']:
        cooldown_in_response(response, char_name)
        craft(char_name, target_code, target_quantity, target_name)
    elif 'error' in response.json():
        asyncio.run(telegram_bot_send_message(response.json()['error']['message']))


def recycle(char_name, target_code, target_quantity, target_name):
    payload = {'code': target_code, 'quantity': target_quantity}
    response = char_action_request(char_name, 'recycling', payload)
    if response.status_code == 200:
        message = f'<b>{char_name}</b> recycles {target_quantity} {target_name}.'
        asyncio.run(telegram_bot_send_message(message))
        response = response_200(response)
    elif 'cooldown' in response.json()['error']['message']:
        cooldown_in_response(response, char_name)
        craft(char_name, target_code, target_quantity, target_name)
    elif 'error' in response.json():
        asyncio.run(telegram_bot_send_message(response.json()['error']['message']))


def is_stop(char_name):
    stop = False if r.hget(
                        char_name, 'stop').decode('utf-8') == 'false' else True
    if stop:
        asyncio.run(telegram_bot_send_message(f'🛑 <b>{char_name}</b> bot was stopped.'))
        r.lrem('bots', 0, char_name)
        return True
    else:
        return False
    

def move_transition(character, direction, map_id):
    char_name = character.name
    if direction == 'to':
        move(character, map_id)
        response = char_action_request(character.name, 'transition')
        if response.status_code == 200:
            response = response_200(response)
        elif 'cooldown' in response.json()['error']['message']:
            cooldown_in_response(response, char_name)
            char_action_request(character.name, 'transition')
    if direction == 'from':
        move(character, map_id)
        response = char_action_request(character.name, 'transition')
        if response.status_code == 200:
            response = response_200(response)
        elif 'cooldown' in response.json()['error']['message']:
            cooldown_in_response(response, char_name)
            char_action_request(character.name, 'transition')
