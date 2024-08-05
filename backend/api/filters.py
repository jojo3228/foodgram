from django_filters.rest_framework import CharFilter, FilterSet, filters

from recipes.models import Recipe, Tag


class RecipeFilter(FilterSet):
    tags = filters.ModelMultipleChoiceFilter(
        field_name="tags__slug",
        to_field_name="slug",
        queryset=Tag.objects.all(),
    )
    is_favorited = filters.BooleanFilter(method="is_favorited_filter")
    is_in_shopping_cart = filters.BooleanFilter(
        method="is_in_shopping_cart_filter"
    )

    class Meta:
        model = Recipe
        fields = (
            "tags",
            "author",
        )

    def is_favorited_filter(self, queryset, name, value):
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(recipe_favorites__user=user)
        return queryset

    def is_in_shopping_cart_filter(self, queryset, name, value):
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(shopping_recipe__user=user)
        return queryset


class IngredientFilter(FilterSet):
    name = CharFilter(field_name="name", lookup_expr="icontains")