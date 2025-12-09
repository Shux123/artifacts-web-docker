from . import db
import json

class Condition(db.Model):
    __tablename__ = 'conditions'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(64))
    operator = db.Column(db.String(64))
    value = db.Column(db.Integer)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'))
    map_id = db.Column(db.Integer, db.ForeignKey('maps.id'))


class Effect(db.Model):
    __tablename__ = 'effects'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    code = db.Column(db.String(64), nullable=False)
    description = db.Column(db.String, nullable=False)
    effect_type = db.Column(db.String(64), nullable=False)
    subtype = db.Column(db.String(64), nullable=False)
    effect_values = db.relationship('EffectValue', backref='effect',
                                   lazy='joined')
    
    @staticmethod
    def get_effect_from_db(effect_code):
        effect = Effect.query.filter_by(code=effect_code).first()
        return effect.id


    def insert_effects():
        from .all_requests import get_data_for_db
        effects = get_data_for_db('/effects')
        for e in effects:
            effect = Effect(
                name = e['name'],
                code = e['code'],
                description = e['description'],
                effect_type = e['type'],
                subtype = e['subtype'],
            )
            db.session.add(effect)
        db.session.commit()


class EffectValue(db.Model):
    __tablename__ = 'effect_values'
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'))
    monster_id = db.Column(db.Integer, db.ForeignKey('monsters.id'))
    effect_id = db.Column(db.Integer, db.ForeignKey('effects.id'))
    character_id = db.Column(db.Integer, db.ForeignKey('characters.id'))
    description = db.Column(db.String)
    value = db.Column(db.Integer)


