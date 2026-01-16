"""
Standart ma'lumotlarni yaratish skripti (SubCategorylar bilan)
"""

import os
import django
from django.db import transaction
from django.contrib.auth.models import User
import sys


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Django settings ni yuklash - sizning loyiha tuzilmangizga qarab
try:
    # 1-variant: agar 'config' nomli papka bo'lsa
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()
except ModuleNotFoundError:
    try:
        # 2-variant: agar 'murojaat_bot' nomli papka bo'lsa
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'murojaat_bot.settings')
        django.setup()
    except ModuleNotFoundError:
        try:
            # 3-variant: agar settings.py direktoriyada bo'lsa
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
            django.setup()
        except ModuleNotFoundError:
            print("❌ Django settings topilmadi!")
            print("Iltimos, quyidagi variantlardan birini tekshiring:")
            print("1. 'config.settings'")
            print("2. 'murojaat_bot.settings'")
            print("3. 'settings'")
            sys.exit(1)

from core.models import Category, SubCategory, Mahalla, TelegramUser


def create_superuser():
    """Django superuser yaratish"""
    try:
        # Superuser allaqachon mavjud bo'lsa
        user = User.objects.get(username='admin')
        print(f"✅ SUPERUSER: {user.username} (allaqachon mavjud)")
        return user
    except User.DoesNotExist:
        # Yangi superuser yaratish
        user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )
        print(f"✅ SUPERUSER: {user.username} parol: admin123")
        return user


@transaction.atomic
def create_categories_with_subcategories():
    """Kategoriya va subkategoriyalarni yaratish"""
    
    # Asosiy kategoriyalar
    categories = [
        ("Elektr ta'minoti", "⚡"),
        ("Ichimlik suvi", "🚰"),
        ("Pensiya", "👴"),
        ("Ijtimoiy to'lovlar", "💰"),
        ("Mahalla yettiligi faoliyati", "🏘️"),
        ("Jinoyatchilik / xavfsizlik", "🚨"),
        ("Tibbiyot", "🏥"),
        ("Avariya holatlari", "🚧"),
        ("Obodonlashtirish", "🌳"),
        ("Chiqindi", "🗑️"),
        ("Yoritish", "💡"),
        ("Ta'lim", "📚"),
        ("Transport", "🚌"),
        ("Boshqa", "📋"),
    ]
    
    # Har bir kategoriya uchun subkategoriyalar
    subcategories_data = {
        "Elektr ta'minoti": [
            "Elektr ta'minotining uzilishi",
            "Oqim kuchining pastligi",
            "Elektr tarmog'idagi nosozlik",
            "Elektr quvvat o'lchagichi muammosi",
        ],
        "Ichimlik suvi": [
            "Suv ta'minotining uzilishi",
            "Suvning sifati past",
            "Suv bosimi past",
            "Suv quvurlarining nosozligi",
        ],
        "Pensiya": [
            "Pensiya to'lovining kechikishi",
            "Pensiya miqdoridagi xato",
            "Pensiya hujjatlarini rasmiylashtirish",
            "Pensiyaga chiqish masalalari",
        ],
        "Ijtimoiy to'lovlar": [
            "Nafaqa to'lovlari",
            "Ijtimoiy yordam",
            "Nogironlik nafaqasi",
            "Bolalar parvarishi nafaqasi",
        ],
        "Mahalla yettiligi faoliyati": [
            "Mahalla yig'ilishlari",
            "Mahalla obodonlashtirish ishlari",
            "Mahalla tadbirlari",
            "Mahalla aholisi bilan ishlash",
        ],
        "Jinoyatchilik / xavfsizlik": [
            "O'g'rilik hodisasi",
            "Tartibsizlik va shovqin",
            "Xavfli joylar",
            "Trafik xavfsizligi",
        ],
        "Tibbiyot": [
            "Shifokor ishtirokisizligi",
            "Dori-darmon yetishmasligi",
            "Shifoxona sharoitlari",
            "Tez yordam xizmati",
        ],
        "Avariya holatlari": [
            "Kommunal avariyalar",
            "Yo'l-transport avariyalari",
            "Tabiiy ofatlar",
            "Qurilish maydonidagi xavflar",
        ],
        "Obodonlashtirish": [
            "Yashil maydonlar",
            "Ko'cha va yo'llarni obodonlashtirish",
            "Dam olish maskanlari",
            "Sport maydonchalari",
        ],
        "Chiqindi": [
            "Chiqindilarni olib ketish",
            "Chiqindi qutilari",
            "Chiqindi maydonlari",
            "Qayta ishlash masalalari",
        ],
        "Yoritish": [
            "Ko'cha chiroqlari ishlamay qolishi",
            "Yorug'lik yetishmasligi",
            "Elektr energiyasi sarfi",
            "Yoritish tizimini ta'mirlash",
        ],
        "Ta'lim": [
            "Maktab binolari holati",
            "O'qituvchilar soni",
            "O'quv uskunalari",
            "Maktab transporti",
        ],
        "Transport": [
            "Avtobuslar qatnovi",
            "Taksi xizmati",
            "Yo'llar holati",
            "Transport narxlari",
        ],
        "Boshqa": [
            "Ruxsatnomali masalalar",
            "Soliq masalalari",
            "Qurilish ruxsatnomalari",
            "Umumiy muammolar",
        ],
    }
    
    created_categories = 0
    created_subcategories = 0
    
    # Kategoriyalarni yaratish
    print("\n📋 KATEGORIYALAR VA SUBKATEGORIYALAR:")
    print("-" * 50)
    
    for name, icon in categories:
        category, created = Category.objects.get_or_create(
            name=name,
            defaults={
                "icon": icon,
                "description": f"{name} bilan bog'liq muammolar"
            }
        )
        
        if created:
            created_categories += 1
            print(f"✅ KATEGORIYA: {icon} {name}")
        else:
            print(f"ℹ️ KATEGORIYA: {icon} {name} (allaqachon mavjud)")
        
        # Subkategoriyalarni yaratish
        if name in subcategories_data:
            for sub_title in subcategories_data[name]:
                subcat, sub_created = SubCategory.objects.get_or_create(
                    category=category,
                    title=sub_title,
                    defaults={
                        "description": f"{sub_title} - {name} kichik kategoriyasi"
                    }
                )
                
                if sub_created:
                    created_subcategories += 1
                    print(f"   ├── 📌 {sub_title}")
                else:
                    print(f"   ├── 📌 {sub_title} (allaqachon mavjud)")
    
    return created_categories, created_subcategories


