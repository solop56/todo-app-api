"""
Serializer for task management.
"""
from rest_framework import serializers
from core.models import Task
from django.utils import timezone
from django.core.validators import MinLengthValidator

class TaskSerializer(serializers.ModelSerializer):
    """Serializer for task operations."""
    
    title = serializers.CharField(
        max_length=255,
        validators=[MinLengthValidator(3)]
    )
    description = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True
    )
    status = serializers.ChoiceField(
        choices=Task.STATUS_CHOICES,
        default='pending'
    )
    priority = serializers.ChoiceField(
        choices=Task.PRIORITY_CHOICES,
        default='medium'
    )
    due_date = serializers.DateField(
        required=False,
        allow_null=True
    )
    user = serializers.PrimaryKeyRelatedField(
        read_only=True
    )
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Task
        fields = [
            'id',
            'title',
            'description',
            'status',
            'priority',
            'due_date',
            'user',
            'created_at',
            'updated_at'
        ]
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