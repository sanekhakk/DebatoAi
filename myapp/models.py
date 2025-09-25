from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class UserProfile(models.Model):
    """Extended user profile for additional user data"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    ai_wins = models.IntegerField(default=0)
    user_wins = models.IntegerField(default=0)
    total_debates = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    def win_rate(self):
        """Calculate user's win percentage"""
        if self.total_debates == 0:
            return 0
        return round((self.user_wins / self.total_debates) * 100, 2)


class DebateCategory(models.Model):
    """Categories for debate topics"""
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Debate Categories"


class DebateTopic(models.Model):
    """Specific debate topics within categories"""
    category = models.ForeignKey(DebateCategory, on_delete=models.CASCADE, related_name='topics')
    title = models.CharField(max_length=200)
    description = models.TextField()
    difficulty_level = models.CharField(
        max_length=10,
        choices=[
            ('easy', 'Easy'),
            ('medium', 'Medium'),
            ('hard', 'Hard')
        ],
        default='medium'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.category.name}: {self.title}"


class Debate(models.Model):
    """Main debate session model"""
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard')
    ]
    
    STATUS_CHOICES = [
        ('setup', 'Setup'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('abandoned', 'Abandoned')
    ]
    
    WINNER_CHOICES = [
        ('user', 'User'),
        ('ai', 'AI'),
        ('ongoing', 'Ongoing')
    ]
    
    # Basic Info
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)  # Null for guest users
    session_id = models.CharField(max_length=100, null=True, blank=True)  
    
    # Debate Settings
    topic = models.ForeignKey(DebateTopic, on_delete=models.CASCADE)
    difficulty_level = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES)
    total_time_limit = models.IntegerField(help_text="Total debate time in minutes")
    reply_time_limit = models.IntegerField(help_text="Per reply time limit in seconds")
    
    # Debate Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='setup')
    winner = models.CharField(max_length=10, choices=WINNER_CHOICES, default='ongoing')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    
    # Statistics
    user_messages_count = models.IntegerField(default=0)
    ai_messages_count = models.IntegerField(default=0)
    
    def __str__(self):
        user_name = self.user.username if self.user else f"Guest_{self.session_id[:8]}"
        return f"Debate: {user_name} vs AI - {self.topic.title}"
    
    def duration_minutes(self):
        """Calculate debate duration in minutes"""
        if self.started_at and self.ended_at:
            duration = self.ended_at - self.started_at
            return duration.total_seconds() / 60
        return 0
    
    def is_guest_debate(self):
        """Check if this is a guest debate"""
        return self.user is None


class DebateMessage(models.Model):
    """Individual messages in a debate"""
    SENDER_CHOICES = [
        ('user', 'User'),
        ('ai', 'AI')
    ]
    
    debate = models.ForeignKey(Debate, on_delete=models.CASCADE, related_name='messages')
    sender = models.CharField(max_length=10, choices=SENDER_CHOICES)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    response_time = models.FloatField(null=True, blank=True, help_text="Time taken to respond in seconds")
    
    def __str__(self):
        return f"{self.sender}: {self.content[:50]}..."
    
    class Meta:
        ordering = ['timestamp']


class GuestSession(models.Model):
    """Track guest users for their one free debate"""
    session_id = models.CharField(max_length=100, unique=True)
    ip_address = models.GenericIPAddressField()
    has_used_free_debate = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Guest: {self.session_id[:8]} - Used: {self.has_used_free_debate}"


# Signal to create UserProfile when User is created
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    try:
        instance.userprofile.save()
    except UserProfile.DoesNotExist:
        UserProfile.objects.create(user=instance)