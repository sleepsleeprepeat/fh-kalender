from dataclasses import dataclass
from datetime import datetime
import os
from bs4 import BeautifulSoup

from ics_export import IcalExporter
from extractor import Page, Event
from student_parser import PageParser


def process_file(path: str) -> dict[str, list[Event]]:
    html = open(path, "r", encoding="ISO-8859-1").read().replace("&nbsp;", "")
    soup = BeautifulSoup(html, "html.parser")

    # get all tables, group them into pages by pairs of 3 (header, table, footer)
    tables = soup.body.find_all("table", recursive=False)
    pages = [Page(tables[i : i + 3]) for i in range(0, len(tables), 3)]

    groups: dict[str, list[Event]] = {}
    for page in pages:
        title = page.header.get_pagetitle()
        title = title.replace("/-in", " ").replace(".", " ").replace("-", " ")
        title = "_".join(title.split())

        if title not in groups:
            groups[title] = []

        groups[title].extend(PageParser(page).get_events())

    return groups


if __name__ == "__main__":
    for filename in os.listdir("input"):
        if not filename.endswith(".htm"):
            continue

        print(f"Processing {filename}")
        groups = process_file("input/" + filename)

        for title, events in groups.items():
            IcalExporter(title.replace(" ", "_")).export(events)
