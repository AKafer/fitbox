import io
import logging
import os
from datetime import date, datetime

from PIL import Image
from fastapi import UploadFile
from starlette.requests import Request

import aiofiles as aiof

import constants
from database.models import User
from settings import BASE_URL, STATIC_FOLDER, PHOTO_FOLDER, PHOTO_DIR


logger = logging.getLogger('control')


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
        if booking.slot and booking.slot.is_done:
            trainings_count += 1
            if booking.energy:
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


def get_full_link(request: Request, filename: str) -> str:
    base_url = BASE_URL or str(request.base_url)
    return f'{base_url}api/{STATIC_FOLDER}/{PHOTO_FOLDER}/{filename}'


async def save_file(new_file: UploadFile, user: User) -> str:
    if user.photo_url is not None:
        delete_file(user.photo_url)
    content = await new_file.read()
    img = Image.open(io.BytesIO(content))
    img.thumbnail((600, 600), Image.Resampling.LANCZOS)

    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    new_name = (
        f'{user.id}--'
        f"{datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')}.webp"
    )
    path_to_file = os.path.join(PHOTO_DIR, new_name)
    img.save(
        path_to_file,
        format="WEBP",
        quality=65,
        method=5,
        optimize=True
    )
    return new_name


def delete_file(filename: str) -> None:
    logger.debug(f'Delete file {filename}')
    try:
        os.remove(os.path.join(PHOTO_DIR, filename))
    except FileNotFoundError:
        pass