class Event(db.Model):
    __tablename__ = 'events'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    code = db.Column(db.String(64), nullable=False)
    content_type = db.Column(db.String(64), nullable=False)
    content_code = db.Column(db.String(64), nullable=False)
    map_skin = db.Column(db.String(64), nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    rate = db.Column(db.Integer, nullable=False)
    maps = db.relationship('Map', backref='event', lazy='joined')
    monster_id = db.Column(db.Integer,db.ForeignKey('monsters.id'))
    resource_id = db.Column(db.Integer,db.ForeignKey('resources.id'))
    npc_id = db.Column(db.Integer, db.ForeignKey('npcs.id'))

    @staticmethod
    def get_event_from_db(event_code):
        event = Event.query.filter_by(code=event_code).first()
        return event.id
    
    @staticmethod
    def insert_events():
        from .all_requests import get_data_for_db, download_map_images
        events = get_data_for_db('/events')
        skins = []
        for e in events:
            for m in e['maps']:
                skins.append(m['skin'])
            event = Event.query.filter_by(code=e['code']).first()
            if event is None:
                monster_id = None
                resource_id = None
                npc_id = None
                if e['content']['type'] == 'monster':
                    monster = Monster.query.filter_by(
                        code=e['content']['code']).first()
                    monster_id = monster.id
                elif e['content']['type'] == 'npc':
                    npc = NPC.query.filter_by(
                        code=e['content']['code']).first()
                    npc_id = npc.id
                else:
                    resource = Resource.query.filter_by(
                        code=e['content']['code']).first()
                    resource_id = resource.id
                event = Event(
                    name = e['name'],
                    code = e['code'],
                    content_type = e['content']['type'],
                    content_code = e['content']['code'],
                    map_skin = e['maps'][0]['skin'],
                    duration = e['duration'],
                    rate = e['rate'],
                    monster_id = monster_id,
                    npc_id = npc_id,
                    resource_id = resource_id,
                )
                db.session.add(event)
                for m in e['maps']:
                    map = Map.query.filter_by(map_id=m['map_id']).first()
                    if map is not None:
                        map.event_id = event.id
                        db.session.add(map)
        db.session.commit()
        download_map_images(set(skins))


class Achievement(db.Model):
    __tablename__ = 'achievements'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    code = db.Column(db.String(64), nullable=False)
    description = db.Column(db.String, nullable=False)
    points = db.Column(db.Integer)
    achiev_type = db.Column(db.String)
    target_item_id = db.Column(db.Integer, db.ForeignKey('items.id'))
    target_monster_id = db.Column(db.Integer, db.ForeignKey('monsters.id'))
    total = db.Column(db.Integer)
    current = db.Column(db.Integer)
    gold_reward = db.Column(db.Integer)
    completed_at = db.Column(db.String)
    completed = db.Column(db.Boolean)

    @staticmethod
    def insert_achievements():
        from .all_requests import get_achievements
        achievements = get_achievements()
        for a in achievements['data']:
            monster_id = None
            item_id = None
            if a['completed_at'] is not None:
                completed = True
            else:
                completed = False
            if a['type'] == 'combat_kill':
                monster = Monster.query.filter_by(
                    code=a['target']).first()
                monster_id = monster.id
            elif a['target'] is not None:
                item = Item.query.filter_by(code=a['target']).first()
                item_id = item.id
            achiev = Achievement(
                name = a['name'],
                code = a['code'],
                description = a['description'],
                points = a['points'],
                achiev_type = a['type'],
                target_monster_id = monster_id,
                target_item_id = item_id,
                total = a['total'],
                current = a['current'],
                gold_reward = a['rewards']['gold'],
                completed_at = a['completed_at'],
                completed = completed,
            )
            db.session.add(achiev)
        character = Character.query.get(1)
        character.all_achiev_points = achievements['all_points']
        character.my_achiev_points = achievements['my_points']
        db.session.commit()

    @staticmethod
    def update_achievements(achievements):
        for a in achievements['data']:
            achiev = Achievement.query.filter_by(code=a['code']).first()
            if achiev is not None and achiev.completed:
                continue
            if a['completed_at'] is not None:
                achiev.completed = True
                achiev.completed_at = a['completed_at']
            achiev.current = a['current']
        character = Character.query.get(1)
        character.my_achiev_points = achievements['my_points']
        character.all_achiev_points = achievements['all_points']
        db.session.commit()


drop_resource_links = db.Table('drop_resource_links',
    db.Column('drop_id', db.Integer, db.ForeignKey('drops.id')),
    db.Column('resource_id', db.Integer, db.ForeignKey('resources.id')),
)


class Drop(db.Model):
    __tablename__ = 'drops'
    id = db.Column(db.Integer, primary_key=True)
    monster_id = db.Column(db.Integer, db.ForeignKey('monsters.id'))
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'))
    rate = db.Column(db.Integer)
    min_quantity = db.Column(db.Integer)
    max_quantity = db.Column(db.Integer)
    resources = db.relationship('Resource',
                            secondary=drop_resource_links,
                            backref=db.backref('drops', lazy='dynamic'),
                            lazy='dynamic')

    @staticmethod
    def insert_drops():
        from .all_requests import get_data_for_db
        monsters = get_data_for_db('monsters')
        for monster in monsters:
            for drop in monster['drops']:
                item = Item.query.filter_by(code=drop['code']).first()
                if item:
                    m = Monster.query.filter_by(code=monster['code']).first()
                    if m:
                        d = Drop(
                            monster_id = m.id,
                            item_id = item.id,
                            rate = drop['rate'],
                            min_quantity = drop['min_quantity'],
                            max_quantity = drop['max_quantity'],
                            )
                        db.session.add(d)
        db.session.commit()


class Monster(db.Model):
    __tablename__ = 'monsters'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    code = db.Column(db.String(64), unique=True, nullable=False)
    level = db.Column(db.Integer)
    monster_type = db.Column(db.String)
    hp = db.Column(db.Integer)
    attack_fire = db.Column(db.Integer)
    attack_earth = db.Column(db.Integer)
    attack_water = db.Column(db.Integer)
    attack_air = db.Column(db.Integer)
    res_fire = db.Column(db.Integer)
    res_earth = db.Column(db.Integer)
    res_water = db.Column(db.Integer)
    res_air = db.Column(db.Integer)
    critical_strike = db.Column(db.Integer)
    initiative = db.Column(db.Integer)
    min_gold = db.Column(db.Integer)
    max_gold = db.Column(db.Integer)
    effects = db.relationship('EffectValue',
                           foreign_keys=[EffectValue.monster_id],
                           backref=db.backref('monster', lazy='select'))
    maps = db.relationship('Map', backref='monster', lazy='select')
    drops = db.relationship('Drop',
                            foreign_keys=[Drop.monster_id],
                            backref='monster', lazy='select')
    achievement = db.relationship('Achievement', uselist=False,
                            foreign_keys=[Achievement.target_monster_id],
                            backref='monster', lazy='select')
    event = db.relationship('Event', uselist=False,
                            foreign_keys=[Event.monster_id],
                            backref='monster', lazy='select')
    
    @staticmethod
    def get_monster_from_db(monster_code):
        monster = Monster.query.filter_by(code=monster_code).first()
        return monster

    @staticmethod
    def from_json_to_dict(column):
        return json.loads(column)

    @staticmethod
    def insert_monsters():
        from .all_requests import get_data_for_db
        for m in get_data_for_db('monsters'):
            monster = Monster.query.filter_by(code=m['code']).first()
            if monster is None:
                monster = Monster(
                    name = m['name'],
                    code = m['code'],
                    level = m['level'],
                    monster_type = m['type'],
                    hp = m['hp'],
                    attack_fire = m['attack_fire'],
                    attack_earth = m['attack_earth'],
                    attack_water = m['attack_water'],
                    attack_air = m['attack_air'],
                    res_fire = m['res_fire'],
                    res_earth = m['res_earth'],
                    res_water = m['res_water'],
                    res_air = m['res_air'],
                    critical_strike = m['critical_strike'],
                    initiative = m['initiative'],
                    min_gold = m['min_gold'],
                    max_gold = m['max_gold'],
                    )                
                db.session.add(monster)
                for e in m['effects']:
                    effect = Effect.query.filter_by(code=e['code']).first()
                    effect_value = EffectValue(
                        monster_id = monster.id,
                        effect_id = effect.id,
                        value = e['value'],
                        description = e['description'],
                    )
                    db.session.add(effect_value)
        db.session.commit()


transition_condition_table = db.Table('transition_condition_table',
    db.Column('transition_id', db.Integer, db.ForeignKey('transitions.id'), primary_key=True),
    db.Column('condition_id', db.Integer, db.ForeignKey('conditions.id'), primary_key=True),
)


class Transition(db.Model):
    __tablename__ = 'transitions'
    id = db.Column(db.Integer, primary_key=True)
    map_from_id = db.Column(db.Integer, db.ForeignKey('maps.id'))
    map_to_id = db.Column(db.Integer, db.ForeignKey('maps.id'))
    layer_to = db.Column(db.String)
    layer_from = db.Column(db.String)
    conditions = db.relationship('Condition',
                            secondary=transition_condition_table,
                            backref=db.backref('transitions', lazy='dynamic'))

    @staticmethod
    def insert_transitions(maps):
        for map in maps:
            if map['interactions']['transition']:
                map_to = Map.query.filter_by(map_id=map['interactions']['transition']['map_id']).first()
                map_from = Map.query.filter_by(map_id=map['map_id']).first()
                transition = Transition(
                    map_to_id = map_to.id,
                    map_from_id = map_from.id,
                    layer_to = map['interactions']['transition']['layer'],
                    layer_from = map['layer'] 
                )
                db.session.add(transition)
                if map['interactions']['transition']['conditions']:                    
                    for c in map['interactions']['transition']['conditions']:
                        condition = Condition.query.filter_by(
                            code=c['code'], operator=c['operator'], value=c['value']).first()
                        if condition is None:
                            condition = Condition(
                                code = c['code'],
                                operator = c['operator'],
                                value = c['value'])
                            db.session.add(condition)
                        transition.conditions.append(condition)
        db.session.commit()

class Map(db.Model):
    __tablename__ = 'maps'
    id = db.Column(db.Integer, primary_key=True)
    map_id = db.Column(db.Integer)
    name = db.Column(db.String(64), nullable=False)
    skin = db.Column(db.String(64), nullable=False)
    x = db.Column(db.Integer, nullable=False)
    y = db.Column(db.Integer, nullable=False)
    layer = db.Column(db.String, nullable=True)
    access_type = db.Column(db.String)
    content_type = db.Column(db.String, nullable=True)
    content_code = db.Column(db.String, nullable=True)
    monster_id = db.Column(db.Integer, db.ForeignKey('monsters.id'))
    image_name = db.Column(db.String)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'))
    npc_id = db.Column(db.Integer, db.ForeignKey('npcs.id'))
    resource_id = db.Column(db.Integer, db.ForeignKey('resources.id'))
    characters = db.relationship('Character',
                            backref=db.backref('map', lazy='select'),
                            lazy='select')
    conditions = db.relationship('Condition', backref='map', lazy='select')
    transition_to = db.relationship('Transition', uselist=False,
                           foreign_keys=[Transition.map_from_id],
                           backref=db.backref('map_from', lazy='select'))
    transition_from = db.relationship('Transition', uselist=False,
                           foreign_keys=[Transition.map_to_id],
                           backref=db.backref('map_to', lazy='select'))

    @staticmethod
    def insert_maps():
        from .all_requests import get_data_for_db, download_map_images
        skins = []
        maps = get_data_for_db('maps')
        for m in maps:
            skins.append(m['skin'])
            map = Map.query.filter_by(map_id=m['map_id']).first()
            if map is None:
                monster_id = None
                npc_id = None
                resource_id = None     
                content_type = None
                content_code = None
                if m['interactions']['content'] is not None:
                    content_type = m['interactions']['content']['type']
                    content_code = m['interactions']['content']['code']
                    if content_type == 'monster':
                        monster = Monster.query.filter_by(
                            code=content_code).first()
                        monster_id = monster.id
                    elif content_type == 'npc':
                        npc = NPC.query.filter_by(
                            code=content_code).first()
                        npc_id = npc.id
                    elif content_type == 'resource':
                        resource = Resource.query.filter_by(
                            code=content_code).first()
                        resource_id = resource.id
                map = Map(
                    map_id = m['map_id'],
                    name = m['name'],
                    skin = m['skin'],
                    x = m['x'],
                    y = m['y'],
                    layer = m['layer'],
                    access_type = m['access']['type'],
                    content_type = content_type,
                    content_code = content_code,
                    monster_id = monster_id,
                    resource_id = resource_id,
                    npc_id = npc_id,
                    image_name = f'images/maps/{m['skin']}.png',
                    )
                db.session.add(map)
                for c in m['access']['conditions']:
                    condition = Condition.query.filter_by(
                        code=c['code'], operator=c['operator'], value=c['value']).first()
                    if condition is None:
                        condition = Condition(
                            code = c['code'],
                            operator = c['operator'],
                            value = c['value'])
                        db.session.add(condition)
                    condition.map_id = map.id
        db.session.commit()
        download_map_images(set(skins))
        Transition.insert_transitions(maps)

    @staticmethod
    def update_map(m):
        map = Map.query.filter_by(map_id=m['map_id']).first()
        monster_id = None
        npc_id = None
        resource_id = None     
        content_type = None
        content_code = None
        if m['interactions']['content'] is not None:
            content_type = m['interactions']['content']['type']
            content_code = m['interactions']['content']['code']
            if content_type == 'monster':
                monster = Monster.query.filter_by(code=content_code).first()
                monster_id = monster.id
            elif content_type == 'npc':
                npc = NPC.query.filter_by(code=content_code).first()
                npc_id = npc.id
            elif content_type == 'resource':
                resource = Resource.query.filter_by(code=content_code).first()
                resource_id = resource.id
        map.name = m['name']
        map.skin = m['skin']
        map.access_type = m['access']['type']
        map.content_type = content_type
        map.content_code = content_code
        map.monster_id = monster_id
        map.resource_id = resource_id
        map.npc_id = npc_id
        map.image_name = f'images/maps/{m['skin']}.png'
        for c in m['access']['conditions']:
            condition = Condition.query.filter_by(
                code=c['code'], operator=c['operator'], value=c['value']).first()
            if condition is None:
                condition = Condition(
                    code = c['code'],
                    operator = c['operator'],
                    value = c['value'])
            db.session.add(condition)
        db.session.commit()


class Craft(db.Model):
    __tablename__ = 'crafts'
    craft_item_id = db.Column(db.Integer, db.ForeignKey('items.id'), primary_key=True)
    crafted_item_id = db.Column(db.Integer, db.ForeignKey('items.id'), primary_key=True)
    quantity = db.Column(db.Integer, nullable=True)

    @staticmethod
    def insert_crafts(items):
        for item in items:
            if item['craft'] is not None:
                crafted_item = Item.query.filter_by(code=item['code']).first()
                if crafted_item:
                    for ingridient in item['craft']['items']:
                        craft_item = Item.query.filter_by(
                            code=ingridient['code']).first()
                        if craft_item:
                            exists = Craft.query.filter_by(
                                craft_item_id=craft_item.id,
                                crafted_item_id=crafted_item.id).first()
                            if not exists:
                                c = Craft(craft_item_id=craft_item.id,
                                    crafted_item_id=crafted_item.id,
                                    quantity=ingridient['quantity'])
                                db.session.add(c)
        db.session.commit()          


class BankItem(db.Model):
    __tablename__ = 'bank_items'
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'))
    quantity = db.Column(db.Integer)

    @staticmethod
    def insert_bank_items():
        from .all_requests import get_data_for_db
        bank_items = get_data_for_db('/my/bank/items')
        db.session.query(BankItem).delete()
        for i in bank_items:
            item = Item.query.filter_by(code=i['code']).first()
            bank_item = BankItem(item_id = item.id, quantity = i['quantity'])
            db.session.add(bank_item)
        db.session.commit()

    @staticmethod
    def update_bank(action, items):
        for item_code, quantity in items:
            item = Item.query.filter_by(code=item_code).first()
            bank_item = BankItem.query.filter_by(item_id=item.id).first()
            if action == 'deposit':
                if bank_item is None:
                    bank_item = BankItem(item_id=item.id, quantity=0)
                    db.session.add(bank_item)
                bank_item.quantity += quantity
            else:
                bank_item.quantity -= quantity
        db.session.commit()


class NPC_Item(db.Model):
    __tablename__ = 'npc_items'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(64), nullable=False)
    buy_price = db.Column(db.Integer)
    sell_price = db.Column(db.Integer)
    gold = db.Column(db.Boolean)
    currency_id = db.Column(db.Integer, db.ForeignKey('items.id'))
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'))
    npc_id = db.Column(db.Integer, db.ForeignKey('npcs.id')) 

    def insert_npc_items():
        from .all_requests import get_data_for_db
        npc_items = get_data_for_db('npcs/items')
        for n_i in npc_items:
            npc_item = NPC_Item.query.filter_by(code=n_i['code']).first()
            if npc_item is None:
                item = Item.query.filter_by(code=n_i['code']).first()
                npc = NPC.query.filter_by(code=n_i['npc']).first()
                gold = False
                currency_id = None
                if n_i['currency'] == 'gold':
                    gold = True
                else:
                    currency = Item.query.filter_by(
                                                code=n_i['currency']).first()
                    currency_id = currency.id
                npc_item = NPC_Item(
                    code = n_i['code'],                    
                    buy_price = n_i['buy_price'],
                    sell_price = n_i['sell_price'],
                    currency_id = currency_id,
                    gold = gold,
                    item_id = item.id,
                    npc_id = npc.id,
                )
                db.session.add(npc_item)
        db.session.commit()


