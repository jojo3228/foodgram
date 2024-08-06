from colorfield.fields import ColorField
from django.contrib.auth import get_user_model
from django.core import validators
from django.db import models

User = get_user_model()


class Tag(models.Model):
    name = models.CharField('Название тега', max_length=200, unique=True)
    color = ColorField('Цвет в HEX')
    slug = models.CharField(
        max_length=200,
        unique=True,
        null=True,
        verbose_name='Слаг',
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField('Название', max_length=200, null=False)
    measurement_unit = models.CharField('Единица измерения', max_length=200)

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
    name = models.CharField('Название рецепта', max_length=200)
    image = models.ImageField('Картинка', upload_to='recipes/', blank=True)
    text = models.TextField('Описание')
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Ингридиенты',
        related_name='recipes',
    )
    tags = models.ManyToManyField(Tag, verbose_name='Теги')
    cooking_time = models.IntegerField(
        'Время приготовления, мин',
        validators=(validators.MinLengthValidator(1),),
    )
    pub_date = models.DateTimeField('Дата публикации', auto_now_add=True)

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-id',)

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
        validators=(validators.MinValueValidator(1),),
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
