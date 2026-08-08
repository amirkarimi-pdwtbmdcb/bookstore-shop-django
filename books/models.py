from django.db import models

from core.models import TimeStampedModel


class Category(TimeStampedModel):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True)
    parent = models.ForeignKey(
        'self', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='children'
    )

    class Meta:
        verbose_name = 'دسته‌بندی'
        verbose_name_plural = 'دسته‌بندی‌ها'

    def __str__(self):
        return self.name


class Author(TimeStampedModel):
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=170, unique=True)
    bio = models.TextField(blank=True)

    class Meta:
        verbose_name = 'نویسنده'
        verbose_name_plural = 'نویسندگان'

    def __str__(self):
        return self.name


class Publisher(TimeStampedModel):
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=170, unique=True)

    class Meta:
        verbose_name = 'ناشر'
        verbose_name_plural = 'ناشران'

    def __str__(self):
        return self.name


class Book(TimeStampedModel):
    class BookType(models.TextChoices):
        PHYSICAL = 'physical', 'فیزیکی'
        DIGITAL = 'digital', 'دیجیتال'

    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, unique=True)
    description = models.TextField(blank=True)

    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name='books'
    )
    authors = models.ManyToManyField(Author, related_name='books')
    publisher = models.ForeignKey(
        Publisher, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='books'
    )

    book_type = models.CharField(
        max_length=10, choices=BookType.choices, default=BookType.PHYSICAL
    )

    price = models.DecimalField(max_digits=10, decimal_places=0)
    discount_price = models.DecimalField(
        max_digits=10, decimal_places=0, null=True, blank=True
    )

    cover_image = models.ImageField(upload_to='books/covers/')

    isbn = models.CharField(max_length=20, blank=True)
    language = models.CharField(max_length=50, default='فارسی')
    page_count = models.PositiveIntegerField(null=True, blank=True)

    stock = models.PositiveIntegerField(default=0)
    digital_file = models.FileField(
        upload_to='books/files/', null=True, blank=True
    )

    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'کتاب'
        verbose_name_plural = 'کتاب‌ها'
        ordering = ['-created_at']

    def __str__(self):
        return self.title