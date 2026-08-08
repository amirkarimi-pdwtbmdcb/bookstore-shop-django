from django.views import generic
from django.db.models import Q

from .models import Book, Category, Author, Publisher


class BookListView(generic.ListView):
    model = Book
    template_name = 'books/books_list.html'
    context_object_name = 'books'
    paginate_by = 12

    def get_queryset(self):
        return Book.objects.filter(is_active=True).select_related(
            'category', 'publisher'
        ).prefetch_related('authors')


class BookDetailView(generic.DetailView):
    model = Book
    template_name = 'books/book_detail.html'
    context_object_name = 'book'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'


class CategoryDetailView(generic.DetailView):
    model = Category
    template_name = 'books/category_detail.html'
    context_object_name = 'category'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['books'] = self.object.books.filter(is_active=True)
        return context


class AuthorDetailView(generic.DetailView):
    model = Author
    template_name = 'books/author_detail.html'
    context_object_name = 'author'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['books'] = self.object.books.filter(is_active=True)
        return context


class PublisherDetailView(generic.DetailView):
    model = Publisher
    template_name = 'books/publisher_detail.html'
    context_object_name = 'publisher'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['books'] = self.object.books.filter(is_active=True)
        return context
