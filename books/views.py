from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.views import generic
from django.db.models import Q

from .models import Book, Category, Author, Publisher, Review, WishList
from .forms import ReviewForm


class BookListView(generic.ListView):
    model = Book
    template_name = 'books/books_list.html'
    context_object_name = 'books'
    paginate_by = 12

    def get_queryset(self):
        queryset = Book.objects.filter(is_active=True).select_related(
        'category', 'publisher'
        ).prefetch_related(
        'authors'
        )

        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )

        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category__slug=category)

        author = self.request.GET.get('author')
        if author:
            queryset = queryset.filter(authors__slug=author)

        publisher = self.request.GET.get('publisher')
        if publisher:
            queryset = queryset.filter(publisher__slug=publisher)

        book_type = self.request.GET.get('book_type')
        if book_type:
            queryset = queryset.filter(book_type=book_type)

        min_price = self.request.GET.get('min_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)

        max_price = self.request.GET.get('max_price')
        if max_price:
            queryset = queryset.filter(price__lte=max_price)

        sort = self.request.GET.get('sort')
        if sort == 'price_asc':
            queryset = queryset.order_by('price')
        elif sort == 'price_desc':
            queryset = queryset.order_by('-price')
        elif sort == 'newest':
            queryset = queryset.order_by('-created_at')

        return queryset.distinct()

    
class BookDetailView(generic.DetailView):
    model = Book
    template_name = 'books/book_detail.html'
    context_object_name = 'book'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['reviews'] = self.object.reviews.filter(is_approved=True)
        return context


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


class ReviewCreateView(LoginRequiredMixin, generic.CreateView):
    model = Review
    form_class = ReviewForm

    def form_valid(self, form):
        form.instance.user = self.request.user
        book = get_object_or_404(Book, id=self.kwargs['book_id'])
        form.instance.book = book

        if Review.objects.filter(user=self.request.user, book=book).exists():
            form.add_error(None, "You have already reviewed this book.")
            return self.form_invalid(form)

        return super().form_valid(form)


@login_required
def wishlist_toggle(request, book_id):
    book = get_object_or_404(Book, id=book_id, is_active=True)
    item, created = WishList.objects.get_or_create(user=request.user, book=book)
    if not created:
        item.delete()
    return redirect('books:book_detail', slug=book.slug)


class WishlistListView(LoginRequiredMixin, generic.ListView):
    model = WishList
    context_object_name = 'wishlist_items'
    template_name = 'books/wishlist_list.html'
    paginate_by = 12

    def get_queryset(self):
        return WishList.objects.filter(user=self.request.user).select_related('book')
