from datetime import datetime
import json
import os
import csv
import sqlite3
import threading
import pdfplumber

from fh_plan import *

WEEKDAYS = ["So", "Mo", "Di", "Mi", "Do", "Fr", "Sa"]
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
    pattern = r"^Vorlesungsplan für\s+([\w\-\s\/]+) (\d+)\. Sem\.\s?[Grupe]*\s?\.?\s?(\d)?\.?\s?\-?\s?([A-Za-z]*)"
    res = re.match(pattern, header)

    if res:
        degree = res.group(1) + " " + res.group(4)
        semester = res.group(2)
        group = res.group(3) or 0
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
        pattern = r"C\d\d-\d?\w?.\d\d"
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
                title=block.text.replace("\n", " ").strip(),
                category=category,
                degree=degree.replace("\n", " ").strip(),
                semester=semester,
                group=group,
                start=start,
                end=end,
                rooms=rooms,
                source=header.replace("\n", " ").strip()
                + f" [Seite: {page.page_number}]",
            )
            events.append(event)

    return events


if __name__ == "__main__":
    path = "./input/SS_23/"

    events = []
    for file in os.listdir(path):
        print(f"Processing {path+file}")
        pdf = pdfplumber.open(path + file)

        for page in pdf.pages:
            events.extend(parse_studentplan_page(page))

        pdf.close()

    print(f"Found {len(events)} events")

    # save to sqlite
    con = sqlite3.connect("output.db")
    cur = con.cursor()

    cur.execute("DROP TABLE IF EXISTS events")

    cur.execute(
        "CREATE TABLE IF NOT EXISTS events (title TEXT, category TEXT, degree TEXT, semester TEXT, sem_group TEXT, start TEXT, end TEXT, room1 TEXT, room2 TEXT, room3 TEXT, room4 TEXT, room5 TEXT, source TEXT)"
    )

    for event in events:
        # fill empty rooms with empty strings
        rooms = event.rooms + [""] * (5 - len(event.rooms))

        # insert event
        cur.execute(
            "INSERT INTO events (title, category, degree, semester, sem_group, start, end, room1, room2, room3, room4, room5, source) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                event.title,
                event.category,
                event.degree,
                event.semester,
                event.group,
                event.start,
                event.end,
                *rooms,
                event.source,
            ),
        )

    con.commit()
    con.close()

    print("Done")
