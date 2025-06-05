from datetime import date


def calc_age(born: date, today: date | None = None) -> int:
    if today is None:
        today = date.today()

    years = today.year - born.year
    if (today.month, today.day) < (born.month, born.day):
        years -= 1
    return years
