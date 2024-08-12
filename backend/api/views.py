from django.db.models import Sum
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from http import HTTPStatus
from rest_framework import filters, mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from api.pagination import PageLimitPagination
from api.serializers import (UserAvatarSerializer, IngredientSerializer,
                             TagSerializer, RecipeReadSerializer,
                             RecipeCreateSerializer, UserCreateSerializer,
                             SubscribeSerializer, FavoriteSerializer,
                             RecipeSmallSerializer, RecipeIngredient)
from backend.settings import FILE_NAME
from recipes.models import (Favorite, Ingredient, Recipe,
                            ShoppingCart, Tag)
from users.models import User, Subscribe
from .filters import IngredientFilter, RecipeFilter
from .permissions import IsAuthorOrReadOnly


class UserCustomViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = UserCreateSerializer
    pagination_class = PageLimitPagination

    @action(
        detail=False,
        methods=('get',),
        pagination_class=None,
        permission_classes=(IsAuthenticated,),
    )
    def me(self, request):
        serializer = UserCreateSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=('put',),
        url_path='me/avatar',
        permission_classes=(IsAuthenticated,),
    )
    def me_avatar(self, request):
        user = self.get_instance()
        serializer = UserAvatarSerializer(instance=user, data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(data=serializer.data, status=status.HTTP_200_OK)

    @me_avatar.mapping.delete
    def delete_avatar(self, request):
        user = self.get_instance()
        if user.avatar:
            user.avatar.delete()
            user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

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
        methods=('post',),
        permission_classes=(IsAuthenticated,),
    )
    def subscribe(self, request, **kwargs):
        author_id = self.kwargs.get('id')
        author = get_object_or_404(User, id=author_id)

        serializer = SubscribeSerializer(
            author, data=request.data, context={'request': request}
        )
        if serializer.is_valid(raise_exception=True):
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

    @subscribe.mapping.delete
    def unsubscribe(self, request, **kwargs):
        author_id = self.kwargs.get('id')
        author = get_object_or_404(User, id=author_id)

        deleted_count, _ = Subscribe.objects.filter(
            subscriber=request.user,
            author=author
        ).delete()

        if deleted_count == 0:
            return Response(
                {'detail': 'Вы не подписаны на этого пользователя.'},
                status=status.HTTP_400_BAD_REQUEST
            )

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
        methods=('post',),
        detail=True,
        permission_classes=(IsAuthenticated,),
    )
    def favorite(self, request, pk):
        user = self.request.user
        recipe = get_object_or_404(Recipe, pk=pk)

        serializer = FavoriteSerializer(
            data={'user': user.id, 'recipe': recipe.id},
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=HTTPStatus.CREATED)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk):
        user = self.request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        deleted_fav, _ = Favorite.objects.filter(user=user,
                                                 recipe=recipe).delete()
        if deleted_fav == 0:
            return Response(
                {'detail': 'Рецепта нет в избранном.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(
            'Рецепт успешно удалён из избранного.',
            status=HTTPStatus.NO_CONTENT,
        )

    @action(
        methods=('post',),
        detail=True,
        permission_classes=[IsAuthenticated],
    )
    def shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)

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

    @shopping_cart.mapping.delete
    def remove_from_shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        deleted_item, _ = ShoppingCart.objects.filter(
            user=request.user, recipe=recipe
        ).delete()

        if deleted_item == 0:
            return Response(
                {'detail': 'Рецепт отсутствует в списке покупок.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(
            {'detail': 'Рецепт удален из списка покупок.'},
            status=status.HTTP_204_NO_CONTENT
        )

    @action(
        detail=False,
        methods=('get',),
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

    @action(
        methods=('get',),
        detail=True,
        permission_classes=(AllowAny,),
        url_path='get-link'
    )
    def get_link(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        full_url = request.build_absolute_uri(f'/recipes/{recipe.short_code}/')
        return Response({'short-link': full_url}, status=status.HTTP_200_OK)
