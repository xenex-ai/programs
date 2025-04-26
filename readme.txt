
==================================================================
                         MasterShell
------------------------------------------------------------------
Interaktive Steuerung mehrerer Python-Skripte in je eigener Session
==================================================================
Ausführung
---------------
Install library --> pip install -r requirements.txt
start master --> chmod +x mastershell.py


Voraussetzungen
---------------
- Python 3.7 oder neuer
- colorama (für farbige Ausgabe):
    pip install colorama

Installation
------------
1. Repository klonen oder Dateien kopieren.
2. mastershell.py ins Arbeits-Verzeichnis legen.
3. Ordnerstruktur:
     .
     ├── mastershell.py
     ├── programm1/
     │   └── app.py
     ├── programm2/
     │   └── run.py
     └── programm3/
         └── start.py

Anpassung
---------
- In mastershell.py kannst du im DICT `PROGRAMS` eigene Prozess-Namen und Pfade zu deinen Skripten anpassen.
- Beispiel:
    PROGRAMS = {
        "worker": Path("tasks/worker.py"),
        "bot":    Path("bots/telegram_bot.py"),
    }

Verwendung
----------
1. Starte die Master-Shell:
     ./mastershell.py
   oder
     python mastershell.py

2. Es öffnet sich die Eingabeaufforderung:
     MasterShell> 

3. Befehle senden:
     <prozessname> <nachricht>
   z.B.:
     prog1 status
     prog2 hello world
     prog3 exit

4. Tab-Completion für Prozess-Namen (drücke Tab).
5. Command-History mit ↑/↓ (wird in ~/.mastershell_history gespeichert).

Beenden
-------
- Tippe `exit` oder drücke Strg-D (EOF).
- Oder Strg-C (SIGINT) für einen sauberen Shutdown aller Subprozesse.

Features
--------
- **Farbcodes** für bessere Lesbarkeit:
  - Cyan: Prozess gestartet
  - Gelb: Ausgabe der Subprozesse
  - Magenta: Prozess beendet
  - Grün/Rot: Eingabe-Aufforderungen und Fehler
- **Thread-basierte** Ausgabe-Leser, damit alle Logs live angezeigt werden
- **Graceful Shutdown**: Prozesse werden erst terminiert, nach 5 Sek. ggf. zwangsabgebrochen
- **Tab-Completion** und **History**, damit du schneller tippen kannst

Troubleshooting
---------------
- „ModuleNotFoundError: No module named 'colorama'“
  → `pip install colorama`
- „Skript nicht gefunden“
  → Pfade in `PROGRAMS` prüfen, relative zum Ordner von mastershell.py
- Keine Ausgabe?
  → Stelle sicher, dass deine Subskripte `print()` verwenden oder stdin per `input()` abfragen.

Viel Spaß beim Orchestrieren deiner Python-Sessions!
