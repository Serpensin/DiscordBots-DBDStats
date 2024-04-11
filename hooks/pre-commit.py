#!/usr/bin/env python
import subprocess
import sys

# Funktion zur Ausf�hrung von Git-Befehlen
def git(*args):
    return subprocess.check_call(['git'] + list(args))

# �berpr�fung, ob das aktuelle Branch der master-Branch ist
def is_master_branch():
    # Hole den aktuell gepushten Branch
    current_branch = subprocess.check_output(['git', 'symbolic-ref', '--short', 'HEAD']).strip().decode('utf-8')

    return current_branch == 'master'

# Hauptfunktion zur �berpr�fung der Variablen
def check_variables():
    # �berpr�fe, ob das aktuelle Branch der master-Branch ist
    if not is_master_branch():
        return

    # �berpr�fe NO_CACHE
    with open('main.py', 'r') as file:
        content = file.read()
        if 'NO_CACHE = False' not in content:
            print("ERROR: Variable 'NO_CACHE' must be set to False in main.py for committing to master branch.")
            sys.exit(1)

    # �berpr�fe connection_string
    expected_connection_string = "f'mongodb://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}'"

    with open('main.py', 'r') as file:
        content = file.read()
        if expected_connection_string not in content:
            print("ERROR: 'connection_string' must be correctly formatted in main.py for committing to master branch.")
            sys.exit(1)

# F�hre die �berpr�fungen aus
check_variables()
