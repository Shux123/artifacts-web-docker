from flask_wtf import FlaskForm
from wtforms import (SelectField,
                    SubmitField,
                    StringField,
                    HiddenField,
                    IntegerField,)
from wtforms.validators import DataRequired, NumberRange

class UtilityEquip(FlaskForm):
    item_id = HiddenField('Item id')
    quantity = IntegerField('Quantity', validators=[NumberRange(
        min=0, max=100, message='Value must be between 1 and 100')])
    submit = SubmitField('Equip')

class MoveCharacter(FlaskForm):
    layers = [('overworld', 'Overworld'), ('underground', 'Underground'),
                ('interior', 'Interior')]
    layer = SelectField('Layer',
                       choices=layers, validators=[DataRequired()])
    x_coord = IntegerField('X:', validators=[NumberRange(
        min=-5, max=11)])
    y_coord = IntegerField('Y:', validators=[NumberRange(
        min=-5, max=22)])
    submit = SubmitField('Move')


class NpcBuySell(FlaskForm):
    b_s_choices = [('npc/buy', 'Buy'), ('npc/sell', 'Sell')]
    buy_sell = SelectField(
        'Buy or sell', choices=b_s_choices, validators=[DataRequired()])
    item = SelectField('Choose Item', validators=[DataRequired()])
    quantity = IntegerField('Quantity',
                            default=1, validators=[NumberRange(min=1, max=999)])
    submit = SubmitField('Submit')
    

class BankDeposit(FlaskForm):
    item_choise = [('gold', 'Gold')]
    deposit_item = SelectField('Deposit',
                       choices=item_choise, validators=[DataRequired()])
    deposit_quantity = IntegerField('Quantity',
                            default=1, validators=[NumberRange(min=1, max=9999999)])
    deposit_submit = SubmitField('Deposit')


class BankWithdraw(FlaskForm):
    item_choise = [('gold', 'Gold')]
    withdraw_item = SelectField('Withdrow',
                       choices=item_choise, validators=[DataRequired()])
    withdraw_quantity = IntegerField('Quantity',
                            default=1, validators=[NumberRange(min=1, max=9999999)])
    withdraw_submit = SubmitField('Withdrow')


class CraftingForm(FlaskForm):
    craft_item = SelectField('Craft', choices=[], validators=[DataRequired()])
    craft_quantity = IntegerField('Quantity',
                            default=1, validators=[NumberRange(min=1, max=999)])
    craft_submit = SubmitField('Craft')


class RecyclingForm(FlaskForm):
    recycle_item = SelectField('Recycle', choices=[], validators=[DataRequired()])
    recycle_quantity = IntegerField('Quantity',
                            default=1, validators=[NumberRange(min=1, max=999)])
    recycle_submit = SubmitField('Recycle')


class EquipMultiSlot(FlaskForm):
    slot_choices = []
    equip = SelectField('Equip slot', choices=[], validators=[DataRequired()])
    equip_item = SelectField('Item', choices=[], validators=[DataRequired()])
    equip_quantity = IntegerField('Quantity',
                            default=1, validators=[NumberRange(min=1, max=999)])
    equip_submit = SubmitField('Equip')


class UseItem(FlaskForm):
    use_item = SelectField('Item', choices=[], validators=[DataRequired()])
    use_quantity = IntegerField('Quantity', default=1,
                        validators=[NumberRange(min=1, max=999)])
    use_submit = SubmitField('Use')


class TaskTrade(FlaskForm):
    trade_item = SelectField('Trade item', choices=[], validators=[DataRequired()])
    trade_quantity = IntegerField('Quantity', default=1,
                        validators=[NumberRange(min=1, max=999)])
    trade_submit = SubmitField('Trade')


class BuyGeOrder(FlaskForm):
    ge_quantity = IntegerField('Quantity', default=1,
                        validators=[NumberRange(min=1, max=999)])
    ge_submit = SubmitField('Buy')


class CreateSellOrder(FlaskForm):
    sell_item = SelectField('Item', choices=[], validators=[DataRequired()])
    sell_quantity = IntegerField('Quantity', default=1,
                        validators=[NumberRange(min=1, max=999)])
    price = IntegerField('Price', default=1,
                        validators=[NumberRange(min=1, max=999999)])
    sell_submit = SubmitField('Create sell order')


class ItemGeHystory(FlaskForm):
    item_ge = SelectField('Item', choices=[], validators=[DataRequired()])
    ge_submit = SubmitField('Get item hystory')


class DeleteItem(FlaskForm):
    del_item = SelectField('Item', choices=[], validators=[DataRequired()])
    del_quantity = IntegerField('Quantity', default=1,
                        validators=[NumberRange(min=1, max=999)])
    dell_submit = SubmitField('Delete item')


class StartBotForm(FlaskForm):
    action_choices = [('craft', 'Craft'),
                        ('fight', 'Fight'),
                        ('gather', 'Gathering')]
    action = SelectField('Action', choices=action_choices, validators=[DataRequired()])
    target = StringField('Target', validators=[DataRequired()])
    inventory_slot = IntegerField('Inv. Slot',
                         validators=[NumberRange(min=0, max=20)])
    submit = SubmitField('Start bot')
