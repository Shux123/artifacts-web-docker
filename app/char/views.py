from flask import render_template, session, current_app, redirect, url_for, flash, request, jsonify
from . import char
from ..models import (Character,
                        Item,
                        Monster,
                        Effect,
                        NPC_Item,
                        NPC,
                        Map,
                        Resource,
                        BankItem)
from .. import db
from .forms import (MoveCharacter,
                    NpcBuySell,
                    BankDeposit,
                    BankWithdraw,
                    CraftingForm,
                    RecyclingForm,
                    EquipMultiSlot,
                    UseItem,
                    TaskTrade,
                    BuyGeOrder,
                    CreateSellOrder,
                    ItemGeHystory,
                    DeleteItem,
                    StartBotForm,
                    )
from ..all_requests import get_data_for_db, get_local_time
from ..char_requests import (char_equip_item,
                            char_unequip_item,
                            char_move_request,
                            get_cooldown,
                            char_action_request,
                            )
from sqlalchemy import distinct
from ..all_requests import get_data_for_db
from ..bot_tasks import bot
from .. import r


@char.errorhandler(404)
def page_not_found(e):
    return render_template('404.html', message=e.description), 404


@char.route('/<char_name>', methods=['GET', 'POST'])
def get_char(char_name):
    character = Character.query.filter_by(name=char_name).first()
    if character:
        if character.map.npc:
            return redirect(url_for('char.char_map_npc', char_name=char_name))
        elif character.map.content_type == 'bank':
            return redirect(url_for('char.char_map_bank', char_name=char_name))
        elif character.map.content_type == 'workshop':
            return redirect(url_for('char.char_map_craft', char_name=char_name))
        elif character.map.content_type == 'tasks_master':
            return redirect(url_for(
                'char.char_map_tasks_master', char_name=char_name))
        elif character.map.content_type == 'grand_exchange':
            return redirect(url_for('char.char_map_ge', char_name=char_name))

    move_form = MoveCharacter()
    if move_form.validate_on_submit():
        x_coord = move_form.x_coord.data
        y_coord = move_form.y_coord.data
        layer = move_form.layer.data
        map = Map.query.filter_by(layer=layer, x=x_coord, y=y_coord).first()
        response = char_move_request(char_name, map.map_id)
        if response.status_code != 200:
            flash(response.json()['error']['message'])
            return redirect(url_for('char.get_char', char_name=char_name))
        else:
            response = response.json()['data']
            Character.update_character(response['character'])
            flash(f'{char_name} moved to {response['destination']['name']} \
                    X: {response['destination']['x']}, Y: \
                        {response['destination']['y']}')
            return redirect(url_for('char.get_char', char_name=char_name))
    if character:
        move_form.x_coord.data = character.x
        move_form.y_coord.data = character.y
        move_form.layer.data = character.layer

    # NPC form
   
    # Bank form

    # Craft form

    # trade_task_form form

    # ge
            
    cooldown = 0
    if character:
        cooldown = int(get_cooldown(character.cooldown_expiration))
    if cooldown < 0:
        cooldown = 0
    if character is not None:
        move_form.x_coord.data = character.x
        move_form.y_coord.data = character.y
    if session.get('action_details'):
        action_details = session.pop('action_details')
    else:
        action_details = {}
    return render_template('char/character.html', character=character,
                           move_form=move_form, cooldown=cooldown,
                           action_details=action_details, Item=Item,
                           Monster=Monster,
                           Character=Character,
                           # npc_form=npc_form, 
                        #    deposit_form=deposit_form,
                        #    withdraw_form=withdraw_form,
                        #    bank_ditails=bank_ditails,
                        #    bank_items=bank_items,
                        #    number_of_items=number_of_items,
                        #    crafting_form=crafting_form,
                        #    recycling_form=recycling_form,
                        #    inventory_form=inventory_form,
                        #    use_form=use_form,
                        #    trade_task_form=trade_task_form,
                        #    ge_orders=ge_orders,
                        #    sell_order_form=sell_order_form,
                           names=current_app.config['NAMES'])


@char.route('/<char_name>/map/npc', methods=['GET', 'POST'])
def char_map_npc(char_name):
    character = Character.query.filter_by(name=char_name).first()

    move_form = MoveCharacter()
    if move_form.validate_on_submit():
        x_coord = move_form.x_coord.data
        y_coord = move_form.y_coord.data
        layer = move_form.layer.data
        map = Map.query.filter_by(layer=layer, x=x_coord, y=y_coord).first()
        response = char_move_request(char_name, map.map_id)
        if response.status_code != 200:
            flash(response.json()['error']['message'])
            return redirect(url_for('char.get_char', char_name=char_name))
        else:
            response = response.json()['data']
            Character.update_character(response['character'])
            flash(f'{char_name} moved to {response['destination']['name']} \
                    X: {response['destination']['x']}, Y: \
                        {response['destination']['y']}')
            return redirect(url_for('char.get_char', char_name=char_name))
    if character:
        move_form.x_coord.data = character.x
        move_form.y_coord.data = character.y
        move_form.layer.data = character.layer

    npc_form = NpcBuySell()
    if character:
        if character.map.npc:
            query = db.session.query(distinct(Item.code))
            query = query.join(NPC_Item, NPC_Item.item_id == Item.id)
            query = query.join(NPC, NPC.id == NPC_Item.npc_id)
            query = query.join(Map, Map.npc_id == NPC.id)
            query = query.join(Character, Character.map_id == Map.id)
            query = query.filter(Character.id == character.id)
            codes = [code[0] for code in query.all()]
            npc_choices = []
            for code in codes:
                item = Item.query.filter_by(code=code).first()
                npc_choices.append((code, item.name))
            npc_form.item.choices = npc_choices
        if npc_form.validate_on_submit():
            action = npc_form.buy_sell.data
            item_code = npc_form.item.data
            quantity = npc_form.quantity.data
            payload = {'code': item_code, 'quantity': quantity}
            response = char_action_request(char_name, action, payload)
            if response.status_code != 200:
                flash(response.json()['error']['message'])
                return redirect(url_for('char.get_char', char_name=character.name))
            text = ''
            if action == 'npc/buy':
                text = 'bought'
            else:
                text = 'sold'
            item = Item.query.filter_by(code=item_code).first()
            flash(f'{character.name} {text} {quantity} {item.name}')
            response = response.json()['data']
            Character.update_character(response['character'])
            response['transaction']['npc_buy_sell'] = True
            session['action_details'] = response['transaction']
            return redirect(url_for('char.char_map_npc', char_name=character.name))
            
    cooldown = 0
    if character:
        cooldown = int(get_cooldown(character.cooldown_expiration))
    if cooldown < 0:
        cooldown = 0
    if character is not None:
        move_form.x_coord.data = character.x
        move_form.y_coord.data = character.y
    if session.get('action_details'):
        action_details = session.pop('action_details')
    else:
        action_details = {}
    return render_template('char/char_map_npc.html', character=character,
                           cooldown=cooldown,
                           action_details=action_details,
                           move_form=move_form,
                           Item=Item,
                           npc_form=npc_form,
                           names=current_app.config['NAMES'])

            
