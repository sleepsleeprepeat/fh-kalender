from datetime import datetime
import json
import os
import csv
import sqlite3
import threading
import pdfplumber

from fh_plan import *

WEEKDAYS = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
CATEGORY_LAB = ["-ÜL", "ÜL-"]
CATEGORY_EXERCISES = ["-Ü", "Ü-"]


@dataclass
class Event:
    start: datetime
    end: datetime
    rooms: list[str]


@dataclass
class Module:
    title: str
    short: str
    lectures: list[Event]
    exercises: list[Event]
    labs: list[Event]


@dataclass
class StudentPlan:
    degree: str
    semester: int
    group: str
    modules: list[Module]


@dataclass
class RawEvent:
    title: str
    category: str
    degree: str
    semester: int
    group: int
    start: datetime
    end: datetime
    rooms: list[str]
    source: str


def parse_studentplan_page(page) -> list[RawEvent]:
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
            event = RawEvent(
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

    raw_events = []
    for file in os.listdir(path):
        print(f"Processing {path+file}")
        pdf = pdfplumber.open(path + file)

        for page in pdf.pages:
            raw_events.extend(parse_studentplan_page(page))

    print(f"Found {len(raw_events)} events")

    # create modules and avoid duplicates
    modules = []
    plans = []
    for raw_event in raw_events:
        event = Event(
            start=raw_event.start,
            end=raw_event.end,
            rooms=raw_event.rooms,
        )

        # create modules and avoid duplicates
        module = next((x for x in modules if x.title == raw_event.title), None)
        if module is None:
            module = Module(
                title=raw_event.title,
                short="",
                lectures=[],
                exercises=[],
                labs=[],
            )

            match raw_event.category:
                case "Vorlesung":
                    module.lectures.append(event)
                case "Übung":
                    module.exercises.append(event)
                case "Labor":
                    module.labs.append(event)

            modules.append(module)

        else:
            match raw_event.category:
                case "Vorlesung":
                    module.lectures.append(event)
                case "Übung":
                    module.exercises.append(event)
                case "Labor":
                    module.labs.append(event)

    for raw_event in raw_events:
        # create student plans and avoid duplicates
        plan = next(
            (
                x
                for x in plans
                if x.degree == raw_event.degree
                and x.semester == raw_event.semester
                and x.group == raw_event.group
            ),
            None,
        )
        if plan is None:
            plan = StudentPlan(
                degree=raw_event.degree,
                semester=raw_event.semester,
                group=raw_event.group,
                modules=[],
            )
            plans.append(plan)

        # add modules to student plans if they are not already in there
        module = next((x for x in modules if x.title == raw_event.title), None)
        if module not in plan.modules:
            plan.modules.append(module)

    print(f"Found {len(modules)} modules")
    print(f"Found {len(plans)} plans")

    # write to json
    json_str = {
        "plans": [],
        "modules": [],
    }

    for plan in plans:
        plan_str = {
            "degree": plan.degree,
            "semester": str(plan.semester),
            "group": str(plan.group),
            "modules": [],
        }

        for module in plan.modules:
            t = module.title.replace("\n", " ").strip()
            plan_str["modules"].append(module.short if module.short else t)

        json_str["plans"].append(plan_str)

    for module in modules:
        module_str = {
            "title": module.title,
            "short": module.short,
            "lectures": [],
            "exercises": [],
            "labs": [],
        }
        for lecture in module.lectures:
            lecture_str = {
                "start": lecture.start.isoformat(),
                "end": lecture.end.isoformat(),
                "rooms": lecture.rooms,
            }
            module_str["lectures"].append(lecture_str)
        for exercise in module.exercises:
            exercise_str = {
                "start": exercise.start.isoformat(),
                "end": exercise.end.isoformat(),
                "rooms": exercise.rooms,
            }
            module_str["exercises"].append(exercise_str)
        for lab in module.labs:
            lab_str = {
                "start": lab.start.isoformat(),
                "end": lab.end.isoformat(),
                "rooms": lab.rooms,
            }
            module_str["labs"].append(lab_str)
        json_str["modules"].append(module_str)

    print("Writing to output.json")
    with open("output.json", "w", encoding="utf-8") as file:
        json.dump(json_str, file, ensure_ascii=False, indent=4)

    print("Done")
