from django.apps import AppConfig


class TravelConfig(AppConfig):
    """功能说明：配置景点应用基础信息。"""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'travel'
    verbose_name = '景点数据'