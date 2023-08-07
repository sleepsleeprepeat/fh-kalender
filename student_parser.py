from extractor import Page
from datetime import datetime, timedelta
from extractor import Event



class PageParser:
    def __init__(self, page: Page) -> None:
        self.page = page

    def get_events(self) -> list[Event]:
        weeknumbers = self.__parse_weeknumbers()
        year = self.__parse_year(self.page.header.get_semester())
        days = self.page.table.get_header()

        events = []
        rows = self.page.table.get_rows()
        for row_idx, row in enumerate(rows):
            for col_idx, cell in enumerate(row.get_cells()):
                if cell.is_empty:
                    continue

                starttime = row.get_time()
                endtime = rows[(row_idx + cell.get_duration())].get_time()

                # the index is used to get the day of the week
                day = days[col_idx]
                for weeknumber in weeknumbers:
                    start = self.__generate_datetime(year, weeknumber, day, starttime)
                    end = self.__generate_datetime(year, weeknumber, day, endtime)

                    events.append(
                        Event(
                            title=f"{cell.get_titleinfo()} {cell.get_title()}",
                            start=start,
                            end=end,
                            location=f"{cell.get_intern_room()} {cell.get_extern_room()}",
                            description=f"{cell.get_lecturer()} ({cell.get_comment()})",
                        )
                    )

        return events

    def __parse_weeknumbers(self) -> list[int]:
        text = self.page.header.get_weeknumbers().strip()

        weeknumbers = []
        for block in text.split(","):
            if "-" in block:
                start, end = block.split("-")
                weeknumbers.extend(range(int(start), int(end) + 1))
            else:
                weeknumbers.append(int(block))

        return weeknumbers

    def __parse_year(self, year: str) -> int:
        return int(year.split(" ")[1].split("/")[0])

    def __translate_day(self, day: str) -> str:
        return {
            "Montag": "Monday",
            "Dienstag": "Tuesday",
            "Mittwoch": "Wednesday",
            "Donnerstag": "Thursday",
            "Freitag": "Friday",
            "Samstag": "Saturday",
            "Sonntag": "Sunday",
        }[day]

    def __generate_datetime(
        self, year: int, weeknumber: int, day: str, time: str
    ) -> datetime:
        day = self.__translate_day(day)
        if weeknumber >= 53:
            weeknumber = weeknumber - 52
            year += 1

        date = datetime.strptime(f"{year} {weeknumber} {day}", "%Y %W %A")
        time = datetime.strptime(time, "%H:%M")
        return date + timedelta(hours=time.hour, minutes=time.minute)
