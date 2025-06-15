__all__ = [

    'BaseModel',
    'Bookings',
    'Slots',
    'User',
]

from database.orm import BaseModel
from .bookings import Bookings
from .slots import Slots
from .users import User
