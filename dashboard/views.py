from decimal import Decimal

from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.db.models import Avg, Count, Sum
from django.shortcuts import redirect, render, get_object_or_404
from django.utils import timezone

from dashboard.forms import UserProfileForm, UserPasswordChangeForm
from finance.forms import CashFlowForm
from finance.models import CashFlow
from manpower.forms import ManpowerForm
from manpower.models import Manpower
from photos.forms import SitePhotoForm
from photos.models import SitePhoto
from progress.forms import ActivityForm, DisciplineForm, DisciplineProgressForm, MonthlyProgressForm
from progress.models import Activity, Discipline, DisciplineProgress, MonthlyProgress
from projects.forms import ProjectForm
from projects.models import Project


def _money(value):
    return value or Decimal("0")


def _percent(value):
    if value is None:
        return 0
    return round(float(value), 1)


def _status_class(status):
    return {
        "GREEN": "green",
        "YELLOW": "yellow",
        "RED": "red",
    }.get(status, "gray")


def _gantt_rows(activity_qs):
    activities = list(activity_qs.order_by("planned_start", "planned_finish")[:10])
    dated_activities = [
        activity for activity in activities if activity.planned_start and activity.planned_finish
    ]
    if not dated_activities:
        return []

    start = min(activity.planned_start for activity in dated_activities)
    finish = max(activity.planned_finish for activity in dated_activities)
    total_days = max((finish - start).days + 1, 1)

    rows = []
    for activity in dated_activities:
        offset = max((activity.planned_start - start).days, 0)
        duration = max((activity.planned_finish - activity.planned_start).days + 1, 1)
        rows.append(
            {
                "name": activity.activity_name,
                "start": activity.planned_start,
                "finish": activity.planned_finish,
                "progress": activity.progress,
                "status_class": _status_class(activity.status),
                "left": round((offset / total_days) * 100, 2),
                "width": max(round((duration / total_days) * 100, 2), 3),
            }
        )
    return rows


