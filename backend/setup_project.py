#!/usr/bin/env python3
"""
Mac uchun Django loyihasini to'liq sozlash skripti
"""

import os
import sys
import shutil
import subprocess
import time

def print_header(text):
    """Sarlavhani chiqarish"""
    print(f"\n{'='*80}")
    print(f"📌 {text}")
    print(f"{'='*80}")

def print_success(text):
    """Muvaffaqiyatli xabarni chiqarish"""
    print(f"✅ {text}")

def print_error(text):
    """Xato xabarni chiqarish"""
    print(f"❌ {text}")

def print_info(text):
    """Ma'lumot xabarni chiqarish"""
    print(f"ℹ️  {text}")

def run_command(cmd, description=None):
    """Komandani bajarish"""
    if description:
        print(f"\n▶️  {description}")
    print(f"   $ {cmd}")
    
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.stdout:
            for line in result.stdout.strip().split('\n'):
                print(f"   │ {line}")
        
        if result.stderr:
            for line in result.stderr.strip().split('\n'):
                if line:  # Faqat bo'sh bo'lmagan qatorlarni chiqaramiz
                    print(f"   ⚠️  {line}")
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"   ❌ Xato: {e}")
        return False

def setup_virtualenv():
    """Virtual environment sozlash"""
    print_header("VIRTUAL ENVIRONMENT")
    
    venv_path = "venv"
    
    # Virtual environment mavjud bo'lsa, o'chirish
    if os.path.exists(venv_path):
        print_info("Eski virtual environment o'chirilmoqda...")
        shutil.rmtree(venv_path)
        print_success("Eski virtual environment o'chirildi")
    
    # Yangi virtual environment yaratish
    success = run_command("python3 -m venv venv", "Yangi virtual environment yaratish")
    if not success:
        return False
    
    # Virtual environment aktivlashtirish (ishlatish uchun)
    if sys.platform == "darwin":  # Mac
        activate_cmd = "source venv/bin/activate"
    else:
        activate_cmd = "venv\\Scripts\\activate"
    
    print_success("Virtual environment yaratildi")
    print_info(f"Aktivlashtirish uchun: {activate_cmd}")
    
    return True

def install_requirements():
    """Paketlarni o'rnatish"""
    print_header("PACKAGE INSTALLATION")
    
    # Virtual environmentdagi pipdan foydalanish
    pip_path = os.path.join("venv", "bin", "pip")
    
    requirements = [
        "Django==4.2.11",
        "djangorestframework==3.14.0",
        "django-filter==23.5",
        "django-cors-headers==4.3.1",
        "django-jazzmin==3.0.1",
        "drf-yasg==1.21.11",
        "drf-spectacular==0.27.1",
        "uritemplate==4.2.0",
        "PyYAML==6.0.3",
        "inflection==0.5.1",
        "sqlparse==0.5.5",
        "pytz==2025.2",
        "requests==2.31.0",
        "aiohttp==3.9.3",
        "urllib3==2.6.3",
        "certifi==2026.1.4",
        "idna==3.11",
        "charset-normalizer==3.4.4",
        "asgiref==3.11.0",
        "attrs==25.4.0",
        "python-dotenv==1.0.0",
        "packaging==25.0",
        "typing_extensions==4.15.0",
        "jsonschema==4.26.0",
        "jsonschema-specifications==2025.9.1",
        "referencing==0.37.0",
        "rpds-py==0.30.0",
    ]
    
    for package in requirements:
        success = run_command(f"{pip_path} install {package}", f"{package} o'rnatish")
        if not success:
            print_error(f"{package} o'rnatishda xato")
            return False
    
    print_success("Barcha paketlar muvaffaqiyatli o'rnatildi")
    return True

def clean_project():
    """Loyihani tozalash"""
    print_header("PROJECT CLEANUP")
    
    # Database fayllari
    db_files = ['db.sqlite3', 'database.sqlite3', 'db.sqlite', 'dev.db']
    for db_file in db_files:
        if os.path.exists(db_file):
            os.remove(db_file)
            print_success(f"{db_file} o'chirildi")
    
    # Migratsiya fayllari (core app uchun)
    migrations_dir = "core/migrations"
    if os.path.exists(migrations_dir):
        for item in os.listdir(migrations_dir):
            if item != "__init__.py" and item.endswith(".py"):
                os.remove(os.path.join(migrations_dir, item))
                print_success(f"core/migrations/{item} o'chirildi")
    
    # Pycache fayllari
    deleted_pycache = 0
    for root, dirs, files in os.walk("."):
        for dir_name in dirs:
            if dir_name == "__pycache__":
                dir_path = os.path.join(root, dir_name)
                try:
                    shutil.rmtree(dir_path)
                    deleted_pycache += 1
                except:
                    pass
    
    if deleted_pycache > 0:
        print_success(f"{deleted_pycache} ta __pycache__ papkasi o'chirildi")
    
    return True

def run_migrations():
    """Migratsiyalarni bajarish"""
    print_header("DATABASE MIGRATIONS")
    
    python_path = os.path.join("venv", "bin", "python3")
    
    # Makemigrations
    success = run_command(f"{python_path} manage.py makemigrations", "Makemigrations")
    if not success:
        return False
    
    # Migrate
    success = run_command(f"{python_path} manage.py migrate", "Migrate")
    if not success:
        return False
    
    print_success("Migratsiyalar muvaffaqiyatli bajarildi")
    return True

