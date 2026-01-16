"""
DRF serializers for API
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from .models import TelegramUser, Mahalla, Category, SubCategory, Complaint, ComplaintImage, StatusHistory, Notification
from django.utils import timezone


class UserSerializer(serializers.ModelSerializer):
    """User serializer for admin users"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_staff']
        read_only_fields = ['is_staff']


class TelegramUserSerializer(serializers.ModelSerializer):
    """Telegram user serializer (yangi versiyasi)"""
    complaints_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = TelegramUser
        fields = ['id', 'telegram_id', 'full_name', 'username', 'phone_number', 
                 'second_phone', 'age', 'language', 'is_active', 'is_blocked',
                 'role', 'registration_completed', 'complaints_count',
                 'last_complaint_date', 'created_at', 'updated_at', 'last_active']
        read_only_fields = ['created_at', 'updated_at', 'last_active', 'complaints_count',
                           'last_complaint_date', 'registration_completed']
    
    def create(self, validated_data):
        # Ro'yxatdan o'tish tugallanmagan holatda yaratish
        user = TelegramUser.objects.create(**validated_data)
        return user


class TelegramUserCreateSerializer(serializers.ModelSerializer):
    """Telegram user creation serializer for bot"""
    class Meta:
        model = TelegramUser
        fields = ['telegram_id', 'full_name', 'username', 'phone_number', 
                 'second_phone', 'age']
    
    def create(self, validated_data):
        # Foydalanuvchi ro'yxatdan o'tgan holatda yaratish
        user = TelegramUser.objects.create(
            **validated_data,
            registration_completed=True
        )
        return user


class TelegramUserUpdateSerializer(serializers.ModelSerializer):
    """Telegram user update serializer"""
    class Meta:
        model = TelegramUser
        fields = ['full_name', 'phone_number', 'second_phone', 'age']
    
    def update(self, instance, validated_data):
        # Yangilash va registration_completed ni true qilish
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Agar barcha majburiy maydonlar to'ldirilgan bo'lsa
        if (instance.full_name and instance.phone_number and instance.age):
            instance.registration_completed = True
        
        instance.save()
        return instance


class MahallaSerializer(serializers.ModelSerializer):
    """Mahalla serializer"""
    complaints_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Mahalla
        fields = ['id', 'name', 'code', 'description', 'created_at', 'complaints_count']
        read_only_fields = ['created_at']
    
    def get_complaints_count(self, obj):
        return obj.complaints.count()


class CategorySerializer(serializers.ModelSerializer):
    """Category serializer"""
    subcategories_count = serializers.SerializerMethodField()
    complaints_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'icon', 'description', 'created_at', 'subcategories_count', 'complaints_count']
        read_only_fields = ['created_at']
    
    def get_subcategories_count(self, obj):
        return obj.subcategories.count()
    
    def get_complaints_count(self, obj):
        return obj.complaints.count()


