#!/usr/bin/env python
"""Django management script for the SafeHaul frontend standalone project."""
import os
import sys


def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'frontend_project.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Could not import Django. Make sure it is installed: pip install django"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
