from datetime import date, timedelta

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0005_remove_dienst_min_personen_dienst_hulpaanvraag_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="availability",
            name="weekday",
            field=models.IntegerField(
                choices=[
                    (1, "Zondag"),
                    (2, "Maandag"),
                    (3, "Dinsdag"),
                    (4, "Woensdag"),
                    (5, "Donderdag"),
                    (6, "Vrijdag"),
                    (7, "Zaterdag"),
                ]
            ),
        ),
        migrations.AddField(
            model_name="availability",
            name="valid_from",
            field=models.DateField(default=date.today),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="availability",
            name="valid_until",
            field=models.DateField(default=date.today() + timedelta(days=28)),
            preserve_default=False,
        ),
    ]
