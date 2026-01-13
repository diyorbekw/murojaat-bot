"""
Finite State Machine states for complaint submission
"""

from aiogram.fsm.state import State, StatesGroup


class ComplaintStates(StatesGroup):
    """FSM states for complaint creation process"""
    
    # Step 1: Select mahalla
    waiting_for_mahalla = State()
    
    # Step 2: Select category
    waiting_for_category = State()
    
    # Step 3: Enter description
    waiting_for_description = State()
    
    # Step 4: Upload images
    waiting_for_images = State()