@char.route('/<char_name>/map/bank', methods=['GET', 'POST'])
def char_map_bank(char_name):
    character = Character.query.filter_by(name=char_name).first()

    move_form = MoveCharacter()
    if move_form.validate_on_submit():
        x_coord = move_form.x_coord.data
        y_coord = move_form.y_coord.data
        layer = move_form.layer.data
        map = Map.query.filter_by(layer=layer, x=x_coord, y=y_coord).first()
        response = char_move_request(char_name, map.map_id)
        if response.status_code != 200:
            flash(response.json()['error']['message'])
            return redirect(url_for('char.get_char', char_name=char_name))
        else:
            response = response.json()['data']
            Character.update_character(response['character'])
            flash(f'{char_name} moved to {response['destination']['name']} \
                    X: {response['destination']['x']}, Y: \
                        {response['destination']['y']}')
            return redirect(url_for('char.get_char', char_name=char_name))
    if character:
        move_form.x_coord.data = character.x
        move_form.y_coord.data = character.y
        move_form.layer.data = character.layer

    deposit_form = BankDeposit()
    withdraw_form = BankWithdraw()
    bank_items = db.session.query(BankItem).filter(BankItem.quantity > 0).order_by(BankItem.id).all()
    number_of_items = 0
    if character:
        if character.map.content_type == 'bank':
            inventory_items_names = []
            for item in character.inventory_items.all():
                if item.item:
                    inventory_items_names.extend(
                                        [(item.item.code, item.item.name)])
            for i in character.inventory_items:
                number_of_items += i.quantity
            deposit_form.deposit_item.choices.extend(sorted(inventory_items_names))            
            bank_items_names = []
            for i in bank_items:
                bank_items_names.extend([(i.item.code, i.item.name)])
            withdraw_form.withdraw_item.choices.extend(sorted(bank_items_names))
    if deposit_form.validate_on_submit():        
        item_code = deposit_form.deposit_item.data
        quantity = deposit_form.deposit_quantity.data
        response = None
        item_name = None
        if item_code == 'gold':
            payload = {'quantity': quantity}
            response = char_action_request(
                character.name, 'bank/deposit/gold', payload=payload)
        else:
            item = Item.query.filter_by(code=item_code).first()
            item_name = item.name
            payload = [{'code': item_code,'quantity': quantity}]
            response = char_action_request(
                character.name, 'bank/deposit/item', payload=payload)
            if response.status_code == 200:
                BankItem.update_bank('deposit', [(item_code, quantity)])
        if response.status_code != 200:
            flash(response.json()['error']['message'])
            return redirect(url_for('char.get_char', char_name=character.name))
        flash(f'{character.name} deposited {quantity} {item_name or 'gold'}')
        response = response.json()['data']
        Character.update_character(response['character'])
        return redirect(url_for('char.get_char', char_name=character.name))

    if withdraw_form.validate_on_submit():
        item_code = withdraw_form.withdraw_item.data
        quantity = withdraw_form.withdraw_quantity.data
        response = None
        item_name = None
        if item_code == 'gold':
            payload = {'quantity': quantity}
            response = char_action_request(
                character.name, 'bank/withdraw/gold', payload=payload)
        else:
            item = Item.query.filter_by(code=item_code).first()
            item_name = item.name
            payload = [{'code': item_code,'quantity': quantity}]
            response = char_action_request(
                character.name, 'bank/withdraw/item', payload=payload)
            if response.status_code == 200:
                BankItem.update_bank('withdraw', [(item_code, quantity)])
        if response.status_code != 200:
            flash(response.json()['error']['message'])
            return redirect(url_for('char.get_char', char_name=character.name))
        flash(f'{character.name} withdrew {quantity} {item_name or 'gold'}')
        response = response.json()['data']
        Character.update_character(response['character'])
        return redirect(url_for('char.get_char', char_name=character.name))
    
    inventory_form = EquipMultiSlot()
    inv_choices = []
    item_choices = []
    if character:
        for i in character.inventory_items:
            if i.item:
                if i.item.can_equip_musliple_slot:
                    if i.item.item_type == 'ring':
                        inv_choices.append(('ring1', 'Ring 1'))
                        inv_choices.append(('ring2', 'Ring 2'))
                        item_choices.append((i.item.code, i.item.name))
                    elif i.item.item_type == 'artifact':
                        inv_choices.append(('artifact1', 'Artifact 1'))
                        inv_choices.append(('artifact2', 'Artifact 2'))
                        inv_choices.append(('artifact3', 'Artifact 3'))
                        item_choices.append((i.item.code, i.item.name))
                    elif i.item.item_type == 'utility':
                        inv_choices.append(('utility1', 'Utility 1'))
                        inv_choices.append(('utility2', 'Utility 2'))
                        item_choices.append((i.item.code, i.item.name))
        inventory_form.equip.choices = sorted(list(set(inv_choices)))
        inventory_form.equip_item.choices = sorted(item_choices)

    if inventory_form.validate_on_submit():
        slot = inventory_form.equip.data
        item_code = inventory_form.equip_item.data
        quantity = inventory_form.equip_quantity.data
        item = Item.query.filter_by(code=item_code).first()
        response = char_equip_item(char_name, item_code, slot, quantity)
        if response.status_code == 200:
            flash(f'{char_name} equiped {item.name}.')
            Character.update_character(response.json()['data']['character'])
        else:
            flash(response.json()['error']['message'])
        if request.referrer:
            return redirect(request.referrer)
        return redirect(url_for('char.inventory', char_name=char_name))

    use_form = UseItem()
    item_choices = []
    if character:
        for i in character.inventory_items:
            if i.item and i.item.item_type == 'consumable':
                item_choices.append((i.item.code, i.item.name))
        use_form.use_item.choices = sorted(item_choices)
    
    if use_form.validate_on_submit():
        item_code = use_form.use_item.data
        quantity = use_form.use_quantity.data
        item = Item.query.filter_by(code=item_code).first()
        payload = {'code': item_code, 'quantity': quantity}
        response = char_action_request(char_name, 'use', payload)
        if response.status_code == 200:
            flash(f'{char_name} used {quantity} {item.name}.')
            Character.update_character(response.json()['data']['character'])
        else:
            flash(response.json()['error']['message'])
        if request.referrer:
            return redirect(request.referrer)
        return redirect(url_for('char.inventory', char_name=char_name))

    cooldown = 0
    if character:
        cooldown = int(get_cooldown(character.cooldown_expiration))
    if cooldown < 0:
        cooldown = 0
    if character is not None:
        move_form.x_coord.data = character.x
        move_form.y_coord.data = character.y
    if session.get('action_details'):
        action_details = session.pop('action_details')
    else:
        action_details = {}
    return render_template('char/char_map_bank.html', character=character,
                           cooldown=cooldown,
                           action_details=action_details,
                           move_form=move_form,
                           Item=Item,
                           deposit_form=deposit_form,
                           withdraw_form=withdraw_form,
                           number_of_items=number_of_items,
                           inventory_form=inventory_form,
                           use_form=use_form,
                           names=current_app.config['NAMES'])


