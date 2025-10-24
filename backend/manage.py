#!/usr/bin/env python
import os
import sys


def main():
    base_dir = os.path.dirname(__file__)
    project_path = os.path.join(base_dir, 'app')
    if project_path not in sys.path:
        sys.path.insert(0, project_path)

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
