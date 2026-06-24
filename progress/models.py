from django.db import models
from projects.models import Project


class Discipline(models.Model):

    name = models.CharField(max_length=100)
    weight = models.DecimalField(max_digits=5,decimal_places=2, null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    
    @property
    def duration(self):
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days
        return None

    def __str__(self):
        return self.name
    

class DisciplineProgress(models.Model):
    project = models.ForeignKey(Project,on_delete=models.CASCADE)
    discipline = models.ForeignKey(Discipline,on_delete=models.CASCADE)
    plan_percentage = models.FloatField()
    actual_percentage = models.FloatField()
    report_date = models.DateField()

    def __str__(self):
        return f"{self.discipline.name} - {self.project.name} ({self.report_date})"


class Activity(models.Model):

    STATUS_CHOICES = [
        ('GREEN', 'In Progress'),
        ('YELLOW', 'Pending'),
        ('RED', 'Completed')
    ]

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE
    )

    activity_name = models.CharField(
        max_length=200
    )

    planned_start = models.DateField()

    planned_finish = models.DateField()

    actual_start = models.DateField(
        null=True,
        blank=True
    )

    actual_finish = models.DateField(
        null=True,
        blank=True
    )

    progress = models.IntegerField(
        default=0
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES
    )

    predecessor = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    def __str__(self):
        return f"{self.activity_name} ({self.project.name})"


class MonthlyProgress(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    month = models.DateField()
    planned_progress = models.FloatField()
    actual_progress = models.FloatField()

    def __str__(self):
        return f"{self.project.name} - {self.month.strftime('%B %Y')}"