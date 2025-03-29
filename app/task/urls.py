"""
URL mapping for the task app.
"""
from django.urls import (
    path,
    include,
)

from rest_framework.routers import DefaultRouter

from task import views


router = DefaultRouter()
router.register('tasks', views.TaskViewSet, basename='task')

app_name = 'task'

urlpatterns = [
    path('api/v1/', include(router.urls)),
]
