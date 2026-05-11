from aiogram.fsm.state import State, StatesGroup


class BookingFlow(StatesGroup):
    choosing_date = State()
    choosing_duration = State()
    choosing_slot = State()
    entering_email = State()
    entering_description = State()
    confirming = State()