@char.route('/<char_name>/bank', methods=['GET', 'POST'])
def char_bank(char_name):
    character = Character.query.filter_by(name=char_name).first()

    bank_ditails = get_data_for_db('my/bank')
    bank_items = db.session.query(BankItem).filter(BankItem.quantity > 0).order_by(BankItem.id).all()

    cooldown = 0
    if character:
        cooldown = int(get_cooldown(character.cooldown_expiration))
    if cooldown < 0:
        cooldown = 0
    if session.get('action_details'):
        action_details = session.pop('action_details')
    else:
        action_details = {}
    return render_template('char/char_bank.html', character=character,
                           cooldown=cooldown,
                           action_details=action_details,
                           Item=Item,
                           bank_ditails=bank_ditails,
                           bank_items=bank_items,
                           names=current_app.config['NAMES'])



@char.route('/<char_name>/map/craft', methods=['GET', 'POST'])
def char_map_craft(char_name):
    character = Character.query.filter_by(name=char_name).first()

    move_form = MoveCharacter()
    if move_form.validate_on_submit():
        x_coord = move_form.x_coord.data
        y_coord = move_form.y_coord.data
        layer = move_form.layer.data
        map = Map.query.filter_by(layer=layer, x=x_coord, y=y_coord).first()
        response = char_move_request(char_name, map.map_id)
        if response.status_code != 200:
            flash(response.json()['error']['message'])
            return redirect(url_for('char.get_char', char_name=char_name))
        else:
            response = response.json()['data']
            Character.update_character(response['character'])
            flash(f'{char_name} moved to {response['destination']['name']} \
                    X: {response['destination']['x']}, Y: \
                        {response['destination']['y']}')
            return redirect(url_for('char.get_char', char_name=char_name))
    if character:
        move_form.x_coord.data = character.x
        move_form.y_coord.data = character.y
        move_form.layer.data = character.layer

    crafting_form = CraftingForm()
    recycling_form = RecyclingForm()
    recycle_items_names = []
    crafting_choices = []
    if character:
        if character.map.content_type == 'workshop':
            for item in character.inventory_items.all():
                if item.item and item.item.can_recycle:
                    if item.item.craft_skill == character.map.content_code:
                        recycle_items_names.extend(
                                        [(item.item.code, item.item.name)])
            recycling_form.recycle_item.choices.extend(sorted(recycle_items_names))

            # get choices for crafting_form, depends on character item inventory
            items_for_craft = []
            crafted_items = []
            inventory_items = {}
            items_for_craft_codes = []
            for inv_item in character.inventory_items:
                if inv_item.item:
                    inventory_items.update({inv_item.item.code: inv_item.quantity})
                    for item in inv_item.item.crafted_items:
                        crafted_items.append(item.crafted_item)
            for item in crafted_items:
                ingridients = []
                if item.craft_skill == character.map.content_code:
                    for ingridient in item.craft_items:
                        ingridients.append({ingridient.craft_item.code: ingridient.quantity})
                    items_for_craft.append({item.code: ingridients})

            for item in items_for_craft:
                item_code = list(item.keys())[0]
                requirements_list = item[item_code]
                can_craft = True
                for requirement in requirements_list:
                    requirement_item_code = list(requirement.keys())[0]
                    requirement_quantity = requirement[requirement_item_code]
                    if requirement_item_code not in inventory_items or \
                        inventory_items[requirement_item_code] < requirement_quantity:
                        can_craft = False
                        break
                if can_craft:
                    items_for_craft_codes.append(item_code)
            
            crafting_choices = []
            for item in set(items_for_craft_codes):
                i = Item.query.filter_by(code=item).first()
                crafting_choices.append((item, i.name))
            crafting_form.craft_item.choices = sorted(crafting_choices)

    if crafting_form.validate_on_submit():
        item_code = crafting_form.craft_item.data
        quantity = crafting_form.craft_quantity.data
        payload = {'code': item_code, 'quantity': quantity}
        response = char_action_request(character.name, 'crafting', payload)
        if response.status_code != 200:
            flash(response.json()['error']['message'])
            return redirect(url_for('char.get_char', char_name=character.name))
        response = response.json()['data']
        item = Item.query.filter_by(code=item_code).first()
        Character.update_character(response['character'])
        flash(f'{char_name} crafted {quantity} {item.name}')
        response['details']['crafting'] = True
        session['action_details'] = response['details']
        return redirect(url_for('char.get_char', char_name=character.name))
    
    if recycling_form.validate_on_submit():
        item_code = recycling_form.recycle_item.data
        quantity = recycling_form.recycle_quantity.data
        payload = {'code': item_code, 'quantity': quantity}
        response = char_action_request(character.name, 'recycling', payload)
        if response.status_code != 200:
            flash(response.json()['error']['message'])
            return redirect(url_for('char.get_char', char_name=character.name))
        response = response.json()['data']
        item = Item.query.filter_by(code=item_code).first()
        Character.update_character(response['character'])
        flash(f'{char_name} recycled {quantity} {item.name}')
        response['details']['recycling'] = True
        session['action_details'] = response['details']
        return redirect(url_for('char.get_char', char_name=character.name))

    cooldown = 0
    if character:
        cooldown = int(get_cooldown(character.cooldown_expiration))
    if cooldown < 0:
        cooldown = 0
    if character is not None:
        move_form.x_coord.data = character.x
        move_form.y_coord.data = character.y
    if session.get('action_details'):
        action_details = session.pop('action_details')
    else:
        action_details = {}
    return render_template('char/char_map_craft.html', character=character,
                           cooldown=cooldown,
                           action_details=action_details,
                           move_form=move_form,
                           Item=Item,
                           crafting_form=crafting_form,
                           recycling_form=recycling_form,
                           names=current_app.config['NAMES'])


