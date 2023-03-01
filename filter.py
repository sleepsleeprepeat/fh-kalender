import sqlite3
import json

con = sqlite3.connect("output.db")
cur = con.cursor()

# get all events
cur.execute("SELECT * FROM events")
events = cur.fetchall()

json_events = []

for event in events:
    # convert to dict
    event = {
        "id": event[0],
        "title": event[1],
        "category": event[2],
        "degree": event[3],
        "semester": event[4],
        "group": event[5],
        "start": event[6],
        "end": event[7],
        "rooms": [event[8], event[9], event[10], event[11], event[12]],
        "source": event[13],
    }

    # remove empty rooms
    event["rooms"] = [room for room in event["rooms"] if room]

    json_events.append(event)

# save to json
with open("output.json", "w", encoding="utf-8") as f:
    json.dump(json_events, f, ensure_ascii=False, indent=4)


con.close()
