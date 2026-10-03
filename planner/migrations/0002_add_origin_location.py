from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('planner', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='routeplan',
            name='origin_location',
            field=models.CharField(blank=True, db_comment='用户出发地地址或经纬度', default='', max_length=200, verbose_name='出发地点'),
        ),
    ]