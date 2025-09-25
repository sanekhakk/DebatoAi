from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    UserProfile, DebateCategory, DebateTopic, 
    Debate, DebateMessage, GuestSession
)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_joined']
        read_only_fields = ['id', 'date_joined']

class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    win_rate = serializers.ReadOnlyField()
    
    class Meta:
        model = UserProfile
        fields = ['user', 'profile_picture', 'ai_wins', 'user_wins', 'total_debates', 'win_rate', 'created_at']
        read_only_fields = ['ai_wins', 'user_wins', 'total_debates', 'win_rate', 'created_at']

class DebateCategorySerializer(serializers.ModelSerializer):
    topics_count = serializers.SerializerMethodField()
    
    class Meta:
        model = DebateCategory
        fields = ['id', 'name', 'description', 'is_active', 'topics_count']
    
    def get_topics_count(self, obj):
        return obj.topics.filter(is_active=True).count()

class DebateTopicSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = DebateTopic
        fields = ['id', 'category', 'category_name', 'title', 'description', 'difficulty_level', 'is_active']

class DebateMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = DebateMessage
        fields = ['id', 'sender', 'content', 'timestamp', 'response_time']
        read_only_fields = ['timestamp']

class DebateSerializer(serializers.ModelSerializer):
    topic_title = serializers.CharField(source='topic.title', read_only=True)
    topic_description = serializers.CharField(source='topic.description', read_only=True)
    category_name = serializers.CharField(source='topic.category.name', read_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True)
    duration = serializers.ReadOnlyField(source='duration_minutes')
    messages = DebateMessageSerializer(many=True, read_only=True)
    is_guest = serializers.ReadOnlyField(source='is_guest_debate')
    
    class Meta:
        model = Debate
        fields = [
            'id', 'user', 'user_name', 'session_id', 'topic', 'topic_title', 
            'topic_description', 'category_name', 'difficulty_level', 
            'total_time_limit', 'reply_time_limit', 'status', 'winner',
            'created_at', 'started_at', 'ended_at', 'duration',
            'user_messages_count', 'ai_messages_count', 'messages', 'is_guest'
        ]
        read_only_fields = [
            'user', 'created_at', 'started_at', 'ended_at', 'duration',
            'user_messages_count', 'ai_messages_count', 'messages', 'is_guest'
        ]

class DebateCreateSerializer(serializers.ModelSerializer):
    """Simplified serializer for creating debates"""
    class Meta:
        model = Debate
        fields = ['topic', 'difficulty_level', 'total_time_limit']
    
    def validate_total_time_limit(self, value):
        if value not in [5, 10, 15, 20]:
            raise serializers.ValidationError("Time limit must be 5, 10, 15, or 20 minutes")
        return value
    
    def validate_difficulty_level(self, value):
        if value not in ['easy', 'medium', 'hard']:
            raise serializers.ValidationError("Difficulty must be easy, medium, or hard")
        return value

class DebateHistorySerializer(serializers.ModelSerializer):
    """Simplified serializer for debate history display"""
    topic_title = serializers.CharField(source='topic.title', read_only=True)
    category_name = serializers.CharField(source='topic.category.name', read_only=True)
    duration = serializers.ReadOnlyField(source='duration_minutes')
    
    class Meta:
        model = Debate
        fields = [
            'id', 'topic_title', 'category_name', 'difficulty_level',
            'status', 'winner', 'duration', 'created_at', 'ended_at'
        ]

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm', 'first_name', 'last_name']
    
    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return data
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user

class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

class GuestSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = GuestSession
        fields = ['session_id', 'has_used_free_debate', 'created_at']
        read_only_fields = ['created_at']

class DashboardSerializer(serializers.Serializer):
    """Serializer for homepage dashboard data"""
    user_profile = UserProfileSerializer(read_only=True)
    recent_debates = DebateHistorySerializer(many=True, read_only=True)
    scoreboard = serializers.DictField(read_only=True)
    available_categories = DebateCategorySerializer(many=True, read_only=True)