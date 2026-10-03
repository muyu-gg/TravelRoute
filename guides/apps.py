from django.apps import AppConfig


class GuidesConfig(AppConfig):
    """功能说明：配置攻略应用基础信息。"""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'guides'
    verbose_name = '攻略管理'