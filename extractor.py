from dataclasses import dataclass
from datetime import datetime


@dataclass
class Event:
    title: str
    start: datetime
    end: datetime
    location: str
    description: str


class Cell:
    def __init__(self, cell) -> None:
        self.data = cell
        self.is_empty = self.data.text == ""
        self.sub_rows = self.data.find_all("table", recursive=False)

    def get_comment(self) -> str:
        return self.sub_rows[0].find_all("td")[0].text

    def get_titleinfo(self) -> str:
        return self.sub_rows[0].find_all("td")[1].text

    def get_lecturer(self) -> str:
        return self.sub_rows[0].find_all("td")[2].text

    def get_title(self) -> str:
        return self.sub_rows[1].find("td").text

    def get_extern_room(self) -> str:
        return self.sub_rows[2].find_all("td")[0].text

    def get_intern_room(self) -> str:
        return self.sub_rows[2].find_all("td")[1].text

    def get_duration(self) -> int:
        return int(self.data["rowspan"])


class Row:
    def __init__(self, row) -> None:
        self.data = row

    def get_time(self) -> str:
        return self.data.find("td", recursive=False).text

    def get_cells(self) -> list[Cell]:
        return [Cell(cell) for cell in self.data.find_all("td", recursive=False)[1:]]


class Table:
    def __init__(self, data) -> None:
        self.data = data

    def get_header(self) -> list[str]:
        cells = self.data.find("tr").find_all("td", recursive=False)[1:]
        return [cell.text for cell in cells]

    def get_rows(self) -> list[Row]:
        return [Row(row) for row in self.data.find_all("tr", recursive=False)[1:]]


class Header:
    def __init__(self, header) -> None:
        self.data = header

    def get_pagetitle(self) -> str:
        return self.data.find("span", {"class": "header-0-0-1"}).text

    def get_semester(self) -> str:
        return self.data.find("span", {"class": "header-0-2-0"}).text

    def get_weeknumbers(self) -> str:
        return self.data.find("span", {"class": "header-2-0-1"}).text

    def get_startdate(self) -> str:
        return self.data.find("span", {"class": "header-2-0-3"}).text

    def get_enddate(self) -> str:
        return self.data.find("span", {"class": "header-2-0-5"}).text

    def get_updatedate(self) -> str:
        return self.data.find("span", {"class": "header-2-2-1"}).text


class Page:
    def __init__(self, tables) -> None:
        self.data = tables
        self.header = Header(tables[0])
        self.table = Table(tables[1])
        # no info in footer
