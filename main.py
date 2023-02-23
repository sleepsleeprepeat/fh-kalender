from datetime import datetime
import os
import csv
import sqlite3
import pdfplumber

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
    source: str


def parse_studentplan_page(page) -> list[Event]:
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
        rooms.extend([""] * (5 - len(rooms)))

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
                source=f"{header} [Seite: {page.page_number}]",
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

    con = sqlite3.connect("fh.db")
    cur = con.cursor()

    cur.execute("DROP TABLE IF EXISTS events")

    cur.execute(
        "CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY, title TEXT, category TEXT, degree TEXT, semester TEXT, sem_group TEXT, start DATETIME, end DATETIME, room1 TEXT, room2 TEXT, room3 TEXT, room4 TEXT, room5 TEXT, source TEXT)"
    )

    for event in events:
        cur.execute(
            "INSERT INTO events (title, category, degree, semester, sem_group, start, end, room1, room2, room3, room4, room5, source) VALUES (?, ? ,?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                event.title,
                event.category,
                event.degree,
                event.semester,
                event.group,
                event.start,
                event.end,
                *event.rooms,
                event.source,
            ),
        )

    con.commit()
    con.close()

    print("Done")
