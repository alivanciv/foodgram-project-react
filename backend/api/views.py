from django.http import HttpResponse
from django.contrib.auth import get_user_model
from django.db.models import Sum, Count
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as BaseUserViewSet
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework import status

from api.viewsets import ReadCreateDeleteModelViewSet
from recipes.models import (
    Recipe,
    Ingredient,
    Tag,
    RecipeFavorite,
    ShoppingCart,
    RecipeIngredient
)
from users.models import Follow
from .filters import (
    RecipeFilter,
    IngredientFilter,
    UserRecipeFilter
)
from .serializers import (
    TagSerializer,
    IngredientSerializer,
    RecipeSerializer,
    CreateRecipeSerializer,
    SubscriptionsSerializer
)
from .permissions import IsAdminOrReadOnly, IsOwner
from .utils import add_delete_to

User = get_user_model()


class TagViewSet(ReadCreateDeleteModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(ReadCreateDeleteModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class RecipeViewSet(ModelViewSet):
    http_method_names = ['get', 'post', 'patch', 'delete']
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = (IsOwner | IsAdminOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ('create', 'partial_update', 'update'):
            return CreateRecipeSerializer
        return super().get_serializer_class()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['post', 'delete'],
            url_path='favorite',
            permission_classes=[IsAuthenticated])
    def favorite_add_delete(self, request, pk):
        return add_delete_to(
            request, pk, Recipe, 'recipe',
            'Нельзя добавить в избранное несуществующий рецепт!',
            'Вы уже добавили этот рецепт в избранное!',
            'Рецепт не был добавлен в избранное!',
            RecipeFavorite, RecipeSerializer, True
        )

    @action(detail=True, methods=['post', 'delete'],
            url_path='shopping_cart',
            permission_classes=[IsAuthenticated])
    def shopping_cart_add_delete(self, request, pk):
        return add_delete_to(
            request, pk, Recipe, 'recipe',
            'Нельзя добавить в покупки несуществующий рецепт!',
            'Вы уже добавили этот рецепт в покупки!',
            'Рецепт не был добавлен в покупки!',
            ShoppingCart, RecipeSerializer, True
        )

    @action(detail=False, methods=['get'],
            url_path='download_shopping_cart',
            permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        user = request.user.id
        recipes = ShoppingCart.objects.filter(user=user).values(
            'recipe_id', 'recipe__name')
        order_data = (
            RecipeIngredient.objects
            .filter(recipe_id__in=recipes.values('recipe_id'))
            .select_related('ingredient')
            .order_by('ingredient__name')
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(total_amount=Sum('amount'))
        )
        ordered_recipes = ', '.join(
            [
                '{}'.format(recipe['recipe__name']) for recipe in recipes
            ]
        )
        ingredients = ';\n'.join(
            [
                '{} - {} {}'.format(
                    position['ingredient__name'],
                    position['total_amount'],
                    position['ingredient__measurement_unit'])
                for position in order_data
            ]
        )
        file_data = '\n'.join(
            ['Вы выбрали следующие рецепты:',
             f'{ordered_recipes}.\n',
             'Список покупок:',
             f'{ingredients}.']
        )
        response = HttpResponse(
            file_data,
            content_type='text/plain'
        )
        response['Content-Disposition'] = 'attachment;filename=file.txt'
        return response


class UserViewSet(BaseUserViewSet):
    filter_backends = (DjangoFilterBackend,)

    def get_queryset(self):
        if self.action in ('subscriptions'):
            return (
                User.objects
                .filter(following__user=self.request.user)
            )
        return super(UserViewSet, self).get_queryset()

    def filter_queryset(self, queryset):
        if self.action in ('subscriptions', 'subscribe'):
            self.filterset_class = UserRecipeFilter
        return super().filter_queryset(queryset)

    def get_permissions(self):
        if self.action == 'me':
            permission_classes = [IsAuthenticated]
            return [permission() for permission in permission_classes]
        return super(UserViewSet, self).get_permissions()

    @action(detail=False, methods=['get'], url_path='subscriptions',
            permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        queryset = (
            queryset
            .annotate(recipes_count=Count('recipes'))
            .order_by('follower__created_at')
        )
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = SubscriptionsSerializer(
                page,
                many=True,
                context={'request': request}
            )
            return self.get_paginated_response(serializer.data)
        serializer = SubscriptionsSerializer(
            queryset,
            many=True,
            context={'request': request}
        )
        return Response(status=status.HTTP_200_OK, data=serializer.data)

    @action(detail=True, methods=['post', 'delete'], url_path='subscribe',
            permission_classes=[IsAuthenticated])
    def subscribe(self, request, id):
        queryset = self.filter_queryset(self.get_queryset())
        return add_delete_to(
            request, id, queryset, 'author',
            'Нельзя добавить в подписки несуществующего пользователя!',
            'Вы уже подписаны на этого пользователя!',
            'Пользователь не был добавлен в подписки!',
            Follow, SubscriptionsSerializer, False
        )
