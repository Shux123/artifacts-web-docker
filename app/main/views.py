from flask import render_template, current_app, redirect, url_for, flash, request
from ..all_requests import (get_achievements,
                            get_active_events,
                            get_data_for_db,
                            create_character_request,
                            delete_character_request,
                            get_one_map,
                            get_local_time,
                            )
from . import main
from ..models import (Monster, Item, Map, Achievement, Resource, NPC, Event,
                        BankItem, Character, Effect, Condition)
from .forms import (ItemFilter,
                    LevelsFilter,
                    ResourceFilter,
                    AchievementFilter,
                    GetToken,
                    CreateCharacter,
                    DeleteCharacter,
                    UpdateMap,           
                    )
from sqlalchemy import and_
from .. import db, r
import os


@main.route('/')
def index():
    if not os.environ.get('ARTIFACTS_TOKEN'):
        return redirect(url_for('main.get_token'))
    names_query = db.session.query(Character.name).order_by(Character.id)
    names = db.session.scalars(names_query).all()
    current_app.config['NAMES'] = names

    data = []
    char_names = r.lrange('bots', 0, -1)
    char_names = [n.decode() for n in char_names]
    for char_name in char_names:
        char_data = r.hgetall(char_name)
        char_data = {k.decode('utf-8'): v.decode(
            'utf-8') for k, v in char_data.items()}
        data.append(char_data)

    return render_template('index.html', data=data,
                           Item=Item,
                           Monster=Monster,
                           Resource=Resource,
                           names=current_app.config['NAMES'])
 

@main.route('/monsters', methods=['GET', 'POST'])
def monsters():
    form = LevelsFilter()

    if form.validate_on_submit():
        levels = form.levels.data

        if levels == 'all':
            return redirect(url_for('main.monsters'))
        levels = int(levels)
        monsters = Monster.query.filter(and_(
                Monster.level < levels, Monster.level >= levels - 10)).all()
        return render_template('monsters.html', monsters=monsters, form=form,
                           names=current_app.config['NAMES'])
    monsters = Monster.query.all()
    return render_template('monsters.html', monsters=monsters, form=form,
                           names=current_app.config['NAMES'])


@main.route('/monsters/<int:id>')
def monster(id):
    monster = Monster.query.get_or_404(id)
    return render_template('monster.html', monster=monster,
                           names=current_app.config['NAMES'])


@main.route('/items', methods=['GET', 'POST'])
def items():
    form = ItemFilter()

    if form.validate_on_submit():
        query = Item.query
        levels = form.levels.data
        skill = form.skill.data
        category = form.category.data

        if levels != 'all':
            levels = int(levels)
            query = query.filter(and_(
                            Item.level < levels, Item.level >= levels - 10))
        if skill != 'all':
            query = query.filter(Item.craft_skill == skill)
        if category != 'all':
            query = query.filter(Item.item_type == category)
        items = query.all()
        return render_template('items.html', items=items, form=form,
                           names=current_app.config['NAMES'])
    items = Item.query.all()
    return render_template('items.html', items=items, form=form,
                           names=current_app.config['NAMES'])


@main.route('/items/<int:id>')
def item(id):
    item = Item.query.get_or_404(id)
    return render_template('item.html', item=item,
                           names=current_app.config['NAMES'])


@main.errorhandler(404)
def page_not_found(e):
    return render_template('404.html', message=e.description), 404


@main.route('/achievement/<int:id>')
def achievement(id):
    achievement = Achievement.query.get_or_404(id)
    return render_template('achievement.html', achievement=achievement,
                           names=current_app.config['NAMES'])


@main.route('/achievements', methods=['GET', 'POST'])
def achievements():
    achievements = get_achievements()
    Achievement.update_achievements(achievements)
    character = Character.query.get(1)
    form = AchievementFilter()

    if form.validate_on_submit():
        query = Achievement.query
        achievement_type = form.achievement_type.data
        completed = form.completed.data
        if achievement_type != 'all':
            query = query.filter(Achievement.achiev_type==achievement_type)
        if completed != 'all':
            completed = True if completed == 'yes' else False
            query = query.filter(Achievement.completed==completed)
        achievements = query.all()
        return render_template('achievements.html', achievements=achievements,
                           Monster=Monster, Item=Item, form=form,
                           character=character,
                           names=current_app.config['NAMES'])
    achievements = Achievement.query.all()
    return render_template('achievements.html', achievements=achievements,
                           Monster=Monster, Item=Item, form=form,
                           character=character,
                           names=current_app.config['NAMES'])


@main.route('/events')
def events():
    events = get_active_events()
    active_events = []
    for e in events:
        active_events.append(e['map']['map_id'])
    my_events = r.lrange('my_events', 0, -1)
    my_events = [int(e.decode()) for e in my_events]
    for a_event in active_events:
        if a_event not in my_events:
            my_events.append(a_event)
            response = get_one_map(a_event)
            if response.status_code != 200:
                flash(response.json()['error']['message'])
                return redirect(url_for('main.events'))
            map_data = response.json()['data']
            Map.update_map(map_data)

    for my_event in my_events[:]:
        if my_event not in active_events:
            response = get_one_map(my_event)
            my_events.remove(my_event)
            if response.status_code != 200:
                flash(response.json()['error']['message'])
                return redirect(url_for('main.events'))
            map_data = response.json()['data']
            Map.update_map(map_data)

    r.delete('my_events')
    if my_events:
        r.rpush('my_events', *my_events)

    if not events:
        events = [{'name': 'There are no active events now.'}]
    return render_template('events.html', events=events, Resource=Resource,
                           Monster=Monster, NPC=NPC, Event=Event,
                           names=current_app.config['NAMES'])


