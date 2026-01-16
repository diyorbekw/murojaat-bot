"""
Django admin configuration
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import TelegramUser, Mahalla, Category, SubCategory, Complaint, ComplaintImage, StatusHistory, Notification


@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    """Admin for Telegram users (yangi versiyasi)"""
    list_display = ['telegram_id', 'full_name', 'username', 'phone_number', 'age', 
                   'registration_completed', 'role', 'complaints_count', 'created_at']
    list_filter = ['role', 'registration_completed', 'is_active', 'created_at']
    search_fields = ['telegram_id', 'full_name', 'username', 'phone_number']
    readonly_fields = ['created_at', 'updated_at', 'last_active', 'complaints_count',
                      'last_complaint_date']
    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('telegram_id', 'full_name', 'username', 'phone_number', 
                      'second_phone', 'age', 'language')
        }),
        ('Holat va Ruxsat', {
            'fields': ('is_active', 'is_blocked', 'role', 'registration_completed')
        }),
        ('Statistika', {
            'fields': ('complaints_count', 'last_complaint_date')
        }),
        ('Faollik', {
            'fields': ('created_at', 'updated_at', 'last_active')
        }),
    )
    
    def complaints_count(self, obj):
        return obj.get_complaints_count()
    complaints_count.short_description = 'Murojaatlar soni'


@admin.register(Mahalla)
class MahallaAdmin(admin.ModelAdmin):
    """Admin for mahallas"""
    list_display = ['name', 'code', 'complaints_count', 'created_at']
    search_fields = ['name', 'code']
    readonly_fields = ['created_at']
    
    def complaints_count(self, obj):
        return obj.complaints.count()
    complaints_count.short_description = 'Murojaatlar soni'


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Admin for categories"""
    list_display = ['name', 'icon', 'subcategories_count', 'complaints_count', 'created_at']
    search_fields = ['name']
    readonly_fields = ['created_at']
    
    def subcategories_count(self, obj):
        return obj.subcategories.count()
    subcategories_count.short_description = 'Subkategoriyalar soni'
    
    def complaints_count(self, obj):
        return obj.complaints.count()
    complaints_count.short_description = 'Murojaatlar soni'


@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    """Admin for subcategories"""
    list_display = ['title', 'category', 'complaints_count', 'created_at']
    list_filter = ['category']
    search_fields = ['title', 'category__name']
    readonly_fields = ['created_at']
    
    def complaints_count(self, obj):
        return obj.complaints.count()
    complaints_count.short_description = 'Murojaatlar soni'


class ComplaintImageInline(admin.TabularInline):
    """Inline for complaint images"""
    model = ComplaintImage
    extra = 0
    readonly_fields = ['channel_message_id', 'file_id', 'file_size', 'created_at']
    can_delete = False


class StatusHistoryInline(admin.TabularInline):
    """Inline for status history"""
    model = StatusHistory
    extra = 0
    readonly_fields = ['old_status', 'new_status', 'changed_by', 'changed_at', 'note']
    can_delete = False


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    """Admin for complaints"""
    list_display = ['id', 'title', 'user', 'mahalla', 'category', 'subcategory', 
                   'status_display', 'priority_display', 'images_count', 'created_at']
    list_filter = ['status', 'priority', 'mahalla', 'category', 'subcategory', 'created_at']
    search_fields = ['title', 'description', 'location', 'admin_notes']
    readonly_fields = ['created_at', 'updated_at', 'resolved_at', 'images_count', 'days_open']
    inlines = [ComplaintImageInline, StatusHistoryInline]
    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('user', 'mahalla', 'category', 'subcategory', 'title', 'description', 'location')
        }),
        ('Holat', {
            'fields': ('status', 'priority', 'admin_notes')
        }),
        ('Vaqt', {
            'fields': ('created_at', 'updated_at', 'resolved_at')
        }),
        ('Statistika', {
            'fields': ('images_count', 'days_open')
        }),
    )
    
    def status_display(self, obj):
        status_icons = {
            'new': '🆕',
            'in_progress': '🔄',
            'solved': '✅',
            'rejected': '❌',
            'delayed': '⏳',
        }
        return f"{status_icons.get(obj.status, '')} {obj.get_status_display()}"
    status_display.short_description = 'Holati'
    
    def priority_display(self, obj):
        priority_colors = {
            'low': 'gray',
            'medium': 'blue',
            'high': 'orange',
            'critical': 'red',
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            priority_colors.get(obj.priority, 'black'),
            obj.get_priority_display()
        )
    priority_display.short_description = 'Muhimlik'
    
    def images_count(self, obj):
        return obj.images.count()
    images_count.short_description = 'Rasmlar soni'


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Admin for notifications"""
    list_display = ['id', 'recipient', 'complaint', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['recipient__full_name', 'message']
    readonly_fields = ['created_at']
    list_editable = ['is_read']


# Customize admin site
admin.site.site_header = "Murojaatlar Tizimi Admin"
admin.site.site_title = "Murojaatlar Admin"
admin.site.index_title = "Boshqaruv paneli"