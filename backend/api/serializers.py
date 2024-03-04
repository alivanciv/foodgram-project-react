import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.validators import MinValueValidator
from djoser.serializers import (
    UserSerializer as BaseUserSerializer,
    UserCreateSerializer as BaseUserCreateSerializer
)
from rest_framework.serializers import (
    ModelSerializer,
    PrimaryKeyRelatedField,
    ImageField,
    IntegerField,
    SerializerMethodField,
    CurrentUserDefault,
    ReadOnlyField,
    ValidationError
)
from recipes.models import (
    Recipe,
    Ingredient,
    Tag,
    RecipeIngredient,
    RecipeFavorite,
    ShoppingCart
)
from users.models import Follow

User = get_user_model()


class UserSerializer(BaseUserSerializer):
    is_subscribed = SerializerMethodField('get_subscribed')

    class Meta:
        model = User
        fields = ('email', 'id', 'username',
                  'first_name', 'last_name', 'is_subscribed')

    def get_subscribed(self, obj):
        user = self.context['request'].user.id
        return Follow.objects.filter(user=user, author=obj).exists()


class UserCreateSerializer(BaseUserCreateSerializer):

    class Meta:
        model = User
        fields = ('email', 'id', 'username',
                  'first_name', 'last_name', 'password')
        extra_kwargs = {'password': {'write_only': True}}


class TagSerializer(ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')
        read_only_fields = ('name', 'color', 'slug')


class IngredientSerializer(ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class Base64ImageField(ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class RecipeIngredientSerializer(ModelSerializer):
    id = PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    name = ReadOnlyField(source='ingredient.name')
    measurement_unit = ReadOnlyField(source='ingredient.measurement_unit')
    amount = IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(ModelSerializer):
    author = UserSerializer(
        read_only=True, default=CurrentUserDefault()
    )
    ingredients = RecipeIngredientSerializer(source='contents', many=True)
    tags = TagSerializer(many=True)
    image = SerializerMethodField('get_image_url', read_only=True)
    is_favorited = SerializerMethodField('get_is_favorited')
    is_in_shopping_cart = SerializerMethodField('get_is_in_shopping_cart')

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients',
                  'is_favorited', 'is_in_shopping_cart',
                  'name', 'image', 'text', 'cooking_time')

    def __init__(self, *args, **kwargs):
        fields = kwargs.pop('fields', None)
        super().__init__(*args, **kwargs)
        if fields is not None:
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)

    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return None

    def get_is_favorited(self, obj):
        user = self.context['request'].user.id
        return RecipeFavorite.objects.filter(user=user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user.id
        return ShoppingCart.objects.filter(user=user, recipe=obj).exists()


class CreateRecipeIngredientSerializer(ModelSerializer):
    id = PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        required=True,
        error_messages={
            'does_not_exist': 'Ингредиент не найден!',
        }
    )
    amount = IntegerField(
        required=True,
        write_only=True,
        validators=[MinValueValidator(
            1,
            message='Количество ингредиента не может быть меньше 0')
        ],
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class CreateRecipeSerializer(ModelSerializer):
    author = UserSerializer(
        read_only=True, default=CurrentUserDefault()
    )
    ingredients = CreateRecipeIngredientSerializer(
        many=True,
        required=True
    )
    image = Base64ImageField(max_length=None, use_url=True)
    tags = PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=True,
        error_messages={
            'does_not_exist': 'Тег не найден!'
        }
    )

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients',
                  'name', 'image', 'text', 'cooking_time')

    def to_representation(self, instance):
        serializer = RecipeSerializer(
            instance,
            context=self.context
        )
        return serializer.data

    def validate(self, data):
        if not data.get('tags'):
            raise ValidationError('Необходимо указать теги!')
        if not data.get('ingredients'):
            raise ValidationError('Необходимо внести ингредиенты!')
        return data

    def validate_tags(self, value):
        if not self.initial_data.get('tags'):
            raise ValidationError('Необходимо указать теги!')
        if not value:
            raise ValidationError('Необходимо указать хотя бы '
                                  'один тег для ингредиента!')
        if len(value) != len(set(value)):
            raise ValidationError('Теги рецепта '
                                  'должны быть уникальны')
        return value

    def validate_ingredients(self, value):
        if not value:
            raise ValidationError('Необходимо внести хотя бы '
                                  'один ингредиент!')
        id_list = []
        for ingredient in value:
            id_list.append(ingredient.get('id'))
            if not ingredient.get('amount'):
                raise ValidationError('Укажите количество '
                                      f'ингредиента {ingredient}')
        if len(id_list) != len(set(id_list)):
            raise ValidationError('Ингредиенты рецепта '
                                  'должны быть уникальны')
        return value

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        for ingredient in ingredients:
            recipe.contents.create(
                ingredient=ingredient['id'],
                amount=ingredient['amount']
            )
        recipe.tags.set(tags)
        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients')
        instance.contents.all().delete()
        tags = validated_data.pop('tags')
        instance.tags.clear()
        for ingredient in ingredients:
            instance.contents.create(
                ingredient=ingredient['id'],
                amount=ingredient['amount']
            )
        instance.tags.set(tags)
        super().update(instance, validated_data)
        return instance


class SubscriptionsSerializer(UserSerializer):
    recipes = RecipeSerializer(
        many=True,
        fields=('id', 'name', 'image', 'cooking_time')
    )
    recipes_count = IntegerField(default=0, read_only=True)

    class Meta(UserSerializer.Meta):
        extra_fields = ('recipes', 'recipes_count')
        fields = UserSerializer.Meta.fields + extra_fields
        read_only_fields = extra_fields
