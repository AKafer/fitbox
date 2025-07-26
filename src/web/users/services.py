from datetime import date

import constants
from database.models import User


def calc_age(born: date, today: date | None = None) -> int | None:
    if born is None:
        return None

    if today is None:
        today = date.today()

    years = today.year - born.year
    if (today.month, today.day) < (born.month, born.day):
        years -= 1
    return years


def calc_count_booking_info(user: User) -> (int, float, str):
    trainings_count, energy = 0, 0
    for booking in user.bookings:
        if hasattr(booking, 'is_done') and booking.is_done:
            trainings_count += 1
            if hasattr(booking, 'energy'):
                energy += booking.energy or 0
    status = ''
    for installed_status, level in constants.status_levels.items():
        if energy >= level:
            status = installed_status
        else:
            break
    return trainings_count, energy, status


def calc_score(user: User) -> int:
    if user.score is None:
        return 0
    return user.score
