#!/usr/bin/env python3
"""
mastershell.py

Starte und verwalte mehrere Python-Subprozesse mit interaktiver Ein-/Ausgabe,
Command-History, Tab-Completion und farbiger Ausgabe.
"""

import sys
import signal
import threading
import subprocess
from pathlib import Path

# Farbe in Konsole: pip install colorama
try:
    from colorama import init, Fore, Style
except ImportError:
    print("✖ Bitte installiere colorama: pip install colorama")
    sys.exit(1)

import readline
import atexit

# === Konfiguration ===
# Prozess-Namen und zugehörige Skript-Pfade (relativ zum Arbeitsordner)
PROGRAMS = {
    "prog1": Path("programm1/app.py"),
    "prog2": Path("programm2/run.py"),
    "prog3": Path("programm3/start.py"),
}

HISTORY_FILE = Path.home() / ".mastershell_history"
PROMPT = Fore.GREEN + "MasterShell> " + Style.RESET_ALL

# === Setup Command-History & Tab-Completion ===
def setup_readline():
    try:
        readline.read_history_file(str(HISTORY_FILE))
    except FileNotFoundError:
        pass
    readline.set_history_length(1000)
    atexit.register(readline.write_history_file, str(HISTORY_FILE))

    def completer(text, state):
        options = [name for name in PROGRAMS if name.startswith(text)]
        if state < len(options):
            return options[state] + " "
        return None

    readline.set_completer(completer)
    readline.parse_and_bind("tab: complete")

# === Ausgabe-Leser für jede Session ===
def reader_thread(name, proc):
    for line in proc.stdout:
        print(f"{Fore.YELLOW}[{name}]{Style.RESET_ALL} {line.rstrip()}")
    print(f"{Fore.MAGENTA}[Info] Prozess '{name}' beendet (Exit-Code {proc.returncode}){Style.RESET_ALL}")

# === Prozesse starten ===
def spawn_processes():
    procs = {}
    for name, script in PROGRAMS.items():
        if not script.exists():
            print(f"{Fore.RED}[Error] Skript nicht gefunden: {script}{Style.RESET_ALL}")
            continue
        cmd = [sys.executable, str(script)]
        p = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        procs[name] = p
        threading.Thread(target=reader_thread, args=(name, p), daemon=True).start()
        print(f"{Fore.CYAN}[Info] Gestartet '{name}': {' '.join(cmd)}{Style.RESET_ALL}")
    return procs

# === Sanfter Shutdown aller Subprozesse ===
def shutdown(procs):
    print(Fore.CYAN + "\nShutting down processes…" + Style.RESET_ALL)
    for name, p in procs.items():
        if p.poll() is None:
            print(f"[{name}] terminate…")
            p.terminate()
    for name, p in procs.items():
        try:
            p.wait(timeout=5)
        except subprocess.TimeoutExpired:
            print(f"[{name}] kill!")
            p.kill()
    print(Fore.CYAN + "All processes terminated." + Style.RESET_ALL)

# === Hauptprogramm ===
def main():
    # Farbausgabe initialisieren
    init(autoreset=True)
    setup_readline()

    procs = spawn_processes()
    if not procs:
        print(Fore.RED + "Keine Prozesse zum Starten. Bitte PROGRAMS prüfen." + Style.RESET_ALL)
        sys.exit(1)

    print(Fore.GREEN + "\nGib ein: '<prozessname> <nachricht>'    (z.B. 'prog1 hallo welt')")
    print("Type 'exit' or Ctrl-D to quit.\n" + Style.RESET_ALL)

    try:
        while True:
            try:
                line = input(PROMPT).strip()
            except EOFError:
                break

            if not line:
                continue
            if line.lower() in ("exit", "quit"):
                break

            parts = line.split(" ", 1)
            if len(parts) != 2:
                print(Fore.RED + "Ungültiges Format. Nutze: '<prozessname> <nachricht>'" + Style.RESET_ALL)
                continue

            name, msg = parts
            if name not in procs:
                print(Fore.RED + f"Unbekannter Prozess: '{name}'" + Style.RESET_ALL)
                continue

            p = procs[name]
            if p.poll() is not None:
                print(Fore.RED + f"Prozess '{name}' ist nicht mehr aktiv." + Style.RESET_ALL)
                continue

            try:
                p.stdin.write(msg + "\n")
                p.stdin.flush()
            except Exception as e:
                print(Fore.RED + f"Fehler beim Senden an '{name}': {e}" + Style.RESET_ALL)

    except KeyboardInterrupt:
        pass
    finally:
        shutdown(procs)

if __name__ == "__main__":
    main()
