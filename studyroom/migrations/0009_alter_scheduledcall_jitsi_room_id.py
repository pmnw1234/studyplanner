# studyroom/migrations/0009_alter_scheduledcall_jitsi_room_id.py
from django.db import migrations, models
import secrets  # Add this import if you want to use a function

def generate_room_id():
    return secrets.token_urlsafe(16)

class Migration(migrations.Migration):

    dependencies = [
        ('studyroom', '0008_scheduledcall'),
    ]

    operations = [
        migrations.AlterField(
            model_name='scheduledcall',
            name='jitsi_room_id',
            field=models.CharField(default=generate_room_id, max_length=50, unique=True),
        ),
    ]