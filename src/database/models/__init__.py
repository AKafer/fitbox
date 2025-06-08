__all__ = [

    'BaseModel',
    'Slots',
    'User',
]

from database.orm import BaseModel
from .users import User
from .slots import Slots

