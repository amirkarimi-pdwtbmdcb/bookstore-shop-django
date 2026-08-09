from django import forms

from .models import Order


class CheckoutForm(forms.ModelForm):
    coupon_code = forms.CharField(required=False, label='کد تخفیف')

    class Meta:
        model = Order
        fields = ['full_name', 'phone_number', 'province', 'city', 'postal_code', 'address', 'order_notes']