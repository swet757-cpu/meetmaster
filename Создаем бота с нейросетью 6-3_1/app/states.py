from aiogram.fsm.state import State, StatesGroup


class AuditFlow(StatesGroup):
    waiting_mode = State()
    waiting_osv = State()
    waiting_mapping = State()
