from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie
from djoser import views
from rest_framework import status, viewsets
from rest_framework.generics import ListAPIView, get_object_or_404
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from users.models import User
from users.serializers import UserSerializer

from api.filters import IngredientFilter, RecipeFilter
from api.models import (FavorRecipes, Follow, Ingredient, Recipe,
                        RecipeComponent, ShoppingList, Tag)
from api.permissions import IsOwnerOrReadOnly
from api.serializers import (FavorSerializer, FollowReadSerializer,
                             FollowSerializer, IngredientSerializer,
                             RecipeReadSerializer, RecipeWriteSerializer,
                             ShoppingSerializer, TagSerializer)


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
    @method_decorator(cache_page(60 * 60))
    def dispatch(self, request, *args, **kwargs):
        """
        Подключили кэширование для самых "тяжеловесных" вьюсетов
        """
        return super(RecipeViewSet, self).dispatch(request, *args, **kwargs)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny, )
    filter_class = IngredientFilter
    search_fields = ['name', ]
    pagination_class = None

    @method_decorator(vary_on_cookie)
    @method_decorator(cache_page(60 * 60))
    def dispatch(self, request, *args, **kwargs):
        return super(IngredientViewSet, self).dispatch(
            request, *args, **kwargs
        )


class FavoriteViewSet(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = FavorSerializer
    obj = Recipe

    def get(self, request, recipe_id):
        user = request.user
        recipe = get_object_or_404(self.obj, id=recipe_id)
        data = {
            'author': user.id,
            'recipes': recipe.id
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
        recipe = get_object_or_404(Recipe, id=recipe_id)
        favorite_obj = get_object_or_404(
            FavorRecipes, author=user, recipes=recipe
        )
        favorite_obj.delete()
        return Response(
            'Removed', status=status.HTTP_204_NO_CONTENT)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class ShoppingViewSet(FavoriteViewSet):
    serializer_class = ShoppingSerializer

    def delete(self, request, recipe_id):
        """
        Наследовать данный метод нецелесообразно, поскольку отличается
        не только объект, но и поля для удаления
        """
        user = request.user
        recipe = get_object_or_404(Recipe, id=recipe_id)
        shopping_list_obj = get_object_or_404(
            ShoppingList, author=user, recipe=recipe)
        shopping_list_obj.delete()
        return Response('Deleted', status=status.HTTP_204_NO_CONTENT)


class AuthorViewSet(views.UserViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    @method_decorator(vary_on_cookie)
    @method_decorator(cache_page(60 * 60))
    def dispatch(self, request, *args, **kwargs):
        return super(AuthorViewSet, self).dispatch(request, *args, **kwargs)


class FollowViewSet(APIView):
    permission_classes = (IsAuthenticated, )

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
    queryset = User.objects.all()
    serializer_class = FollowReadSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return User.objects.filter(following__user=self.request.user)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({'request': self.request})
        return context

    @method_decorator(vary_on_cookie)
    @method_decorator(cache_page(60 * 60))
    def dispatch(self, request, *args, **kwargs):
        return super(FollowReadViewSet, self).dispatch(
            request, *args, **kwargs
        )


class ShoppingCartDL(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        К сожалению, полное извлечение данных с помощью аннотаций и F() не
        осилил, но количество запросов уменьшили
        """
        user = request.user
        ingredts = RecipeComponent.objects.filter(
            recipe__author__author__author_id=user.id
        )
        shop_list = {}
        for ingredient in ingredts:
            amount = ingredient.amount
            name = ingredient.ingredient.name
            unit = ingredient.ingredient.units
            if name not in shop_list:
                shop_list[name] = {
                    'units': unit,
                    'amount': amount
                }
            else:
                shop_list[name]['amount'] += amount
        # Comprehansion применил, но без двойных кавычек тут
        # сложновато обойтись
        wishlist = [f'{item} - {shop_list[item]["amount"]} '
                    f'{shop_list[item]["unit"]} \r\n' for item in shop_list]
        wishlist.append('\r\n')
        wishlist.append('FoodGram, 2021')
        response = HttpResponse(wishlist, 'Content-Type: text/plain')
        response['Content-Disposition'] = 'attachment; filename="wishlist.txt"'
        return response
