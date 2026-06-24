from django.db import models
from projects.models import Project


class SitePhoto(models.Model):

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE
    )

    title = models.CharField(
        max_length=200
    )

    image = models.ImageField(
        upload_to='site_photos/'
    )

    remarks = models.TextField()

    uploaded_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.title} ({self.project.name})"