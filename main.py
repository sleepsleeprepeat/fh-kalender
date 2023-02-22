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
    start: datetime
    end: datetime
    rooms: list[str]


@dataclass
class Module:
    title: str
    category: str
    members: list[(str, int, int)]  # degree, semester, group
    events: list[Event]


def studentplans_to_json(path):
    modules: list[Module] = []

    # loop over all studentplans in path
    for studentplan in os.listdir(path):
        print(studentplan)
        # combine duplicate modules
        new_modules = parse_studentplan(path + studentplan)
        for new_module in new_modules:
            module = next((x for x in modules if x.title == new_module.title), None)
            if module:
                # check if event already exists
                for new_event in new_module.events:
                    event = next(
                        (x for x in module.events if x.start == new_event.start), None
                    )
                    if not event:
                        module.events.append(new_event)

                # check if member already exists
                for new_member in new_module.members:
                    member = next((x for x in module.members if x == new_member), None)
                    if not member:
                        module.members.append(new_member)

            else:
                modules.append(new_module)

    # convert to json
    json_modules = []
    for module in modules:
        json_events = []
        for event in module.events:
            json_events.append(
                {
                    "start": event.start.strftime("%Y-%m-%dT%H:%M:%S"),
                    "end": event.end.strftime("%Y-%m-%dT%H:%M:%S"),
                    "rooms": event.rooms,
                }
            )

        json_members = []
        for member in module.members:
            json_members.append(
                {"degree": member[0], "semester": member[1], "group": member[2]}
            )

        json_modules.append(
            {
                "title": module.title,
                "category": module.category,
                "members": json_members,
                "events": json_events,
            }
        )

    with open("modules.json", "w") as f:
        json.dump(json_modules, f, indent=4)


def parse_studentplan(path) -> list[Module]:
    pdf = pdfplumber.open(path)

    modules = []
    for page in pdf.pages:
        modules.extend(parse_studentplan_page(page))

    return modules


def parse_studentplan_page(page: Page) -> list[Module]:
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

    modules = []
    for block in blocks:

        # parse rooms
        pattern = r"C\d\d-\d.\d\d"
        rooms = re.findall(pattern, block.text)

        # parse start and end
        block_start = timerange[block.start]
        block_end = timerange[block.end]
        block_day = WEEKDAYS.index(block.day)

        events = []
        for weeknum in weeknums:
            start_str = f"{year} {weeknum} {block_day} {block_start}"
            start = datetime.strptime(start_str, "%Y %W %w %H:%M")

            end_str = f"{year} {weeknum} {block_day} {block_end}"
            end = datetime.strptime(end_str, "%Y %W %w %H:%M")

            event = Event(start, end, rooms)
            events.append(event)

        category = "Vorlesung"
        if any(x in block.text for x in CATEGORY_LAB):
            category = "Labor"
        elif any(x in block.text for x in CATEGORY_EXERCISES):
            category = "Übung"

        module = next((x for x in modules if x.title == degree), None)
        if module:
            module.events.extend(events)
        else:
            module = Module(block.text, category, [(degree, semester, group)], events)
            modules.append(module)

    return modules


if __name__ == "__main__":
    path = "./input/SS_23/"
    studentplans_to_json(path)
