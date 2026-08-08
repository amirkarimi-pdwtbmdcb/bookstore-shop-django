from django.urls import path

from . import views


app_name = 'books'

urlpatterns = [
    path('', views.BookListView.as_view(), name='book_list'),
    path('book/<slug:slug>/', views.BookDetailView.as_view(), name='book_detail'),
    path('category/<slug:slug>/', views.CategoryDetailView.as_view(), name='category_detail'),
    path('author/<slug:slug>/', views.AuthorDetailView.as_view(), name='author_detail'),
    path('publisher/<slug:slug>/', views.PublisherDetailView.as_view(), name='publisher_detail'),
]