@login_required
def dashboard(request):
    today = timezone.localdate()

    projects = Project.objects.all().order_by("name")
    selected_project_id = request.GET.get("project")
    project = None
    if selected_project_id:
        project = projects.filter(id=selected_project_id).first()
    if project is None:
        project = projects.first()

    activity_qs = Activity.objects.none()
    discipline_qs = DisciplineProgress.objects.none()
    cash_qs = CashFlow.objects.none()
    photos_qs = SitePhoto.objects.none()
    latest_manpower = None

    if project:
        activity_qs = Activity.objects.filter(project=project)
        discipline_qs = DisciplineProgress.objects.filter(project=project).select_related("discipline")
        cash_qs = CashFlow.objects.filter(project=project).order_by("month")
        photos_qs = SitePhoto.objects.filter(project=project).order_by("-uploaded_at")
        latest_manpower = Manpower.objects.filter(project=project).order_by("-report_date").first()

    latest_progress = MonthlyProgress.objects.filter(project=project).order_by("-month").first() if project else None
    activity_progress = activity_qs.aggregate(avg=Avg("progress"))["avg"]
    planned_progress = _percent(latest_progress.planned_progress if latest_progress else None)
    actual_progress = _percent(latest_progress.actual_progress if latest_progress else activity_progress)
    spi = round(actual_progress / planned_progress, 2) if planned_progress else 0

    cash_flow = cash_qs.aggregate(
        planned=Sum("planned_amount"),
        actual=Sum("actual_amount"),
    )
    planned_cash = _money(cash_flow["planned"])
    actual_cash = _money(cash_flow["actual"])
    cpi = round(float(planned_cash / actual_cash), 2) if actual_cash else 0

    status_counts = dict(
        activity_qs.values("status").annotate(total=Count("id")).values_list("status", "total")
    )
    activity_total = sum(status_counts.values())

    manpower = {
        "skilled": latest_manpower.skilled if latest_manpower else 0,
        "semi_skilled": latest_manpower.semi_skilled if latest_manpower else 0,
        "unskilled": latest_manpower.unskilled if latest_manpower else 0,
        "engineers": latest_manpower.engineers if latest_manpower else 0,
    }
    manpower_total = sum(manpower.values())

    # Calculate percentages for the donut chart conic-gradient
    m_total = manpower_total or 1
    p_skilled = round((manpower["skilled"] / m_total) * 100, 1)
    p_semi_skilled_end = round(((manpower["skilled"] + manpower["semi_skilled"]) / m_total) * 100, 1)
    p_unskilled_end = round(((manpower["skilled"] + manpower["semi_skilled"] + manpower["unskilled"]) / m_total) * 100, 1)

    discipline_rows = []
    for row in discipline_qs.order_by("discipline__name", "-report_date"):
        variance = round(float(row.actual_percentage - row.plan_percentage), 1)
        status = "GREEN" if variance >= 0 else "YELLOW" if variance >= -5 else "RED"
        
        start_date = row.discipline.start_date
        end_date = row.discipline.end_date
        duration = (end_date - start_date).days if start_date and end_date else None

        discipline_rows.append(
            {
                "discipline": row.discipline.name,
                "start_date": start_date,
                "end_date": end_date,
                "duration": duration,
                "planned": _percent(row.plan_percentage),
                "actual": _percent(row.actual_percentage),
                "status": status,
                "status_class": _status_class(status),
            }
        )

    cash_rows = [
        {
            "month": row.month,
            "planned": row.planned_amount,
            "actual": row.actual_amount,
            "planned_width": min(int((row.planned_amount / planned_cash) * 100), 100) if planned_cash else 0,
            "actual_width": min(int((row.actual_amount / planned_cash) * 100), 100) if planned_cash else 0,
        }
        for row in cash_qs[:12]
    ]

    status_cards = []
    for item in [
        ("GREEN", "In Progress"),
        ("YELLOW", "Pending"),
        ("RED", "Completed"),
    ]:
        count = status_counts.get(item[0], 0)
        status_cards.append(
            {
                "label": item[1],
                "count": count,
                "percent": round((count / activity_total) * 100) if activity_total else 0,
                "class": _status_class(item[0]),
            }
        )

    context = {
        "today": today,
        "project": project,
        "projects": projects,
        "selected_project_id": project.id if project else None,
        "stats": {
            "project_count": projects.count(),
            "planned_progress": planned_progress,
            "actual_progress": actual_progress,
            "spi": spi,
            "cpi": cpi,
            "activity_total": activity_total,
            "manpower_total": manpower_total,
            "planned_cash": planned_cash,
            "actual_cash": actual_cash,
        },
        "status_cards": status_cards,
        "discipline_rows": discipline_rows,
        "gantt_rows": _gantt_rows(activity_qs),
        "cash_rows": cash_rows,
        "recent_photos": photos_qs,
        "manpower": manpower,
        "manpower_chart": {
            "p_skilled": p_skilled,
            "p_semi_skilled_end": p_semi_skilled_end,
            "p_unskilled_end": p_unskilled_end,
            "has_data": manpower_total > 0,
        },
    }
    return render(request, "dashboard/dashboard.html", context)


@login_required
def data_entry(request):
    form_classes = {
        "project": ("Project", "Set up the core project profile shown in the dashboard header.", ProjectForm),
        "discipline": ("Discipline / Area", "Create work areas such as Civil, Piping, Electrical, and Utilities.", DisciplineForm),
        "discipline_progress": ("Discipline Progress", "Record planned and actual progress for each work area.", DisciplineProgressForm),
        "monthly_progress": ("Monthly Progress", "Update project-level planned and actual progress for SPI and summary KPIs.", MonthlyProgressForm),
        "activity": ("Activity", "Add schedule activities that drive the Gantt chart and status summary.", ActivityForm),
        "cash_flow": ("Cash Flow", "Feed planned and actual financial progress for management review.", CashFlowForm),
        "manpower": ("Manpower", "Capture the latest manpower split visible on the dashboard.", ManpowerForm),
        "site_photo": ("Site Photo", "Upload site progress photos that can be enlarged from the dashboard.", SitePhotoForm),
    }

    models_mapping = {
        "project": Project,
        "discipline": Discipline,
        "discipline_progress": DisciplineProgress,
        "monthly_progress": MonthlyProgress,
        "activity": Activity,
        "cash_flow": CashFlow,
        "manpower": Manpower,
        "site_photo": SitePhoto,
    }

    if request.method == "POST":
        form_key = request.POST.get("form_key")
        if form_key not in form_classes:
            messages.error(request, "Invalid form submitted.")
            return redirect("dashboard:data_entry")
        form_label, _description, form_class = form_classes[form_key]
        form = form_class(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, f"{form_label} saved.")
            return redirect("dashboard:data_entry")
    else:
        form_key = None
        form = None

    forms = []
    for key, item in form_classes.items():
        label, description, form_class = item
        model_class = models_mapping[key]

        if key == "project" or key == "discipline":
            records = model_class.objects.all().order_by("name")
        elif key == "discipline_progress":
            records = model_class.objects.all().select_related("project", "discipline").order_by("-report_date")
        elif key == "monthly_progress":
            records = model_class.objects.all().select_related("project").order_by("-month")
        elif key == "activity":
            records = model_class.objects.all().select_related("project").order_by("planned_start")
        elif key == "cash_flow":
            records = model_class.objects.all().select_related("project").order_by("-month")
        elif key == "manpower":
            records = model_class.objects.all().select_related("project").order_by("-report_date")
        elif key == "site_photo":
            records = model_class.objects.all().select_related("project").order_by("-uploaded_at")
        else:
            records = model_class.objects.all()

        forms.append(
            {
                "key": key,
                "label": label,
                "description": description,
                "form": form if key == form_key else form_class(),
                "records": records,
            }
        )

    return render(request, "dashboard/data_entry.html", {"forms": forms})


