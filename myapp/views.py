import uuid
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.decorators import login_required 
from django.db.models import Count
from .models import (
    UserProfile, DebateCategory, DebateTopic, 
    Debate, DebateMessage, GuestSession
)
from .serializers import (
    UserProfileSerializer, DebateCategorySerializer, DebateTopicSerializer,
    DebateSerializer, DebateCreateSerializer, DebateHistorySerializer,
    DebateMessageSerializer, UserRegistrationSerializer, UserLoginSerializer,
    GuestSessionSerializer, DashboardSerializer
)
from .ai_service import DebateAIService
import logging
from django.http import JsonResponse

logger = logging.getLogger(__name__)

def login_page(request):
    """Render the login page"""
    return render(request, 'login.html')

def register_page(request):
    """Render the registration page"""
    return render(request, 'register.html')

def landing_page(request):
    total_debates = Debate.objects.filter(status='completed').count()
    active_users = User.objects.count() 
    topics_count = DebateTopic.objects.filter(is_active=True).count()

    context = {
        'total_debates': total_debates,
        'active_users': active_users,
        'topics_count': topics_count,
    }
    return render(request, 'landing.html', context)

@login_required
def dashboard_page(request):
    """Render the user's dashboard page."""
    try:
        profile = request.user.userprofile
        recent_debates = Debate.objects.filter(user=request.user).order_by('-created_at')[:5]
        
        context = {
            'profile': profile,
            'recent_debates': recent_debates,
            'scoreboard': {
                'user_wins': profile.user_wins,
                'ai_wins': profile.ai_wins,
                'total_debates': profile.total_debates,
                'win_rate': profile.win_rate()
            }
        }
        return render(request, 'dashboard.html', context)
    except UserProfile.DoesNotExist:
        # If for some reason a profile doesn't exist, redirect to home
        return redirect('landing')


def debate_setup_page(request):
    """Render the debate setup page"""
    return render(request, 'debate_setup.html')

def debate_room_page(request, debate_id):
    """Render the debate room page - FIXED VERSION"""
    logger.info(f"Accessing debate room {debate_id}")
    
    # Get debate or 404
    if request.user.is_authenticated:
        try:
            debate = Debate.objects.get(id=debate_id, user=request.user)
            logger.info(f"Authenticated user {request.user.username} accessing debate {debate_id}")
        except Debate.DoesNotExist:
            logger.error(f"Debate {debate_id} not found for user {request.user.username}")
            return render(request, '404.html', status=404)
    else:
        session_id = request.session.session_key
        if not session_id:
            logger.error("No session ID for guest user")
            return render(request, '404.html', status=404)
        try:
            debate = Debate.objects.get(id=debate_id, session_id=session_id)
            logger.info(f"Guest user {session_id} accessing debate {debate_id}")
        except Debate.DoesNotExist:
            logger.error(f"Debate {debate_id} not found for session {session_id}")
            return render(request, '404.html', status=404)
    
    # Get debate messages
    messages = debate.messages.all().order_by('timestamp')
    logger.info(f"Found {messages.count()} messages for debate {debate_id}")
    
    # Serialize debate data for JavaScript
    debate_data = {
        'id': debate.id,
        'status': debate.status,
        'topic_title': debate.topic.title,
        'topic_description': debate.topic.description,
        'difficulty_level': debate.difficulty_level,
        'total_time_limit': debate.total_time_limit,
        'reply_time_limit': debate.reply_time_limit,
        'user_messages_count': debate.user_messages_count,
        'ai_messages_count': debate.ai_messages_count,
        'created_at': debate.created_at.isoformat() if debate.created_at else None,
        'started_at': debate.started_at.isoformat() if debate.started_at else None,
    }
    
    context = {
        'debate': debate,
        'messages': messages,
        'debate_data': debate_data  # This is crucial for JavaScript
    }
    
    return render(request, 'debate_room.html', context)

# Helper function to get client IP
def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

