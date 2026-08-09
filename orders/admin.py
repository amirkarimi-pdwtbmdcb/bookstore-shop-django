from django.contrib import admin

from .models import Coupon


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_percent', 'valid_from', 'valid_to', 'times_used', 'usage_limit', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('code',)