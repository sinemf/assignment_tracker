# Assignment Tracker 📚

A cozy, pixel-styled monthly planner for tracking course assignments, built
with Django. Assignments appear on a calendar, color-coded by status, with
progress bars for the day, week, and month, one-click complete toggles, and
export to any calendar app via .ics.

## Features

- Monthly calendar view with previous/next navigation
- Add assignments directly on a date from the calendar
- One-click complete/incomplete toggle; overdue items highlighted in red
- Day / week / month completion progress bars
- Export all assignments to an `.ics` file for Google/Apple/Outlook calendars
- Timezone-aware "today" via a browser-detected timezone cookie
- Print-friendly styling for a PDF copy

## Tech

Django 4.2, SQLite, vanilla HTML/CSS templates (VT323 pixel font), and the
`icalendar` library for the calendar export. Includes a small test suite for
the model, form, and views.

## Run it

```
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Then open http://127.0.0.1:8000/.

Run the tests with:

```
python manage.py test
```
