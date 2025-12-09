from flask import current_app
from app import db, create_app
from app.models import (Monster,
                        Map,
                        Item,
                        Drop,
                        Achievement,
                        Event,
                        Craft,
                        NPC_Item,
                        Resource,
                        NPC,
                        Character,
                        Effect,
                        BankItem,
                        Condition,
                        Transition,
                        )
from app.all_requests import download_map_images

flask_app = create_app()
celery_app = flask_app.extensions["celery"]

def insert_data_in_database():
    db.drop_all()
    db.create_all()
    Effect.insert_effects()
    Item.insert_items()
    Monster.insert_monsters()
    Drop.insert_drops()
    NPC.insert_npc()
    NPC_Item.insert_npc_items()
    Resource.insert_resources()
    Map.insert_maps()
    Event.insert_events()
    BankItem.insert_bank_items()
    Character.insert_characters()
    Achievement.insert_achievements()

    print('Database initialized and populated successfully.')


@flask_app.cli.command('init-db')
def init_db_command():
    """Initializes and populates the database."""
    with flask_app.app_context():
        db.drop_all()
        db.create_all()
        Effect.insert_effects()
        Item.insert_items()
        Monster.insert_monsters()
        Drop.insert_drops()
        NPC.insert_npc()
        NPC_Item.insert_npc_items()
        Resource.insert_resources()
        Map.insert_maps()
        Event.insert_events()
        BankItem.insert_bank_items()
        Character.insert_characters()
        Achievement.insert_achievements()

        print('Database initialized and populated successfully.')


@flask_app.cli.command('update')
def update_bank():
    with flask_app.app_context():
        BankItem.insert_bank_items()
        print('Bank updated successfully.')


@flask_app.shell_context_processor
def make_shell_context():
    return dict(db=db, Monster=Monster, Map=Map, Item=Item, Drop=Drop,
                Achievement=Achievement, Event=Event, Resource=Resource,
                Craft=Craft, NPC=NPC, NPC_Item=NPC_Item,
                Effect=Effect, BankItem=BankItem,
                Character=Character,
                Condition=Condition,
                Transition=Transition,
                insert_data_in_database=insert_data_in_database,
                download_map_images=download_map_images)
