from datetime import date

from django.test import TestCase
from django.urls import reverse

from .forms import AssignmentForm
from .models import Assignment


class AssignmentModelTests(TestCase):
   def test_str_includes_course_and_title(self):
       assignment = Assignment.objects.create(
           course="OMIS 3730", title="ER Diagram", due_date=date(2026, 10, 1)
       )
       self.assertEqual(str(assignment), "OMIS 3730: ER Diagram")


class AssignmentFormTests(TestCase):
   def test_form_includes_course_field(self):
       self.assertIn("course", AssignmentForm().fields)

   def test_form_rejects_missing_title(self):
       form = AssignmentForm(data={"course": "OMIS 3730", "due_date": "2026-10-01"})
       self.assertFalse(form.is_valid())
       self.assertIn("title", form.errors)


class DashboardViewTests(TestCase):
   def test_dashboard_loads(self):
       response = self.client.get(reverse("dashboard"))
       self.assertEqual(response.status_code, 200)

   def test_dashboard_survives_bad_query_params(self):
       response = self.client.get(reverse("dashboard"), {"year": "abc", "month": "xyz"})
       self.assertEqual(response.status_code, 200)

   def test_dashboard_survives_bad_timezone_cookie(self):
       self.client.cookies["user_timezone"] = "Not/AZone"
       response = self.client.get(reverse("dashboard"))
       self.assertEqual(response.status_code, 200)

   def test_dashboard_shows_assignment_on_its_due_date(self):
       Assignment.objects.create(
           course="OMIS 3730", title="ER Diagram", due_date=date.today()
       )
       response = self.client.get(reverse("dashboard"))
       self.assertContains(response, "ER Diagram")


class AssignmentActionTests(TestCase):
   def setUp(self):
       self.assignment = Assignment.objects.create(
           course="OMIS 3730", title="ER Diagram", due_date=date(2026, 10, 1)
       )

   def test_toggle_complete_flips_status(self):
       self.client.post(reverse("toggle", args=[self.assignment.id]))
       self.assignment.refresh_from_db()
       self.assertTrue(self.assignment.completed)
       self.client.post(reverse("toggle", args=[self.assignment.id]))
       self.assignment.refresh_from_db()
       self.assertFalse(self.assignment.completed)

   def test_toggle_requires_post(self):
       response = self.client.get(reverse("toggle", args=[self.assignment.id]))
       self.assertEqual(response.status_code, 405)

   def test_delete_get_shows_confirmation_page(self):
       response = self.client.get(reverse("delete", args=[self.assignment.id]))
       self.assertEqual(response.status_code, 200)
       self.assertTrue(Assignment.objects.filter(id=self.assignment.id).exists())

   def test_delete_post_removes_assignment(self):
       self.client.post(reverse("delete", args=[self.assignment.id]))
       self.assertFalse(Assignment.objects.filter(id=self.assignment.id).exists())

   def test_edit_unknown_id_returns_404(self):
       response = self.client.get(reverse("edit", args=[9999]))
       self.assertEqual(response.status_code, 404)
