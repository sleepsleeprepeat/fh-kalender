import sqlite3


def generate_clean_table():
    # create table for cleaned events
    cur.execute("DROP TABLE IF EXISTS events_clean")
    cur.execute(
        "CREATE TABLE IF NOT EXISTS events_clean (id INTEGER PRIMARY KEY, title TEXT, category TEXT, degree TEXT, semester TEXT, sem_group TEXT, start DATETIME, end DATETIME, room1 TEXT, room2 TEXT, room3 TEXT, room4 TEXT, room5 TEXT, source TEXT)"
    )

    # copy over events to new table
    cur.execute("SELECT * FROM events")
    for event in cur.fetchall():
        cur.execute(
            "INSERT INTO events_clean (title, category, degree, semester, sem_group, start, end, room1, room2, room3, room4, room5, source) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            event[1:],
        )


def export_titles():
    with open("titles_old.txt", "w", encoding="utf-8") as f:
        cur.execute("SELECT DISTINCT title FROM events")
        for title in cur.fetchall():
            f.write(title[0].replace("\n", " ").strip() + "\n")


def replace_titles():
    with open("titles_old.txt", "r", encoding="utf-8") as f:
        titles = f.readlines()

    with open("titles_new.txt", "r", encoding="utf-8") as f:
        new_titles = f.readlines()

    for i in range(len(titles)):
        titles[i] = titles[i].strip()
        new_titles[i] = new_titles[i].strip()

    # get all events
    cur.execute("SELECT * FROM events_clean")
    events = cur.fetchall()

    # replace titles
    for idx, event in enumerate(len(events)):
        striped_title = event[1].replace("\n", " ").strip()
        events[idx][1] = new_titles[titles.index(event[1])]
        cur.execute(
            "UPDATE events_clean SET title = ? WHERE id = ?",
            (events[idx][1], events[idx][0]),
        )


if __name__ == "__main__":
    # connect to database
    con = sqlite3.connect("fh.db")
    cur = con.cursor()

    # generate_clean_table()

    # export all uqique titles to a file
    # export_titles()

    # replace titles
    replace_titles()

    # commit changes
    con.commit()
    con.close()
