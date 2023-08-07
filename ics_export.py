from dataclasses import dataclass
from datetime import datetime
import icalendar as ical

from extractor import Event


class IcalExporter:
    def __init__(self, filename):
        self.filename = filename
        self.calendar = ical.Calendar()

    def export(self, events: list[Event]):
        for event in events:
            e = ical.Event()
            e.add("summary", event.title)
            e.add("dtstart", event.start)
            e.add("dtend", event.end)
            e.add("location", event.location)
            e.add("description", event.description)
            self.calendar.add_component(e)

        f = open(f"output/{self.filename}.ics", "wb")
        f.write(self.calendar.to_ical())
        f.close()