def create_mahallas():
    """Mahallalarni yaratish"""
    created_mahallas = 0
    
    print("\n🏘️ MAHALLALAR:")
    print("-" * 30)
    
    for i in range(1, 11):
        mahalla_name = f"{i}-mahalla"
        code = f"M{str(i).zfill(3)}"
        
        mahalla, created = Mahalla.objects.get_or_create(
            name=mahalla_name,
            defaults={
                "code": code,
                "description": f"{mahalla_name} - Karmana tumani"
            }
        )
        
        if created:
            created_mahallas += 1
            print(f"✅ MAHALLA: {mahalla_name} ({code})")
        else:
            print(f"ℹ️ MAHALLA: {mahalla_name} ({code}) - allaqachon mavjud")
    
    return created_mahallas


def create_default_admin():
    """Telegram admin foydalanuvchini yaratish"""
    admin_telegram_id = 5515940993  # Sizning ID'ingiz
    
    print("\n👨‍💻 TELEGRAM ADMIN:")
    print("-" * 30)
    
    try:
        user, created = TelegramUser.objects.get_or_create(
            telegram_id=admin_telegram_id,
            defaults={
                "full_name": "Admin User",
                "username": "admin",
                "role": "admin",
                "registration_completed": True,
                "phone_number": "+998901234567",
                "age": 30,
                "is_active": True
            }
        )
        
        if created:
            print(f"✅ TELEGRAM ADMIN: {user.full_name} (@{user.username})")
            return True
        else:
            print(f"ℹ️ TELEGRAM ADMIN: {user.full_name} (@{user.username}) - allaqachon mavjud")
            return False
            
    except Exception as e:
        print(f"❌ Telegram Admin yaratishda xato: {e}")
        return False


def create_test_users():
    """Test foydalanuvchilarni yaratish"""
    test_users = [
        {
            "telegram_id": 123456789,
            "full_name": "Test User 1",
            "username": "testuser1",
            "phone_number": "+998901111111",
            "age": 25,
            "role": "user"
        },
        {
            "telegram_id": 987654321,
            "full_name": "Test User 2",
            "username": "testuser2",
            "phone_number": "+998902222222",
            "age": 35,
            "role": "user"
        },
    ]
    
    print("\n👥 TEST FOYDALANUVCHILAR:")
    print("-" * 30)
    
    created_users = 0
    
    for user_data in test_users:
        try:
            user, created = TelegramUser.objects.get_or_create(
                telegram_id=user_data["telegram_id"],
                defaults={
                    "full_name": user_data["full_name"],
                    "username": user_data["username"],
                    "phone_number": user_data["phone_number"],
                    "age": user_data["age"],
                    "role": user_data["role"],
                    "registration_completed": True,
                    "is_active": True
                }
            )
            
            if created:
                created_users += 1
                print(f"✅ TEST USER: {user.full_name} (@{user.username})")
            else:
                print(f"ℹ️ TEST USER: {user.full_name} - allaqachon mavjud")
                
        except Exception as e:
            print(f"❌ Test user yaratishda xato: {e}")
    
    return created_users


