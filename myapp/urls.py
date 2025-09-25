from django.urls import path
from .views import (
    # Authentication Views
    UserRegistrationView, UserLoginView, UserLogoutView, check_auth_status,
    
    # Page Views
    landing_page, debate_setup_page, debate_room_page, login_page, register_page,
    
    # Dashboard and Profile
    DashboardView, UserProfileView, dashboard_page,
    
    # Debate Content
    DebateCategoryListView, DebateTopicListView,
    
    # Debate Management
    DebateCreateView, DebateDetailView, DebateMessageView, DebateHistoryView,
    
    # AI Response
    AIResponseView
)
from . import views

urlpatterns = [
    # Main pages
    path('', views.landing_page, name='landing'),
    path('dashboard/', views.dashboard_page, name='dashboard_page'),
    path('login/', views.login_page, name='login_page'),
    path('register/', views.register_page, name='register_page'),
    path('debate/setup/', views.debate_setup_page, name='debate_setup'),
    path('debate/<int:debate_id>/', views.debate_room_page, name='debate_room'),
    
    # API endpoints for Authentication
    path('api/auth/register/', UserRegistrationView.as_view(), name='register'),
    path('api/auth/login/', UserLoginView.as_view(), name='login'),
    path('api/auth/logout/', UserLogoutView.as_view(), name='logout'),
    path('api/auth/status/', check_auth_status, name='auth_status'),
    
    # API endpoints for Dashboard and Profile
    path('api/dashboard/', DashboardView.as_view(), name='dashboard'),
    path('api/profile/', UserProfileView.as_view(), name='profile'),
    
    # API endpoints for Debate Content
    path('api/categories/', DebateCategoryListView.as_view(), name='categories'),
    path('api/topics/', DebateTopicListView.as_view(), name='topics'),
    
    # API endpoints for Debate Management
    path('api/debates/create/', DebateCreateView.as_view(), name='create_debate'),
    path('api/debates/<int:debate_id>/', DebateDetailView.as_view(), name='debate_detail'),
    path('api/debates/<int:debate_id>/messages/', DebateMessageView.as_view(), name='debate_messages'),
    path('api/debates/<int:debate_id>/ai-response/', AIResponseView.as_view(), name='ai_response'),
    path('api/debates/history/', DebateHistoryView.as_view(), name='debate_history'),
]