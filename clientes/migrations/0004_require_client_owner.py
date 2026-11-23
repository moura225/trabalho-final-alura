from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def require_client_owners(apps, schema_editor):
    cliente_model = apps.get_model('clientes', 'Cliente')
    database = schema_editor.connection.alias
    if cliente_model.objects.using(database).filter(
        responsavel__isnull=True,
    ).exists():
        raise RuntimeError(
            'Assign a responsible user to every existing client before '
            'applying this migration.'
        )


class Migration(migrations.Migration):

    dependencies = [
        ('clientes', '0003_add_client_owner_and_roles'),
    ]

    operations = [
        migrations.RunPython(
            require_client_owners,
            migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name='cliente',
            name='responsavel',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='clientes',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
