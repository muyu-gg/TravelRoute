"""功能说明：旅游攻略后台管理配置。"""
from django.contrib import admin

from guides.models import TravelGuide, TravelGuideImage, TravelGuideAttraction


class TravelGuideImageInline(admin.TabularInline):
    """功能说明：在攻略详情页内联编辑图片。"""

    model = TravelGuideImage
    extra = 1
    readonly_fields = ('created_at',)
    ordering = ('sort_order',)


class TravelGuideAttractionInline(admin.TabularInline):
    """功能说明：在攻略详情页内联编辑关联景点。"""

    model = TravelGuideAttraction
    extra = 1
    readonly_fields = ('created_at',)
    autocomplete_fields = ('attraction',)


@admin.register(TravelGuide)
class TravelGuideAdmin(admin.ModelAdmin):
    """功能说明：在 Django 后台管理旅游攻略。"""

    list_display = ('title', 'city', 'author', 'view_count', 'created_at')
    list_display_links = ('title', 'city')
    list_filter = ('city', 'created_at')
    search_fields = ('title', 'summary', 'content', 'author__username')
    readonly_fields = ('view_count', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    list_per_page = 20
    save_on_top = True
    inlines = [TravelGuideImageInline, TravelGuideAttractionInline]
    autocomplete_fields = ('author',)


@admin.register(TravelGuideImage)
class TravelGuideImageAdmin(admin.ModelAdmin):
    """功能说明：在 Django 后台管理攻略图片。"""

    list_display = ('guide', 'image', 'sort_order', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('guide__title',)
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    list_per_page = 20


@admin.register(TravelGuideAttraction)
class TravelGuideAttractionAdmin(admin.ModelAdmin):
    """功能说明：在 Django 后台管理攻略关联景点。"""

    list_display = ('guide', 'attraction', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('guide__title', 'attraction__name')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    list_per_page = 20
    autocomplete_fields = ('guide', 'attraction')