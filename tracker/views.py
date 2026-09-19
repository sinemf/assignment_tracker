from datetime import date, timedelta, datetime
from calendar import Calendar, monthrange
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.views.decorators.http import require_POST
from icalendar import Calendar as iCalendar, Event
from django.utils.timezone import now as django_now
from zoneinfo import ZoneInfo
from .models import Assignment
from .forms import AssignmentForm




def dashboard(request):
   tz_name = request.COOKIES.get('user_timezone', 'UTC')
   try:
       tz = ZoneInfo(tz_name)
   except (KeyError, ValueError):
       tz = ZoneInfo('UTC')
   now = django_now().astimezone(tz)
   today = now.date()


   # Get selected month and year from query params, or default to current
   try:
       year = int(request.GET.get('year', today.year))
       month = int(request.GET.get('month', today.month))
   except (TypeError, ValueError):
       year, month = today.year, today.month


   if month > 12:
       month = 1
       year += 1
   elif month < 1:
       month = 12
       year -= 1


   start_of_month = date(year, month, 1)
   end_of_month = date(year, month, monthrange(year, month)[1])


   # One query for the whole month, grouped by day (avoids a query per calendar cell)
   month_assignments = Assignment.objects.filter(due_date__range=(start_of_month, end_of_month))
   assignments_by_day = {}
   for assignment in month_assignments:
       assignments_by_day.setdefault(assignment.due_date, []).append(assignment)


   cal = Calendar(firstweekday=0)
   calendar_weeks = []
   for week in cal.monthdatescalendar(year, month):
       week_data = []
       for day in week:
           if day.month == month:
               week_data.append({
                   'day': day,
                   'assignments': assignments_by_day.get(day, []),
               })
           else:
               week_data.append(None)
       calendar_weeks.append(week_data)


   def get_progress(qs):
       total = qs.count()
       done = qs.filter(completed=True).count()
       return (done / total * 100) if total > 0 else 0


   start_of_week = today - timedelta(days=today.weekday())
   end_of_week = start_of_week + timedelta(days=6)
   week_assignments = Assignment.objects.filter(due_date__range=(start_of_week, end_of_week))
   day_assignments = Assignment.objects.filter(due_date=today)


   context = {
       'calendar_weeks': calendar_weeks,
       'month_progress': get_progress(month_assignments),
       'week_progress': get_progress(week_assignments),
       'day_progress': get_progress(day_assignments),
       'today': today,
       'current_month': month,
       'current_year': year,
   }


   return render(request, 'dashboard.html', context)




def add_assignment(request):
   if request.method == 'POST':
       form = AssignmentForm(request.POST)
       if form.is_valid():
           form.save()
           return redirect('dashboard')
   else:
       form = AssignmentForm()


   return render(request, 'add_assignment.html', {'form': form})




def add_assignment_with_date(request, due_date):
   if isinstance(due_date, str):
       due_date_obj = datetime.strptime(due_date, "%Y-%m-%d").date()
   else:
       due_date_obj = due_date


   if request.method == 'POST':
       form = AssignmentForm(request.POST)
       if form.is_valid():
           assignment = form.save(commit=False)
           assignment.due_date = due_date_obj
           assignment.save()
           return redirect('dashboard')
   else:
       form = AssignmentForm(initial={'due_date': due_date_obj})


   return render(request, 'add_assignment.html', {'form': form})




def edit_assignment(request, id):
   assignment = get_object_or_404(Assignment, id=id)
   if request.method == 'POST':
       form = AssignmentForm(request.POST, instance=assignment)
       if form.is_valid():
           form.save()
           return redirect('dashboard')
   else:
       form = AssignmentForm(instance=assignment)


   return render(request, 'edit_assignment.html', {'form': form, 'assignment': assignment})




@require_POST
def toggle_complete(request, id):
   assignment = get_object_or_404(Assignment, id=id)
   assignment.completed = not assignment.completed
   assignment.save()
   return redirect('dashboard')




@require_POST
def delete_assignment(request, id):
   assignment = get_object_or_404(Assignment, id=id)
   assignment.delete()
   return redirect('dashboard')




def export_calendar(request):
   cal = iCalendar()
   cal.add('prodid', '-//Assignment Tracker//')
   cal.add('version', '2.0')


   assignments = Assignment.objects.all()
   for assignment in assignments:
       event = Event()
       event.add('summary', f"{assignment.course}: {assignment.title}" if assignment.course else assignment.title)
       event.add('description', assignment.description or "")
       event.add('dtstart', assignment.due_date)
       event.add('dtend', assignment.due_date)
       event.add('dtstamp', django_now())
       cal.add_component(event)


   response = HttpResponse(cal.to_ical(), content_type='text/calendar')
   response['Content-Disposition'] = 'attachment; filename=assignments.ics'
   return response