class Equipment(db.Model):
    __tablename__ = 'equipments'
    character_id = db.Column(db.Integer, db.ForeignKey('characters.id'), primary_key=True)
    weapon_slot = db.Column(db.Integer, db.ForeignKey('items.id'))
    rune_slot = db.Column(db.Integer, db.ForeignKey('items.id'))
    shield_slot = db.Column(db.Integer, db.ForeignKey('items.id'))
    helmet_slot = db.Column(db.Integer, db.ForeignKey('items.id'))
    body_armor_slot = db.Column(db.Integer, db.ForeignKey('items.id'))
    leg_armor_slot = db.Column(db.Integer, db.ForeignKey('items.id'))
    boots_slot = db.Column(db.Integer, db.ForeignKey('items.id'))
    ring1_slot = db.Column(db.Integer, db.ForeignKey('items.id'))
    ring2_slot = db.Column(db.Integer, db.ForeignKey('items.id'))
    amulet_slot = db.Column(db.Integer, db.ForeignKey('items.id'))
    artifact1_slot = db.Column(db.Integer, db.ForeignKey('items.id'))
    artifact2_slot = db.Column(db.Integer, db.ForeignKey('items.id'))
    artifact3_slot = db.Column(db.Integer, db.ForeignKey('items.id'))
    utility1_slot = db.Column(db.Integer, db.ForeignKey('items.id'))
    utility1_slot_quantity = db.Column(db.Integer)
    utility2_slot = db.Column(db.Integer, db.ForeignKey('items.id'))
    utility2_slot_quantity = db.Column(db.Integer)
    bag_slot = db.Column(db.Integer, db.ForeignKey('items.id'))


