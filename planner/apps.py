from django.apps import AppConfig


class PlannerConfig(AppConfig):
    """功能说明：配置路线规划应用基础信息。"""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'planner'
    verbose_name = 'AI路线规划'