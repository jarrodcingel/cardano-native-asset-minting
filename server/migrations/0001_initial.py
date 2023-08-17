from django.db import migrations, models
import server.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AssetAddress',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cborHex', models.CharField(max_length=200)),
                ('readableAddress', models.CharField(max_length=200)),
                ('status', models.CharField(choices=[('free', 'free'), ('minting', 'minting'), ('failed', 'failed'), ('done', 'done')], default='free', max_length=16)),
                ('lastUpdate', models.DateTimeField(auto_now_add=True)),
                ('pendingLovelace', models.IntegerField(default=0)),
                ('metadataToMint', models.JSONField(default=server.models.AssetAddress.metadata_default, verbose_name='MetadataToMint')),
            ],
        ),
    ]
