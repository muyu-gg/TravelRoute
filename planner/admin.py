

"""功能说明：AI 路线规划后台管理配置。"""
from django.contrib import admin

from planner.models import RoutePlan, RoutePlanStop


class RoutePlanStopInline(admin.TabularInline):
    """功能说明：在路线规划详情页内联编辑站点。"""

    model = RoutePlanStop
    extra = 0
    readonly_fields = ('created_at',)
    ordering = ('day_index', 'sequence')
    autocomplete_fields = ('attraction',)


@admin.register(RoutePlan)
class RoutePlanAdmin(admin.ModelAdmin):
    """功能说明：在 Django 后台管理路线规划记录。"""

    list_display = ('city', 'user', 'status', 'created_at')
    list_display_links = ('city', 'user')
    list_filter = ('status', 'city', 'created_at')
    search_fields = ('city', 'user__username', 'final_plan', 'error_message')
    readonly_fields = ('intent_data', 'process_steps', 'final_plan', 'error_message', 'created_at')
    ordering = ('-created_at',)
    list_per_page = 20
    save_on_top = True
    inlines = [RoutePlanStopInline]
    autocomplete_fields = ('user',)


@admin.register(RoutePlanStop)
class RoutePlanStopAdmin(admin.ModelAdmin):
    """功能说明：在 Django 后台管理路线站点。"""

    list_display = ('plan', 'day_index', 'sequence', 'name', 'city_name')
    list_filter = ('city_name', 'day_index')
    search_fields = ('name', 'city_name', 'plan__city')
    readonly_fields = ('created_at',)
    ordering = ('plan', 'day_index', 'sequence')
    list_per_page = 20
    autocomplete_fields = ('plan', 'attraction')