@char.route('/<char_name>/map/tasks_master', methods=['GET', 'POST'])
def char_map_tasks_master(char_name):
    character = Character.query.filter_by(name=char_name).first()

    move_form = MoveCharacter()
    if move_form.validate_on_submit():
        x_coord = move_form.x_coord.data
        y_coord = move_form.y_coord.data
        layer = move_form.layer.data
        map = Map.query.filter_by(layer=layer, x=x_coord, y=y_coord).first()
        response = char_move_request(char_name, map.map_id)
        if response.status_code != 200:
            flash(response.json()['error']['message'])
            return redirect(url_for('char.get_char', char_name=char_name))
        else:
            response = response.json()['data']
            Character.update_character(response['character'])
            flash(f'{char_name} moved to {response['destination']['name']} \
                    X: {response['destination']['x']}, Y: \
                        {response['destination']['y']}')
            return redirect(url_for('char.get_char', char_name=char_name))
    if character:
        move_form.x_coord.data = character.x
        move_form.y_coord.data = character.y
        move_form.layer.data = character.layer

    trade_task_form = TaskTrade()
    trade_choices = []
    if character:
        if character.task_type == 'items':
            task_item = Item.query.filter_by(code=character.task).first()
            for item in character.inventory_items:
                if item.item == task_item:
                    trade_choices = (task_item.code, task_item.name)
                    trade_task_form.trade_item.choices.append(trade_choices)
                    trade_task_form.trade_quantity.data = item.quantity
        if trade_task_form.validate_on_submit():
            item_code = trade_task_form.trade_item.data
            trade_quantity = trade_task_form.trade_quantity.data
            item = Item.query.filter_by(code=item_code).first()
            payload = {'code': item_code, 'quantity': trade_quantity}
            response = char_action_request(char_name, 'task/trade', payload)
            if response.status_code != 200:
                flash(response.json()['error']['message'])
                return redirect(url_for('char.get_char', char_name=char_name))
            flash(f'{char_name} traded {trade_quantity} {item.name}.')
            response = response.json()['data']
            Character.update_character(response['character'])
            response['trade']['task_trade'] = True
            session['action_details'] = response['trade']
            return redirect(url_for('char.get_char', char_name=char_name))

    cooldown = 0
    if character:
        cooldown = int(get_cooldown(character.cooldown_expiration))
    if cooldown < 0:
        cooldown = 0
    if character is not None:
        move_form.x_coord.data = character.x
        move_form.y_coord.data = character.y
    if session.get('action_details'):
        action_details = session.pop('action_details')
    else:
        action_details = {}
    return render_template('char/char_map_tasks_master.html', character=character,
                           cooldown=cooldown,
                           Monster=Monster,
                           Item=Item,
                           action_details=action_details,
                           move_form=move_form,
                           trade_task_form=trade_task_form,
                           names=current_app.config['NAMES'])


