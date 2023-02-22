from datetime import datetime
import os
import pdfplumber
from pdfplumber.page import Page
import json
from fh_plan import *

WEEKDAYS = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
CATEGORY_LAB = ["-ÜL", "ÜL-"]
CATEGORY_EXERCISES = ["-Ü", "Ü-"]


@dataclass
class Event:
    title: str
    category: str
    degree: str
    semester: int
    group: int
    start: datetime
    end: datetime
    rooms: list[str]


def parse_studentplan_page(page: Page) -> list[Event]:
    text = page.extract_text()
    table = page.extract_table()

    # parse header
    header = parse_header(text)
    pattern = r"^Vorlesungsplan für\s+([\w\-\s]+) (\d+). Sem. Gruppe (\d+)"
    res = re.match(pattern, header)

    if res:
        degree = res.group(1)
        semester = int(res.group(2))
        group = int(res.group(3))
    else:
        degree = header
        semester = 0
        group = 0

    weeknums = parse_weeknums(text)
    timerange = parse_timerange(table)
    year = parse_year(text)

    blocks: list[Block] = []
    for row in table:
        blocks.extend(parse_row(row))

    events = []
    for block in blocks:

        # parse rooms
        pattern = r"C\d\d-\d.\d\d"
        rooms = re.findall(pattern, block.text)

        # parse start and end
        block_start = timerange[block.start]
        block_end = timerange[block.end]
        block_day = WEEKDAYS.index(block.day)

        # parse weeknums
        dates = []
        for weeknum in weeknums:
            start_str = f"{year} {weeknum} {block_day} {block_start}"
            start = datetime.strptime(start_str, "%Y %W %w %H:%M")

            end_str = f"{year} {weeknum} {block_day} {block_end}"
            end = datetime.strptime(end_str, "%Y %W %w %H:%M")
            dates.append((start, end))

        # parse category
        category = "Vorlesung"
        if any(x in block.text for x in CATEGORY_LAB):
            category = "Labor"
        elif any(x in block.text for x in CATEGORY_EXERCISES):
            category = "Übung"

        for date in dates:
            start, end = date
            event = Event(
                title=block.text,
                category=category,
                degree=degree,
                semester=semester,
                group=group,
                start=start,
                end=end,
                rooms=rooms,
            )
            events.append(event)

    return events


if __name__ == "__main__":
    path = "./input/SS_23/"

    events = []
    for file in os.listdir(path):
        print(f"Processing {file}")
        pdf = pdfplumber.open(path + file)

        for page in pdf.pages:
            events.extend(parse_studentplan_page(page))

    print(f"Found {len(events)} events")
