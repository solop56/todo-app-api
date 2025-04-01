"""
Serializer for task management.
"""
from rest_framework import serializers
from core.models import Task
from django.utils import timezone

class TaskSerializer(serializers.ModelSerializer):
    """Serializer for task operations."""
    
    user = serializers.PrimaryKeyRelatedField(
        read_only=True
    )
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Task
        fields = '__all__'
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def validate_due_date(self, value):
        """Validate that due_date is not in the past."""
        if value and value < timezone.now().date():
            raise serializers.ValidationError("Due date cannot be in the past")
        return value

    def create(self, validated_data):
        """Create a new task."""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Update a task efficiently."""
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save(update_fields=list(validated_data.keys()))
        return instance

    def to_representation(self, instance):
        """Convert the instance to a dictionary."""
        representation = super().to_representation(instance)
        # Add any additional computed fields or formatting here
        return representation

class TaskDetails(TaskSerializer):
    """Serializers for task details view"""

    class Meta(TaskSerializer.Meta):
        fields = TaskSerializer.Meta.fields