@char.route('/<char_name>/map/ge', methods=['GET', 'POST'])
def char_map_ge(char_name):
    character = Character.query.filter_by(name=char_name).first()

    move_form = MoveCharacter()
    if move_form.validate_on_submit():
        x_coord = move_form.x_coord.data
        y_coord = move_form.y_coord.data
        layer = move_form.layer.data
        map = Map.query.filter_by(layer=layer, x=x_coord, y=y_coord).first()
        response = char_move_request(char_name, map.map_id)
        if response.status_code != 200:
            flash(response.json()['error']['message'])
            return redirect(url_for('char.get_char', char_name=char_name))
        else:
            response = response.json()['data']
            Character.update_character(response['character'])
            flash(f'{char_name} moved to {response['destination']['name']} \
                    X: {response['destination']['x']}, Y: \
                        {response['destination']['y']}')
            return redirect(url_for('char.get_char', char_name=char_name))
    if character:
        move_form.x_coord.data = character.x
        move_form.y_coord.data = character.y
        move_form.layer.data = character.layer

    ge_orders = None
    sell_order_form = None
    if character:
        if character.map.content_type == 'grand_exchange':
            ge_orders = get_data_for_db('grandexchange/orders')
            total_ge_orders = 0
            for order in ge_orders:
                total_ge_orders += 1
                created_at = get_local_time(order['created_at'])
                order['created_at'] = created_at.strftime('%d-%m-%Y %H:%M')
            character.total_ge_orders = total_ge_orders

        sell_order_form = CreateSellOrder()
        inventory_items_names = []
        for item in character.inventory_items.all():
            if item.item:
                inventory_items_names.extend([(item.item.code, item.item.name)])
        sell_order_form.sell_item.choices = sorted(inventory_items_names)
        
        if sell_order_form.validate_on_submit():
            item_code = sell_order_form.sell_item.data
            sell_quantity = sell_order_form.sell_quantity.data
            price = sell_order_form.price.data
            item = Item.query.filter_by(code=item_code).first()
            payload = {'code': item_code,
                       'quantity': sell_quantity,
                       'price': price}
            response = char_action_request(
                                    char_name, 'grandexchange/sell', payload)
            if response.status_code != 200:
                flash(response.json()['error']['message'])
                return redirect(url_for('char.get_char', char_name=char_name))
            flash(f'{char_name} created grand exchange sell order.')
            response = response.json()['data']
            Character.update_character(response['character'])
            response['order']['sell_order'] = True
            created_at = get_local_time(response['order']['created_at'])
            response['order']['created_at'] = created_at.strftime('%d-%m-%Y %H:%M')
            session['action_details'] = response['order']
            return redirect(url_for('char.get_char', char_name=char_name))

    cooldown = 0
    if character:
        cooldown = int(get_cooldown(character.cooldown_expiration))
    if cooldown < 0:
        cooldown = 0
    if character is not None:
        move_form.x_coord.data = character.x
        move_form.y_coord.data = character.y
    if session.get('action_details'):
        action_details = session.pop('action_details')
    else:
        action_details = {}
    return render_template('char/char_map_ge.html', character=character,
                           cooldown=cooldown,
                           action_details=action_details,
                           move_form=move_form,
                           Item=Item,
                           sell_order_form=sell_order_form,
                           ge_orders=ge_orders,
                           names=current_app.config['NAMES'])


@char.route('/<char_name>/skills')
def get_char_skills(char_name):
    character = Character.query.filter_by(name=char_name).first()
    cooldown = 0
    if character:
        cooldown = int(get_cooldown(character.cooldown_expiration))
    if cooldown < 0:
        cooldown = 0
    return render_template('char/skills.html', character=character,
                           cooldown=cooldown,
                           names=current_app.config['NAMES'])


@char.route('/<char_name>/stats')
def get_char_stats(char_name):
    character = Character.query.filter_by(name=char_name).first()
    cooldown = 0
    if character:
        cooldown = int(get_cooldown(character.cooldown_expiration))
    if cooldown < 0:
        cooldown = 0
    return render_template('char/stats.html', character=character,
                           Effect=Effect, cooldown=cooldown,
                           names=current_app.config['NAMES'])


@char.route('/<char_name>/equipments')
def get_equipments(char_name):
    character = Character.query.filter_by(name=char_name).first()
    cooldown = 0
    if character:
        cooldown = int(get_cooldown(character.cooldown_expiration))
    if cooldown < 0:
        cooldown = 0
    return render_template('char/equipments.html', character=character,
                           cooldown=cooldown,
                           names=current_app.config['NAMES'])


