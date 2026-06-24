from django.db import models


class Project(models.Model):

    name = models.CharField(max_length=200)
    location = models.CharField(max_length=200)
    client = models.CharField(max_length=200)
    pmc = models.CharField(max_length=200)
    contractor = models.CharField(max_length=200)
    project_type = models.CharField(max_length=200, blank=True)
    start_date = models.DateField()
    target_completion = models.DateField()
    budget = models.DecimalField(
        max_digits=15,
        decimal_places=2
    )
    def __str__(self):
        return self.name