class Inventory(db.Model):
    __tablename__ = 'Inventory'
    id = db.Column(db.Integer, primary_key=True)
    slot = db.Column(db.Integer)
    character_id = db.Column(db.Integer, db.ForeignKey('characters.id'))
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'))
    quantity = db.Column(db.Integer)


class Character(db.Model):
    __tablename__ = 'characters'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    account = db.Column(db.String(64))
    skin = db.Column(db.String(64))
    level = db.Column(db.Integer)
    xp = db.Column(db.Integer)
    max_xp = db.Column(db.Integer)
    gold = db.Column(db.Integer)
    speed = db.Column(db.Integer)
    mining_level = db.Column(db.Integer)
    mining_xp = db.Column(db.Integer)
    mining_max_xp = db.Column(db.Integer)
    woodcutting_level = db.Column(db.Integer)
    woodcutting_xp = db.Column(db.Integer)
    woodcutting_max_xp = db.Column(db.Integer)
    fishing_level = db.Column(db.Integer)
    fishing_xp = db.Column(db.Integer)
    fishing_max_xp = db.Column(db.Integer)
    weaponcrafting_level = db.Column(db.Integer)
    weaponcrafting_xp = db.Column(db.Integer)
    weaponcrafting_max_xp = db.Column(db.Integer)
    gearcrafting_level = db.Column(db.Integer)
    gearcrafting_xp = db.Column(db.Integer)
    gearcrafting_max_xp = db.Column(db.Integer)
    jewelrycrafting_level = db.Column(db.Integer)
    jewelrycrafting_xp = db.Column(db.Integer)
    jewelrycrafting_max_xp = db.Column(db.Integer)
    cooking_level = db.Column(db.Integer)
    cooking_xp = db.Column(db.Integer)
    cooking_max_xp = db.Column(db.Integer)
    alchemy_level = db.Column(db.Integer)
    alchemy_xp = db.Column(db.Integer)
    alchemy_max_xp = db.Column(db.Integer)
    hp = db.Column(db.Integer)
    max_hp = db.Column(db.Integer)
    haste = db.Column(db.Integer)
    critical_strike = db.Column(db.Integer)
    wisdom = db.Column(db.Integer)
    prospecting = db.Column(db.Integer)
    initiative = db.Column(db.Integer)
    threat = db.Column(db.Integer)
    attack_fire = db.Column(db.Integer)
    attack_earth = db.Column(db.Integer)
    attack_water = db.Column(db.Integer)
    attack_air = db.Column(db.Integer)
    dmg = db.Column(db.Integer)
    dmg_fire = db.Column(db.Integer)
    dmg_earth = db.Column(db.Integer)
    dmg_water = db.Column(db.Integer)
    dmg_air = db.Column(db.Integer)
    res_fire = db.Column(db.Integer)
    res_earth = db.Column(db.Integer)
    res_water = db.Column(db.Integer)
    res_air = db.Column(db.Integer)
    x = db.Column(db.Integer)
    y = db.Column(db.Integer)
    layer = db.Column(db.String)
    char_map_id = db.Column(db.Integer)
    cooldown = db.Column(db.Integer)
    cooldown_expiration = db.Column(db.String)
    task = db.Column(db.String)
    task_type = db.Column(db.String)
    task_progress = db.Column(db.Integer)
    task_total = db.Column(db.Integer)
    inventory_max_items = db.Column(db.Integer)
    all_achiev_points = db.Column(db.Integer)
    my_achiev_points = db.Column(db.Integer)
    map_id = db.Column(db.Integer, db.ForeignKey('maps.id'))
    total_ge_orders = db.Column(db.Integer)
    inventory_items = db.relationship('Inventory',
                            foreign_keys=[Inventory.character_id],
                            backref=db.backref('character', lazy='joined'),
                            lazy='dynamic', cascade='all, delete-orphan',
                            order_by='Inventory.slot')
    equipment = db.relationship('Equipment', uselist=False,
                            foreign_keys=[Equipment.character_id],
                            backref=db.backref('character', lazy='joined'),
                            cascade='all, delete-orphan')
    effects = db.relationship('EffectValue',
                            foreign_keys=[EffectValue.character_id],
                            backref=db.backref('character', lazy='select'),
                            cascade='all, delete-orphan')
    
    
    @staticmethod
    def get_character_by_name(char_name):
        character = Character.query.filter_by(name=char_name).first()
        return character        
    
    @staticmethod
    def update_character(c):
        character = Character.query.filter_by(name=c['name']).first()
        SIMPLE_ATTRIBUTES = ['level', 'xp', 'max_xp', 'gold', 'speed',
                            'mining_level', 'mining_xp', 'mining_max_xp',
                            'woodcutting_level', 'woodcutting_xp',
                            'woodcutting_max_xp', 'fishing_level', 'fishing_xp',
                            'fishing_max_xp', 'weaponcrafting_level',
                            'weaponcrafting_xp', 'weaponcrafting_max_xp',
                            'gearcrafting_level', 'gearcrafting_xp',
                            'gearcrafting_max_xp', 'jewelrycrafting_level',
                            'jewelrycrafting_xp', 'jewelrycrafting_max_xp',
                            'cooking_level', 'cooking_xp', 'cooking_max_xp',
                            'alchemy_level', 'alchemy_xp', 'alchemy_max_xp',
                            'hp', 'max_hp', 'haste', 'critical_strike',
                            'wisdom', 'prospecting', 'initiative',
                            'threat', 'attack_fire', 'attack_earth',
                            'attack_water', 'attack_air', 'dmg', 'dmg_fire',
                            'dmg_earth', 'dmg_water', 'dmg_air', 'res_fire',
                            'res_earth', 'res_water', 'res_air',
                            'x', 'y', 'layer', 'cooldown',
                            'cooldown_expiration', 'task', 'task_type',
                            'task_progress', 'task_total',
                            'inventory_max_items']  

        if character is None:
            character = Character(
                name=c['name'],
                account = c['account'],
                skin = c['skin'],
                **{attr: c.get(attr) for attr in SIMPLE_ATTRIBUTES if attr in c}
                )
            db.session.add(character)
            equipment = Equipment(character_id=character.id)
            character.equipment = equipment
            for inv_item in c['inventory']:
                item = Item.query.filter_by(code=inv_item['code']).first()
                inventory = Inventory(
                                    slot=inv_item['slot'],
                                    character_id=character.id,
                                    item_id=item.id if item else None,
                                    quantity=inv_item['quantity'])
                db.session.add(inventory)
        
        else:
            for attr in SIMPLE_ATTRIBUTES:
                if attr in c and getattr(character, attr) != c[attr]:
                    setattr(character, attr, c[attr])

        if character.char_map_id != c['map_id']:
            character.char_map_id = c['map_id']
            char_map = Map.query.filter_by(map_id=c['map_id']).first()
            character.map = char_map

        if character.equipment.weapon_slot is not None:
            if c['weapon_slot'] != character.equipment.weapon.code:
                weapon = Item.query.filter_by(code=c['weapon_slot']).first()
                character.equipment.weapon = weapon
        elif character.equipment.weapon_slot is None and c['weapon_slot'] != '':
            weapon = Item.query.filter_by(code=c['weapon_slot']).first()
            character.equipment.weapon = weapon
        if character.equipment.rune_slot is not None:
            if c['rune_slot'] != character.equipment.rune.code:
                rune = Item.query.filter_by(code=c['rune_slot']).first()
                character.equipment.rune = rune
        elif character.equipment.rune_slot is None and c['rune_slot'] != '':
            rune = Item.query.filter_by(code=c['rune_slot']).first()
            character.equipment.rune = rune
        if character.equipment.shield_slot is not None:
            if c['shield_slot'] != character.equipment.shield.code:
                shield = Item.query.filter_by(code=c['shield_slot']).first()
                character.equipment.shield = shield
        elif character.equipment.shield_slot is None and c['shield_slot'] != '':
            shield = Item.query.filter_by(code=c['shield_slot']).first()
            character.equipment.shield = shield
        if character.equipment.helmet_slot is not None:
            if c['helmet_slot'] != character.equipment.helmet.code:
                helmet = Item.query.filter_by(code=c['helmet_slot']).first()
                character.equipment.helmet = helmet
        elif character.equipment.helmet_slot is None and c['helmet_slot'] != '':
            helmet = Item.query.filter_by(code=c['helmet_slot']).first()
            character.equipment.helmet = helmet
        if character.equipment.body_armor_slot is not None:
            if c['body_armor_slot'] != character.equipment.body_armor.code:
                body_armor = Item.query.filter_by(code=c['body_armor_slot']).first()
                character.equipment.body_armor = body_armor
        elif character.equipment.body_armor_slot is None and c['body_armor_slot'] != '':
            body_armor = Item.query.filter_by(code=c['body_armor_slot']).first()
            character.equipment.body_armor = body_armor
        if character.equipment.leg_armor_slot is not None:
            if c['leg_armor_slot'] != character.equipment.leg_armor.code:
                leg_armor = Item.query.filter_by(code=c['leg_armor_slot']).first()
                character.equipment.leg_armor = leg_armor
        elif character.equipment.leg_armor_slot is None and c['leg_armor_slot'] != '':
            leg_armor = Item.query.filter_by(code=c['leg_armor_slot']).first()
            character.equipment.leg_armor = leg_armor
        if character.equipment.boots_slot is not None:
            if c['boots_slot'] != character.equipment.boots.code:
                boots = Item.query.filter_by(code=c['boots_slot']).first()
                character.equipment.boots = boots
        elif character.equipment.boots_slot is None and c['boots_slot'] != '':
            boots = Item.query.filter_by(code=c['boots_slot']).first()
            character.equipment.boots = boots
        if character.equipment.ring1_slot is not None:
            if c['ring1_slot'] != character.equipment.ring1.code:
                ring1 = Item.query.filter_by(code=c['ring1_slot']).first()
                character.equipment.ring1 = ring1
        elif character.equipment.ring1_slot is None and c['ring1_slot'] != '':
            ring1 = Item.query.filter_by(code=c['ring1_slot']).first()
            character.equipment.ring1 = ring1
        if character.equipment.ring2_slot is not None:
            if c['ring2_slot'] != character.equipment.ring2.code:
                ring2 = Item.query.filter_by(code=c['ring2_slot']).first()
                character.equipment.ring2 = ring2
        elif character.equipment.ring2_slot is None and c['ring2_slot'] != '':
            ring2 = Item.query.filter_by(code=c['ring2_slot']).first()
            character.equipment.ring2 = ring2
        if character.equipment.amulet_slot is not None:
            if c['amulet_slot'] != character.equipment.amulet.code:
                amulet = Item.query.filter_by(code=c['amulet_slot']).first()
                character.equipment.amulet = amulet
        elif character.equipment.amulet_slot is None and c['amulet_slot'] != '':
            amulet = Item.query.filter_by(code=c['amulet_slot']).first()
            character.equipment.amulet = amulet
        if character.equipment.artifact1_slot is not None:
            if c['artifact1_slot'] != character.equipment.artifact1.code:
                artifact1 = Item.query.filter_by(code=c['artifact1_slot']).first()
                character.equipment.artifact1 = artifact1
        elif character.equipment.artifact1_slot is None and c['artifact1_slot'] != '':
            artifact1 = Item.query.filter_by(code=c['artifact1_slot']).first()
            character.equipment.artifact1 = artifact1
        if character.equipment.artifact2_slot is not None:
            if c['artifact2_slot'] != character.equipment.artifact2.code:
                artifact2 = Item.query.filter_by(code=c['artifact2_slot']).first()
                character.equipment.artifact2 = artifact2
        elif character.equipment.artifact2_slot is None and c['artifact2_slot'] != '':
            artifact2 = Item.query.filter_by(code=c['artifact2_slot']).first()
            character.equipment.artifact2 = artifact2
        if character.equipment.artifact3_slot is not None:
            if c['artifact3_slot'] != character.equipment.artifact3.code:
                artifact3 = Item.query.filter_by(code=c['artifact3_slot']).first()
                character.equipment.artifact3 = artifact3
        elif character.equipment.artifact3_slot is None and c['artifact3_slot'] != '':
            artifact3 = Item.query.filter_by(code=c['artifact3_slot']).first()
            character.equipment.artifact3 = artifact3
        if character.equipment.utility1_slot is not None:
            if c['utility1_slot'] != character.equipment.utility1.code:
                utility1 = Item.query.filter_by(code=c['utility1_slot']).first()
                character.equipment.utility1 = utility1
        elif character.equipment.utility1_slot is None and c['utility1_slot'] != '':
            utility1 = Item.query.filter_by(code=c['utility1_slot']).first()
            character.equipment.utility1 = utility1
        if character.equipment.utility2_slot is not None:
            if c['utility2_slot'] != character.equipment.utility2.code:
                utility2 = Item.query.filter_by(code=c['utility2_slot']).first()
                character.equipment.utility2 = utility2
        elif character.equipment.utility2_slot is None and c['utility2_slot'] != '':
            utility2 = Item.query.filter_by(code=c['utility2_slot']).first()
            character.equipment.utility2 = utility2
        if character.equipment.bag_slot is not None:
            if c['bag_slot'] != character.equipment.bag.code:
                bag = Item.query.filter_by(code=c['bag_slot']).first()
                character.equipment.bag = bag
        elif character.equipment.bag_slot is None and c['bag_slot'] != '':
            bag = Item.query.filter_by(code=c['bag_slot']).first()
            character.equipment.bag = bag

        if character.equipment.utility1_slot_quantity != c['utility1_slot_quantity']:
            character.equipment.utility1_slot_quantity = c['utility1_slot_quantity']
        if character.equipment.utility2_slot_quantity != c['utility2_slot_quantity']:
            character.equipment.utility2_slot_quantity = c['utility2_slot_quantity']
        
        for inv_slot_model, inv_item_data in zip(character.inventory_items, c['inventory']):
            incoming_code = inv_item_data['code']
            incoming_quantity = inv_item_data['quantity']
            current_code = inv_slot_model.item.code if inv_slot_model.item else ''

            if current_code != incoming_code:
                if incoming_code:
                    item = Item.query.filter_by(code=incoming_code).first()
                else:
                    item = None
                inv_slot_model.item = item
            if inv_slot_model.quantity != incoming_quantity:
                inv_slot_model.quantity = incoming_quantity

        effect_codes = [e['code'] for e in c['effects']]
        my_effects = []
        if character.effects:
            for e in character.effects:
                if e.effect.code not in effect_codes:
                    db.session.delete(e)
                else:
                    my_effects.append(e.effect.code)
        if c['effects'] != []:
            for e in c['effects']:
                if e['code'] not in my_effects:
                    effect = Effect.query.filter_by(code=e['code']).first()
                    effect_value = EffectValue(
                            effect_id = effect.id,
                            character_id = character.id,
                            value = e['value'],
                            )
                    db.session.add(effect_value)

        db.session.commit()

    @staticmethod
    def insert_characters():
        db.session.query(Character).delete()
        db.session.query(Equipment).delete()
        db.session.query(Inventory).delete()
        from app.all_requests import get_data_for_db
        characters = get_data_for_db('/my/characters')
        for c in characters:
            Character.update_character(c)


