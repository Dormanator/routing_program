import re
from typing import Tuple


class Time:
    def __init__(self, hours: int = 0, minutes: int = 0):
        self.__total_minutes = 0
        self.add_hours(hours)
        self.add_minutes(minutes)

    # Returns time as an (Hours, Minutes) tuple
    def get_time(self) -> Tuple[int, int]:
        total_hours = self.__total_minutes // 60
        remaining_minutes = self.__total_minutes % 60
        return total_hours, remaining_minutes

    # Add to current time
    def add_hours(self, hours: int) -> "Time":
        self.add_minutes(hours * 60)
        return self

    def add_minutes(self, minutes: int) -> "Time":
        # Ensure minutes calculated don't exceed that of a full day, if so use the remainder.
        minutes_in_a_day = 60 * 24
        self.__total_minutes = (self.__total_minutes + minutes) % minutes_in_a_day
        return self

    # Utility method to test if string value is appropriate for time conversion
    @staticmethod
    def is_valid_time_str(hh_mm_midday_string: str = "00:00 AM"):
        # If we got an empty or invalid string return false
        valid_pattern = re.compile(r"\d{1,2}:\d{1,2}\s(AM|PM)", re.IGNORECASE)
        if valid_pattern.fullmatch(hh_mm_midday_string) is None:
            return False
        return True

    # Conversion method to help read csv values incoming as HH:MM AM/PM
    @staticmethod
    def str_to_time_tuple(hh_mm_midday_string: str = "00:00 AM") -> Tuple[int, int]:
        # If we got an empty or invalid string return a time tuple of 0, 0
        if not Time.is_valid_time_str(hh_mm_midday_string):
            return 0, 0

        # Convert input string into hour and minute integers and find out
        # if it is past-midday.
        split_time_string = hh_mm_midday_string.split(" ")
        hh_mm_int_arr = [int(s) for s in split_time_string[0].split(":")]
        is_past_midday = True if split_time_string[1].upper() == "PM" else False

        # If it is past-midday (PM) and not 12:00 PM we need to add 12 hours to the hour.
        # If it is before-midday (AM) and 12:00 AM then add 12 hours (24:00 hours = 12:00 AM)
        if (is_past_midday and hh_mm_int_arr[0] != 12) or (not is_past_midday and hh_mm_int_arr[0] == 12):
            hh_mm_int_arr[0] += 12

        # Use hour and minute counts to determine representation in seconds.
        return hh_mm_int_arr[0], hh_mm_int_arr[1]

    # Convenience methods
    def __sub__(self, other_time):
        difference_in_hr = self.get_time()[0] - other_time.get_time()[0]
        difference_in_min = self.get_time()[1] - other_time.get_time()[1]
        return difference_in_hr, difference_in_min

    def __lt__(self, other_time):
        return self.__total_minutes < other_time.__total_minutes

    def __le__(self, other_time):
        return self.__total_minutes <= other_time.__total_minutes

    def __gt__(self, other_time):
        return self.__total_minutes > other_time.__total_minutes

    def __ge__(self, other_time):
        return self.__total_minutes >= other_time.__total_minutes

    def __eq__(self, other_time):
        return self.__total_minutes == other_time.__total_minutes

    def __copy__(self):
        return Time(*self.get_time())

    def __str__(self):
        # Make sure this is a time before converting
        if self.__total_minutes == 0 or self.__total_minutes is None:
            return "N/A"

        # Convert seconds to HH:MM AM/PM representation
        current_time = self.get_time()
        midday_notation = "AM"
        hours = current_time[0]

        if hours > 12:
            hours -= 12
            midday_notation = "PM"

        # Convert ints to strings
        total_hours = str(hours)
        minutes_passed_hour = str(current_time[1])

        # Pad hours and minutes so we get format HH:MM
        while len(total_hours) < 2:
            total_hours = "0" + total_hours

        while len(minutes_passed_hour) < 2:
            minutes_passed_hour = "0" + minutes_passed_hour

        return f"{total_hours}:{minutes_passed_hour} {midday_notation}"
