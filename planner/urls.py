"""功能说明：AI 路线规划路由配置。"""
from django.urls import path

from planner import views


app_name = 'planner'

urlpatterns = [
    path('', views.planner_view, name='planner'),
    path('submit/', views.planner_submit_view, name='planner_submit'),
    path('result/<int:plan_id>/', views.planner_result_view, name='planner_result'),
    path('result/<int:plan_id>/delete/', views.planner_delete_view, name='planner_delete'),
    path('api/geocode/', views.api_geocode, name='api_geocode'),
    path('api/regeo/', views.api_regeo, name='api_regeo'),
    path('api/transit-routes/', views.api_transit_routes, name='api_transit_routes'),
]