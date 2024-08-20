import random
import string

from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

import api.constants as const

User = get_user_model()


class Tag(models.Model):
    name = models.CharField('Название',
                            max_length=const.TAG_CHAR_LEN)
    slug = models.CharField(
        max_length=const.TAG_CHAR_LEN,
        unique=True,
        null=True,
        verbose_name='Уникальный слаг',
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField('Название',
                            max_length=const.INGREDIENT_CHAR_LEN,
                            null=False)
    measurement_unit = models.CharField('Единица измерения',
                                        max_length=const.MEASUREMENT_CHAR_LEN)

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('name',)

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор',
    )
    name = models.CharField('Название', max_length=const.RECIPE_CHAR_LEN)
    image = models.ImageField('Картинка', upload_to='media/recipes/',
                              blank=True)
    text = models.TextField('Описание')
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Ингридиенты',
        related_name='recipes',
    )
    tags = models.ManyToManyField(Tag, verbose_name='Теги')
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления, мин',
        validators=(MinValueValidator(const.MIN_LEN_VALIDATOR,
                                      message='Меньше минуты'),
                    MaxValueValidator(const.MAX_LEN_VALIDATOR,
                                      message='Блюдо сгорит')),
    )
    pub_date = models.DateTimeField('Дата публикации', auto_now_add=True)
    short_code = models.CharField(max_length=const.CODE_MAX_LEN,
                                  blank=True, null=True, unique=True)

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)

    @staticmethod
    def generate_short_code(length=6):
        return ''.join(random.choices(string.ascii_letters
                                      + string.digits, k=length))

    def generate_unique_short_code(self):
        while True:
            code = self.generate_short_code()
            if not Recipe.objects.filter(short_code=code).exists():
                return code

    def save(self, *args, **kwargs):
        if not self.short_code:
            self.short_code = self.generate_unique_short_code()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    '''Модель количества ингредиентов.'''

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe',
        verbose_name='Рецепт',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент',
        related_name='ingredients',
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество',
        validators=(MinValueValidator(const.MIN_LEN_VALIDATOR,
                                      message='Ничего нет'),
                    MaxValueValidator(const.MAX_LEN_VALIDATOR,
                                      message='Нет места')),
    )

    class Meta:
        verbose_name = 'Ингредиенты в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'
        ordering = ('recipe',)
        constraints = (models.UniqueConstraint(
            fields=('recipe', 'ingredient'), name='unique_combination'
        ),
        )

    def __str__(self):
        return f'{self.recipe} - {self.ingredient}, {self.amount}'


class Favorite(models.Model):
    '''Модель для избранных рецептов.'''

    user = models.ForeignKey(
        User,
        verbose_name='Пользователь',
        on_delete=models.CASCADE,
        related_name='user_favorites',
    )
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        on_delete=models.CASCADE,
        related_name='recipe_favorites',
    )

    class Meta:
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        constraints = (
            models.UniqueConstraint(
                fields=(
                    'recipe',
                    'user'
                ),
                name='favorite_unique'
            ),
        )

    def __str__(self):
        return f'{self.user} добавил {self.recipe} в избранное'


class ShoppingCart(models.Model):
    '''Модель рецептов в корзине.'''

    user = models.ForeignKey(
        User,
        verbose_name='Пользователь',
        on_delete=models.CASCADE,
        related_name='shopping_cart_user',
    )
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        on_delete=models.CASCADE,
        related_name='shopping_recipe',
    )

    class Meta:
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзины'
        constraints = (
            models.UniqueConstraint(
                fields=(
                    'recipe',
                    'user'
                ),
                name='shopping_cart_unique'
            ),
        )

    def __str__(self):
        return f'{self.user} добавил {self.recipe} в корзину'
