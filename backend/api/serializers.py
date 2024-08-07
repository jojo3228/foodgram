from django.db.models import F

from djoser.serializers import UserCreateSerializer
from drf_base64.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.fields import SerializerMethodField
from rest_framework.validators import UniqueTogetherValidator

from .validators import username_validator
from recipes.models import (Ingredient, Tag, Recipe,
                            RecipeIngredient, Favorite, ShoppingCart)
from users.models import User, Subscribe


class UserCreateSerializer(UserCreateSerializer):

    username = serializers.CharField(
        validators=(username_validator,)
    )
    is_subscribed = SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Subscribe.objects.filter(
                subscriber=request.user,
                author=obj,
            ).exists()
        return False


class UserCreationSerializer(UserCreateSerializer):
    '''Сериализатор для создания пользователей.'''

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password',
        )


class UserReadSerializer(serializers.ModelSerializer):
    '''Сериализатор для информации о пользователе.'''

    is_subscribed = SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Subscribe.objects.filter(
                subscriber=request.user,
                author=obj,
            ).exists()
        return False


class RecipeSmallSerializer(serializers.ModelSerializer):
    '''Список рецептов без ингридиентов.'''

    image = Base64ImageField(read_only=True)
    name = serializers.ReadOnlyField()
    cooking_time = serializers.ReadOnlyField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class FavoriteSerializer(serializers.ModelSerializer):
    '''Сериализатор для избранного.'''

    class Meta:
        model = Favorite
        fields = ('user', 'recipe')
        validators = [
            UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=('user', 'recipe'),
                message='Рецепт уже есть в избранном.',
            )
        ]

    def to_representation(self, instance):
        return RecipeSmallSerializer(
            instance.recipe,
            context=self.context,
        ).data


class TagSerializer(serializers.ModelSerializer):
    '''Сериализатор для тэгов.'''

    id = serializers.IntegerField(required=True)

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug',)


class IngredientSerializer(serializers.ModelSerializer):
    '''Сериализатор для ингредиентов.'''

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeReadSerializer(serializers.ModelSerializer):
    '''Сериализатор для списка рецептов.'''

    author = UserCreateSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = serializers.SerializerMethodField()
    image = Base64ImageField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def get_is_in_shopping_cart(self, obj):
        return (
            self.context.get('request').user.is_authenticated
            and ShoppingCart.objects.filter(
                user=self.context['request'].user, recipe=obj
            ).exists()
        )

    def get_is_favorited(self, obj):
        return (
            self.context.get('request').user.is_authenticated
            and Favorite.objects.filter(
                user=self.context['request'].user, recipe=obj
            ).exists()
        )

    def get_ingredients(self, obj):
        ingredients = obj.ingredients.values(
            'id',
            'name',
            'measurement_unit',
            amount=F('ingredients__amount'),
        )
        return ingredients


class RecipeIngredientCreateSerializer(serializers.ModelSerializer):
    '''Ингредиент и количество для создания рецепта.'''

    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(min_value=1)

    class Meta:
        model = RecipeIngredient
        fields = (
            'id',
            'amount',
        )


class RecipeCreateSerializer(serializers.ModelSerializer):
    '''Создание, изменение и удаление рецепта.'''

    author = UserCreateSerializer(read_only=True)
    ingredients = RecipeIngredientCreateSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all()
    )
    image = Base64ImageField()
    cooking_time = serializers.IntegerField(min_value=1)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'image',
            'author',
            'ingredients',
            'name',
            'text',
            'cooking_time',
        )

    def validate(self, obj):
        tags = obj.get('tags', [])
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError('Теги должны быть уникальными.')

        required_fields = {'name': 'Название рецепта',
                           'text': 'Описание',
                           'cooking_time': 'Время приготовления'}
        for field, field_name in required_fields.items():
            if not obj.get(field):
                raise serializers.ValidationError(
                    f'{field_name} - Обязательное поле.')

        if not tags:
            raise serializers.ValidationError(
                'Должен быть указан минимум 1 тег.')

        ingredients = obj.get('ingredients', [])
        if not ingredients:
            raise serializers.ValidationError(
                'Должен быть указан минимум 1 ингредиент.')

        ingredient_ids = [ingredient['id'] for ingredient in ingredients]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                'Ингредиенты должны быть уникальными.')

        return obj

    def tags_and_ingredients_set(self, recipe, tags, ingredients):
        recipe.tags.set(tags)

        ingredients_to_add = [
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient_data['id'],
                amount=ingredient_data['amount'],
            )
            for ingredient_data in ingredients
        ]

        RecipeIngredient.objects.bulk_create(ingredients_to_add)

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        self.tags_and_ingredients_set(recipe, tags, ingredients)
        return recipe

    def update(self, instance, validated_data):
        instance.image = validated_data.get('image', instance.image)
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time
        )
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        RecipeIngredient.objects.filter(
            recipe=instance, ingredient__in=instance.ingredients.all()
        ).delete()
        self.tags_and_ingredients_set(instance, tags, ingredients)
        instance.save()
        return instance

    def to_representation(self, instance):
        return RecipeReadSerializer(
            instance, context={'request': self.context.get('request')}
        ).data


class SubscribeSerializer(serializers.ModelSerializer):
    '''Подписка/отписка на автора.'''

    email = serializers.ReadOnlyField()
    username = serializers.ReadOnlyField()
    first_name = serializers.ReadOnlyField()
    last_name = serializers.ReadOnlyField()
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
            'avatar',
        )

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return Subscribe.objects.filter(subscriber=user, author=obj).exists()

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        recipes = obj.recipes.all()
        if limit:
            recipes = recipes[: int(limit)]
        serializer = RecipeSmallSerializer(recipes, many=True, read_only=True)
        return serializer.data


class UserAvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=False)

    class Meta:
        model = User
        fields = ('avatar',)
