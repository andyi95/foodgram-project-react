from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.generics import get_object_or_404

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
        user = self.context.get('request').user
        author_id = data['author'].id

        if self.context.get('request').method == 'GET':
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
    # Изначально не смотрел на то, как фронт обращается к API и назвал поле
    # units в моделях. Но что, если интерфейс API поменяется и надо
    # переименовать поле без перезаписи БД?
    measurement_unit = serializers.SerializerMethodField()

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')

    def get_measurement_unit(self, obj):
        return obj.units


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
    measurement_units = serializers.SlugRelatedField(
        source='ingredient.units',
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
        source='ingredient.units',
        slug_field='name',
        read_only=True
    )

    class Meta:
        model = Ingredient
        fields = ('id', 'amount', 'measurement_unit')


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
        slug_field='units',
        read_only=True
    )

    class Meta:
        model = RecipeComponent
        fields = ('id', 'name', 'measurement_unit', 'amount',)


class RecipeWriteSerializer(serializers.ModelSerializer):
    """
    Сериализатор для валидации создания и обновления рецептов
    """
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
        for ingredient in ingredients:
            if int(ingredient['amount']) <= 0:
                raise serializers.ValidationError(
                    {'ingredients': 'Поле amount не может быть отрицательным'}
                )
        return attrs

    def create_update_method(self, validated_data, recipe=None):
        """Common method implementing DRY for update() and create() actions"""
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        if recipe:
            recipe.component_recipes.all().delete()
        else:
            recipe = Recipe.objects.create(**validated_data)
        ingredient_instances = []
        for ingredient in ingredients:
            ingr_id = get_object_or_404(Ingredient, id=ingredient['id'])
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


class ShoppingSerializer(serializers.ModelSerializer):

    class Meta:
        model = ShoppingList
        fields = '__all__'

    def validate(self, attrs):
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
