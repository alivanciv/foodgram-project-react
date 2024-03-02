from django.db.models import Subquery, OuterRef, Prefetch
import django_filters

from recipes.models import Recipe, Ingredient, RecipeFavorite, ShoppingCart
from django.contrib.auth import get_user_model
from .utils import list_related_recipes

User = get_user_model()

CHOICES = (
    ('breakfast', 'breakfast'),
    ('launch', 'launch'),
    ('dinner', 'dinner'),
)


class RecipeFilter(django_filters.FilterSet):
    tags = django_filters.MultipleChoiceFilter(
        choices=CHOICES,
        field_name='tags__slug',
        lookup_expr='exact'
    )
    author = django_filters.NumberFilter(
        field_name='author__id',
        lookup_expr='exact'
    )
    is_favorited = django_filters.NumberFilter(
        method='get_is_favorited'
    )
    is_in_shopping_cart = django_filters.NumberFilter(
        method='get_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = ('tags', 'author')

    def get_is_favorited(self, queryset, name, value):
        return list_related_recipes(
            self, queryset, value,
            RecipeFavorite, 'favorited'
        )

    def get_is_in_shopping_cart(self, queryset, name, value):
        return list_related_recipes(
            self, queryset, value,
            ShoppingCart, 'buyers'
        )


class IngredientFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='startswith')

    class Meta:
        model = Ingredient
        fields = ('name',)


class UserRecipeFilter(django_filters.FilterSet):
    recipes_limit = django_filters.NumberFilter(
        method='get_recipes_limit'
    )

    class Meta:
        model = User
        fields = '__all__'

    def get_recipes_limit(self, queryset, name, value):
        recipe_sq = Subquery(
            Recipe.objects.filter(
                author__id=OuterRef('id')
            ).values('id')[:value]
        )
        user_sq = Subquery(
            queryset.filter(
                recipes__id__in=recipe_sq
            ).values_list('recipes__id'))
        return queryset.prefetch_related(
            Prefetch(
                'recipes',
                queryset=Recipe.objects.filter(id__in=user_sq)
            )
        )