@main.route('/event/<int:id>')
def event(id):
    event = Event.query.get_or_404(id)
    return render_template('event.html', event=event,
                           names=current_app.config['NAMES'])


@main.route('/maps/<layer>')
def maps(layer):
    y_min = current_app.config['Y_MIN_MAX']['y_min']
    y_max = current_app.config['Y_MIN_MAX']['y_max']
    y_coords = [y for y in range(y_min, y_max)]
    maps = db.session.query(Map).filter_by(layer=layer).order_by(Map.id).all()
    return render_template('maps.html', maps=maps, y_coords=y_coords,
                           Item=Item,
                           names=current_app.config['NAMES'])

@main.route('/logs', methods=['GET', 'POST'])
def logs():
    logs = get_data_for_db('my/logs')
    for log in logs:
        created_at = get_local_time(log['created_at'])
        log['created_at'] = created_at.strftime('%d-%m-%Y %H:%M')
    return render_template('logs.html',
                           logs=logs,
                           Character=Character,
                           Monster=Monster,
                           Resource=Resource,
                           Item=Item,
                           names=current_app.config['NAMES'])


@main.route('/npcs')
def npcs():
    npcs = NPC.query.all()
    return render_template('npcs.html', npcs=npcs,
                           names=current_app.config['NAMES'])


@main.route('/npc/<int:id>')
def npc(id):
    npc = NPC.query.get_or_404(id)
    return render_template('npc.html', npc=npc,
                           names=current_app.config['NAMES'])


@main.route('/resources', methods=['GET', 'POST'])
def resources():
    form = ResourceFilter()

    if form.validate_on_submit():
        skill = form.skill.data

        if skill == 'all':
            return redirect(url_for('main.resources'))
        resources = Resource.query.filter_by(skill=skill).all()
        return render_template('resources.html', resources=resources, form=form,
                           names=current_app.config['NAMES'])
    resources = Resource.query.all()
    return render_template('resources.html', resources=resources, form=form,
                           names=current_app.config['NAMES'])


@main.route('/resource/<int:id>')
def resource(id):
    resource = Resource.query.get_or_404(id)
    return render_template('resource.html', resource=resource,
                           names=current_app.config['NAMES'])

@main.route('/bank')
def bank():
    bank_ditails = get_data_for_db('my/bank')
    bank_items = db.session.query(BankItem).filter(BankItem.quantity > 0).order_by(BankItem.id).all()
    return render_template('bank.html', bank_ditails=bank_ditails,
                           bank_items=bank_items, Item=Item,
                           names=current_app.config['NAMES'])


@main.route('/get_token', methods=['GET', 'POST'])
def get_token():
    form = GetToken()
    if form.validate_on_submit():
        token = form.token.data
        os.environ['ARTIFACTS_TOKEN'] = token
        return redirect('main.index')

    if os.environ.get('ARTIFACTS_TOKEN'):
        message = 'Token has already inserted.'
        return render_template('get_token.html', message=message,
                               names=current_app.config['NAMES'])
    return render_template('get_token.html', form=form)


@main.route('/create_character', methods=['GET', 'POST'])
def create_character():
    names = current_app.config['NAMES']
    if len(names) == 5:
        flash('Maximum characters number is already reached')
        return redirect(url_for('main.index'))
    form = CreateCharacter()
    if form.validate_on_submit():
        name = form.name.data
        skin = form.skin.data
        char = create_character_request(name, skin)
        Character.update_character(char)
        names_query = db.session.query(Character.name)
        names = db.session.scalars(names_query).all()
        current_app.config['NAMES'] = names
        char = Character.query.filter_by(name=char['name']).first()
        return redirect(url_for('char.get_char', char_name=char.name))
    return render_template('create_character.html', form=form,
                           names=current_app.config['NAMES'])


@main.route('/delete_character', methods=['GET', 'POST'])
def delete_character():
    form = DeleteCharacter()

    if form.validate_on_submit():
        name = form.name.data
        response = delete_character_request(name)
        if response != 200:
            flash(response.json()['error']['message'])
        flash(f'Character {name} was deleted.')
        character = Character.query.filter_by(name=name).first()
        db.session.delete(character)
        db.session.commit()
        names_query = db.session.query(Character.name)
        names = db.session.scalars(names_query).all()
        current_app.config['NAMES'] = names
        return redirect(url_for('main.index'))
    return render_template('delete_character.html', form=form,
                           names=current_app.config['NAMES'])


@main.route('/effect/<int:id>')
def effect(id):
    e = Effect.query.get(id)
    return render_template('effect.html', effect=e,
                           names=current_app.config['NAMES'])


@main.route('/update-one-map', methods=['GET', 'POST'])
def update_one_map():
    form = UpdateMap()

    if form.validate_on_submit():
        x = form.x_coord.data
        y = form.y_coord.data
        layer = form.layer.data
        map_to_update = Map.query.filter_by(x=x, y=y, layer=layer).first()
        response = get_one_map(map_to_update.map_id)
        if response.status_code != 200:
                flash(response.json()['error']['message'])
                return redirect(url_for('main.events'))
        map_data = response.json()['data']
        Map.update_map(map_data)
        return redirect(url_for('main.maps', layer='overworld'))

    return render_template('update_one_map.html',
                           form=form,
                           names=current_app.config['NAMES'])

@main.route('/update_bank')
def update_bank():
    BankItem.insert_bank_items()
    return redirect(url_for('main.bank'))