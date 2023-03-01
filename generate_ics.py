from ics import Calendar, Event
import json

input_file = "output.json"

events = json.load(open(input_file, "r", encoding="utf-8"))

# find unique sources
unique_sources = set()
for event in events:
    s = event["source"].split("[")[0].strip()
    unique_sources.add(s)

print(f"Found {len(unique_sources)} unique sources")

# generate a iCalendar file for each source
for source in unique_sources:
    event_data = {}

    cal = Calendar()
    for event in events:
        if source in event["source"]:
            event_data = event
            e = Event()
            e.name = event["title"]
            e.begin = event["start"]
            e.end = event["end"]
            e.location = ", ".join(event["rooms"])
            cal.events.add(e)

    degree = event_data["degree"]

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
        degree = "mecha"

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

    group = event_data["group"]
    if group == "0":
        group = ""
    else:
        group = f"_{group}"

    file_name = event_data["semester"] + "_" + degree + group
    with open(f"output/{file_name}.ics", "w", encoding="utf-8") as f:
        f.writelines(cal)