# Authentication Views
class UserRegistrationView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            login(request, user)
            return Response({
                'message': 'User registered successfully',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email
                }
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserLoginView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']
            
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                return Response({
                    'message': 'Login successful',
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email
                    }
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'error': 'Invalid credentials'
                }, status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserLogoutView(APIView):
    def post(self, request):
        logout(request)
        return Response({'message': 'Logout successful'}, status=status.HTTP_200_OK)

# Dashboard and Profile Views
class DashboardView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        data = {}
        
        categories = DebateCategory.objects.filter(is_active=True)
        data['available_categories'] = DebateCategorySerializer(categories, many=True).data
        
        if request.user.is_authenticated:
            try:
                profile = request.user.userprofile
                data['user_profile'] = UserProfileSerializer(profile).data
                
                recent_debates = Debate.objects.filter(user=request.user).order_by('-created_at')[:5]
                data['recent_debates'] = DebateHistorySerializer(recent_debates, many=True).data
                
                data['scoreboard'] = {
                    'user_wins': profile.user_wins,
                    'ai_wins': profile.ai_wins,
                    'total_debates': profile.total_debates,
                    'win_rate': profile.win_rate()
                }
                
            except UserProfile.DoesNotExist:
                data['user_profile'] = None
        else:
            session_id = request.session.session_key
            if not session_id:
                request.session.create()
                session_id = request.session.session_key
            
            guest_session, created = GuestSession.objects.get_or_create(
                session_id=session_id,
                defaults={'ip_address': get_client_ip(request)}
            )
            
            data['guest_session'] = GuestSessionSerializer(guest_session).data
            data['can_debate'] = not guest_session.has_used_free_debate
        
        return Response(data, status=status.HTTP_200_OK)

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            profile = request.user.userprofile
            return Response(UserProfileSerializer(profile).data)
        except UserProfile.DoesNotExist:
            return Response({'error': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)
    
    def put(self, request):
        try:
            profile = request.user.userprofile
            serializer = UserProfileSerializer(profile, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except UserProfile.DoesNotExist:
            return Response({'error': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)

# Debate Content Views
class DebateCategoryListView(generics.ListAPIView):
    queryset = DebateCategory.objects.filter(is_active=True)
    serializer_class = DebateCategorySerializer
    permission_classes = [AllowAny]

class DebateTopicListView(generics.ListAPIView):
    serializer_class = DebateTopicSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        queryset = DebateTopic.objects.filter(is_active=True)
        category_id = self.request.query_params.get('category', None)
        difficulty = self.request.query_params.get('difficulty', None)
        
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        if difficulty:
            queryset = queryset.filter(difficulty_level=difficulty)
            
        return queryset

# Debate Management Views
class DebateCreateView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        """FIXED: Create debate with proper session handling"""
        logger.info(f"Creating debate: {request.data}")
        
        serializer = DebateCreateSerializer(data=request.data)
        if not serializer.is_valid():
            logger.error(f"Invalid debate data: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Handle guest user session
            if not request.user.is_authenticated:
                session_id = request.session.session_key
                if not session_id:
                    request.session.create()
                    session_id = request.session.session_key
                
                guest_session, created = GuestSession.objects.get_or_create(
                    session_id=session_id,
                    defaults={'ip_address': get_client_ip(request)}
                )
                
                if guest_session.has_used_free_debate:
                    return Response({
                        'error': 'Guest users can only have one free debate. Please register to continue.'
                    }, status=status.HTTP_403_FORBIDDEN)
                
                logger.info(f"Guest session: {session_id}, created: {created}")
            
            # Create debate
            debate_data = serializer.validated_data
            difficulty = debate_data['difficulty_level']
            reply_time_map = {'easy': 60, 'medium': 45, 'hard': 30}
            
            # Generate unique session_id for authenticated users too
            if request.user.is_authenticated:
                import uuid
                session_id = str(uuid.uuid4())
            else:
                session_id = request.session.session_key
            
            debate = Debate.objects.create(
                user=request.user if request.user.is_authenticated else None,
                session_id=session_id,
                topic=debate_data['topic'],
                difficulty_level=difficulty,
                total_time_limit=debate_data['total_time_limit'],
                reply_time_limit=reply_time_map[difficulty],
                status='setup'
            )
            
            logger.info(f"Debate created: {debate.id}, user: {request.user if request.user.is_authenticated else 'guest'}")
            
            return Response(DebateSerializer(debate).data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error creating debate: {str(e)}")
            return Response({'error': 'Failed to create debate'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class DebateDetailView(APIView):
    permission_classes = [AllowAny]
    
    def get_debate(self, debate_id, request):
        try:
            if request.user.is_authenticated:
                return Debate.objects.get(id=debate_id, user=request.user)
            else:
                session_id = request.session.session_key
                if not session_id:
                    return None
                return Debate.objects.get(id=debate_id, session_id=session_id)
        except Debate.DoesNotExist:
            return None
    
    def get(self, request, debate_id):
        debate = self.get_debate(debate_id, request)
        if not debate:
            return Response({'error': 'Debate not found'}, status=status.HTTP_404_NOT_FOUND)
        
        return Response(DebateSerializer(debate).data)
    
    def patch(self, request, debate_id):
        """FIXED: Handle debate status updates properly"""
        logger.info(f"PATCH request for debate {debate_id}: {request.data}")
        
        debate = self.get_debate(debate_id, request)
        if not debate:
            logger.error(f"Debate {debate_id} not found")
            return Response({'error': 'Debate not found'}, status=status.HTTP_404_NOT_FOUND)
        
        action = request.data.get('action')
        logger.info(f"Debate {debate_id} action: {action}")
        
        try:
            if action == 'start':
                if debate.status != 'setup':
                    return Response({'error': 'Debate is not in setup state'}, status=status.HTTP_400_BAD_REQUEST)
                
                debate.status = 'active'
                debate.started_at = timezone.now()
                debate.save()
                logger.info(f"Debate {debate_id} started successfully")
                
            elif action == 'end':
                if debate.status not in ['active', 'setup']:
                    return Response({'error': 'Debate cannot be ended from current state'}, status=status.HTTP_400_BAD_REQUEST)
                
                debate.status = 'completed'
                debate.ended_at = timezone.now()
                
                winner = request.data.get('winner', 'ai')
                debate.winner = winner
                
                # Update user statistics
                if winner == 'user' and debate.user:
                    try:
                        profile = debate.user.userprofile
                        profile.user_wins += 1
                        profile.total_debates += 1
                        profile.save()
                        logger.info(f"User {debate.user.username} stats updated - win")
                    except UserProfile.DoesNotExist:
                        logger.error(f"UserProfile not found for user {debate.user.username}")
                        
                elif winner == 'ai':
                    if debate.user:
                        try:
                            profile = debate.user.userprofile
                            profile.ai_wins += 1
                            profile.total_debates += 1
                            profile.save()
                            logger.info(f"User {debate.user.username} stats updated - loss")
                        except UserProfile.DoesNotExist:
                            logger.error(f"UserProfile not found for user {debate.user.username}")
                    else:
                        # Mark guest session as used
                        try:
                            guest_session = GuestSession.objects.get(session_id=debate.session_id)
                            guest_session.has_used_free_debate = True
                            guest_session.save()
                            logger.info(f"Guest session {debate.session_id} marked as used")
                        except GuestSession.DoesNotExist:
                            logger.error(f"GuestSession not found for session {debate.session_id}")
                
                debate.save()
                logger.info(f"Debate {debate_id} ended, winner: {winner}")
                
            elif action == 'abandon':
                debate.status = 'abandoned'
                debate.ended_at = timezone.now()
                debate.winner = 'ai'
                debate.save()
                logger.info(f"Debate {debate_id} abandoned")
                
            else:
                return Response({'error': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Return updated debate data
            return Response(DebateSerializer(debate).data)
            
        except Exception as e:
            logger.error(f"Error updating debate {debate_id}: {str(e)}")
            return Response({'error': 'Failed to update debate'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DebateMessageView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request, debate_id):
        """FIXED: Handle user message creation properly"""
        logger.info(f"User message for debate {debate_id}: {request.data}")
        
        # Get debate
        if request.user.is_authenticated:
            try:
                debate = Debate.objects.get(id=debate_id, user=request.user)
            except Debate.DoesNotExist:
                return Response({'error': 'Debate not found'}, status=status.HTTP_404_NOT_FOUND)
        else:
            session_id = request.session.session_key
            if not session_id:
                return Response({'error': 'Session not found'}, status=status.HTTP_400_BAD_REQUEST)
            try:
                debate = Debate.objects.get(id=debate_id, session_id=session_id)
            except Debate.DoesNotExist:
                return Response({'error': 'Debate not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Validate message content
        content = request.data.get('content', '').strip()
        if not content:
            return Response({'error': 'Message content is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        if len(content) > 1000:
            return Response({'error': 'Message too long (max 1000 characters)'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Create message
            message_data = {
                'debate': debate.id,
                'sender': request.data.get('sender', 'user'),
                'content': content,
                'response_time': request.data.get('response_time')
            }
            
            serializer = DebateMessageSerializer(data=message_data)
            if serializer.is_valid():
                message = serializer.save(debate=debate)
                
                # Update message count
                if message.sender == 'user':
                    debate.user_messages_count += 1
                else:
                    debate.ai_messages_count += 1
                debate.save()
                
                logger.info(f"Message created for debate {debate_id}, sender: {message.sender}")
                
                return Response(DebateMessageSerializer(message).data, status=status.HTTP_201_CREATED)
            else:
                logger.error(f"Invalid message data for debate {debate_id}: {serializer.errors}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error creating message for debate {debate_id}: {str(e)}")
            return Response({'error': 'Failed to create message'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DebateHistoryView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        debates = Debate.objects.filter(user=request.user).order_by('-created_at')
        serializer = DebateHistorySerializer(debates, many=True)
        return Response(serializer.data)

# Check authentication status
@api_view(['GET'])
@permission_classes([AllowAny])
def check_auth_status(request):
    if request.user.is_authenticated:
        return Response({
            'is_authenticated': True,
            'user': {
                'id': request.user.id,
                'username': request.user.username,
                'email': request.user.email
            }
        })
    else:
        return Response({
            'is_authenticated': False,
            'user': None
        })

class AIResponseView(APIView):
    permission_classes = [AllowAny]
    
    def __init__(self):
        super().__init__()
        self.ai_service = DebateAIService()
    
    def post(self, request, debate_id):
        """FIXED: Generate AI responses properly"""
        logger.info(f"AI response request for debate {debate_id}")
        
        # Get debate
        if request.user.is_authenticated:
            try:
                debate = Debate.objects.get(id=debate_id, user=request.user)
            except Debate.DoesNotExist:
                return Response({'error': 'Debate not found'}, status=status.HTTP_404_NOT_FOUND)
        else:
            session_id = request.session.session_key
            if not session_id:
                return Response({'error': 'Session not found'}, status=status.HTTP_400_BAD_REQUEST)
            try:
                debate = Debate.objects.get(id=debate_id, session_id=session_id)
            except Debate.DoesNotExist:
                return Response({'error': 'Debate not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Ensure debate is active
        if debate.status != 'active':
            return Response({'error': 'Debate is not active'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get conversation history
        messages = debate.messages.all().order_by('timestamp')
        conversation_history = [
            {
                'sender': msg.sender,
                'content': msg.content,
                'timestamp': msg.timestamp.isoformat()
            }
            for msg in messages
        ]
        
        # Get user's last message
        user_message = request.data.get('user_message', '')
        if not user_message:
            last_user_message = messages.filter(sender='user').last()
            if last_user_message:
                user_message = last_user_message.content
        
        if not user_message:
            return Response({'error': 'No user message found'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Generate AI response
            logger.info(f"Generating AI response for debate {debate_id}, difficulty: {debate.difficulty_level}")
            ai_response = self.ai_service.generate_response(
                user_message=user_message,
                topic=debate.topic.title,
                difficulty=debate.difficulty_level,
                conversation_history=conversation_history
            )
            
            # Create AI message in database
            ai_message = DebateMessage.objects.create(
                debate=debate,
                sender='ai',
                content=ai_response['content'],
                response_time=ai_response['response_time']
            )
            
            # Update debate message count
            debate.ai_messages_count += 1
            debate.save()
            
            logger.info(f"AI response created for debate {debate_id}")
            
            return Response({
                'message': DebateMessageSerializer(ai_message).data,
                'debate_status': {
                    'user_messages': debate.user_messages_count,
                    'ai_messages': debate.ai_messages_count,
                    'total_messages': debate.user_messages_count + debate.ai_messages_count
                }
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error generating AI response for debate {debate_id}: {str(e)}")
            return Response({
                'error': 'Failed to generate AI response',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
