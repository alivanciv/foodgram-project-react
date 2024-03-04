from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.auth import get_user_model

from recipes.constants import (
    MAX_TEXT_LENGTH,
    MAX_NAME_LENGTH,
    MAX_COLOR_LENGTH,
    TAG_CHOICES,
)

User = get_user_model()


class Tag(models.Model):
    name = models.CharField(
        'Тег',
        max_length=MAX_NAME_LENGTH,
        choices=TAG_CHOICES,
        unique=True
    )
    color = models.CharField(
        'Цветовой код',
        max_length=MAX_COLOR_LENGTH,
        unique=True
    )
    slug = models.SlugField(unique=True)

    class Meta:
        ordering = ('name',)
        verbose_name = 'тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name[:MAX_TEXT_LENGTH]


class Ingredient(models.Model):
    name = models.CharField(
        'Название',
        max_length=MAX_NAME_LENGTH
    )
    measurement_unit = models.CharField(
        'Единицы измерения',
        max_length=MAX_NAME_LENGTH
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = [
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='unique_ingredient_units',
                violation_error_message='Вы уже создавали ингредиент '
                                        'с такими ед.изм.'
            )
        ]

    def __str__(self):
        return self.name[:MAX_TEXT_LENGTH]


class Recipe(models.Model):
    author = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор'
    )
    pub_date = models.DateTimeField('Дата публикации', auto_now_add=True)
    name = models.CharField(
        'Название',
        max_length=MAX_NAME_LENGTH
    )
    image = models.ImageField(
        'Фото',
        upload_to='recipes_images'
    )
    text = models.TextField('Описание')
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Ингредиенты',
        related_name='recipes'
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги',
        related_name='recipes'
    )
    cooking_time = models.PositiveIntegerField(
        'Время приготовления',
        validators=[MinValueValidator(1, 'Время должно быть больше 0')],
        help_text='Введите время в минутах'
    )

    class Meta:
        ordering = ('-pub_date', 'name')
        verbose_name = 'рецепт'
        verbose_name_plural = 'Рецепты'
        constraints = [
            models.UniqueConstraint(
                fields=('author', 'name'),
                name='unique_user_recipe',
                violation_error_message='Вы уже создавали рецепт '
                                        'с таким названием'
            )
        ]

    def __str__(self):
        return self.name[:MAX_TEXT_LENGTH]


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='contents'
    )
    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.CASCADE,
        verbose_name='Ингредиент',
        related_name='composes'
    )
    amount = models.PositiveIntegerField(
        'Количество',
        validators=[MinValueValidator(1)]
    )

    class Meta:
        ordering = ('ingredient__name',)
        constraints = [
            models.UniqueConstraint(
                fields=('recipe', 'ingredient'),
                name='unique_composition'
            )
        ]
        verbose_name = 'ингредиент рецепта'
        verbose_name_plural = 'Ингредиенты рецепта'

    def __str__(self):
        return ('{} - {} {}'.format(
            self.ingredient,
            self.amount,
            self.ingredient.measurement_unit)
        )


class RecipeFavorite(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='favorites')
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE,
        related_name='favorited'
    )
    created_at = models.DateTimeField('Дата добавления', auto_now_add=True)

    class Meta:
        verbose_name = 'избранное'
        verbose_name_plural = 'Избранное'
        ordering = ('-created_at',)
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_user_favorite_recipe',
            )
        ]


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='shopping_cart')
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE,
        related_name='buyers'
    )
    created_at = models.DateTimeField('Дата публикации', auto_now_add=True)

    class Meta:
        verbose_name = 'список покупок'
        verbose_name_plural = 'Списки покупок'
        ordering = ('-created_at',)
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_user_recipe_to_buy'
            )
        ]
