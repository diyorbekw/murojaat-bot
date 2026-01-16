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
    
    # Step 3: Select subcategory (if available)
    waiting_for_subcategory = State()
    
    # Step 4: Enter description
    waiting_for_description = State()
    
    # Step 5: Upload media (photos, videos, voice, video_notes)
    waiting_for_media = State()
    
    # Step 6: Ask for urgent notification
    waiting_for_urgent_confirm = State()
    
    # Step 7: Ask for location if urgent (only for urgent complaints)
    waiting_for_location = State()