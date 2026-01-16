"""
Django models for complaints system with SQLite
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
import uuid


class TelegramUser(models.Model):
    """
    Telegram user model (yangi versiyasi)
    """
    ROLE_CHOICES = [
        ('user', 'Foydalanuvchi'),
        ('admin', 'Administrator'),
    ]
    
    telegram_id = models.BigIntegerField(unique=True, verbose_name=_("Telegram ID"))
    full_name = models.CharField(max_length=255, verbose_name=_("To'liq ism"))
    username = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Username"))
    phone_number = models.CharField(max_length=20, blank=True, null=True, verbose_name=_("Asosiy telefon raqam"))
    second_phone = models.CharField(max_length=20, blank=True, null=True, verbose_name=_("Qo'shimcha telefon raqam"))
    age = models.PositiveIntegerField(blank=True, null=True, verbose_name=_("Yosh"))
    language = models.CharField(max_length=10, default='uz', verbose_name=_("Til"))
    is_active = models.BooleanField(default=True, verbose_name=_("Faol"))
    is_blocked = models.BooleanField(default=False, verbose_name=_("Bloklangan"))
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user', verbose_name=_("Rol"))
    registration_completed = models.BooleanField(default=False, verbose_name=_("Ro'yxatdan o'tish tugallandi"))
    
    # Statistika uchun
    complaints_count = models.PositiveIntegerField(default=0, verbose_name=_("Murojaatlar soni"))
    last_complaint_date = models.DateTimeField(blank=True, null=True, verbose_name=_("Oxirgi murojaat sanasi"))
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Yaratilgan sana"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Yangilangan sana"))
    last_active = models.DateTimeField(auto_now=True, verbose_name=_("Oxirgi faollik"))
    
    class Meta:
        verbose_name = _("Telegram foydalanuvchi")
        verbose_name_plural = _("Telegram foydalanuvchilar")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['telegram_id']),
            models.Index(fields=['role']),
            models.Index(fields=['created_at']),
            models.Index(fields=['is_active']),
            models.Index(fields=['registration_completed']),
        ]
    
    def __str__(self):
        return f"{self.full_name} (@{self.username})" if self.username else self.full_name
    
    def get_complaints_count(self):
        return self.complaints.count()
    
    def update_complaint_stats(self):
        """Murojaatlar statistikasini yangilash"""
        self.complaints_count = self.complaints.count()
        last_complaint = self.complaints.order_by('-created_at').first()
        if last_complaint:
            self.last_complaint_date = last_complaint.created_at
        self.save(update_fields=['complaints_count', 'last_complaint_date'])
    
    def complete_registration(self):
        """Ro'yxatdan o'tishni tugatish"""
        self.registration_completed = True
        self.save(update_fields=['registration_completed'])


class Mahalla(models.Model):
    """
    Mahalla model
    """
    name = models.CharField(max_length=100, unique=True, verbose_name=_("Mahalla nomi"))
    code = models.CharField(max_length=10, unique=True, verbose_name=_("Mahalla kodi"))
    description = models.TextField(blank=True, null=True, verbose_name=_("Tavsif"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Yaratilgan sana"))
    
    class Meta:
        verbose_name = _("Mahalla")
        verbose_name_plural = _("Mahallalar")
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Category(models.Model):
    """
    Complaint category model
    """
    name = models.CharField(max_length=100, unique=True, verbose_name=_("Kategoriya nomi"))
    icon = models.CharField(max_length=50, default='📝', verbose_name=_("Ikonka"))
    description = models.TextField(blank=True, null=True, verbose_name=_("Tavsif"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Yaratilgan sana"))
    
    class Meta:
        verbose_name = _("Kategoriya")
        verbose_name_plural = _("Kategoriyalar")
        ordering = ['name']
    
    def __str__(self):
        return f"{self.icon} {self.name}"


class SubCategory(models.Model):
    """
    Subcategory model for more specific classification
    """
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subcategories', verbose_name=_("Kategoriya"))
    title = models.CharField(max_length=150, verbose_name=_("Subkategoriya nomi"))
    description = models.TextField(blank=True, null=True, verbose_name=_("Tavsif"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Yaratilgan sana"))
    
    class Meta:
        verbose_name = _("Subkategoriya")
        verbose_name_plural = _("Subkategoriyalar")
        ordering = ['category', 'title']
        unique_together = ['category', 'title']
    
    def __str__(self):
        return f"{self.category.name} - {self.title}"


class Complaint(models.Model):
    """
    Main complaint model
    """
    STATUS_CHOICES = [
        ('new', '🆕 Yangi'),
        ('in_progress', '🔄 Jarayonda'),
        ('solved', '✅ Hal qilindi'),
        ('rejected', '❌ Rad etildi'),
        ('delayed', '⏳ Kehtirildi'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Past'),
        ('medium', 'Oʻrta'),
        ('high', 'Yuqori'),
        ('critical', 'Judayam muhim'),
    ]
    
    user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE, related_name='complaints', verbose_name=_("Foydalanuvchi"))
    mahalla = models.ForeignKey(Mahalla, on_delete=models.SET_NULL, null=True, related_name='complaints', verbose_name=_("Mahalla"))
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='complaints', verbose_name=_("Kategoriya"))
    subcategory = models.ForeignKey(SubCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='complaints', verbose_name=_("Subkategoriya"))
    title = models.CharField(max_length=200, verbose_name=_("Sarlavha"))
    description = models.TextField(verbose_name=_("Muammo tavsifi"))
    location = models.CharField(max_length=500, blank=True, null=True, verbose_name=_("Aniq manzil"))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new', verbose_name=_("Holati"))
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium', verbose_name=_("Muhimlik darajasi"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Yaratilgan sana"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Yangilangan sana"))
    resolved_at = models.DateTimeField(blank=True, null=True, verbose_name=_("Hal qilingan sana"))
    admin_notes = models.TextField(blank=True, null=True, verbose_name=_("Administrator izohlari"))
    
    class Meta:
        verbose_name = _("Murojaat")
        verbose_name_plural = _("Murojaatlar")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['priority']),
            models.Index(fields=['created_at']),
            models.Index(fields=['mahalla', 'status']),
            models.Index(fields=['category', 'subcategory']),
        ]
    
    def __str__(self):
        return f"Murojaat #{self.id} - {self.title[:50]}"
    
    def save(self, *args, **kwargs):
        # Update resolved_at if status changed to solved
        is_new = self.pk is None
        if not is_new:
            old_status = Complaint.objects.get(pk=self.pk).status
            if old_status != 'solved' and self.status == 'solved':
                self.resolved_at = timezone.now()
            elif old_status == 'solved' and self.status != 'solved':
                self.resolved_at = None
        elif self.status == 'solved':
            self.resolved_at = timezone.now()
        
        super().save(*args, **kwargs)
        
        # Foydalanuvchi statistikasini yangilash
        if is_new:
            self.user.update_complaint_stats()
    
    @property
    def images_count(self):
        return self.images.count()
    
    @property
    def days_open(self):
        if self.created_at:
            return (timezone.now() - self.created_at).days
        return 0


class ComplaintImage(models.Model):
    """
    Complaint images model
    """
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='images', verbose_name=_("Murojaat"))
    channel_message_id = models.BigIntegerField(verbose_name=_("Kanal xabar IDsi"))
    file_id = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Fayl ID"))
    file_size = models.IntegerField(blank=True, null=True, verbose_name=_("Fayl hajmi"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Yaratilgan sana"))
    
    class Meta:
        verbose_name = _("Murojaat rasmi")
        verbose_name_plural = _("Murojaat rasmlari")
        ordering = ['created_at']
    
    def __str__(self):
        return f"Rasm #{self.id} - Murojaat #{self.complaint.id}"


class StatusHistory(models.Model):
    """
    Complaint status history model
    """
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='status_history', verbose_name=_("Murojaat"))
    old_status = models.CharField(max_length=20, choices=Complaint.STATUS_CHOICES, verbose_name=_("Oldingi holat"))
    new_status = models.CharField(max_length=20, choices=Complaint.STATUS_CHOICES, verbose_name=_("Yangi holat"))
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("O'zgartirgan"))
    changed_at = models.DateTimeField(auto_now_add=True, verbose_name=_("O'zgartirilgan sana"))
    note = models.TextField(blank=True, null=True, verbose_name=_("Izoh"))
    
    class Meta:
        verbose_name = _("Holat tarixi")
        verbose_name_plural = _("Holat tarixlari")
        ordering = ['-changed_at']
    
    def __str__(self):
        return f"#{self.complaint.id} - {self.old_status} → {self.new_status}"


class Notification(models.Model):
    """
    Notification model for admin notifications
    """
    TYPE_CHOICES = [
        ('new_complaint', 'Yangi murojaat'),
        ('status_change', 'Holat o\'zgarishi'),
        ('admin_message', 'Administrator xabari'),
        ('reminder', 'Eslatma'),
    ]
    
    recipient = models.ForeignKey(TelegramUser, on_delete=models.CASCADE, verbose_name=_("Qabul qiluvchi"))
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, null=True, blank=True, verbose_name=_("Murojaat"))
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES, verbose_name=_("Xabar turi"))
    message = models.TextField(verbose_name=_("Xabar matni"))
    is_read = models.BooleanField(default=False, verbose_name=_("O'qilgan"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Yaratilgan sana"))
    
    class Meta:
        verbose_name = _("Xabar")
        verbose_name_plural = _("Xabarlar")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
        ]
    
    def __str__(self):
        return f"{self.notification_type} - {self.recipient.full_name}"