from aiogram.fsm.state import State, StatesGroup

class EssayStates(StatesGroup):
    waiting_for_topic = State()
    waiting_for_essay = State()

class PaymentStates(StatesGroup):
    waiting_for_receipt = State()