class Item(db.Model):
    __tablename__ = 'items'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    code = db.Column(db.String(64), nullable=False)
    level = db.Column(db.Integer)
    item_type = db.Column(db.String(64))
    subtype = db.Column(db.String(64))
    description = db.Column(db.String)
    craft_skill = db.Column(db.String, nullable=True)
    craft_level = db.Column(db.Integer, nullable=True)
    craft_quantity = db.Column(db.Integer, nullable=True)
    tradeable = db.Column(db.Boolean)
    can_equip = db.Column(db.Boolean)
    can_equip_musliple_slot = db.Column(db.Boolean)
    can_recycle = db.Column(db.Boolean)
    conditions = db.relationship('Condition', backref='item', lazy='select')
    effects = db.relationship('EffectValue',
                           foreign_keys=[EffectValue.item_id],
                           backref=db.backref('item', lazy='select'))
    craft_items = db.relationship('Craft',
                                foreign_keys=[Craft.crafted_item_id],
                                backref=db.backref('crafted_item', lazy='select'))
    crafted_items = db.relationship('Craft',
                                foreign_keys=[Craft.craft_item_id],
                                backref=db.backref('craft_item', lazy='select'))
    drops = db.relationship('Drop',
                           foreign_keys=[Drop.item_id],
                           backref=db.backref('item', lazy='select'))
    npc_item = db.relationship('NPC_Item', uselist=False,
                           foreign_keys=[NPC_Item.item_id],
                           backref=db.backref('item', lazy='select'))
    achievement = db.relationship('Achievement', uselist=False,
                            foreign_keys=[Achievement.target_item_id],
                            backref=db.backref('item', lazy='select'))
    currencies = db.relationship('NPC_Item',
                            foreign_keys=[NPC_Item.currency_id],
                            backref=db.backref('currency', lazy='select'))
    item_in_bank = db.relationship('BankItem',
                            foreign_keys=[BankItem.item_id],
                            backref=db.backref('item', lazy='select'))
    inventory = db.relationship('Inventory',
                            foreign_keys=[Inventory.item_id],
                            backref=db.backref('item', lazy='select'))
    weapon_slots = db.relationship('Equipment',
                            foreign_keys=[Equipment.weapon_slot],
                            backref=db.backref('weapon', lazy='select'))
    rune_slots = db.relationship('Equipment',
                            foreign_keys=[Equipment.rune_slot],
                            backref=db.backref('rune', lazy='select'))
    shield_slots = db.relationship('Equipment',
                            foreign_keys=[Equipment.shield_slot],
                            backref=db.backref('shield', lazy='select'))
    helmet_slots = db.relationship('Equipment',
                            foreign_keys=[Equipment.helmet_slot],
                            backref=db.backref('helmet', lazy='select'))
    body_armor_slots = db.relationship('Equipment',
                            foreign_keys=[Equipment.body_armor_slot],
                            backref=db.backref('body_armor', lazy='select'))
    leg_armor_slots = db.relationship('Equipment',
                            foreign_keys=[Equipment.leg_armor_slot],
                            backref=db.backref('leg_armor', lazy='select'))
    boots_slots = db.relationship('Equipment',
                            foreign_keys=[Equipment.boots_slot],
                            backref=db.backref('boots', lazy='select'))
    ring1_slots = db.relationship('Equipment',
                            foreign_keys=[Equipment.ring1_slot],
                            backref=db.backref('ring1', lazy='select'))
    ring2_slots = db.relationship('Equipment',
                            foreign_keys=[Equipment.ring2_slot],
                            backref=db.backref('ring2', lazy='select'))
    amulet_slots = db.relationship('Equipment',
                            foreign_keys=[Equipment.amulet_slot],
                            backref=db.backref('amulet', lazy='select'))
    artifact1_slots = db.relationship('Equipment',
                            foreign_keys=[Equipment.artifact1_slot],
                            backref=db.backref('artifact1', lazy='select'))
    artifact2_slots = db.relationship('Equipment',
                            foreign_keys=[Equipment.artifact2_slot],
                            backref=db.backref('artifact2', lazy='select'))
    artifact3_slots = db.relationship('Equipment',
                            foreign_keys=[Equipment.artifact3_slot],
                            backref=db.backref('artifact3', lazy='select'))
    utility1_slots = db.relationship('Equipment',
                            foreign_keys=[Equipment.utility1_slot],
                            backref=db.backref('utility1', lazy='select'))
    utility2_slots = db.relationship('Equipment',
                            foreign_keys=[Equipment.utility2_slot],
                            backref=db.backref('utility2', lazy='select'))
    bag_slots = db.relationship('Equipment',
                            foreign_keys=[Equipment.bag_slot],
                            backref=db.backref('bag', lazy='select'))


    @staticmethod
    def from_json_to_dict(column):
        return json.loads(column)
    
    @staticmethod
    def get_item_from_db(item_code):
        item = Item.query.filter_by(code=item_code).first()
        return item

    @staticmethod
    def insert_items():
        from .all_requests import get_data_for_db
        items = get_data_for_db('items')
        for i in items:
            item = Item.query.filter_by(code=i['code']).first()
            if item is None:
                if i['craft'] is not None:
                    craft_skill = i['craft']['skill']
                    craft_level = i['craft']['level']
                    craft_quantity = i['craft']['quantity']
                else:
                    craft_skill = None
                    craft_level = None
                    craft_quantity = None
                if i['type'] in ['weapon', 'amulet', 'rune', 'shield', 'helmet',
                                'body_armor', 'leg_armor', 'boots','bag']:
                    can_equip = True
                else:
                    can_equip = False
                if i['type'] in ['utility', 'ring', 'artifact']:
                    can_equip_musliple_slot = True
                else:
                    can_equip_musliple_slot = False
                if i['type'] in ['weapon', 'ring', 'amulet', 'shield', 'helmet',
                                'body_armor', 'leg_armor', 'boots', 'bag']:
                    can_recycle = True
                else:
                    can_recycle = False
                
                item = Item(
                    name = i['name'],
                    code = i['code'],
                    level = i['level'],
                    item_type = i['type'],
                    subtype = i['subtype'],
                    description = i['description'],
                    craft_skill = craft_skill,
                    craft_level = craft_level,
                    craft_quantity = craft_quantity,
                    tradeable = i['tradeable'],
                    can_equip = can_equip,
                    can_equip_musliple_slot = can_equip_musliple_slot,
                    can_recycle = can_recycle,
                    )                
                db.session.add(item)
                for e in i['effects']:
                    effect = Effect.query.filter_by(code=e['code']).first()
                    effect_value = EffectValue(
                        item_id = item.id,
                        effect_id = effect.id,
                        value = e['value'],
                        description = e['description'],
                    )
                    db.session.add(effect_value)
                for c in i['conditions']:
                    condition = Condition.query.filter_by(
                        code=c['code'], operator=c['operator'], value=c['value']).first()
                    if condition is None:
                        condition = Condition(
                            code = c['code'],
                            operator = c['operator'],
                            value = c['value'])
                        db.session.add(condition)
                    condition.item_id = item.id
        db.session.commit()
        Craft.insert_crafts(items)

                