def create_sample_complaints():
    """Namuna murojaatlarni yaratish"""
    try:
        # Test foydalanuvchini olish
        test_user = TelegramUser.objects.filter(role='user').first()
        if not test_user:
            print("❌ Test foydalanuvchi topilmadi")
            return 0
        
        # Kategoriya va subkategoriyalarni olish
        category = Category.objects.first()
        if not category:
            print("❌ Kategoriya topilmadi")
            return 0
        
        subcategory = SubCategory.objects.filter(category=category).first()
        
        # Mahallani olish
        mahalla = Mahalla.objects.first()
        
        from core.models import Complaint
        from django.utils import timezone
        
        sample_complaints = [
            {
                "title": "Ko'cha chiroqlari ishlamay qolgan",
                "description": "1-mahalla 5-ko'chasidagi chiroqlar kechasi yonmayapti",
                "location": "1-mahalla, 5-ko'cha",
                "status": "new",
                "priority": "medium"
            },
            {
                "title": "Suv bosimi juda past",
                "description": "Uyga suv bosimi juda past, uchinchi qavatga chiqmayapti",
                "location": "2-mahalla, 12-uy",
                "status": "in_progress",
                "priority": "high"
            },
        ]
        
        created_count = 0
        
        print("\n📝 NAMUNA MUROJAATLAR:")
        print("-" * 30)
        
        for complaint_data in sample_complaints:
            complaint = Complaint.objects.create(
                user=test_user,
                mahalla=mahalla,
                category=category,
                subcategory=subcategory,
                **complaint_data
            )
            
            created_count += 1
            print(f"✅ MUROJAAT: {complaint.title} (ID: {complaint.id})")
        
        return created_count
        
    except Exception as e:
        print(f"❌ Murojaat yaratishda xato: {e}")
        return 0


def create_default_data():
    """Barcha standart ma'lumotlarni yaratish"""
    print("=" * 60)
    print("STANDART MA'LUMOTLAR YARATILMOQDA...")
    print("=" * 60)
    
    # 1. Django Superuser yaratish
    print("\n👑 DJANGO SUPERUSER:")
    print("-" * 30)
    superuser = create_superuser()
    
    # 2. Kategoriya va subkategoriyalarni yaratish
    categories_count, subcategories_count = create_categories_with_subcategories()
    
    # 3. Mahallalarni yaratish
    mahallas_count = create_mahallas()
    
    # 4. Telegram Admin yaratish
    admin_created = create_default_admin()
    
    # 5. Test foydalanuvchilarni yaratish
    test_users_count = create_test_users()
    
    # 6. Namuna murojaatlarni yaratish (ixtiyoriy)
    sample_complaints_count = create_sample_complaints()
    
    # 7. Natija
    print("\n" + "=" * 60)
    print("NATIJA:")
    print("=" * 60)
    print(f"👑 Django Superuser: {superuser.username}")
    print(f"✅ Yangi kategoriyalar: {categories_count} ta")
    print(f"✅ Yangi subkategoriyalar: {subcategories_count} ta")
    print(f"✅ Yangi mahallalar: {mahallas_count} ta")
    print(f"✅ Telegram admin foydalanuvchi: {'Yaratildi' if admin_created else 'Mavjud edi'}")
    print(f"✅ Test foydalanuvchilar: {test_users_count} ta")
    print(f"✅ Namuna murojaatlar: {sample_complaints_count} ta")
    print("-" * 40)
    print(f"📊 Jami kategoriyalar: {Category.objects.count()} ta")
    print(f"📊 Jami subkategoriyalar: {SubCategory.objects.count()} ta")
    print(f"📊 Jami mahallalar: {Mahalla.objects.count()} ta")
    print(f"📊 Jami foydalanuvchilar: {TelegramUser.objects.count()} ta")
    print("=" * 60)
    
    # 8. Ro'yxatni ko'rsatish
    print("\n📋 KATEGORIYALAR VA SUBKATEGORIYALAR RO'YXATI:")
    print("-" * 50)
    categories = Category.objects.all().order_by('name')
    for category in categories:
        print(f"\n{category.icon} {category.name}:")
        subcategories = category.subcategories.all()
        if subcategories:
            for subcat in subcategories:
                print(f"   ├── {subcat.title}")
        else:
            print("   ├── (Subkategoriyalar yo'q)")
    
    print("\n🏘️ MAHALLALAR RO'YXATI:")
    print("-" * 30)
    mahallas = Mahalla.objects.all().order_by('name')
    for mahalla in mahallas:
        print(f"• {mahalla.name} ({mahalla.code})")
    
    print("\n👥 FOYDALANUVCHILAR RO'YXATI:")
    print("-" * 30)
    users = TelegramUser.objects.all().order_by('-created_at')
    for user in users:
        role_icon = "👨‍💻" if user.role == 'admin' else "👤"
        print(f"• {role_icon} {user.full_name} (@{user.username}) - {user.role}")
    
    print("\n" + "=" * 60)
    print("✅ Barcha standart ma'lumotlar muvaffaqiyatli yaratildi!")
    print("=" * 60)
    print("\n🔗 LINKS:")
    print("-" * 20)
    print("🌐 Admin panel: http://127.0.0.1:8000/admin/")
    print("📊 API Docs: http://127.0.0.1:8000/api/swagger/")
    print("📄 API Docs (Redoc): http://127.0.0.1:8000/api/redoc/")
    print("\n🔐 ADMIN LOGIN:")
    print("-" * 20)
    print("👤 Username: admin")
    print("🔑 Password: admin123")
    print("=" * 60)


if __name__ == "__main__":
    try:
        create_default_data()
    except Exception as e:
        print(f"❌ Xatolik yuz berdi: {e}")
        import traceback
        traceback.print_exc()