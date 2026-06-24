from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from projects.models import Project
from manpower.models import Manpower
import datetime

class DashboardDataEntryTests(TestCase):
    def setUp(self):
        # Create user
        self.username = "testuser"
        self.password = "password123"
        self.user = User.objects.create_user(username=self.username, password=self.password)
        
        # Create a sample project
        self.project = Project.objects.create(
            name="Test Project",
            location="Test Location",
            client="Test Client",
            pmc="Test PMC",
            contractor="Test Contractor",
            project_type="Civil",
            start_date=datetime.date(2026, 1, 1),
            target_completion=datetime.date(2026, 12, 31),
            budget=100000.00
        )
        
        # Create a manpower entry
        self.manpower = Manpower.objects.create(
            project=self.project,
            skilled=10,
            semi_skilled=20,
            unskilled=30,
            engineers=5,
            report_date=datetime.date(2026, 6, 21)
        )

    def test_anonymous_redirected_from_data_entry(self):
        response = self.client.get(reverse("dashboard:data_entry"))
        self.assertRedirects(response, f"/accounts/login/?next={reverse('dashboard:data_entry')}")

    def test_authenticated_can_view_data_entry_with_records(self):
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(reverse("dashboard:data_entry"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Project")
        self.assertContains(response, "Existing Manpower Entries")
        # Check if the manpower count columns are displayed
        self.assertContains(response, "10")
        self.assertContains(response, "20")
        self.assertContains(response, "30")

    def test_edit_manpower_entry_get(self):
        self.client.login(username=self.username, password=self.password)
        url = reverse("dashboard:edit_entry", kwargs={"model_name": "manpower", "pk": self.manpower.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Edit Manpower")
        self.assertContains(response, 'value="10"')  # Skilled input should be pre-filled

    def test_edit_manpower_entry_post(self):
        self.client.login(username=self.username, password=self.password)
        url = reverse("dashboard:edit_entry", kwargs={"model_name": "manpower", "pk": self.manpower.pk})
        data = {
            "project": self.project.pk,
            "skilled": 50,  # updated from 10 to 50
            "semi_skilled": 20,
            "unskilled": 30,
            "engineers": 5,
            "report_date": "2026-06-21"
        }
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse("dashboard:data_entry"))
        self.manpower.refresh_from_db()
        self.assertEqual(self.manpower.skilled, 50)

    def test_delete_manpower_entry_get(self):
        self.client.login(username=self.username, password=self.password)
        url = reverse("dashboard:delete_entry", kwargs={"model_name": "manpower", "pk": self.manpower.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Delete Manpower")
        self.assertContains(response, "Test Project &mdash; Manpower Report")

    def test_delete_manpower_entry_post(self):
        self.client.login(username=self.username, password=self.password)
        url = reverse("dashboard:delete_entry", kwargs={"model_name": "manpower", "pk": self.manpower.pk})
        response = self.client.post(url)
        self.assertRedirects(response, reverse("dashboard:data_entry"))
        self.assertFalse(Manpower.objects.filter(pk=self.manpower.pk).exists())
