from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField, StringField, IntegerField
from wtforms.validators import DataRequired, NumberRange

class ItemFilter(FlaskForm):
    categories = [('all', 'All'), ('amulet', 'Amulet'),
                    ('artifact', 'Artifact'), ('bag', 'Bag'),
                    ('body_armor', 'Body armor'), ('boots', 'Boots'),
                    ('consumable', 'Consumable'), ('currency', 'Currency'),
                    ('helmet', 'Helmet'), ('leg_armor', 'Leg armor'),
                    ('resource', 'Resource'), ('ring', 'Ring'),
                    ('rune', 'Rune'), ('shield', 'Shield'),
                    ('utility', 'Utility'), ('weapon', 'Weapon')]
    skills = [('all', 'All'), ('alchemy', 'Alchemy'), ('cooking', 'Cooking'),
                ('gearcrafting', 'Gearcrafting'),
                ('jewelrycrafting', 'Jewelrycrafting'), ('mining', 'Mining'),
                ('weaponcrafting', 'Weaponcrafting'),
                ('woodcutting', 'Woodcutting')]
    lvl_choices = [('all', 'All'), (10, '1-9'), (20, '10-19'), (30, '20-29'),
                (40, '30-39'), (50, '40-49'), (60, '50-59')]
    levels = SelectField(
                'Levels', choices=lvl_choices, validators=[DataRequired()])
    skill = SelectField(
                'Skill', choices=skills, validators=[DataRequired()])
    category = SelectField(
                'Category', choices=categories, validators=[DataRequired()])
    submit = SubmitField('Submit')


class LevelsFilter(FlaskForm):
    lvl_choices = [('all', 'All'), (10, '1-9'), (20, '10-19'), (30, '20-29'),
                (40, '30-39'), (50, '40-49'), (60, '50-59')]
    levels = SelectField(
                'Levels', choices=lvl_choices, validators=[DataRequired()])
    submit = SubmitField('Submit')


class ResourceFilter(FlaskForm):
    skills_choises = [('all', 'All'), ('alchemy', 'Alchemy'),
                    ('fishing', 'Fishing'), ('mining', 'Mining'),
                    ('woodcutting', 'Woodcutting')]
    skill = SelectField(
                'Skills', choices=skills_choises, validators=[DataRequired()])
    submit = SubmitField('Submit')


class AchievementFilter(FlaskForm):
    completed_choices = [('all', 'All'), ('yes', 'Completed'),
                        ('no', 'Uncompleted')]
    achieve_types = [('all', 'All'), ('combat_drop', 'Combat drop'),
                    ('combat_kill', 'Combat kill'),
                    ('combat_level', 'Combat level'),                    
                    ('crafting', 'Crafting'), ('gathering', 'Gathering'),
                    ('recycling', 'Recycling'), ('task', 'Task'),                    
                    ('use', 'Use')]
    achievement_type = SelectField(
                'Type', choices=achieve_types, validators=[DataRequired()])
    completed = SelectField(
            'Completed', choices=completed_choices, validators=[DataRequired()])
    submit = SubmitField('Submit')


class GetToken(FlaskForm):
    token = StringField('Token', validators=[DataRequired()])
    submit = SubmitField('Submit')


class CreateCharacter(FlaskForm):
    skin_names = ['men1', 'men2', 'men3', 'women1', 'women2', 'women3']
    name = StringField('Name', validators=[DataRequired()])
    skin = SelectField('Skin', choices=skin_names, validators=[DataRequired()])
    submit = SubmitField('Submit')


class DeleteCharacter(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    submit = SubmitField('Submit')


class UpdateMap(FlaskForm):
    layers = [('overworld', 'Overworld'), ('underground', 'Underground'),
                ('interior', 'Interior')]
    layer = SelectField('Layer', choices=layers, validators=[DataRequired()])
    x_coord = IntegerField('X:', validators=[NumberRange(min=-5, max=11)])
    y_coord = IntegerField('Y:', validators=[NumberRange(min=-5, max=22)])
    submit = SubmitField('Update')