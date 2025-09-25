from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    UserProfile, DebateCategory, DebateTopic, 
    Debate, DebateMessage, GuestSession
)

# Inline admin for UserProfile
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'

# Extend User admin to include profile
class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'ai_wins', 'user_wins', 'total_debates', 'win_rate', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at']
    
    def win_rate(self, obj):
        return f"{obj.win_rate()}%"
    win_rate.short_description = 'Win Rate'

@admin.register(DebateCategory)
class DebateCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name']
    prepopulated_fields = {'description': ('name',)}

@admin.register(DebateTopic)
class DebateTopicAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'difficulty_level', 'is_active', 'created_at']
    list_filter = ['category', 'difficulty_level', 'is_active', 'created_at']
    search_fields = ['title', 'description']
    readonly_fields = ['created_at']

class DebateMessageInline(admin.TabularInline):
    model = DebateMessage
    extra = 0
    readonly_fields = ['timestamp', 'response_time']
    fields = ['sender', 'content', 'response_time', 'timestamp']

@admin.register(Debate)
class DebateAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'status', 'winner', 'difficulty_level', 'duration_display', 'created_at']
    list_filter = ['status', 'winner', 'difficulty_level', 'created_at']
    search_fields = ['user__username', 'topic__title', 'session_id']
    readonly_fields = ['created_at', 'started_at', 'ended_at', 'duration_display']
    inlines = [DebateMessageInline]
    
    def duration_display(self, obj):
        duration = obj.duration_minutes()
        if duration:
            return f"{duration:.1f} minutes"
        return "Not completed"
    duration_display.short_description = 'Duration'

@admin.register(DebateMessage)
class DebateMessageAdmin(admin.ModelAdmin):
    list_display = ['debate', 'sender', 'content_preview', 'response_time', 'timestamp']
    list_filter = ['sender', 'timestamp']
    search_fields = ['content', 'debate__user__username']
    readonly_fields = ['timestamp']
    
    def content_preview(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content Preview'

@admin.register(GuestSession)
class GuestSessionAdmin(admin.ModelAdmin):
    list_display = ['session_preview', 'ip_address', 'has_used_free_debate', 'created_at']
    list_filter = ['has_used_free_debate', 'created_at']
    search_fields = ['session_id', 'ip_address']
    readonly_fields = ['created_at']
    
    def session_preview(self, obj):
        return f"Guest_{obj.session_id[:8]}..."
    session_preview.short_description = 'Session ID'

# Customize admin site header and title
admin.site.site_header = "Debato AI Administration"
admin.site.site_title = "Debato AI Admin"
admin.site.index_title = "Welcome to Debato AI Administration"