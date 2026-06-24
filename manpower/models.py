from django.db import models
from projects.models import Project

class Manpower(models.Model):

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE
    )

    skilled = models.IntegerField()

    semi_skilled = models.IntegerField()

    unskilled = models.IntegerField()

    engineers = models.IntegerField()

    report_date = models.DateField()

    def __str__(self):
        return f"{self.project.name} - Manpower ({self.report_date})"