from datetime import datetime, timedelta


class CronConverter:
    IS_ALWAYS = "stringFillaBadManKilla"

    def __init__(self, cron_string, dt_input=None):
        self.minute, self.hour, self.day_date, self.month, self.day_weekday = cron_string.split(" ")
        if dt_input is None:
            dt_input = datetime.now().replace(minute=0, second=0)

        if self.minute == "*" and self.hour == "*":
            # If both is '*' need to test every minute and every hours
            td_args = {
                "minutes": 1
            }
        elif self.str_is_int(self.minute) and self.hour == "*":
            # If onluy hour is '*' just need to test a single specific time an hour
            dt_input = dt_input.replace(minute=int(minute))
            td_args = {
                "hours": 1
            }
        elif self.str_is_int(self.minute) and self.str_is_int(self.hour):
            # If neither minute or hour is '*', only need to test once a day.
            dt_input = dt_input.replace(minute=int(self.minute), hour=int(self.hour))
            if self.str_is_int(self.day_weekday):
                td_args = {
                    "days": 1
                }
            else:
                td_args = {
                    "days": self.__cron_to_interval(self.day_weekday)
                }
        elif self.__cron_to_interval(self.minute) > 1 and (self.hour == "*" or "-" in self.hour):
            # Causes a error.
            td_args = {
                "minutes": self.__cron_to_interval(self.minute)
            }
        else:
            # Else should use the interval for both minute and hour defined.
            if self.str_is_int(self.minute):
                dt_input = dt_input.replace(minute=int(self.minute))
            if self.str_is_int(self.hour):
                dt_input = dt_input.replace(hour=int(self.hour))
            td_args = {
                "minutes": self.__cron_to_interval(self.minute),
                "hours": self.__cron_to_interval(self.hour)
            }

        self.td_obj = timedelta(**td_args)
        self.dt_obj = dt_input

    @staticmethod
    def str_is_int(string):
        try:
            int(string)
            return True
        except ValueError:
            return False

    def __cron_to_interval(self, subcron_slice):
        subcron_slice: str
        if subcron_slice == "*":
            return 1
        elif self.str_is_int(subcron_slice):
            return 0
        elif "/" in subcron_slice:
            # If interval counter (ie */30) should return 30 since thats the interval
            return int(subcron_slice.split("/")[1])
        elif "-" in subcron_slice:
            # ie(1-5) should return 1 but needs another check later if time is inside range.
            return 1

    def __cron_to_range(self, subcron_string, inclusive=True):
        """
        Converts a subcron string to a range of accepted values
        :param inclusive if the range should include the last integer (IE '2-4' -> [2,3](not inclusive), [2,3,4](inclusive)
        """
        subcron_string: str
        if self.str_is_int(subcron_string):
            return [int(subcron_string)]
        elif "-" in subcron_string:
            start, stop = subcron_string.split("-")
            start = int(start)
            stop = int(stop) if not inclusive else int(stop) + 1
            return [x for x in range(start, stop)]
        else:
            return IS_ALWAYS

    def __time_accepted(self, new_dt):
        new_dt: datetime
        day_weekday_range = self.__cron_to_range(self.day_weekday)
        day_date_range = self.__cron_to_range(self.day_date)
        month_range = self.__cron_to_range(self.month)
        minute_range = self.__cron_to_range(self.minute)
        hour_range = self.__cron_to_range(self.hour, inclusive=False)

        minute_acccepted = new_dt.minute in minute_range if minute_range != IS_ALWAYS else True
        hour_accepted = new_dt.hour in hour_range if hour_range != IS_ALWAYS else True
        clock_accepted = minute_acccepted and hour_accepted

        day_weekday_accepted = new_dt.weekday() in day_weekday_range if day_weekday_range != IS_ALWAYS else True
        day_date_accepted = new_dt.day in day_date_range if day_date_range != IS_ALWAYS else True
        month_accepted = new_dt.month in month_range if month_range != IS_ALWAYS else True
        return day_weekday_accepted and day_date_accepted and month_accepted and clock_accepted

    def get_next_time(self) -> datetime:
        t_now = datetime.now()
        self.dt_obj = self.dt_obj + self.td_obj
        while self.dt_obj < t_now or not self.__time_accepted(self.dt_obj):
            self.dt_obj = self.dt_obj + self.td_obj

        return self.dt_obj


def test():
    cron_string = "*/30 * * * *"

    c = CronConverter(cron_string)
    for _ in range(50):
        print(c.get_next_time().strftime("%d/%m/%Y, %H:%M:%S"))
