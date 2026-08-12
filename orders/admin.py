from django.contrib import admin

from .models import Order, OrderItem, Coupon


class OrderItemInlaine(admin.TabularInline):
    model = OrderItem
    fields = ('order', 'book', 'quantity', 'price', )
    extra = 1


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'created_at', 'status', )

    inlines = [
        OrderItemInlaine,
    ]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'book', 'quantity', 'price', )


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_percent', 'valid_from',
                    'valid_to', 'times_used', 'usage_limit', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('code',)
