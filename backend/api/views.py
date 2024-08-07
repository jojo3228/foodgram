import pyshorteners

from http import HTTPStatus

from django.db.models import Sum
from django.http import HttpResponse
from djoser.views import UserViewSet
from backend.settings import FILE_NAME
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from users.models import User, Subscribe
from .filters import IngredientFilter, RecipeFilter
from .permissions import IsAuthorOrReadOnly
from api.serializers import (UserAvatarSerializer, IngredientSerializer,
                             TagSerializer, RecipeReadSerializer,
                             RecipeCreateSerializer, UserReadSerializer,
                             SubscribeSerializer, FavoriteSerializer,
                             RecipeSmallSerializer, RecipeIngredient)
from api.pagination import PageLimitPagination
from recipes.models import (Favorite, Ingredient, Recipe,
                            ShoppingCart, Tag)
from rest_framework import filters, mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response


class UserViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = UserReadSerializer
    pagination_class = PageLimitPagination

    @action(
        detail=False,
        methods=('get',),
        pagination_class=None,
        permission_classes=(IsAuthenticated,),
    )
    def me(self, request):
        serializer = UserReadSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,),
        pagination_class=PageLimitPagination,
    )
    def subscriptions(self, request):
        subscriptions = Subscribe.objects.filter(subscriber=request.user)
        subscribing_users = User.objects.filter(
            subscribing__in=subscriptions
        )
        serializer = SubscribeSerializer(
            self.paginate_queryset(subscribing_users),
            many=True,
            context={'request': request},
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(IsAuthenticated,),
    )
    def subscribe(self, request, **kwargs):
        author_id = self.kwargs.get('id')
        author = get_object_or_404(User, id=author_id)

        if request.method == 'POST':
            if request.user == author:
                return Response(
                    {'detail': 'Вы не можете подписаться на себя.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            serializer = SubscribeSerializer(
                author, data=request.data, context={'request': request}
            )
            if serializer.is_valid():
                if Subscribe.objects.filter(
                    subscriber=request.user, author=author
                ).exists():
                    return Response(
                        {'detail': 'Вы уже подписаны на этого пользователя.'},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                Subscribe.objects.create(
                    subscriber=request.user, author=author
                )
                return Response(
                    serializer.data, status=status.HTTP_201_CREATED
                )

        get_object_or_404(
            Subscribe, subscriber=request.user, author=author
        ).delete()
        return Response(
            {'detail': 'Успешная отписка'}, status=status.HTTP_204_NO_CONTENT
        )


class TagViewSet(
    viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin
):
    '''Вьюсет тэгов.'''

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(
    viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin
):
    '''Вьюсет ингредиентов.'''

    queryset = Ingredient.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    filterset_class = IngredientFilter


class RecipeViewSet(viewsets.ModelViewSet):
    '''Вьюсет рецептов.'''

    queryset = Recipe.objects.all()
    pagination_class = PageLimitPagination
    permission_classes = (IsAuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method in permissions.SAFE_METHODS:
            return RecipeReadSerializer
        return RecipeCreateSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        ('post', 'delete'),
        detail=True,
        permission_classes=(IsAuthenticated,),
    )
    def favorite(self, request, pk):
        user = self.request.user
        recipe = get_object_or_404(Recipe, pk=pk)

        if request.method == 'POST':
            if Favorite.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    'Рецепт уже есть в избранном.',
                    status=HTTPStatus.BAD_REQUEST,
                )
            serializer = FavoriteSerializer(
                data={'user': user.id, 'recipe': recipe.id},
                context={'request': request},
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=HTTPStatus.CREATED)

        if not Favorite.objects.filter(user=user, recipe=recipe).exists():
            return Response(
                'Рецепта нет в избранном.',
                status=HTTPStatus.NOT_FOUND,
            )
        Favorite.objects.filter(user=user, recipe=recipe).delete()
        return Response(
            'Рецепт успешно удалён из избранного.',
            status=HTTPStatus.NO_CONTENT,
        )

    @action(
        methods=['post', 'delete'],
        detail=True,
        permission_classes=[IsAuthenticated],
    )
    def shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, id=pk)

        if request.method == 'POST':
            serializer = RecipeSmallSerializer(
                recipe, data=request.data, context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            if not ShoppingCart.objects.filter(user=request.user,
                                               recipe=recipe).exists():
                ShoppingCart.objects.create(user=request.user, recipe=recipe)
                return Response(serializer.data,
                                status=status.HTTP_201_CREATED)
            return Response(
                {'errors': 'Рецепт уже добавлен в список покупок.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        shopping_cart_item = get_object_or_404(ShoppingCart,
                                               user=request.user,
                                               recipe=recipe)
        shopping_cart_item.delete()
        return Response(
            {'detail': 'Рецепт удален из списка покупок.'},
            status=status.HTTP_204_NO_CONTENT
        )

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
    )
    def download_shopping_cart(self, request, **kwargs):
        ingredients = RecipeIngredient.objects.filter(
            recipe__shopping_recipe__user=request.user
        ).select_related('ingredient').annotate(
            total_amount=Sum('amount')
        ).values_list(
            'ingredient__name', 'total_amount', 'ingredient__measurement_unit'
        )

        shopping_list = [
            f"{name} - {amount} {unit}."
            for name, amount, unit in ingredients
        ]

        response_content = 'Список покупок:\n' + '\n'.join(shopping_list)
        response = HttpResponse(response_content, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename={FILE_NAME}'

        return response


class UserAvatarViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserAvatarSerializer
    permission_classes = [IsAuthorOrReadOnly]

    def get_queryset(self):
        return User.objects.filter(id=self.request.user.id)

    def update(self, request, *args, **kwargs):
        partial = request.method == 'PATCH'
        serializer = self.get_serializer(self.get_object(),
                                         data=request.data,
                                         partial=partial)
        if serializer.is_valid():
            self.perform_update(serializer)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=False,
        methods=('put', 'delete',),
        url_path='me/avatar/',
    )
    def avatar(self, request):
        user = request.user
        if 'avatar' in request.data:
            file = request.data['avatar']
            user.avatar = file
            user.save()
            return Response({'status': 'avatar updated'},
                            status=status.HTTP_200_OK)
        return Response({'error': 'No avatar provided'},
                        status=status.HTTP_400_BAD_REQUEST)


class ShortLinkViewSet(viewsets.ViewSet):
    def shorten(request, url):
        shortener = pyshorteners.Shortener()
        shortened_url = shortener.chilpit.short(url)
        return HttpResponse(
            f'Shortened URL: <a href="{shortened_url}">{shortened_url}</a>')
