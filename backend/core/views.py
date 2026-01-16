"""
API views for complaints system
"""

from django.utils import timezone
from django.db.models import Count
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from django_filters import rest_framework as filters

from .models import TelegramUser, Mahalla, Category, SubCategory, Complaint, ComplaintImage, StatusHistory, Notification
from .serializers import (
    TelegramUserSerializer, TelegramUserCreateSerializer, TelegramUserUpdateSerializer,
    MahallaSerializer, CategorySerializer, SubCategorySerializer,
    ComplaintSerializer, ComplaintCreateSerializer, ComplaintStatusUpdateSerializer,
    ComplaintImageSerializer, StatusHistorySerializer, NotificationSerializer,
    StatsSerializer
)


class TelegramUserViewSet(viewsets.ModelViewSet):
    """Telegram users API (yangi versiyasi)"""
    queryset = TelegramUser.objects.all().order_by('-created_at')
    serializer_class = TelegramUserSerializer
    permission_classes = [AllowAny]
    filterset_fields = ['role', 'username', 'registration_completed', 'is_active']
    search_fields = ['full_name', 'username', 'telegram_id', 'phone_number']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return TelegramUserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return TelegramUserUpdateSerializer
        return TelegramUserSerializer
    
    @action(detail=True, methods=['get'])
    def complaints(self, request, pk=None):
        """Get user's complaints"""
        user = self.get_object()
        complaints = user.complaints.all().order_by('-created_at')
        page = self.paginate_queryset(complaints)
        
        if page is not None:
            serializer = ComplaintSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = ComplaintSerializer(complaints, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def complete_registration(self, request, pk=None):
        """Complete user registration"""
        user = self.get_object()
        user.complete_registration()
        return Response({'status': 'Registration completed'})
    
    @action(detail=True, methods=['post'])
    def update_profile(self, request, pk=None):
        """Update user profile from bot"""
        user = self.get_object()
        serializer = TelegramUserUpdateSerializer(user, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def admins(self, request):
        """Get all admin users"""
        admins = TelegramUser.objects.filter(role='admin').order_by('-created_at')
        serializer = self.get_serializer(admins, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def unregistered(self, request):
        """Get unregistered users (registration_completed=False)"""
        unregistered = TelegramUser.objects.filter(registration_completed=False).order_by('-created_at')
        serializer = self.get_serializer(unregistered, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_telegram_id(self, request):
        """Get user by telegram_id"""
        telegram_id = request.query_params.get('telegram_id')
        if telegram_id:
            try:
                user = TelegramUser.objects.get(telegram_id=telegram_id)
                serializer = self.get_serializer(user)
                return Response(serializer.data)
            except TelegramUser.DoesNotExist:
                return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'error': 'telegram_id parameter required'}, status=status.HTTP_400_BAD_REQUEST)


class MahallaViewSet(viewsets.ModelViewSet):
    """Mahallas API"""
    queryset = Mahalla.objects.all().order_by('name')
    serializer_class = MahallaSerializer
    permission_classes = [AllowAny]
    filterset_fields = ['name', 'code']
    search_fields = ['name', 'code', 'description']
    
    @action(detail=True, methods=['get'])
    def complaints(self, request, pk=None):
        """Get mahalla's complaints"""
        mahalla = self.get_object()
        complaints = mahalla.complaints.all().order_by('-created_at')
        page = self.paginate_queryset(complaints)
        
        if page is not None:
            serializer = ComplaintSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = ComplaintSerializer(complaints, many=True)
        return Response(serializer.data)


class CategoryViewSet(viewsets.ModelViewSet):
    """Categories API"""
    queryset = Category.objects.all().order_by('name')
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    filterset_fields = ['name']
    search_fields = ['name', 'description']
    
    @action(detail=True, methods=['get'])
    def complaints(self, request, pk=None):
        """Get category's complaints"""
        category = self.get_object()
        complaints = category.complaints.all().order_by('-created_at')
        page = self.paginate_queryset(complaints)
        
        if page is not None:
            serializer = ComplaintSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = ComplaintSerializer(complaints, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def subcategories(self, request, pk=None):
        """Get category's subcategories"""
        category = self.get_object()
        subcategories = category.subcategories.all().order_by('title')
        serializer = SubCategorySerializer(subcategories, many=True)
        return Response(serializer.data)


class SubCategoryViewSet(viewsets.ModelViewSet):
    """SubCategories API"""
    queryset = SubCategory.objects.all().select_related('category').order_by('category__name', 'title')
    serializer_class = SubCategorySerializer
    permission_classes = [AllowAny]
    filterset_fields = ['category']
    search_fields = ['title', 'description', 'category__name']
    
    @action(detail=True, methods=['get'])
    def complaints(self, request, pk=None):
        """Get subcategory's complaints"""
        subcategory = self.get_object()
        complaints = subcategory.complaints.all().order_by('-created_at')
        page = self.paginate_queryset(complaints)
        
        if page is not None:
            serializer = ComplaintSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = ComplaintSerializer(complaints, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """Get subcategories by category_id"""
        category_id = request.query_params.get('category_id')
        if category_id:
            try:
                subcategories = SubCategory.objects.filter(category_id=category_id).order_by('title')
                serializer = self.get_serializer(subcategories, many=True)
                return Response(serializer.data)
            except ValueError:
                return Response({'error': 'Invalid category_id'}, status=400)
        return Response({'error': 'category_id parameter required'}, status=400)


class ComplaintFilter(filters.FilterSet):
    """Filters for complaints"""
    status = filters.CharFilter(field_name='status')
    priority = filters.CharFilter(field_name='priority')
    mahalla = filters.NumberFilter(field_name='mahalla__id')
    category = filters.NumberFilter(field_name='category__id')
    subcategory = filters.NumberFilter(field_name='subcategory__id')
    user = filters.NumberFilter(field_name='user__id')
    created_after = filters.DateFilter(field_name='created_at', lookup_expr='gte')
    created_before = filters.DateFilter(field_name='created_at', lookup_expr='lte')
    
    class Meta:
        model = Complaint
        fields = ['status', 'priority', 'mahalla', 'category', 'subcategory', 'user']


class ComplaintViewSet(viewsets.ModelViewSet):
    """Complaints API"""
    queryset = Complaint.objects.all().select_related(
        'user', 'mahalla', 'category', 'subcategory'
    ).prefetch_related(
        'images', 'status_history'
    ).order_by('-created_at')
    
    serializer_class = ComplaintSerializer
    permission_classes = [AllowAny]
    filterset_class = ComplaintFilter
    search_fields = ['title', 'description', 'location', 'admin_notes']
    
    def get_queryset(self):
        """
        Override queryset to filter by telegram_id if provided
        """
        queryset = super().get_queryset()
        
        # GET request bo'lsa va telegram_id parametri bo'lsa
        if self.request.method == 'GET':
            telegram_id = self.request.query_params.get('telegram_id')
            
            if telegram_id:
                try:
                    telegram_id = int(telegram_id)
                    # Faqat shu telegram_id ga tegishli complaintlarni qaytaramiz
                    queryset = queryset.filter(user__telegram_id=telegram_id)
                except ValueError:
                    # telegram_id raqam emas bo'lsa, barchasini qaytaramiz
                    pass
        
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ComplaintCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ComplaintStatusUpdateSerializer
        return ComplaintSerializer
    
    @action(detail=False, methods=['post'])
    def telegram_create(self, request):
        """Create complaint from Telegram bot"""
        serializer = ComplaintCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            # Add user data from Telegram
            request.user_data = {
                'full_name': request.data.get('full_name', 'Unknown User'),
                'username': request.data.get('username')
            }
            complaint = serializer.save()
            
            # Foydalanuvchi statistikasini yangilash
            complaint.user.update_complaint_stats()
            
            # Create notification for admins
            admins = TelegramUser.objects.filter(role='admin')
            for admin in admins:
                Notification.objects.create(
                    recipient=admin,
                    complaint=complaint,
                    notification_type='new_complaint',
                    message=f"🆕 Yangi murojaat: {complaint.title}"
                )
            
            return Response(
                ComplaintSerializer(complaint, context={'request': request}).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def add_image(self, request, pk=None):
        """Add image to complaint"""
        complaint = self.get_object()
        
        # Check permission: faqat complaint egasi yoki admin rasm qo'sha oladi
        telegram_id = request.data.get('telegram_id')
        if telegram_id:
            try:
                telegram_id = int(telegram_id)
                if complaint.user.telegram_id != telegram_id:
                    # Admin ekanligini tekshirish
                    user = TelegramUser.objects.filter(telegram_id=telegram_id, role='admin').first()
                    if not user:
                        return Response(
                            {'error': 'Siz bu murojaatga rasm qo\'sha olmaysiz'},
                            status=status.HTTP_403_FORBIDDEN
                        )
            except (ValueError, TypeError):
                pass
        
        serializer = ComplaintImageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(complaint=complaint)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def images(self, request, pk=None):
        """Get complaint images"""
        complaint = self.get_object()
        
        # Check permission: faqat complaint egasi yoki admin rasmlarni ko'ra oladi
        telegram_id = request.query_params.get('telegram_id')
        if telegram_id:
            try:
                telegram_id = int(telegram_id)
                if complaint.user.telegram_id != telegram_id:
                    # Admin ekanligini tekshirish
                    user = TelegramUser.objects.filter(telegram_id=telegram_id, role='admin').first()
                    if not user:
                        return Response(
                            {'error': 'Siz bu murojaat rasmlarini ko\'ra olmaysiz'},
                            status=status.HTTP_403_FORBIDDEN
                        )
            except (ValueError, TypeError):
                pass
        
        images = complaint.images.all()
        serializer = ComplaintImageSerializer(images, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        """Get complaint status history"""
        complaint = self.get_object()
        
        # Check permission: faqat complaint egasi yoki admin history ni ko'ra oladi
        telegram_id = request.query_params.get('telegram_id')
        if telegram_id:
            try:
                telegram_id = int(telegram_id)
                if complaint.user.telegram_id != telegram_id:
                    # Admin ekanligini tekshirish
                    user = TelegramUser.objects.filter(telegram_id=telegram_id, role='admin').first()
                    if not user:
                        return Response(
                            {'error': 'Siz bu murojaat tarixini ko\'ra olmaysiz'},
                            status=status.HTTP_403_FORBIDDEN
                        )
            except (ValueError, TypeError):
                pass
        
        history = complaint.status_history.all().order_by('-changed_at')
        serializer = StatusHistorySerializer(history, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get complaints statistics"""
        # Telegram_id parametri bo'lsa, faqat shu user uchun statistika
        telegram_id = request.query_params.get('telegram_id')
        
        if telegram_id:
            try:
                telegram_id = int(telegram_id)
                user = TelegramUser.objects.filter(telegram_id=telegram_id).first()
                if not user:
                    return Response({'error': 'Foydalanuvchi topilmadi'}, status=404)
                
                # User uchun statistika
                total_complaints = user.complaints.count()
                
                complaints_by_status = dict(
                    user.complaints.values_list('status').annotate(count=Count('id')).order_by('status')
                )
                
                # Time-based statistics
                today = timezone.now().date()
                start_of_week = today - timezone.timedelta(days=today.weekday())
                start_of_month = today.replace(day=1)
                
                complaints_today = user.complaints.filter(
                    created_at__date=today
                ).count()
                
                complaints_this_week = user.complaints.filter(
                    created_at__date__gte=start_of_week
                ).count()
                
                complaints_this_month = user.complaints.filter(
                    created_at__date__gte=start_of_month
                ).count()
                
                stats = {
                    'total_complaints': total_complaints,
                    'complaints_by_status': complaints_by_status,
                    'complaints_today': complaints_today,
                    'complaints_this_week': complaints_this_week,
                    'complaints_this_month': complaints_this_month,
                }
                
                serializer = StatsSerializer(stats)
                return Response(serializer.data)
                
            except ValueError:
                pass
        
        # Umumiy statistika
        total_complaints = Complaint.objects.count()
        total_users = TelegramUser.objects.filter(registration_completed=True).count()
        
        complaints_by_status = dict(
            Complaint.objects.values_list('status').annotate(count=Count('id')).order_by('status')
        )
        
        # Complaints by category
        complaints_by_category = {}
        for cat in Category.objects.all():
            complaints_by_category[cat.name] = cat.complaints.count()
        
        # Complaints by subcategory
        complaints_by_subcategory = {}
        for subcat in SubCategory.objects.all():
            count = subcat.complaints.count()
            if count > 0:
                complaints_by_subcategory[subcat.title] = count
        
        # Complaints by mahalla
        complaints_by_mahalla = {}
        for mahalla in Mahalla.objects.all():
            complaints_by_mahalla[mahalla.name] = mahalla.complaints.count()
        
        # Time-based statistics
        today = timezone.now().date()
        start_of_week = today - timezone.timedelta(days=today.weekday())
        start_of_month = today.replace(day=1)
        
        complaints_today = Complaint.objects.filter(
            created_at__date=today
        ).count()
        
        complaints_this_week = Complaint.objects.filter(
            created_at__date__gte=start_of_week
        ).count()
        
        complaints_this_month = Complaint.objects.filter(
            created_at__date__gte=start_of_month
        ).count()
        
        stats = {
            'total_complaints': total_complaints,
            'total_users': total_users,
            'complaints_by_status': complaints_by_status,
            'complaints_by_category': complaints_by_category,
            'complaints_by_subcategory': complaints_by_subcategory,
            'complaints_by_mahalla': complaints_by_mahalla,
            'complaints_today': complaints_today,
            'complaints_this_week': complaints_this_week,
            'complaints_this_month': complaints_this_month,
        }
        
        serializer = StatsSerializer(stats)
        return Response(serializer.data)


class StatusHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """Status history API"""
    queryset = StatusHistory.objects.all().select_related(
        'complaint', 'changed_by'
    ).order_by('-changed_at')
    
    serializer_class = StatusHistorySerializer
    permission_classes = [AllowAny]
    filterset_fields = ['complaint', 'new_status', 'changed_by']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        complaint_id = self.request.query_params.get('complaint_id')
        
        if complaint_id:
            queryset = queryset.filter(complaint_id=complaint_id)
        
        return queryset


class NotificationViewSet(viewsets.ModelViewSet):
    """Notifications API"""
    serializer_class = NotificationSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        # Hozircha hamma notificationlarni qaytaramiz
        return Notification.objects.all().order_by('-created_at')
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all notifications as read"""
        queryset = self.get_queryset()
        queryset.update(is_read=True)
        return Response({'status': 'All notifications marked as read'})
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark notification as read"""
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({'status': 'Notification marked as read'})


class StatsAPIView(APIView):
    """Statistics API"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        # Get statistics
        total_complaints = Complaint.objects.count()
        total_users = TelegramUser.objects.filter(registration_completed=True).count()
        
        # Status distribution
        status_stats = {}
        for status_code, status_name in Complaint.STATUS_CHOICES:
            count = Complaint.objects.filter(status=status_code).count()
            status_stats[status_name] = count
        
        # Category distribution
        category_stats = {}
        for category in Category.objects.all():
            count = Complaint.objects.filter(category=category).count()
            category_stats[category.name] = count
        
        # Subcategory distribution
        subcategory_stats = {}
        for subcategory in SubCategory.objects.all():
            count = subcategory.complaints.count()
            if count > 0:
                subcategory_stats[subcategory.title] = count
        
        # Mahalla distribution
        mahalla_stats = {}
        for mahalla in Mahalla.objects.all():
            count = Complaint.objects.filter(mahalla=mahalla).count()
            mahalla_stats[mahalla.name] = count
        
        # Recent activity
        today = timezone.now().date()
        start_of_week = today - timezone.timedelta(days=today.weekday())
        start_of_month = today.replace(day=1)
        
        today_count = Complaint.objects.filter(created_at__date=today).count()
        week_count = Complaint.objects.filter(created_at__date__gte=start_of_week).count()
        month_count = Complaint.objects.filter(created_at__date__gte=start_of_month).count()
        
        # Recent complaints
        recent_complaints = Complaint.objects.all().order_by('-created_at')[:10]
        recent_serializer = ComplaintSerializer(recent_complaints, many=True)
        
        data = {
            'total_complaints': total_complaints,
            'total_users': total_users,
            'status_distribution': status_stats,
            'category_distribution': category_stats,
            'subcategory_distribution': subcategory_stats,
            'mahalla_distribution': mahalla_stats,
            'today_complaints': today_count,
            'week_complaints': week_count,
            'month_complaints': month_count,
            'recent_complaints': recent_serializer.data,
        }
        
        return Response(data)


@api_view(['POST'])
@permission_classes([AllowAny])
def telegram_webhook(request):
    """Webhook for Telegram bot (simplified)"""
    # This endpoint would receive updates from Telegram
    # For now, just return success
    return Response({'status': 'ok'})


# Public endpoints for Telegram bot
@api_view(['GET'])
@permission_classes([AllowAny])
def get_mahallas(request):
    """Get list of mahallas for Telegram bot"""
    mahallas = Mahalla.objects.all().values('id', 'name')
    return Response(list(mahallas))


@api_view(['GET'])
@permission_classes([AllowAny])
def get_categories(request):
    """Get list of categories for Telegram bot"""
    categories = Category.objects.all().values('id', 'name', 'icon')
    return Response(list(categories))


@api_view(['GET'])
@permission_classes([AllowAny])
def get_subcategories(request):
    """Get list of subcategories for Telegram bot"""
    category_id = request.query_params.get('category_id')
    if category_id:
        subcategories = SubCategory.objects.filter(category_id=category_id).values('id', 'title')
    else:
        subcategories = SubCategory.objects.all().values('id', 'title', 'category_id')
    return Response(list(subcategories))


@api_view(['POST'])
@permission_classes([AllowAny])
def telegram_register_user(request):
    """Register Telegram user (yangi versiyasi)"""
    telegram_id = request.data.get('telegram_id')
    full_name = request.data.get('full_name')
    username = request.data.get('username')
    phone_number = request.data.get('phone_number')
    second_phone = request.data.get('second_phone')
    age = request.data.get('age')
    
    if not telegram_id or not full_name:
        return Response(
            {'error': 'telegram_id va full_name majburiy'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Foydalanuvchi bor-yo'qligini tekshirish
    user_exists = TelegramUser.objects.filter(telegram_id=telegram_id).exists()
    
    if user_exists:
        # Mavjud foydalanuvchini yangilash
        user = TelegramUser.objects.get(telegram_id=telegram_id)
        user.full_name = full_name
        user.username = username
        
        # Agar telefon va yosh kiritilgan bo'lsa
        if phone_number:
            user.phone_number = phone_number
        if second_phone:
            user.second_phone = second_phone
        if age:
            user.age = age
        
        # Agar barcha majburiy maydonlar to'ldirilgan bo'lsa
        if (phone_number and age):
            user.registration_completed = True
        
        user.save()
        serializer = TelegramUserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    else:
        # Yangi foydalanuvchi yaratish
        data = {
            'telegram_id': telegram_id,
            'full_name': full_name,
            'username': username,
            'phone_number': phone_number,
            'second_phone': second_phone,
            'age': age
        }
        
        serializer = TelegramUserCreateSerializer(data=data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                TelegramUserSerializer(user).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def telegram_update_profile(request):
    """Update Telegram user profile (alohida endpoint)"""
    telegram_id = request.data.get('telegram_id')
    full_name = request.data.get('full_name')
    phone_number = request.data.get('phone_number')
    second_phone = request.data.get('second_phone')
    age = request.data.get('age')
    
    if not telegram_id:
        return Response(
            {'error': 'telegram_id majburiy'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        user = TelegramUser.objects.get(telegram_id=telegram_id)
    except TelegramUser.DoesNotExist:
        return Response(
            {'error': 'Foydalanuvchi topilmadi'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Yangilash
    if full_name:
        user.full_name = full_name
    if phone_number:
        user.phone_number = phone_number
    if second_phone:
        user.second_phone = second_phone
    if age:
        user.age = age
    
    # Agar barcha majburiy maydonlar to'ldirilgan bo'lsa
    if (user.phone_number and user.age and user.full_name):
        user.registration_completed = True
    
    user.save()
    serializer = TelegramUserSerializer(user)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def check_user_registration(request, telegram_id):
    """Check if user is registered and has completed registration"""
    try:
        user = TelegramUser.objects.get(telegram_id=telegram_id)
        return Response({
            'exists': True,
            'registration_completed': user.registration_completed,
            'full_name': user.full_name,
            'phone_number': user.phone_number,
            'age': user.age,
            'second_phone': user.second_phone,
            'username': user.username,
            'role': user.role
        })
    except TelegramUser.DoesNotExist:
        return Response({
            'exists': False,
            'registration_completed': False
        })