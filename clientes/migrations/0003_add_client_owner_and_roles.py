from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def create_roles(apps, schema_editor):
    group_model = apps.get_model('auth', 'Group')
    database = schema_editor.connection.alias
    group_model.objects.using(database).get_or_create(name='administrador')
    group_model.objects.using(database).get_or_create(name='vendedor')


class Migration(migrations.Migration):

    dependencies = [
        ('clientes', '0002_nota'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='cliente',
            name='responsavel',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='clientes',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.RunPython(create_roles, migrations.RunPython.noop),
    ]
