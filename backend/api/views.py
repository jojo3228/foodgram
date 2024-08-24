from django.db.models import Sum
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from djoser.views import UserViewSet
from rest_framework import filters, mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from api.pagination import PageLimitPagination
from api.serializers import (UserAvatarSerializer, IngredientSerializer,
                             TagSerializer, RecipeReadSerializer,
                             RecipeCreateSerializer, UserCreateSerializer,
                             SubscribeCreateSerializer,
                             SubscribeDisplaySerializer, FavoriteSerializer,
                             ShoppingCartCreateSerializer, RecipeIngredient)
from backend.settings import FILE_NAME
from recipes.models import (Favorite, Ingredient, Recipe,
                            ShoppingCart, Tag)
from users.models import User, Subscribe
from .filters import IngredientFilter, RecipeFilter
from .permissions import IsAuthorOrReadOnly


# def redirect_link(request, pk, recipe_hash):
#     # Получаем объект рецепта, проверяя наличие по pk и short_code
#     recipe = get_object_or_404(Recipe, pk=pk, short_code=short_code)
#     # Перенаправляем на нужный URL
#     return redirect(f'/recipes/{pk}')

def redirect_link(request, recipe_hash):
    print(da)
    recipe = get_object_or_404(Recipe, short_code=recipe_hash)
    relative_url = '/recipes/' + str(recipe.pk) + '/'
    full_url = request.build_absolute_uri(relative_url)
    return HttpResponseRedirect(full_url)


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
        serializer.is_valid(raise_exception=True)
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
        serializer = SubscribeDisplaySerializer(
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
        author = get_object_or_404(User, id=author_id).pk
        data = {
            'subscriber': request.user.pk,
            'author': author,
        }

        serializer = SubscribeCreateSerializer(
            data=data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            serializer.data, status=status.HTTP_201_CREATED
        )

    @subscribe.mapping.delete
    def unsubscribe(self, request, id=None):
        author_id = get_object_or_404(User, pk=id).pk
        deleted_count, _ = Subscribe.objects.filter(
            subscriber=request.user.pk,
            author=author_id
        ).delete()
        if not deleted_count:
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
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk):
        user = self.request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        deleted_fav, _ = Favorite.objects.filter(user=user,
                                                 recipe=recipe).delete()
        if not deleted_fav:
            return Response(
                {'detail': 'Рецепта нет в избранном.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(
            'Рецепт успешно удалён из избранного.',
            status=status.HTTP_204_NO_CONTENT,
        )

    @action(
        methods=('post',),
        detail=True,
        permission_classes=[IsAuthenticated],
    )
    def shopping_cart(self, request, pk=None):
        user = self.request.user
        recipe = get_object_or_404(Recipe, pk=pk).pk

        data = {
            'user': user.pk,
            'recipe': recipe,
        }

        serializer = ShoppingCartCreateSerializer(
            data=data, context={'request': request}
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @shopping_cart.mapping.delete
    def remove_from_shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        deleted_item, _ = ShoppingCart.objects.filter(
            user=request.user, recipe=recipe
        ).delete()
        if not deleted_item:
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
            recipe__shopping_recipe__user=request.user).values(
                'ingredient__name', 'ingredient__measurement_unit').annotate(
                    total_amount=Sum('amount')).order_by(
            'ingredient__name', 'ingredient__measurement_unit'
        )

        shopping_list = [
            (f"{item['ingredient__name']} - "
             f"{item['total_amount']} {item['ingredient__measurement_unit']}.")
            for item in ingredients
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
        full_url = request.build_absolute_uri(f'/s/{recipe.short_code}')
        return Response({'short-link': full_url}, status=status.HTTP_200_OK)
