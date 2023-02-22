from dataclasses import dataclass
from datetime import datetime
import re


@dataclass
class Block:
    start: int
    end: int
    day: str
    text: str


def parse_header(text: str) -> str:
    return text.split("\n")[0]


def parse_weeknums(text: str) -> list[int]:
    text = text.split("\n")[2][16:].split("Datum:")[0].replace(" ", "")

    weeknums = []
    for number in text.split(","):
        if "-" in number:
            start, end = number.split("-")
            weeknums.extend(range(int(start), int(end) + 1))
        else:
            weeknums.append(int(number))

    return weeknums


def parse_year(text: str) -> int:
    text = text.split("\n")[1]
    return int(text.split(" ")[1].split("/")[0])


def parse_timerange(table: list[list[str]]) -> list[str]:
    pattern = r"\d?\d?(\d?)\d\d(\d):(:):\d\d(\d)\d\d(\d)"

    times = []
    for cell in table[0][1:-1]:  # first row, first and last cell are empty
        res = list(re.match(pattern, cell).groups())
        times.append("".join(res))

    return times


def parse_table(table: list[list[str]]) -> list[Block]:
    events = []
    for row in table:
        events.extend(parse_row(row))

    return events


def parse_row(row: list[str]) -> list[Block]:
    events = []

    day = row[0]
    row = row[1:-1]  # remove first (day) and last (empty) cell

    tracking = False
    event = None
    for idx, cell in enumerate(row):
        if not tracking and cell != "":
            tracking = True
            event = Block(idx, 0, day, cell)

        if tracking and cell == "":
            tracking = False
            event.end = idx
            events.append(event)

    return events
