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

    list_display = ('user', 'get_followings',
                    'get_followers', 'get_followers_count')
    list_display_links = ('user', )
    list_filter = ('user', )
    search_fields = ['user']
    empty_value_display = '-пусто-'

    @admin.display(description='Подписки')
    def get_followings(self, obj):
        followings_set = obj.follower.all()
        data = [f'{following.firs_name} {following.last_name}'
                for following in followings_set]
        return format_html('<br/>'.join(data))

    @admin.display(description='Подписчики')
    def get_followers(self, obj):
        followers_set = obj.following.all()
        data = [f'{follower.firs_name} {follower.last_name}'
                for follower in followers_set]
        return format_html('<br/>'.join(data))

    @admin.display(description='Кол-во подписчиков')
    def get_followers_count(self, obj):
        return obj.following.all().count()
