from django import forms

from .models import Review


RATING_CHOICES = [(i, f'{i} ستاره') for i in range(1, 6)]


class ReviewForm(forms.ModelForm):
    rating = forms.ChoiceField(choices=RATING_CHOICES, label='امتیاز')

    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'comment': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'نظرت رو درباره‌ی این کتاب بنویس…',
            }),
        }