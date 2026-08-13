from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model, login
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.views import generic

from .forms import CustomUserCreationForm, ProfileUpdateForm


User = get_user_model()


class ProfileView(LoginRequiredMixin, generic.DetailView):
    model = User
    template_name = 'accounts/profile.html'
    context_object_name = 'profile_user'

    def get_object(self):
        return self.request.user


class ProfileUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = User
    form_class = ProfileUpdateForm
    template_name = 'accounts/profile_edit.html'
    success_url = reverse_lazy('accounts:profile')

    def get_object(self):
        return self.request.user


class SignUpView(generic.CreateView):
    form_class = CustomUserCreationForm
    template_name = "registration/signup.html"
    success_url = reverse_lazy("books:book_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        login(
            self.request,
            self.object,
            backend='accounts.backends.UsernameOrPhoneBackend',
        )
        return response


class CustomLoginView(LoginView):
    def form_valid(self, form):
        self.request.session['guest_cart_session_key'] = self.request.session.session_key

        return super().form_valid(form)
    