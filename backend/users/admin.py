from django.conf import settings
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .forms import CustomUserCreationForm
from .models import CustomUser, Subscribe


class CustomUserAdmin(UserAdmin):
    model = CustomUser
    add_form = CustomUserCreationForm
    list_display = (
        'username',
        'email',
        'first_name',
        'last_name'
    )
    search_fields = (
        'username',
        'email',
        'first_name',
        'last_name',
    )
    list_filter = ('email', 'username',)
    ordering = ('id',)
    empty_value_display = settings.EMPTY_VALUE_DISPLAY


class SubscribeAdmin(admin.ModelAdmin):
    list_display = ('user', 'author')
    search_fields = ('user', 'author')
    list_filter = ('user', 'author')
    empty_value_display = settings.EMPTY_VALUE_DISPLAY


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Subscribe, SubscribeAdmin)
