#!/usr/bin/env python
import subprocess
import sys

# Funktion zur Ausführung von Git-Befehlen
def git(*args):
    return subprocess.check_call(['git'] + list(args))

# Überprüfung, ob das aktuelle Branch der master-Branch ist
def is_master_branch():
    # Hole den aktuell gepushten Branch
    current_branch = subprocess.check_output(['git', 'symbolic-ref', '--short', 'HEAD']).strip().decode('utf-8')

    return current_branch == 'master'

# Hauptfunktion zur Überprüfung der Variablen
def check_variables():
    # Überprüfe, ob das aktuelle Branch der master-Branch ist
    if not is_master_branch():
        return

    # Überprüfe NO_CACHE
    with open('main.py', 'r') as file:
        content = file.read()
        if 'NO_CACHE = False' not in content:
            print("ERROR: Variable 'NO_CACHE' must be set to False in main.py for committing to master branch.")
            sys.exit(1)

    # Überprüfe connection_string
    expected_connection_string = "f'mongodb://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}'"

    with open('main.py', 'r') as file:
        content = file.read()
        if expected_connection_string not in content:
            print("ERROR: 'connection_string' must be correctly formatted in main.py for committing to master branch.")
            sys.exit(1)

# Führe die Überprüfungen aus
check_variables()
