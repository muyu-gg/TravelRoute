"""功能说明：景点应用路由配置。"""
from django.urls import path

from travel import views


app_name = 'travel'

urlpatterns = [
    path('', views.attraction_list_view, name='attraction_list'),
    path('attraction/<int:attraction_id>/', views.attraction_detail_view, name='attraction_detail'),
    path('attraction/<int:attraction_id>/comment/', views.add_comment_view, name='add_comment'),
    path('favorite/', views.favorite_toggle_view, name='favorite_toggle'),
]