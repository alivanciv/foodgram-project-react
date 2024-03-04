from django.contrib import admin
from django.contrib.auth import get_user_model
from django.utils.html import format_html

from recipes.models import (
    Tag,
    Ingredient,
    Recipe,
    RecipeIngredient,
    RecipeFavorite,
    ShoppingCart
)

User = get_user_model()


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Tag information"""

    list_display = ('pk', 'name', 'color', 'slug')
    list_display_links = ('name', )
    search_fields = ['name']
    empty_value_display = '-пусто-'


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Ingredient information"""

    list_display = ('pk', 'name', 'measurement_unit')
    list_display_links = ('name', )
    list_filter = ('name', )
    search_fields = ['name']
    empty_value_display = '-пусто-'


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 0
    min_num = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Recipe information"""

    inlines = (RecipeIngredientInline,)
    list_display = ('pk', 'name', 'author',
                    'get_ingredients', 'get_favorited_count')
    filter_horizontal = ('tags',)
    list_display_links = ('name', )
    list_filter = ('tags__name', 'author', 'name')
    search_fields = ['name']
    empty_value_display = '-пусто-'
    date_hierarchy = 'pub_date'

    @admin.display(description='Ингредиенты')
    def get_ingredients(self, obj):
        ingr_set = obj.ingredients.all()
        ri_set = RecipeIngredient.objects.filter(recipe=obj)
        data = [ri_set.get(ingredient=ingr).__str__() for ingr in ingr_set]
        return format_html('<br/>'.join(data))

    @admin.display(description='Избран')
    def get_favorited_count(self, obj):
        return obj.favorited.all().count()


@admin.register(RecipeFavorite)
class RecipeFavoriteAdmin(admin.ModelAdmin):
    """RecipeFavorite information"""

    list_display = ('user', 'recipe')
    list_display_links = ('user', )
    list_filter = ('user', )
    search_fields = ['user']
    empty_value_display = '-пусто-'


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """ShoppingCart information"""

    list_display = ('user', 'recipe')
    list_display_links = ('user', )
    list_filter = ('user', )
    search_fields = ['user']
    empty_value_display = '-пусто-'
