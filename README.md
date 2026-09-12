# کتاب‌فروشی آنلاین (Django Bookstore)

یک فروشگاه اینترنتی کتاب (فیزیکی و دیجیتال) با جنگو، شامل مدیریت سبد خرید،
ثبت سفارش، علاقه‌مندی‌ها (Wishlist)، نظرات کاربران، کد تخفیف و پنل مدیریت
اختصاصی برای staff.

## امکانات

- احراز هویت با کاربر سفارشی (شماره‌ی موبایل به‌جای ایمیل)
- لیست/جست‌وجو/فیلتر کتاب‌ها (دسته‌بندی، نویسنده، ناشر، بازه‌ی قیمت، نوع کتاب)
- سبد خرید برای کاربر مهمان (بر اساس session) و کاربر لاگین‌شده، با merge خودکار
  سبد مهمان به سبد کاربر هنگام لاگین
- ثبت سفارش با کسر موجودی و پشتیبانی از کد تخفیف
- علاقه‌مندی‌ها (Wishlist) و امتیازدهی/نظر برای هر کتاب
- پنل مدیریت جدا (`/dashboard/`) مخصوص کاربران staff

## پیش‌نیازها

- Python 3.12+
- pip

## نصب و اجرا

```bash
git clone <repo-url>
cd bookstore-shop-django

python -m venv venv
source venv/bin/activate   # ویندوز: venv\Scripts\activate

pip install -r requirements.txt
```

### متغیرهای محیطی

یک فایل `.env` در ریشه‌ی پروژه بساز (این فایل در `.gitignore` هست و نباید commit بشه):

```env
DJANGO_SECRET_KEY=یک-رشته-تصادفی-و-امن-اینجا-بذار
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
```

> برای تولید یک SECRET_KEY امن:
> `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`

### راه‌اندازی دیتابیس و اجرا

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

سایت روی `http://127.0.0.1:8000` بالا میاد و پنل مدیریت جنگو روی `/admin/`.

## اجرای تست‌ها

```bash
python manage.py test
```

## ساختار پروژه

| اپ | مسئولیت |
|---|---|
| `accounts` | کاربر سفارشی، ثبت‌نام، پروفایل |
| `books` | کتاب، دسته‌بندی، نویسنده، ناشر، نظرات، علاقه‌مندی‌ها |
| `cart` | سبد خرید (مهمان + کاربر لاگین‌شده) |
| `orders` | ثبت سفارش، کد تخفیف |
| `dashboard` | پنل مدیریت اختصاصی staff |
| `core` | مدل‌ها/تمپلیت‌تگ‌های مشترک |

## وضعیت پروژه

این پروژه هنوز کامل نیست و در حال توسعه است. مواردی که فعلاً پیاده‌سازی
نشده‌اند:

- درگاه پرداخت واقعی (سفارش‌ها فعلاً با وضعیت «پرداخت‌نشده» ثبت می‌شوند)
- دانلود امن فایل دیجیتال کتاب پس از خرید
