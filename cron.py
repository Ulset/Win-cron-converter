class Scheduler:
    """
    Håndterer scripts som skal startes basert på en tid, tiden kommer fra en .json fil i CRON syntax."

    Syntax:
    "Test": {
        "time": "* * * * *",
        "scriptNavn": "testScript.py",
        "description": "Dette scriptet kjøres som en test"
    }
    """

    def __init__(self, master: Master):
        self._date_generated = None

        self.__create_time_table()
        threading.Thread(target=self.time_loop).start()
    
    def __is_refreshed(self):
        """Returns True if the timeschedule is refreshed today"""
        dt = datetime.datetime.now()
        datenow = dt.strftime("%d.%m.%Y")
        if(self._date_generated == datenow):
            return True
        else:
            return False
    
    def __set_refreshed(self):
        """Sets the last refresh date to now"""
        dt = datetime.datetime.now()
        datenow = dt.strftime("%d.%m.%Y")
        self._date_generated = datenow



    def __create_time_table(self):
        """Lager et dictionary med alle tidspunktene ila en dag, legger scripts inn på hvilken tid de skal kjøres."""
        self.timeschedule = {}
        for hour in range(24):
            hour = str(hour)
            for minute in range(60):
                minute = str(minute)
                self.timeschedule[f"{hour.rjust(2, '0')}:{minute.rjust(2, '0')}"] = [
                ]

        self.__populate_timetable()
        self.__set_refreshed()

    def __populate_timetable(self):
        """Parser .json fil etter CRON syntax"""
        timeInp = open(os.path.join(
            os.getcwd(), "Script_Dependencies", "Server", "Scheduler.json"))
        timeObj = json.load(timeInp)
        for el in timeObj:
            try:
                timeObj[el]["scriptNavn"]
                timeObj[el]["description"]
                timeObj[el]["time"]
            except:
                print(
                    f"Scheduler: '{el}' er ikke definert riktig i JSON filen, hopper over.")
                continue

            timelist = self.cron_to_list_parser(timeObj[el]["time"])
            for timeEl in timelist:
                inputObj = {
                    "navn": el,
                    "scriptNavn": timeObj[el]["scriptNavn"],
                    "description": timeObj[el]["description"]
                }
                self.timeschedule[timeEl].append(inputObj)
            self.logger.log(json.dumps(self.timeschedule, indent=4))

    def cron_to_list_parser(self, cronString: str):
        """Genererer en liste med godkjente tider IDAG etter cronString."""
        assert len(cronString.split(
            " ")) == 5, f"Cronstring: {cronString} følger ikke riktig formatering."

        def subcron_parser(subCronString, subType):
            output = []
            rangeValues = {
                "minute": [0, 59],
                "hour": [0, 23],
                "day": [1, 31],
                "month": [1, 12],
                "weekday": [0, 6]
            }
            assert subType in rangeValues, f"Argument subType må være en av disse verdiene: {[value for value in rangeValues]}"
            if subCronString[0] == "*" and len(subCronString) == 1:
                # Hvis det er bare en stjerne skal den bare gi alle mulige kombinasjoner tilbake
                [output.append(str(tid).rjust(2, "0")) for tid in range(
                    rangeValues[subType][0], rangeValues[subType][1]+1)]
                return output
            elif subCronString[0] == "*" and subCronString[1] == "/":
                step = subCronString.split("/")[1]
                [output.append(str(tid).rjust(2, "0")) for tid in range(
                    rangeValues[subType][0], rangeValues[subType][1]+1, int(step))]
                return output
            elif subCronString[0].isnumeric() and len(subCronString) <= 2:
                output.append(str(subCronString).rjust(2, "0"))
                return output
            elif subCronString[0].isnumeric() and len(subCronString) > 2:
                stepFlag = False
                if "/" in subCronString:
                    assert len(subCronString.split(
                        "/")) == 2, f"Kan bare være 1 step operatør('/') i CRON syntax. Input: {subCronString}"
                    step = int(subCronString.split("/")[1])
                    stepFlag = True
                if "-" in subCronString:
                    assert len(subCronString.split(
                        "-")) == 2, f"Kan bare være 1 range('-') operatør i CRON syntax. Input: {subCronString}"
                    intervalStart, intervalEnd = subCronString.split("-")
                    # hvis input var feks 1-20/6 vil intervalEnd være '20/6', splitter derfor intervalEnd etter '/' og bruker første index -> '20'
                    intervalEnd = intervalEnd.split("/")[0]
                if stepFlag:
                    for i in range(int(intervalStart), int(intervalEnd), step):
                        output.append(str(i).rjust(2, "0"))
                else:
                    for i in range(int(intervalStart), int(intervalEnd)):
                        output.append(str(i).rjust(2, "0"))
                return output

        minute, hour, day, month, weekday = cronString.split(" ")
        datetimeObj = datetime.datetime.today()
        monthToday = datetimeObj.strftime("%m")
        dateToday = datetimeObj.strftime("%d")
        weekdayToday = datetimeObj.strftime("%w")
        # zero padder den siden datetime ikke gjør det
        weekdayToday = weekdayToday.rjust(2, "0")
        if not monthToday in subcron_parser(month, "month") or not dateToday in subcron_parser(day, "day") or not weekdayToday in subcron_parser(weekday, "weekday"):
            # Denne kicker hvis dagen/måneden/ukedagen IDAG ikke stemmer med når scriptet skal kjøre, derfor returnerer den bare en tom liste
            #
            return []
        else:
            output = []
            approvedHours = subcron_parser(hour, "hour")
            approvedMinutes = subcron_parser(minute, "minute")
            for h in approvedHours:
                for m in approvedMinutes:
                    output.append(f"{h}:{m}")
            return output