@login_required
def edit_entry(request, model_name, pk):
    form_classes = {
        "project": (Project, ProjectForm, "Project"),
        "discipline": (Discipline, DisciplineForm, "Discipline / Area"),
        "discipline_progress": (DisciplineProgress, DisciplineProgressForm, "Discipline Progress"),
        "monthly_progress": (MonthlyProgress, MonthlyProgressForm, "Monthly Progress"),
        "activity": (Activity, ActivityForm, "Activity"),
        "cash_flow": (CashFlow, CashFlowForm, "Cash Flow"),
        "manpower": (Manpower, ManpowerForm, "Manpower"),
        "site_photo": (SitePhoto, SitePhotoForm, "Site Photo"),
    }

    if model_name not in form_classes:
        messages.error(request, "Invalid model name.")
        return redirect("dashboard:data_entry")

    model_class, form_class, label = form_classes[model_name]
    instance = get_object_or_404(model_class, pk=pk)

    if request.method == "POST":
        form = form_class(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, f"{label} updated successfully.")
            return redirect("dashboard:data_entry")
    else:
        form = form_class(instance=instance)

    context = {
        "form": form,
        "label": label,
        "model_name": model_name,
        "instance": instance,
    }
    return render(request, "dashboard/edit_entry.html", context)


@login_required
def delete_entry(request, model_name, pk):
    form_classes = {
        "project": (Project, "Project"),
        "discipline": (Discipline, "Discipline / Area"),
        "discipline_progress": (DisciplineProgress, "Discipline Progress"),
        "monthly_progress": (MonthlyProgress, "Monthly Progress"),
        "activity": (Activity, "Activity"),
        "cash_flow": (CashFlow, "Cash Flow"),
        "manpower": (Manpower, "Manpower"),
        "site_photo": (SitePhoto, "Site Photo"),
    }

    if model_name not in form_classes:
        messages.error(request, "Invalid model name.")
        return redirect("dashboard:data_entry")

    model_class, label = form_classes[model_name]
    instance = get_object_or_404(model_class, pk=pk)

    if request.method == "POST":
        instance.delete()
        messages.success(request, f"{label} deleted successfully.")
        return redirect("dashboard:data_entry")

    context = {
        "label": label,
        "model_name": model_name,
        "instance": instance,
    }
    return render(request, "dashboard/confirm_delete.html", context)


def register(request):
    if request.user.is_authenticated:
        return redirect("dashboard:home")

    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration complete.")
            return redirect("dashboard:home")
    else:
        form = UserCreationForm()

    return render(request, "registration/register.html", {"form": form})


@login_required
def logout_user(request):
    if request.method == "POST":
        logout(request)
        return redirect("login")
    return redirect("dashboard:home")


@login_required
def profile(request):
    """Profile page – edit personal info and/or change password."""
    profile_form = UserProfileForm(instance=request.user)
    password_form = UserPasswordChangeForm(user=request.user)

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "update_profile":
            profile_form = UserProfileForm(request.POST, instance=request.user)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, "Profile updated successfully.")
                return redirect("dashboard:profile")

        elif action == "change_password":
            password_form = UserPasswordChangeForm(user=request.user, data=request.POST)
            if password_form.is_valid():
                password_form.save()
                # Keep the user logged in after a password change
                update_session_auth_hash(request, password_form.user)
                messages.success(request, "Password changed successfully.")
                return redirect("dashboard:profile")

    return render(request, "dashboard/profile.html", {
        "profile_form": profile_form,
        "password_form": password_form,
    })