@char.route('/<char_name>/inventory', methods=['GET', 'POST'])
def inventory(char_name):
    character = Character.query.filter_by(name=char_name).first()
    inventory_form = EquipMultiSlot()
    inv_choices = []
    item_choices = []
    for i in character.inventory_items:
        if i.item:
            if i.item.can_equip_musliple_slot:
                if i.item.item_type == 'ring':
                    inv_choices.append(('ring1', 'Ring 1'))
                    inv_choices.append(('ring2', 'Ring 2'))
                    item_choices.append((i.item.code, i.item.name))
                elif i.item.item_type == 'artifact':
                    inv_choices.append(('artifact1', 'Artifact 1'))
                    inv_choices.append(('artifact2', 'Artifact 2'))
                    inv_choices.append(('artifact3', 'Artifact 3'))
                    item_choices.append((i.item.code, i.item.name))
                elif i.item.item_type == 'utility':
                    inv_choices.append(('utility1', 'Utility 1'))
                    inv_choices.append(('utility2', 'Utility 2'))
                    item_choices.append((i.item.code, i.item.name))
    inventory_form.equip.choices = sorted(list(set(inv_choices)))
    inventory_form.equip_item.choices = sorted(item_choices)

    if inventory_form.validate_on_submit():
        slot = inventory_form.equip.data
        item_code = inventory_form.equip_item.data
        quantity = inventory_form.equip_quantity.data
        item = Item.query.filter_by(code=item_code).first()
        response = char_equip_item(char_name, item_code, slot, quantity)
        if response.status_code == 200:
            flash(f'{char_name} equiped {item.name}.')
            Character.update_character(response.json()['data']['character'])
        else:
            flash(response.json()['error']['message'])
        if request.referrer:
            return redirect(request.referrer)
        return redirect(url_for('char.inventory', char_name=char_name))
    
    use_form = UseItem()
    item_choices = []
    for i in character.inventory_items:
        if i.item and i.item.item_type == 'consumable':
            item_choices.append((i.item.code, i.item.name))
    use_form.use_item.choices = sorted(item_choices)

    if use_form.validate_on_submit():
        item_code = use_form.use_item.data
        quantity = use_form.use_quantity.data
        item = Item.query.filter_by(code=item_code).first()
        payload = {'code': item_code, 'quantity': quantity}
        response = char_action_request(char_name, 'use', payload)
        if response.status_code == 200:
            flash(f'{char_name} used {quantity} {item.name}.')
            Character.update_character(response.json()['data']['character'])
        else:
            flash(response.json()['error']['message'])
        if request.referrer:
            return redirect(request.referrer)
        return redirect(url_for('char.inventory', char_name=char_name))


    cooldown = 0
    if character:
        cooldown = int(get_cooldown(character.cooldown_expiration))
    if cooldown < 0:
        cooldown = 0
    number_of_items = 0
    for i in character.inventory_items:
        number_of_items += i.quantity
    return render_template('char/inventory.html', character=character,
                           number_of_items=number_of_items,
                           cooldown=cooldown,
                           inventory_form=inventory_form,
                           use_form=use_form,
                           names=current_app.config['NAMES'])


@char.route('/<char_name>/task')
def get_task(char_name):
    character = Character.query.filter_by(name=char_name).first()
    cooldown = 0
    if character:
        cooldown = int(get_cooldown(character.cooldown_expiration))
    if cooldown < 0:
        cooldown = 0
    return render_template('char/task.html', character=character,
                           Item=Item,
                           Monster=Monster,
                           cooldown=cooldown,
                           names=current_app.config['NAMES'])


@char.route('/<char_name>/equip/<int:id>')
def equip_item(char_name, id):
    item = Item.query.get_or_404(id)
    response = char_equip_item(char_name, item.code, item.item_type)
    if response.status_code == 200:
        flash(f'{char_name} equiped {item.name}.')
        Character.update_character(response.json()['data']['character'])
    else:
        flash(response.json()['error']['message'])
    if request.referrer:
        return redirect(request.referrer)
    return redirect(url_for('char.inventory', char_name=char_name))


@char.route('/<char_name>/unequip/<int:id>/<slot>/<int:quantity>')
def unequip_item(char_name, id, slot, quantity):
    item = Item.query.get_or_404(id)
    response = char_unequip_item(char_name, slot, quantity)
    if response.status_code == 200:
        flash(f'{item.item_type.capitalize()} {item.name} unequiped.')
        Character.update_character(response.json()['data']['character'])
    else:
        flash(response.json()['error']['message'])
    return redirect(url_for('char.get_equipments', char_name=char_name))


@char.route('/<char_name>/rest')
def rest(char_name):
    response = char_action_request(char_name, 'rest')
    if response.status_code == 200:
        response = response.json()['data']
        flash(f'{char_name} rested and restored {response['hp_restored']} hp.')
        Character.update_character(response['character'])
    else:
        flash(response.json()['error']['message'])
    return redirect(url_for('char.get_char', char_name=char_name))


@char.route('/<char_name>/fight')
def fight(char_name):
    character = Character.query.filter_by(name=char_name).first()
    if character.map.monster.monster_type == 'boss':
        char_names = [char.name for char in character.map.characters]
        char_names.remove(char_name)
        payload = {'participants': char_names}
        response = char_action_request(char_name, 'fight', payload)
    else:
        response = char_action_request(char_name, 'fight')
    if response.status_code == 200:
        monster = character.map.monster.name
        response = response.json()['data']
        for char in response['characters']:
            Character.update_character(char)
        flash(f'{char_name} fought {monster} and {response['fight']['result']}')
        response['fight']['fight'] = True
        session['action_details'] = response['fight']
    else:
        flash(response.json()['error']['message'])
    return redirect(url_for('char.get_char', char_name=char_name))


@char.route('/<char_name>/gathering')
def gathering(char_name):
    response = char_action_request(char_name, 'gathering')
    if response.status_code == 200:
        character = Character.query.filter_by(name=char_name).first()
        resource = character.map.resource.name
        response = response.json()['data']
        Character.update_character(response['character'])
        flash(f'{char_name} gathered {resource}')
        response['details']['gathering'] = True
        session['action_details'] = response['details']
    else:
        flash(response.json()['error']['message'])
    return redirect(url_for('char.get_char', char_name=char_name))


@char.route('/<char_name>/new_task')
def new_task(char_name):
    response = char_action_request(char_name, 'task/new')
    if response.status_code != 200:
        flash(response.json()['error']['message'])
        return redirect(url_for('char.get_char', char_name=char_name))
    character = Character.query.filter_by(name=char_name).first()
    if character:
        response = response.json()['data']
        Character.update_character(response['character'])
        flash(f'{char_name} received new task.')
        response['task']['task'] = True
        session['action_details'] = response['task']
        return redirect(url_for('char.get_char', char_name=char_name))


