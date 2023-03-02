from dataclasses import dataclass
from datetime import datetime, timedelta
import os
import sqlite3
from ics import Calendar, Event


@dataclass
class FhEvent:
    id: int
    title: str
    category: str
    degree: str
    semester: str
    group: str
    start: datetime
    end: datetime
    rooms: list[str]
    source: str


# create folder for ics files
if not os.path.exists("output"):
    os.makedirs("output")

con = sqlite3.connect("output.db")
cur = con.cursor()

# get all events
cur.execute("SELECT * FROM events")

# convert to Event objects
events: list[FhEvent] = []
for event in cur.fetchall():
    events.append(
        FhEvent(
            id=event[0],
            title=event[1],
            category=event[2],
            degree=event[3],
            semester=event[4],
            group=event[5],
            start=datetime.strptime(event[6], "%Y-%m-%d %H:%M:%S"),
            end=datetime.strptime(event[7], "%Y-%m-%d %H:%M:%S"),
            rooms=[event[8], event[9], event[10], event[11], event[12]],
            source=event[13],
        )
    )

# find all unique combinations of semester, degree and group
unique_sources = set()
for event in events:
    unique_sources.add((event.semester, event.degree, event.group))

# generate one ical file per unique combination
for source in unique_sources:
    cal = Calendar()
    for event in events:
        if (
            event.semester == source[0]
            and event.degree == source[1]
            and event.group == source[2]
        ):
            rooms = []
            for room in event.rooms:
                if room:
                    rooms.append(room)

            e = Event()
            e.name = event.title
            e.begin = event.start
            e.end = event.end
            e.location = ", ".join(rooms)
            cal.events.add(e)

    degree = source[1]
    if degree.startswith("Elektrotechnik"):
        if "Energie" in degree:
            degree = "e-technik_e"
        elif "Informatik" in degree:
            degree = "e-technik_i"
        elif "Kommunikation" in degree:
            degree = "e-technik_k"
        else:
            degree = "e-technik"

    if degree.startswith("Informatik"):
        if "AE" in degree:
            degree = "inf_ae"
        elif "KI" in degree:
            degree = "inf_ki"
        else:
            degree = "inf"
    if degree.startswith("Mechatronik"):
        degree = "mech"

    if degree.startswith("Wirtschaftsingenieurwesen"):
        if "DW" in degree:
            degree = "wing_dw"
        elif "NE" in degree:
            degree = "wing_ne"
        elif "Kommunikation" in degree:
            degree = "wing_k"
        else:
            degree = "wing"

    if degree.startswith("Medieningenieur"):
        degree = "ming"

    file_name = source[0] + "_" + degree + "_" + source[2]
    with open(f"output/{file_name}.ics", "w", encoding="utf-8") as f:
        f.writelines(cal)
