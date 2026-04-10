from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0006_availability_valid_period"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="availability",
            options={"ordering": ["valid_from", "weekday", "start_time"]},
        ),
    ]