@char.route('/<char_name>/complete_task')
def complete_task(char_name):
    response = char_action_request(char_name, 'task/complete')
    if response.status_code != 200:
        flash(response.json()['error']['message'])
        return redirect(url_for('char.get_char', char_name=char_name))
    character = Character.query.filter_by(name=char_name).first()
    if character:
        response = response.json()['data']
        Character.update_character(response['character'])
        flash(f'{char_name} completed the task.')
        response['rewards']['task_rewards'] = True
        session['action_details'] = response['rewards']
        return redirect(url_for('char.get_char', char_name=char_name))


@char.route('/<char_name>/cancel_task')
def cancel_task(char_name):
    response = char_action_request(char_name, 'task/cancel')
    if response.status_code != 200:
        flash(response.json()['error']['message'])
        return redirect(url_for('char.get_char', char_name=char_name))
    character = Character.query.filter_by(name=char_name).first()
    if character:
        response = response.json()['data']
        Character.update_character(response['character'])
        flash(f'{char_name} canceled the task.')
        return redirect(url_for('char.get_char', char_name=char_name))


@char.route('/<char_name>/exchange_coins')
def exchange_coins(char_name):
    response = char_action_request(char_name, 'task/exchange')
    if response.status_code != 200:
        flash(response.json()['error']['message'])
        return redirect(url_for('char.get_char', char_name=char_name))
    character = Character.query.filter_by(name=char_name).first()
    if character:
        response = response.json()['data']
        Character.update_character(response['character'])
        flash(f'{char_name} exchanged tasks coins.')
        response['rewards']['task_rewards'] = True
        session['action_details'] = response['rewards']
        return redirect(url_for('char.get_char', char_name=char_name))


@char.route('/<char_name>/ge_order/<id>', methods=['GET', 'POST'])
def ge_order(char_name, id):
    order = get_data_for_db(f'grandexchange/orders/{id}')
    character = Character.query.filter_by(name=char_name).first()
    local_time = get_local_time(order['created_at'])
    order['created_at'] = local_time.strftime('%d-%m-%Y %H:%M')
    buy_ge_form = BuyGeOrder()
    if buy_ge_form.validate_on_submit():
        quantity = buy_ge_form.ge_quantity.data
        payload = {'id': id, 'quantity': quantity}
        response = char_action_request(char_name, 'grandexchange/buy', payload)
        if response.status_code != 200:
            flash(response.json()['error']['message'])
            return redirect(url_for('char.get_char', char_name=char_name))
        if character:
            response = response.json()['data']
            Character.update_character(response['character'])
            flash(f'{char_name} bought item in grand exchange.')
            response['order']['bought_order'] = True
            session['action_details'] = response['order']
            return redirect(url_for('char.get_char', char_name=char_name))

    cooldown = 0
    if character:
        cooldown = int(get_cooldown(character.cooldown_expiration))
    if cooldown < 0:
        cooldown = 0
    return render_template('char/ge_order.html',
                           cooldown=cooldown,
                           character=character,
                           order=order,
                           Item=Item,
                           buy_ge_form=buy_ge_form,
                           names=current_app.config['NAMES'])


@char.route('/<char_name>/cancel_ge_order/<id>')
def cancel_ge_order(char_name, id):
    payload = { "id": id }
    response = char_action_request(char_name, 'grandexchange/cancel', payload)
    if response.status_code != 200:
        flash(response.json()['error']['message'])
        return redirect(url_for('char.get_char', char_name=char_name))
    character = Character.query.filter_by(name=char_name).first()
    if character:
        response = response.json()['data']
        Character.update_character(response['character'])
        flash(f'{char_name} canceled the grand exchange order.')
        response['order']['canceled_order'] = True
        session['action_details'] = response['order']
        return redirect(url_for('char.get_char', char_name=char_name))


@char.route('/<char_name>/my_ge_orders')
def my_ge_orders(char_name):
    ge_orders = None
    character = Character.query.filter_by(name=char_name).first()
    if character:
        ge_orders = get_data_for_db('/my/grandexchange/orders')
        total_ge_orders = 0
        for order in ge_orders:
            total_ge_orders += 1
            created_at = get_local_time(order['created_at'])
            order['created_at'] = created_at.strftime('%d-%m-%Y %H:%M')
        character.total_ge_orders = total_ge_orders

    cooldown = 0
    if character:
        cooldown = int(get_cooldown(character.cooldown_expiration))
    if cooldown < 0:
        cooldown = 0
    return render_template('char/my_ge_orders.html', character=character,
                           Item=Item,
                           cooldown=cooldown,
                           ge_orders=ge_orders,
                           names=current_app.config['NAMES'])


@char.route('/<char_name>/my_ge_hystory')
def my_ge_hystory(char_name):
    ge_orders = None
    character = Character.query.filter_by(name=char_name).first()
    if character:
        ge_orders = get_data_for_db('/my/grandexchange/history')
        for order in ge_orders:
            sold_at = get_local_time(order['sold_at'])
            order['sold_at'] = sold_at.strftime('%d-%m-%Y %H:%M')

    cooldown = 0
    if character:
        cooldown = int(get_cooldown(character.cooldown_expiration))
    if cooldown < 0:
        cooldown = 0
    return render_template('char/my_ge_hystory.html', character=character,
                           Item=Item,
                           cooldown=cooldown,
                           ge_orders=ge_orders,
                           names=current_app.config['NAMES'])