class Resource(db.Model):
    __tablename__ = 'resources'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    code = db.Column(db.String(64), nullable=False)
    skill = db.Column(db.String(64), nullable=False)
    level = db.Column(db.Integer, nullable=False)
    maps = db.relationship('Map', backref='resource', lazy='joined')
    event = db.relationship('Event', uselist=False,
                            foreign_keys=[Event.resource_id],
                            backref='resource', lazy='joined')
    
    @staticmethod
    def get_resource_from_db(resource_code):
        resource = Resource.query.filter_by(code=resource_code).first()
        return resource
    
    def insert_resources():
        from .all_requests import get_data_for_db
        resources = get_data_for_db('resources')
        for r in resources:
            resource = Resource.query.filter_by(code=r['code']).first()
            if resource is None:
                resource = Resource(
                    name = r['name'],
                    code = r['code'],
                    skill = r['skill'],
                    level = r['level'],
                )
                db.session.add(resource)
            for d in r['drops']:
                item = Item.query.filter_by(code=d['code']).first()
                drop = Drop.query.filter_by(item_id=item.id).first()
                if drop is None:
                    drop = Drop(
                        item_id = item.id,
                        rate = d['rate'],
                        min_quantity = d['min_quantity'],
                        max_quantity = d['max_quantity'],
                    )
                    db.session.add(drop)
                drop.resources.append(resource)
        db.session.commit()


class NPC(db.Model):
    __tablename__ = 'npcs'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    code = db.Column(db.String(64), nullable=False)
    description = db.Column(db.String, nullable=False)
    npc_type = db.Column(db.String(64), nullable=False)
    npc_items = db.relationship('NPC_Item', backref='npc', lazy='joined')
    maps = db.relationship('Map', backref='npc', lazy='joined')
    event = db.relationship('Event', uselist=False,
                            foreign_keys=[Event.npc_id],
                            backref='npc', lazy='joined')
    
    @staticmethod
    def get_npc_from_db(npc_code):
        npc = NPC.query.filter_by(code=npc_code).first()
        return npc.id

    def insert_npc():
        from .all_requests import get_data_for_db
        npcs = get_data_for_db('npcs/details')
        for n in npcs:
            npc = NPC.query.filter_by(code=n['code']).first()
            if npc is None:
                npc = NPC(
                    name = n['name'],
                    code = n['code'],
                    description = n['description'],
                    npc_type = n['type'],
                )
                db.session.add(npc)
        db.session.commit()
