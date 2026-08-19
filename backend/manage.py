#!/usr/bin/env python
import os
import sys
from pathlib import Path


def main():
    # Les commandes doivent se comporter de façon identique depuis la racine
    # du dépôt ou depuis backend/. Sans cela, Django ne découvre aucun test
    # lorsqu'on lance `python backend/manage.py test` depuis la racine.
    os.chdir(Path(__file__).resolve().parent)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