@char.route('/<char_name>/item_ge_hystory', methods=['GET', 'POST'])
def item_ge_hystory(char_name):
    ge_orders = None
    character = Character.query.filter_by(name=char_name).first()
    item_hystory_form = ItemGeHystory()
    items = Item.query.all()
    items_names = []
    for item in items:
        if item.tradeable:
            items_names.append((item.code, item.name))
    item_hystory_form.item_ge.choices = sorted(items_names)
    if item_hystory_form.validate_on_submit():
        item_code = item_hystory_form.item_ge.data
        ge_orders = get_data_for_db(f'/grandexchange/history/{item_code}')
        for order in ge_orders:
            sold_at = get_local_time(order['sold_at'])
            order['sold_at'] = sold_at.strftime('%d-%m-%Y %H:%M')

    cooldown = 0
    if character:
        cooldown = int(get_cooldown(character.cooldown_expiration))
    if cooldown < 0:
        cooldown = 0
    return render_template('char/item_ge_hystory.html', character=character,
                           Item=Item,
                           cooldown=cooldown,
                           ge_orders=ge_orders,
                           item_hystory_form=item_hystory_form,
                           names=current_app.config['NAMES'])


@char.route('/<char_name>/delete_item', methods=['GET', 'POST'])
def delete_item(char_name):
    character = Character.query.filter_by(name=char_name).first()
    delete_item_form = DeleteItem()
    items = character.inventory_items.all()
    items_names = []
    for item in items:
            if item.item:
                items_names.append((item.item.code, item.item.name))
    delete_item_form.del_item.choices = sorted(items_names)
    if delete_item_form.validate_on_submit():
        item_code = delete_item_form.del_item.data
        quantity = delete_item_form.del_quantity.data
        payload = {'code': item_code, 'quantity': quantity}
        response = char_action_request(char_name, 'delete', payload)
        if response.status_code != 200:
            flash(response.json()['error']['message'])
            return redirect(url_for('char.get_char', char_name=char_name))
        response = response.json()['data']
        Character.update_character(response['character'])
        item = Item.query.filter_by(code=item_code).first()
        flash(f'{character.name} deleted {quantity} {item.name}')
        response['item']['delete_item'] = True
        session['action_details'] = response['item']
        return redirect(url_for('char.delete_item', char_name=char_name))
        
    cooldown = 0
    if character:
        cooldown = int(get_cooldown(character.cooldown_expiration))
    if cooldown < 0:
        cooldown = 0
    if session.get('action_details'):
        action_details = session.pop('action_details')
    else:
        action_details = {}
    return render_template('char/delete_item.html', character=character,
                           Item=Item,
                           cooldown=cooldown,
                           delete_item_form=delete_item_form,
                           action_details=action_details,
                           names=current_app.config['NAMES'])


@char.route('/<char_name>/transition')
def transition(char_name):
    response = char_action_request(char_name, 'transition')
    if response.status_code != 200:
            flash(response.json()['error']['message'])
            return redirect(url_for('char.get_char', char_name=char_name))
    response = response.json()['data']
    Character.update_character(response['character'])
    flash(f'{char_name} made a transition to different layer.')
    return redirect(url_for('char.get_char', char_name=char_name))


@char.route('/<char_name>/bank/buy_expansion')
def bank_buy_expansion(char_name):
    from ..char_requests import char_action_request
    response = char_action_request(char_name, '/bank/buy_expansion')
    previous_url = request.referrer
    if response.status_code == 200:
        flash('Bank expansion successfully bought.')
        response = response.json()['data']
        Character.update_character(response['character'])
    else:
        flash(response.json()['error']['message'])
    return redirect(previous_url)


@char.route('/get_action_choices/<action_category>')
def get_action_choices(action_category):
    choices = []
    if action_category == 'gather':
        resources = Resource.query.all()
        for resource in resources:
            choices.append((resource.code, resource.name))
    elif action_category == 'craft':
        items = Item.query.all()
        for item in items:
            if item.craft_skill:
                choices.append((item.code, item.name))
    elif action_category == 'fight':
        monsters = Monster.query.all()
        for monster in monsters:
            choices.append((monster.code, monster.name))
    return jsonify(sorted(choices))


@char.route('/<char_name>/start_bot', methods=['GET', 'POST'])
def start_bot(char_name):
    character = Character.query.filter_by(name=char_name).first()
    start_bot_form = StartBotForm()

    if start_bot_form.validate_on_submit():
        bots = r.lrange('bots', 0, -1)
        bots = [b.decode('utf-8') for b in bots]
        if char_name in bots:
            flash(f'{char_name} bot is already in work.')
            return redirect(url_for('main.index'))
        action = start_bot_form.action.data
        target = start_bot_form.target.data
        slot = start_bot_form.inventory_slot.data
        task = bot.delay(char_name, slot, action, target)
        item, monster, resource = '', '', ''
        if action == 'craft':
            item = target
        elif action == 'fight':
            monster = target
        else:
            resource = target
        task_status = {'task_id': task.id, 'char_status': '',
                       'char_name': char_name, 'stop': 'false',
                       'monster': monster,
                       'item': item,
                       'resource': resource}
        r.rpush('bots', char_name)
        r.hmset(char_name, task_status)
        return redirect(url_for('main.index'))
    
    slot_number = 0
    for item in character.inventory_items:
        if item.item:
            slot_number = item.slot
    start_bot_form.inventory_slot.data = slot_number
    
    cooldown = 0
    if character:
        cooldown = int(get_cooldown(character.cooldown_expiration))
    if cooldown < 0:
        cooldown = 0
    return render_template('char/start_bot.html',
                           character=character,
                           cooldown=cooldown,
                           start_bot_form=start_bot_form,
                           names=current_app.config['NAMES'])


@char.route('/<char_name>/stop_bot')
def stop_bot(char_name):
    r.hset(char_name, 'stop', 'true')
    r.lrem('bots', 0, char_name)
    flash(f'Bot has stopped for {char_name}')
    return redirect(url_for('main.index'))
