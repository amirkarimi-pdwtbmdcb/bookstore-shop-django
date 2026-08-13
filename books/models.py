from django.core.validators import MinValueValidator, MaxValueValidator, FileExtensionValidator
from django.core.exceptions import ValidationError
from django.conf import settings
from django.urls import reverse
from django.db import models

from core.models import TimeStampedModel


def validate_file_size(value):
    max_size_mb = 20
    if value.size > max_size_mb * 1024 * 1024:
        raise ValidationError(f'حجم فایل نباید بیشتر از {max_size_mb} مگابایت باشد')


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

    cover_image = models.ImageField(
        upload_to='books/covers/',
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp']), validate_file_size]
    )

    isbn = models.CharField(max_length=20, blank=True)
    language = models.CharField(max_length=50, default='فارسی')
    page_count = models.PositiveIntegerField(null=True, blank=True)

    stock = models.PositiveIntegerField(default=0)
    digital_file = models.FileField(
    upload_to='books/files/', null=True, blank=True,
    validators=[FileExtensionValidator(allowed_extensions=['pdf', 'epub']), validate_file_size]
    )

    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'کتاب'
        verbose_name_plural = 'کتاب‌ها'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('books:book_detail', kwargs={'slug': self.slug})

    @property
    def average_rating(self):
        result = self.reviews.filter(is_approved=True).aggregate(models.Avg('rating'))
        return round(result['rating__avg'] or 0, 1)


class Review(TimeStampedModel):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews')
    comment = models.TextField()
    rating = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    is_approved = models.BooleanField(default=False)

    class Meta:
        constraints = [
        models.UniqueConstraint(
            fields=['book', 'user'],
            name="unique_review_per_user_book"
        )
    ]

    def get_absolute_url(self):
        return reverse('books:book_detail', kwargs={'slug': self.book.slug})


class WishList(TimeStampedModel):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='wishlisted_by')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favorites')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'book'],
                name='unique_wishlist_per_user_book'
            )
        ]
    