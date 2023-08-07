# FH-Kalender 
Dieses Projekt ist ein kleines Python Script, welches den Stundenplan der FH Kiel in einen Kalender exportiert.

Es handelt sich nicht um ein offizielles Projekt der FH Kiel. Die hier erstellten Kalender sind nicht offiziell und können Fehler enthalten.

## Input Format
Der Export aus S-Plus erfolgt mit der `HTML/CSS` Option. Die werden in den Ordner `input` gespeichert. 

## Output Format
Der Output ist ein `ics` File, welches in den Ordner `output` gespeichert wird.

Andere Formate sind möglich, aber nicht implementiert.

## Usage
```bash
python main.py
```

## Dependencies
- Python 3.11+
- icalendar
- bs4