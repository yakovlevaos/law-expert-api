from django.db import migrations


class Migration(migrations.Migration):
    """Rename Competencies -> Competency (singular, per Django convention).

    Must be a RenameModel: a Create+Delete pair would drop every competency
    row and every game<->competency link.
    """

    dependencies = [
        ("games", "0001_initial"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="Competencies",
            new_name="Competency",
        ),
    ]
