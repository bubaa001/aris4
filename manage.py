#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

# Must be at module level so Windows spawn-based multiprocessing
# (used by django-q2's qcluster) inherits it in worker processes.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ONLportal.settings')


def main():
    """Run administrative tasks."""
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    # runserver defaults:
    #   python manage.py runserver           → 127.0.0.1:8000 (local only)
    #   python manage.py runserver --ngrok   → 0.0.0.0:80 (for ngrok tunnel)
    argv = list(sys.argv)
    if len(argv) >= 2 and argv[1] == 'runserver':
        if '--ngrok' in argv:
            argv.remove('--ngrok')
            if len(argv) == 2:
                argv.append('0.0.0.0:80')
        elif len(argv) == 2:
            argv.append('127.0.0.1:8000')

    execute_from_command_line(argv)


if __name__ == '__main__':
    main()
