from django.contrib import admin
from django.utils.safestring import mark_safe
from import_export import resources

from .models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                     ShoppingCart, Tag)


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1
    min_num = 1


class RecipeTagInline(admin.TabularInline):
    model = Recipe.tags.through
    extra = 1
    min_num = 1


class IngredientResource(resources.ModelResource):
    class Meta:
        model = Ingredient


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    '''Админка ингредиентов.'''

    list_display = ('name', 'measurement_unit')
    list_filter = ('name',)
    search_fields = ('name',)
    resource_class = IngredientResource


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    '''Админка тэгов.'''

    list_display = ('name', 'slug')
    list_editable = ('slug',)
    list_display_links = ('name',)
    search_fields = ('name', 'slug')
    empty_value_display = '-пусто-'


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    '''Админка рецетов.'''

    list_display = (
        'name',
        'cooking_time',
        'text',
        'author',
        'ingredients_list',
        'favorites_count',
        'image',
    )
    list_editable = (
        'cooking_time',
        'text',
        'image',
        'author',
    )
    list_display_links = ('name',)
    list_filter = ('name',)
    search_fields = ('name', 'author')
    empty_value_display = '-пусто-'

    inlines = [RecipeIngredientInline, RecipeTagInline]

    def ingredients_list(self, obj):
        return ', '.join(
            (str(ingredient) for ingredient in obj.ingredients.all())
        )

    def favorites_count(self, obj):
        return obj.recipe_favorites.count()

    def image(self, obj):
        return mark_safe(f"<img src={obj.image.url} width='80' height='60'>")


@admin.register(RecipeIngredient)
class RecipeIngredientsAdmin(admin.ModelAdmin):
    '''Админка ингридиентов для рецепта.'''

    list_display = ('recipe', 'ingredient', 'amount')
    search_fields = ('recipe',)
    empty_value_display = '-пусто-'


@admin.register(ShoppingCart)
class ShoppingCartListAdmin(admin.ModelAdmin):
    '''Админка корзины.'''

    list_display = (
        'user',
        'recipe',
    )
    search_fields = ('recipe',)
    empty_value_display = '-пусто-'


@admin.register(Favorite)
class FavouriteAdmin(admin.ModelAdmin):
    '''Админка избранного.'''

    list_display = (
        'user',
        'recipe',
    )
    search_fields = ('recipe', 'user')
    empty_value_display = '-пусто-'