class SubCategorySerializer(serializers.ModelSerializer):
    """SubCategory serializer"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    complaints_count = serializers.SerializerMethodField()
    
    class Meta:
        model = SubCategory
        fields = ['id', 'category', 'category_name', 'title', 'description', 'created_at', 'complaints_count']
        read_only_fields = ['created_at']
    
    def get_complaints_count(self, obj):
        return obj.complaints.count()


class ComplaintImageSerializer(serializers.ModelSerializer):
    """Complaint image serializer"""
    class Meta:
        model = ComplaintImage
        fields = ['id', 'channel_message_id', 'file_id', 'file_size', 'created_at']
        read_only_fields = ['created_at']


class StatusHistorySerializer(serializers.ModelSerializer):
    """Status history serializer"""
    changed_by = UserSerializer(read_only=True)
    
    class Meta:
        model = StatusHistory
        fields = ['id', 'old_status', 'new_status', 'changed_by', 'changed_at', 'note']
        read_only_fields = ['changed_at']


class ComplaintSerializer(serializers.ModelSerializer):
    """Complaint serializer with related data"""
    user = TelegramUserSerializer(read_only=True)
    mahalla = MahallaSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    subcategory = SubCategorySerializer(read_only=True)
    images = ComplaintImageSerializer(many=True, read_only=True)
    status_history = StatusHistorySerializer(many=True, read_only=True)
    images_count = serializers.IntegerField(read_only=True)
    days_open = serializers.IntegerField(read_only=True)
    
    # Write-only fields for creation/update
    mahalla_id = serializers.PrimaryKeyRelatedField(
        queryset=Mahalla.objects.all(),
        write_only=True,
        source='mahalla',
        required=False
    )
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        write_only=True,
        source='category',
        required=False
    )
    subcategory_id = serializers.PrimaryKeyRelatedField(
        queryset=SubCategory.objects.all(),
        write_only=True,
        source='subcategory',
        required=False,
        allow_null=True
    )
    telegram_user_id = serializers.IntegerField(write_only=True, required=False)
    
    class Meta:
        model = Complaint
        fields = [
            'id', 'user', 'mahalla', 'category', 'subcategory', 'title', 'description', 'location',
            'status', 'priority', 'created_at', 'updated_at', 'resolved_at',
            'admin_notes', 'images', 'status_history', 'images_count', 'days_open',
            'mahalla_id', 'category_id', 'subcategory_id', 'telegram_user_id'
        ]
        read_only_fields = ['created_at', 'updated_at', 'resolved_at', 'images_count', 'days_open']
    
    def create(self, validated_data):
        # Get telegram_user_id if provided
        telegram_user_id = validated_data.pop('telegram_user_id', None)
        
        if telegram_user_id:
            # TelegramUser ni topish
            try:
                telegram_user = TelegramUser.objects.get(telegram_id=telegram_user_id)
            except TelegramUser.DoesNotExist:
                # Agar topilmasa, yangi yaratish
                request = self.context.get('request')
                user_data = {}
                
                if request and hasattr(request, 'user_data'):
                    user_data = request.user_data
                
                telegram_user = TelegramUser.objects.create(
                    telegram_id=telegram_user_id,
                    full_name=user_data.get('full_name', 'Unknown User'),
                    username=user_data.get('username'),
                    role='user',
                    registration_completed=False  # Ro'yxat to'liq emas
                )
            
            # Set the user
            validated_data['user'] = telegram_user
        
        return super().create(validated_data)


class ComplaintCreateSerializer(serializers.ModelSerializer):
    """Simplified serializer for complaint creation from Telegram"""
    telegram_id = serializers.IntegerField(write_only=True)
    mahalla_name = serializers.CharField(write_only=True, max_length=100)
    category_name = serializers.CharField(write_only=True, max_length=100)
    subcategory_title = serializers.CharField(write_only=True, max_length=150, required=False, allow_blank=True)
    
    class Meta:
        model = Complaint
        fields = ['telegram_id', 'mahalla_name', 'category_name', 'subcategory_title', 'title', 
                 'description', 'location', 'priority']
    
    def create(self, validated_data):
        telegram_id = validated_data.pop('telegram_id')
        mahalla_name = validated_data.pop('mahalla_name')
        category_name = validated_data.pop('category_name')
        subcategory_title = validated_data.pop('subcategory_title', None)
        
        # TelegramUser ni topish
        try:
            telegram_user = TelegramUser.objects.get(telegram_id=telegram_id)
        except TelegramUser.DoesNotExist:
            # Agar topilmasa, yangi yaratish (ro'yxat to'liq emas)
            request = self.context.get('request')
            user_data = request.user_data if request and hasattr(request, 'user_data') else {}
            
            telegram_user = TelegramUser.objects.create(
                telegram_id=telegram_id,
                full_name=user_data.get('full_name', 'Unknown User'),
                username=user_data.get('username'),
                role='user',
                registration_completed=False
            )
        
        # Update last_active
        telegram_user.last_active = timezone.now()
        telegram_user.save()
        
        # Get or create Mahalla
        mahalla, _ = Mahalla.objects.get_or_create(
            name=mahalla_name,
            defaults={
                'code': mahalla_name.replace('-', '').lower()[:10],
                'description': f"{mahalla_name} mahallasi"
            }
        )
        
        # Get or create Category
        category, _ = Category.objects.get_or_create(
            name=category_name,
            defaults={
                'icon': '📝',
                'description': f"{category_name} kategoriyasi"
            }
        )
        
        # Get SubCategory if provided
        subcategory = None
        if subcategory_title and subcategory_title.strip():
            subcategory, _ = SubCategory.objects.get_or_create(
                category=category,
                title=subcategory_title.strip(),
                defaults={
                    'description': f"{subcategory_title.strip()} - {category_name} kichik kategoriyasi"
                }
            )
        
        # Create complaint
        complaint = Complaint.objects.create(
            user=telegram_user,
            mahalla=mahalla,
            category=category,
            subcategory=subcategory,
            **validated_data
        )
        
        return complaint


class ComplaintStatusUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating complaint status"""
    note = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = Complaint
        fields = ['status', 'admin_notes', 'note']
    
    def update(self, instance, validated_data):
        note = validated_data.pop('note', None)
        old_status = instance.status
        new_status = validated_data.get('status', old_status)
        
        # Save old admin_notes if exists
        old_admin_notes = instance.admin_notes
        
        # Update complaint
        instance = super().update(instance, validated_data)
        
        # Create status history if status changed
        if old_status != new_status:
            StatusHistory.objects.create(
                complaint=instance,
                old_status=old_status,
                new_status=new_status,
                changed_by=self.context.get('request').user if self.context.get('request').user.is_authenticated else None,
                note=note or f"Holat {old_status} dan {new_status} ga o'zgartirildi"
            )
        
        return instance


class NotificationSerializer(serializers.ModelSerializer):
    """Notification serializer"""
    complaint_id = serializers.IntegerField(source='complaint.id', read_only=True)
    complaint_title = serializers.CharField(source='complaint.title', read_only=True)
    
    class Meta:
        model = Notification
        fields = ['id', 'recipient', 'complaint_id', 'complaint_title', 
                 'notification_type', 'message', 'is_read', 'created_at']
        read_only_fields = ['created_at']


class StatsSerializer(serializers.Serializer):
    """Statistics serializer"""
    total_complaints = serializers.IntegerField()
    total_users = serializers.IntegerField()
    complaints_by_status = serializers.DictField()
    complaints_by_category = serializers.DictField()
    complaints_by_subcategory = serializers.DictField()
    complaints_by_mahalla = serializers.DictField()
    complaints_today = serializers.IntegerField()
    complaints_this_week = serializers.IntegerField()
    complaints_this_month = serializers.IntegerField()
    
    def to_representation(self, instance):
        return instance