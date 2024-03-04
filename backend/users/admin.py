from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.utils.html import format_html

from .models import Follow

User = get_user_model()
admin.site.unregister(Group)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """User information"""

    list_display = ('pk', 'username', 'email', 'first_name', 'last_name')
    list_display_links = ('username', )
    list_filter = ('username', 'email')
    search_fields = ['username']
    empty_value_display = '-пусто-'


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    """Follow information"""

    list_display = ('user', 'author', 'get_subs')
    list_display_links = ('user', )
    list_filter = ('user', )
    search_fields = ['user']
    empty_value_display = '-пусто-'

    @admin.display(description='Подписки')
    def get_subs(self, obj):
        subs = (
            User.objects
            .filter(following__user=obj.user)
        )
        data = [sub.first_name for sub in subs]
        return format_html('<br/>'.join(data))
