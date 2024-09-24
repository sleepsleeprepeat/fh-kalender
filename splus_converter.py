import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta

from bs4 import BeautifulSoup
import icalendar


INPUT_DIR = "./input/"
OURPUT_DIR = "./output/"


@dataclass
class Event:
    title: str
    titleinfo: str
    extrainfo: str
    start: datetime
    end: datetime
    locations: list[str]
    teachers: list[str]


@dataclass
class Page:
    header: BeautifulSoup
    body: BeautifulSoup
    footer: BeautifulSoup


def convert_daynames(days: str) -> str:
    converted = []
    for day in days.split(", "):
        converted.append(
            {
                "Montag": "Monday",
                "Dienstag": "Tuesday",
                "Mittwoch": "Wednesday",
                "Donnerstag": "Thursday",
                "Freitag": "Friday",
                "Samstag": "Saturday",
                "Sonntag": "Sunday",
            }[day]
        )

    return converted


def convert_weeknumbers(weeknumbers_str: str) -> list[int]:
    if weeknumbers_str.strip() == "":
        return []

    weeknumbers = []
    for block in weeknumbers_str.split(", "):
        if "-" in block:
            start, end = block.split("-")
            weeknumbers.extend(range(int(start), int(end) + 1))
        else:
            weeknumbers.append(int(block))

    return weeknumbers


def convert_year(year_str: str) -> int:
    return int(year_str.split(" ")[1].split("/")[0])


def generate_datetime(year: int, weeknumber: int, day: str, time: str) -> datetime:
    if weeknumber >= 53:
        weeknumber = weeknumber - 52
        year += 1

    date = datetime.strptime(f"{year} {weeknumber} {day}", "%Y %W %A")
    time = datetime.strptime(time, "%H:%M")
    return date + timedelta(hours=time.hour, minutes=time.minute)


def process_page(page: Page) -> list[Event]:
    semester = page.header.find("span", {"class": "header-0-2-0"}).text
    weeknumbers_str = page.header.find("span", {"class": "header-2-0-1"}).text

    cells = page.body.find_all("td", {"class": "object-cell-border"})

    events = []
    for cell in cells:
        # cells are grouped into 3 rows, each containing a table with 3 columns
        cell_rows = cell.find_all("table", recursive=False)

        # top row: comment, info, teacher
        extrainfo = cell_rows[0].find_all("td")[0].text
        titleinfo = cell_rows[0].find_all("td")[1].text
        teacher = cell_rows[0].find_all("td")[2].text

        # middle row: starttime, title, endtime
        starttime = cell_rows[1].find_all("td")[0].text
        title = cell_rows[1].find_all("td")[1].text
        endtime = cell_rows[1].find_all("td")[2].text

        # bottom row: extern roon, weekday, internal room
        external_room = cell_rows[2].find_all("td")[0].text
        weekday_names = cell_rows[2].find_all("td")[1].text
        internal_room = cell_rows[2].find_all("td")[2].text

        # process data
        daynames = convert_daynames(weekday_names)
        weeknumbers = convert_weeknumbers(weeknumbers_str)
        year = convert_year(semester)
        internal_rooms = [r.strip() for r in internal_room.split(",")]
        external_rooms = [r.strip() for r in external_room.split(",")]
        teachers = [t.strip() for t in teacher.split(",")]
        title = title.replace("_", " ").strip()
        titleinfo = titleinfo.replace(" ", "_").strip()
        extrainfo = extrainfo.replace(" ", "_").strip()

        if len(weeknumbers) == 0:
            print(
                "No weeknumbers found:",
                page.header.find("span", {"class": "header-0-0-1"}).text,
            )

        # generate event for each weeknumber
        for weeknumber in weeknumbers:
            for dayname in daynames:
                start = generate_datetime(year, weeknumber, dayname, starttime)
                end = generate_datetime(year, weeknumber, dayname, endtime)
                event = Event(
                    title=title,
                    titleinfo=titleinfo,
                    extrainfo=extrainfo,
                    start=start,
                    end=end,
                    locations=internal_rooms + external_rooms,
                    teachers=teachers,
                )

                if event not in events:
                    events.append(event)

    return events


def process_file(path: str) -> dict[str, list[Event]]:
    html = open(path, "r", encoding="ISO-8859-1").read().replace("&nbsp;", "")
    soup = BeautifulSoup(html, "html.parser")

    # get all tables, group them into pages by pairs of 3 (header, table, footer)
    tables = soup.body.find_all("table", recursive=False)
    pages = [
        Page(
            header=tables[i],
            body=tables[i + 1],
            footer=tables[i + 2],
        )
        for i in range(0, len(tables), 3)
    ]

    courses: dict[str, list[Event]] = {}
    for page in pages:
        # refine page title
        pagetitle = page.header.find("span", {"class": "header-0-0-1"}).text
        pagetitle = pagetitle.replace("/-in", " ").replace(".", " ").replace("-", " ")
        pagetitle = "_".join(pagetitle.split())

        if pagetitle not in courses:
            courses[pagetitle] = []

        courses[pagetitle].extend(process_page(page))

    return courses


def export_ical(path, events: list[Event]):
    cal = icalendar.Calendar()
    cal.add("prodid", "-//Veranstaltungsplan der FH Kiel//fh-kalender.de//")
    cal.add("version", "2.0")

    for event in events:
        locations = filter(None, event.locations)
        teachers = filter(None, event.teachers)
        info = (event.titleinfo + " " + event.extrainfo + " ").strip()

        e = icalendar.Event()
        e.add("summary", event.title)
        e.add("dtstart", event.start)
        e.add("dtend", event.end)
        e.add("location", ", ".join(locations))
        e.add("description", info + ", ".join(teachers))
        e.add("dtstamp", datetime.now())
        e.add("uid", uuid.uuid4())
        cal.add_component(e)

    with open(path, "wb") as f:
        f.write(cal.to_ical())
        f.close()


if __name__ == "__main__":
    for filename in os.listdir(INPUT_DIR):
        if not filename.endswith(".htm"):
            continue
        print(f"Processing", filename)

        courses = process_file(INPUT_DIR + filename)
        for title, events in courses.items():
            export_ical(
                OURPUT_DIR
                + title.replace(" ", "_").replace("/", "_").replace("__", "_")
                + ".ics",
                events,
            )
