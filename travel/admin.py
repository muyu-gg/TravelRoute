"""功能说明：景点数据后台管理配置。"""
from django.contrib import admin
from django.db.models import QuerySet

from travel.models import Attraction, AttractionFavorite, AttractionComment


@admin.register(Attraction)
class AttractionAdmin(admin.ModelAdmin):
    """功能说明：在 Django 后台管理景点信息。"""

    list_display = ('name', 'city_name', 'area', 'score', 'heat_score', 'comment_count', 'is_free', 'is_advertisement')
    list_display_links = ('name', 'city_name')
    list_filter = ('city_name', 'is_free', 'is_advertisement', 'is_recommend')
    search_fields = ('name', 'area', 'tags', 'city_name')
    readonly_fields = ('poi_id',)
    ordering = ('-heat_score', '-score', '-comment_count', 'id')
    list_per_page = 20
    save_on_top = True


@admin.register(AttractionFavorite)
class AttractionFavoriteAdmin(admin.ModelAdmin):
    """功能说明：在 Django 后台管理景点收藏。"""

    list_display = ('user', 'attraction', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'attraction__name')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    list_per_page = 20


@admin.register(AttractionComment)
class AttractionCommentAdmin(admin.ModelAdmin):
    """功能说明：在 Django 后台管理景点评论。"""

    list_display = ('user', 'attraction', 'content_preview', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'attraction__name', 'content')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    list_per_page = 20

    @admin.display(description='评论预览')
    def content_preview(self, obj: AttractionComment) -> str:
        """功能说明：在后台列表展示评论内容前 50 个字符。"""
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content