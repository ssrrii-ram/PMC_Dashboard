from django.contrib import admin

from .models import Activity, Discipline, DisciplineProgress, MonthlyProgress


admin.site.register(Discipline)
admin.site.register(DisciplineProgress)
admin.site.register(Activity)
admin.site.register(MonthlyProgress)
