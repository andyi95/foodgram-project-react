from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.exceptions import APIException
from rest_framework.generics import get_object_or_404
from foodgram_api.settings import PAGE_SIZE
from api.paginators import PageNumberPaginatorModified
from api.models import (FavorRecipes, Follow, Ingredient, Recipe,
                        RecipeComponent, ShoppingList, Tag)
from users.models import User
from users.serializers import UserSerializer


class FollowSerializer(serializers.ModelSerializer):
    queryset = User.objects.all()
    user = serializers.PrimaryKeyRelatedField(queryset=queryset)
    author = serializers.PrimaryKeyRelatedField(queryset=queryset)

    class Meta:
        model = Follow
        fields = ('user', 'author')

    def validate(self, data):
        # По большому счёту, здесь и не нужна проверка метода - сериализатор
        # вызывается только из метода get(), для delete() он не нужен, а
        # на всё остальное Django сам вернёт ошибку 405
        user = self.context.get('request').user
        author_id = data['author'].id
        if user.pk == author_id:
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя'
            )
        follow_exist = Follow.objects.filter(
            user=user,
            author__id=author_id
        ).exists()
        if follow_exist:
            raise serializers.ValidationError(
                'Подписка существует')

        return data

    def to_representation(self, instance):
        request = self.context.get('request')
        context = {'request': request}
        return FollowReadSerializer(
            instance.author,
            context=context).data


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientReadSerializer(serializers.ModelSerializer):
    id = serializers.SlugRelatedField(
        source='ingredient',
        slug_field='id',
        queryset=Ingredient.objects.all()
    )
    name = serializers.SlugRelatedField(
        source='ingredient',
        slug_field='name',
        read_only=True
    )
    measurement_unit = serializers.SlugRelatedField(
        source='ingredient.measurement_unit',
        slug_field='name',
        read_only=True
    )

    class Meta:
        model = RecipeComponent
        fields = ('id', 'name', 'measurement_unit', 'amount')


class IngredientWriteSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    amount = serializers.IntegerField()
    measurement_unit = serializers.SlugRelatedField(
        source='ingredient.measurement_unit',
        slug_field='name',
        read_only=True
    )

    class Meta:
        model = Ingredient
        fields = ('id', 'amount', 'measurement_unit')

    def validate(self, attrs):
        """Валидация количества ингредиента.

        Условие исправил - лучше избегать неоднозначностей в коде. Сначала
        я сомневался, оставить-ли возможность нулевого количества, поскольку
        есть ингредиенты 'по вкусу', но их потом будет не посчитать в корзине.
        """
        if not Ingredient.objects.filter(pk=attrs['id']).exists:
            raise serializers.ValidationError(
                {
                    'ingredients': f'Ингредениет с id {attrs["id"]} не найден'
                },
            )
        if int(attrs['amount']) < 1:
            raise serializers.ValidationError(
                {
                    'ingredients':
                        'Количество ингредиента не может быть меньше 1'
                }
            )
        return attrs


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class RecipeComponentSerializer(serializers.ModelSerializer):
    id = serializers.SlugRelatedField(
        source='ingredient',
        slug_field='id',
        queryset=Ingredient.objects.all()
    )
    name = serializers.SlugRelatedField(
        source='ingredient',
        slug_field='name',
        read_only=True
    )
    measurement_unit = serializers.SlugRelatedField(
        source='ingredient',
        slug_field='measurement_unit',
        read_only=True
    )

    class Meta:
        model = RecipeComponent
        fields = ('id', 'name', 'measurement_unit', 'amount',)


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для валидации создания и обновления рецептов."""
    tags = serializers.SlugRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        slug_field='id'
    )
    cooking_time = serializers.IntegerField()
    ingredients = IngredientWriteSerializer(many=True)
    author = UserSerializer(read_only=True)
    image = Base64ImageField(max_length=None, use_url=True, required=False)

    class Meta:
        model = Recipe
        fields = ('id', 'author', 'tags', 'ingredients', 'name',
                  'image', 'text', 'cooking_time')

    def validate(self, attrs):
        ingredients = self.initial_data.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError(
                {'ingredients':
                    'Список ингредиентов не получен'}
            )
        return attrs

    def create_update_method(self, validated_data, recipe=None):
        """Common method implementing DRY for update(), create() actions."""
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        if recipe:
            recipe.component_recipes.all().delete()
        else:
            recipe = Recipe.objects.create(**validated_data)
        ingredient_instances = []
        seen_ingredients = set()
        for ingredient in ingredients:
            id = ingredient['id']
            if id in seen_ingredients:
                raise serializers.ValidationError(
                    f'Найден дублирующийся ингредиент id {id}'
                )
            seen_ingredients.add(id)
            ingr_id = Ingredient.objects.get(pk=id)
            amt = ingredient['amount']
            ingredient_instances.append(
                RecipeComponent(ingredient=ingr_id, recipe=recipe, amount=amt)
            )
        RecipeComponent.objects.bulk_create(ingredient_instances)
        recipe.tags.set(tags)
        return recipe

    def create(self, validated_data):
        return self.create_update_method(validated_data)

    def update(self, instance, validated_data):
        instance = self.create_update_method(validated_data, recipe=instance)
        instance.name = validated_data.pop('name')
        instance.text = validated_data.pop('text')
        if validated_data.get('image') is not None:
            instance.image = validated_data.pop('image')
        instance.cooking_time = validated_data.pop('cooking_time')
        instance.save()
        return instance

    def to_representation(self, instance):
        return RecipeReadSerializer(
            instance,
            context={
                'request': self.context.get('request')
            }
        ).data


class RecipeReadSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)

    is_favorited = serializers.BooleanField(read_only=True)
    is_in_shopping_cart = serializers.BooleanField(read_only=True)
    ingredients = serializers.SerializerMethodField('get_ingredients')

    class Meta:
        model = Recipe
        fields = '__all__'

    def get_ingredients(self, recipe):
        queryset = RecipeComponent.objects.filter(recipe=recipe)
        return RecipeComponentSerializer(queryset, many=True).data


class FollowReadSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.BooleanField(read_only=True)
    recipes = RecipeReadSerializer(many=True, read_only=True)
    recipes_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count'
        )

    def paginated_recipes(self, obj):
        paginator = PageNumberPaginatorModified(obj.recipes.all(), PAGE_SIZE)



class ShoppingSerializer(serializers.ModelSerializer):

    class Meta:
        model = ShoppingList
        fields = '__all__'

    def validate(self, attrs):
        if not Ingredient.objects.filter(pk=attrs['id']).exists:
            raise serializers.ValidationError(
                {
                    'ingredients':
                        f'Ингредениет с id {attrs["recipes"]} не найден'
                },
            )
        author = self.context.get('request').user
        recipe = attrs['recipes']
        recipe_exists = ShoppingList.objects.filter(
            author=author,
            recipes=recipe
        ).exists()
        if recipe_exists:
            raise serializers.ValidationError(
                'Рецепт уже в корзине'
            )
        return attrs


class FavorSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        if not Recipe.objects.filter(pk=attrs['recipes'].id).exists:
            raise serializers.ValidationError(
                {
                    'recipes': f'Рецепт с id {attrs["recipes"]} не найден'
                }
            )
        follow_exists = FavorRecipes.objects.filter(
            author=attrs['author'],
            recipes=attrs['recipes']
        ).exists()
        if follow_exists:
            raise serializers.ValidationError(
                'Вы уже добавили рецепт в избранное'
            )
        return attrs

    class Meta:
        model = FavorRecipes
        fields = '__all__'


class ListFavorSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
