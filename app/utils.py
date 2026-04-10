from types import SimpleNamespace

from django.db import connection

from .models import Availability, UserProfile


WEEKDAY_LABELS = {
    1: "Zondag",
    2: "Maandag",
    3: "Dinsdag",
    4: "Woensdag",
    5: "Donderdag",
    6: "Vrijdag",
    7: "Zaterdag",
}


def ensure_user_profile(user):
    if not getattr(user, "is_authenticated", False):
        return None

    profile, _ = UserProfile.objects.get_or_create(
        user=user,
        defaults={"role": "hulpvrager"},
    )
    return profile


def get_user_role(user, default=None, create_missing=False):
    if not getattr(user, "is_authenticated", False):
        return default

    if create_missing:
        profile = ensure_user_profile(user)
        return profile.role if profile else default

    try:
        return user.userprofile.role
    except UserProfile.DoesNotExist:
        return default


def user_has_role(user, role):
    return get_user_role(user) == role


def heeft_rol(user, rol):
    """
    Controleert of een gebruiker een bepaalde rol heeft.
    Bijvoorbeeld:
    heeft_rol(request.user, "admin")
    """
    return get_user_role(user) == rol


def availability_has_period_fields():
    table_names = connection.introspection.table_names()
    if "app_availability" not in table_names:
        return False

    with connection.cursor() as cursor:
        columns = {
            column.name
            for column in connection.introspection.get_table_description(cursor, "app_availability")
        }

    return {"valid_from", "valid_until"}.issubset(columns)


def _build_legacy_availability(row):
    return SimpleNamespace(
        id=row[0],
        volunteer_id=row[1],
        weekday=row[2],
        start_time=row[3],
        end_time=row[4],
        valid_from=None,
        valid_until=None,
        weekday_label=WEEKDAY_LABELS.get(row[2], str(row[2])),
    )


def list_user_availability(user):
    if availability_has_period_fields():
        return [
            SimpleNamespace(
                id=item.id,
                volunteer_id=item.volunteer_id,
                weekday=item.weekday,
                start_time=item.start_time,
                end_time=item.end_time,
                valid_from=item.valid_from,
                valid_until=item.valid_until,
                weekday_label=item.get_weekday_display(),
            )
            for item in Availability.objects.filter(volunteer=user).order_by("valid_from", "weekday", "start_time")
        ]

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT id, volunteer_id, weekday, start_time, end_time
            FROM app_availability
            WHERE volunteer_id = %s
            ORDER BY weekday, start_time
            """,
            [user.id],
        )
        rows = cursor.fetchall()

    return [_build_legacy_availability(row) for row in rows]


def list_active_availability(user, today):
    if availability_has_period_fields():
        return [
            SimpleNamespace(
                id=item.id,
                volunteer_id=item.volunteer_id,
                weekday=item.weekday,
                start_time=item.start_time,
                end_time=item.end_time,
                valid_from=item.valid_from,
                valid_until=item.valid_until,
                weekday_label=item.get_weekday_display(),
            )
            for item in Availability.objects.filter(
                volunteer=user,
                valid_from__lte=today,
                valid_until__gte=today,
            ).order_by("valid_from", "weekday", "start_time")
        ]

    return list_user_availability(user)


def create_availability_for_user(user, cleaned_data):
    if availability_has_period_fields():
        return Availability.objects.create(
            volunteer=user,
            weekday=cleaned_data["weekday"],
            start_time=cleaned_data["start_time"],
            end_time=cleaned_data["end_time"],
            valid_from=cleaned_data["valid_from"],
            valid_until=cleaned_data["valid_until"],
        )

    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO app_availability (volunteer_id, weekday, start_time, end_time)
            VALUES (%s, %s, %s, %s)
            """,
            [
                user.id,
                cleaned_data["weekday"],
                cleaned_data["start_time"],
                cleaned_data["end_time"],
            ],
        )


def delete_availability_for_user(user, availability_id):
    if availability_has_period_fields():
        Availability.objects.filter(id=availability_id, volunteer=user).delete()
        return

    with connection.cursor() as cursor:
        cursor.execute(
            """
            DELETE FROM app_availability
            WHERE id = %s AND volunteer_id = %s
            """,
            [availability_id, user.id],
        )
