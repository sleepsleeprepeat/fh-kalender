from extractor import Page, Cell
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
        # create a tabel of all rows and columns
        table: list[list[Cell]] = []
        for row in self.page.table.get_rows():
            table.append(row.get_cells())

        rows = self.page.table.get_rows()
        row_errors = 0
        for row_idx, row in enumerate(table):
            for col_idx, cell in enumerate(row):
                if cell.is_empty:
                    continue

                duration = cell.get_duration()

                # insert empty cells in the same column for the duration of the event to the rows below
                for i in range(1, duration):
                    table[row_idx + i].insert(col_idx, Cell(None))

                starttime = rows[row_idx].get_time()
                endtime = rows[(row_idx + duration)].get_time()

                # the index is used to get the day of the week
                day = days[col_idx]
                for weeknumber in weeknumbers:
                    start = self.__generate_datetime(year, weeknumber, day, starttime)
                    end = self.__generate_datetime(year, weeknumber, day, endtime)

                    description = cell.get_lecturer()
                    if cell.get_comment() != "":
                        description += f" ({cell.get_comment()})"

                    events.append(
                        Event(
                            title=f"{cell.get_titleinfo()} {cell.get_title().replace('_', ' ')}",
                            start=start,
                            end=end,
                            location=f"{cell.get_intern_room()} {cell.get_extern_room()}",
                            description=description,
                        )
                    )

            if len(row) < 5:
                row_errors += 1

        if row_errors > 0:
            print(
                f"Page: {self.page.header.get_pagetitle()} has {row_errors} rows with errors"
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
