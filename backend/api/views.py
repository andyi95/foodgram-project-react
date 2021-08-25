from django.db.models import BooleanField, Count, Sum, Value
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie
from django.core.cache import cache
from djoser import views
from api.paginators import PageNumberPaginatorModified
from rest_framework import status, viewsets
from rest_framework.generics import ListAPIView, get_object_or_404
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from rest_framework.views import APIView

from api.filters import IngredientFilter, RecipeFilter
from api.models import (FavorRecipes, Follow, Ingredient, Recipe,
                        RecipeComponent, ShoppingList, Tag)
from api.permissions import IsOwnerOrReadOnly
from api.serializers import (FavorSerializer, FollowReadSerializer,
                             FollowSerializer, IngredientSerializer,
                             RecipeReadSerializer, RecipeWriteSerializer,
                             ShoppingSerializer, TagSerializer)
from foodgram_api.settings import CACHE_TIMEOUT
from users.models import User
from users.serializers import UserSerializer


class RecipeViewSet(viewsets.ModelViewSet):
    filter_class = RecipeFilter
    permission_classes = [IsOwnerOrReadOnly, ]
    queryset = Recipe.objects.prefetch_related(
        'ingredients', 'author', 'tags'
    )

    def get_queryset(self):
        user = self.request.user
        queryset = super(RecipeViewSet, self).get_queryset()
        if user.is_anonymous or user is None:
            return queryset
        return queryset.opt_annotations(user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        cache.clear()
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        return serializer.save(author=self.request.user)

    def get_serializer_class(self):
        if self.request.method in ['GET', ]:
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({'request': self.request})
        return context

    @method_decorator(vary_on_cookie)
    @method_decorator(cache_page(CACHE_TIMEOUT))
    def dispatch(self, request, *args, **kwargs):
        """Подключили кэширование для самых "тяжеловесных" вьюсетов."""
        return super(RecipeViewSet, self).dispatch(request, *args, **kwargs)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny, )
    filter_class = IngredientFilter
    search_fields = ['name', ]
    pagination_class = None

    @method_decorator(vary_on_cookie)
    @method_decorator(cache_page(CACHE_TIMEOUT))
    def dispatch(self, request, *args, **kwargs):
        return super(IngredientViewSet, self).dispatch(
            request, *args, **kwargs
        )


class CommonViewSet(APIView):
    """Common viewset for creation by get and delete methods."""
    permission_classes = [IsOwnerOrReadOnly]
    serializer_class = None
    obj = Recipe
    del_obj = None

    def get(self, request, recipe_id):
        user = request.user
        data = {
            'author': user.id,
            'recipes': recipe_id
        }
        serializer = self.serializer_class(
            data=data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED)

    def delete(self, request, recipe_id):
        user = request.user
        deletion_obj = get_object_or_404(
            self.del_obj, author=user, recipes_id=recipe_id
        )
        deletion_obj.delete()
        return Response(
            'Removed', status=status.HTTP_204_NO_CONTENT
        )


class FavoriteViewSet(CommonViewSet):
    obj = Recipe
    serializer_class = FavorSerializer
    del_obj = FavorRecipes


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class ShoppingViewSet(CommonViewSet):
    serializer_class = ShoppingSerializer
    obj = Recipe
    del_obj = ShoppingList


class AuthorViewSet(views.UserViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    @method_decorator(vary_on_cookie)
    @method_decorator(cache_page(CACHE_TIMEOUT))
    def dispatch(self, request, *args, **kwargs):
        return super(AuthorViewSet, self).dispatch(request, *args, **kwargs)


class FollowViewSet(APIView):
    permission_classes = [IsOwnerOrReadOnly]

    def get(self, request, author_id):
        user = request.user
        data = {
            'user': user.id,
            'author': author_id
        }
        serializer = FollowSerializer(data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, author_id):
        user = request.user
        follow = get_object_or_404(
            Follow, user_id=user.id, author_id=author_id
        )
        follow.delete()
        return Response('Вы успешно отписаны',
                        status=status.HTTP_204_NO_CONTENT)


class FollowReadViewSet(ListAPIView):
    serializer_class = FollowReadSerializer
    permission_classes = [IsOwnerOrReadOnly]
    pagination_class = PageNumberPaginatorModified

    def get_queryset(self):
        """
        Получаем список подписок вместе с подвязанными рецептами и подсчитанным
        количеством записей. Если мы отдаём список подписок, то делать
        отдельный запрос на признак подписки нецелесообразно - априори будет
        True
        """
        qs = User.objects.filter(
            following__user=self.request.user
        ).prefetch_related('recipes').annotate(
            is_subscribed=Value(True, output_field=BooleanField()),
            recipes_count=Count('recipes__author')
        ).order_by('-author__id')
        return qs

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({'request': self.request})
        return context

    @method_decorator(vary_on_cookie)
    @method_decorator(cache_page(CACHE_TIMEOUT))
    def dispatch(self, request, *args, **kwargs):
        return super(FollowReadViewSet, self).dispatch(
            request, *args, **kwargs
        )


class ShoppingCartDL(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Скачать список покупок с суммированным количеством."""
        user = request.user
        shop_list = RecipeComponent.objects.shop_list(user=user)
        wishlist = [f'{item["name"]} - {item["sum"]} '
                    f'{item["unit"]} \r\n' for item in shop_list]
        wishlist.append('\r\n')
        wishlist.append('FoodGram, 2021')
        response = HttpResponse(wishlist, 'Content-Type: text/plain')
        response['Content-Disposition'] = 'attachment; filename="wishlist.txt"'
        return response
