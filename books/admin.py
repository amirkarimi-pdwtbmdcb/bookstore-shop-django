from django.contrib import admin

from .models import Category, Author, Publisher, Book, Review


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'parent')
    search_fields = ('name',)
    list_filter = ('parent',)


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)


@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'category', 'book_type', 'price',
        'stock', 'is_active', 'created_at',
    )
    list_filter = ('book_type', 'category', 'is_active')
    search_fields = ('title', 'isbn')
    autocomplete_fields = ('category', 'publisher', 'authors')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('book', 'user', 'rating', 'is_approved', 'created_at')
    list_filter = ('is_approved', 'rating')
    actions = ['approve_reviews']

    @admin.action(description='تایید نظرات انتخاب‌شده')
    def approve_reviews(self, request, queryset):
        queryset.update(is_approved=True)
