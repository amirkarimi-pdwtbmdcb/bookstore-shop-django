from django.contrib import admin

from .models import Category, Author, Publisher, Book


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