def create_superuser():
    """Superuser yaratish"""
    print_header("SUPERUSER CREATION")
    
    python_path = os.path.join("venv", "bin", "python3")
    
    # Django shell orqali superuser yaratish
    script = '''
from django.contrib.auth.models import User
import os

username = 'admin'
email = 'admin@example.com'
password = 'admin123'

try:
    user = User.objects.get(username=username)
    print(f"Superuser {username} allaqachon mavjud")
except User.DoesNotExist:
    User.objects.create_superuser(username, email, password)
    print(f"Superuser {username} yaratildi (parol: {password})")
except Exception as e:
    print(f"Xato: {e}")
'''
    
    # Shell scriptini faylga yozish
    with open("create_superuser_temp.py", "w") as f:
        f.write(script)
    
    # Scriptni ishga tushirish
    success = run_command(
        f"{python_path} manage.py shell < create_superuser_temp.py",
        "Superuser yaratish"
    )
    
    # Vaqtinchalik faylni o'chirish
    if os.path.exists("create_superuser_temp.py"):
        os.remove("create_superuser_temp.py")
    
    return success

def create_seed_data():
    """Seed ma'lumotlarni yaratish"""
    print_header("SEED DATA CREATION")
    
    python_path = os.path.join("venv", "bin", "python3")
    
    seed_script = '''
import os
import django
from django.db import transaction

# Django settings ni yuklash
try:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()
except:
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'murojaat_bot.settings')
        django.setup()
    except:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
        django.setup()

from core.models import Category, SubCategory, Mahalla, TelegramUser
from django.contrib.auth.models import User

@transaction.atomic
def create_data():
    print("\\n📋 KATEGORIYALAR VA SUBKATEGORIYALAR:")
    print("-" * 50)
    
    # Kategoriyalar
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
    
    created_cats = 0
    created_subs = 0
    
    for name, icon in categories:
        cat, created = Category.objects.get_or_create(
            name=name,
            defaults={"icon": icon, "description": f"{name} bilan bog'liq muammolar"}
        )
        
        if created:
            created_cats += 1
            print(f"✅ {icon} {name}")
        
        if name in subcategories_data:
            for sub_title in subcategories_data[name]:
                sub, sub_created = SubCategory.objects.get_or_create(
                    category=cat,
                    title=sub_title,
                    defaults={"description": f"{sub_title} - {name}"}
                )
                if sub_created:
                    created_subs += 1
                    print(f"   ├── {sub_title}")
    
    print(f"\\n✅ {created_cats} ta kategoriya, {created_subs} ta subkategoriya yaratildi")
    
    # Mahallalar
    print("\\n🏘️ MAHALLALAR:")
    print("-" * 30)
    
    created_mahallas = 0
    for i in range(1, 11):
        name = f"{i}-mahalla"
        code = f"M{str(i).zfill(3)}"
        mahalla, created = Mahalla.objects.get_or_create(
            name=name,
            defaults={"code": code, "description": f"{name} - Karmana tumani"}
        )
        if created:
            created_mahallas += 1
            print(f"✅ {name} ({code})")
    
    print(f"\\n✅ {created_mahallas} ta mahalla yaratildi")
    
    # Telegram Admin
    print("\\n👨‍💻 TELEGRAM ADMIN:")
    print("-" * 30)
    
    try:
        TelegramUser.objects.get_or_create(
            telegram_id=5515940993,
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
        print("✅ Telegram admin yaratildi")
    except:
        print("ℹ️ Telegram admin allaqachon mavjud")
    
    print("\\n" + "="*60)
    print("✅ Barcha seed ma'lumotlar yaratildi!")
    print("="*60)

if __name__ == "__main__":
    create_data()
'''
    
    # Scriptni faylga yozish
    with open("seed_data_temp.py", "w") as f:
        f.write(seed_script)
    
    # Scriptni ishga tushirish
    success = run_command(f"{python_path} seed_data_temp.py", "Seed ma'lumotlarni yaratish")
    
    # Vaqtinchalik faylni o'chirish
    if os.path.exists("seed_data_temp.py"):
        os.remove("seed_data_temp.py")
    
    return success

def start_server():
    """Serverni ishga tushirish"""
    print_header("STARTING SERVER")
    
    python_path = os.path.join("venv", "bin", "python3")
    
    print_info("Server ishga tushmoqda...")
    print_info("Ctrl+C bosib to'xtating")
    print_info("")
    print_info("🌐 Admin panel: http://127.0.0.1:8000/admin/")
    print_info("📊 API Docs: http://127.0.0.1:8000/api/swagger/")
    print_info("👤 Username: admin")
    print_info("🔑 Password: admin123")
    print_info("")
    
    try:
        # Serverni ishga tushirish
        subprocess.run(f"{python_path} manage.py runserver", shell=True)
    except KeyboardInterrupt:
        print_info("\nServer to'xtatildi")
    except Exception as e:
        print_error(f"Server xatosi: {e}")

def main():
    """Asosiy funksiya"""
    print_header("DJANGO PROJECT SETUP FOR MAC")
    print("📁 Loyiha: Karmana tumani murojaatlar tizimi")
    print("💻 Platforma: macOS")
    print("⏰ Vaqt: " + time.strftime("%Y-%m-%d %H:%M:%S"))
    
    # 2. Virtual environment sozlash
    if not setup_virtualenv():
        sys.exit(1)
    
    # 3. Paketlarni o'rnatish
    if not install_requirements():
        sys.exit(1)
    
    # 4. Loyihani tozalash
    clean_project()
    
    # 5. Migratsiyalarni bajarish
    if not run_migrations():
        sys.exit(1)
    
    # 6. Superuser yaratish
    if not create_superuser():
        sys.exit(1)
    
    # 7. Seed ma'lumotlarni yaratish
    create_seed_data()
    
    # 8. Serverni ishga tushirish
    start_server()

if __name__ == "__main__":
    main()