from django.db import models
from projects.models import Project

class CashFlow(models.Model):

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE
    )

    month = models.DateField()

    planned_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2
    )

    actual_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2
    )

    def __str__(self):
        return f"{self.project.name} - {self.month.strftime('%B %Y')}"