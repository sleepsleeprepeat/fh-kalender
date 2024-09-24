import os
import sys


def main(path: str, filenames: bool = False) -> None:
    try:
        if not os.path.exists(path):
            print("Der angegebene Pfad existiert nicht.")
            return
        if not os.path.isdir(path):
            print("Der angegebene Pfad ist kein Ordner.")
            return

        if filenames:
            print("Dateinamen:")
            for filename in os.listdir(path):
                print(filename)
        else:
            for filename in os.listdir(path):
                print(filename.replace(".ics", "").replace("_", ". "))

    except Exception as e:
        print("Ein Fehler ist aufgetreten:", e)

    pass


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Bitte geben Sie den Pfad zu einem Ordner an. (-f für die Dateinamen)")
    else:
        path = sys.argv[1]
        filenames = False
        if len(sys.argv) > 2 and sys.argv[2] == "-f":
            filenames = True
        main(path, filenames)
