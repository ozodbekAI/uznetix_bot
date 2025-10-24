from aiogram.fsm.state import State, StatesGroup


class UserStates(StatesGroup):

    waiting_start_confirmation = State()
    waiting_verification = State()
    waiting_email = State()
    
    main_menu = State()
    
    interview_in_progress = State()
    

    admin_menu = State()
    viewing_stats = State()


    advisor_chat = State()

    waiting_for_search = State()
    waiting_for_history = State()
    waiting_for_broadcast = State()