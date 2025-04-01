"""
Views for the task API
"""
from typing import Any
from rest_framework import viewsets, status, response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from core.models import Task
from task import serializers
from django.http import Http404
import logging

logger = logging.getLogger(__name__)


class TaskViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Task APIs.
    
    Provides CRUD operations for tasks with authentication, filtering,
    searching, and pagination capabilities.
    """
    serializer_class = serializers.TaskDetails
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'priority', 'due_date']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'due_date', 'priority']
    ordering = ['-created_at']
    queryset = Task.objects.all()
    
    def get_queryset(self) -> Task.objects:
        """
        Retrieve tasks for authenticated user.
        
        Returns:
            QuerySet: Filtered and ordered tasks for the current user
        """
        return (
            Task.objects.filter(user=self.request.user)
            .order_by('-id')
            .distinct()
        )
    
    def perform_create(self, serializer: serializers.TaskDetails) -> None:
        """
        Create a new task with the current user.
        
        Args:
            serializer: The serializer instance containing the task data
        """
        serializer.save(user=self.request.user)
    
    def retrieve(self, request: Any, *args: Any, **kwargs: Any) -> response.Response:
        """
        Retrieve a specific task by ID.
        
        Args:
            request: The HTTP request
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
            
        Returns:
            Response: The task data
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return response.Response(serializer.data)
    
    def get_object(self) -> Task:
        """
        Get the task object for the current user.
        
        Returns:
            Task: The task object
            
        Raises:
            Http404: If the task does not exist or belongs to another user
        """
        obj = super().get_object()
        if obj.user != self.request.user:
            raise Http404("Task not found")
        return obj
    
    def update(self, request, *args, **kwargs):
        """Update a task."""
        try:
            return super().update(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Update error: {str(e)}", exc_info=True)
            return response.Response(
                {'error': f'An unexpected error occurred: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def destroy(self, request, *args, **kwargs):
        """Delete a task."""
        try:
            return super().destroy(request, *args, **kwargs)
        except Exception:
            return response.Response(
                {'error': 'An unexpected error occurred'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    

