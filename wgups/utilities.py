import os
from typing import Optional


def debug(message: str) -> None:
    if os.getenv('WGUPS_DEBUG_MODE'):
        print(f'== [MODE: DEBUG] {message} ==')


# If we can make an integer do so, otherwise None. We want to handle
# empty string values incoming from a csv where an integer is expected.
def str_to_int_or_none(str_value: str) -> Optional[int]:
    if isinstance(str_value, str) and len(str_value) > 0:
        try:
            value = int(str_value)
        except ValueError:
            value = None
        return value
    else:
        return None


# If we can make a positive integer do so, otherwise return negative 1
def parse_user_choice(str_value: str) -> int:
    value = str_to_int_or_none(str_value)
    return value if value is not None and value >= 0 else -1
