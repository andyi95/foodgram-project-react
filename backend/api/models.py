from django.core.validators import MinValueValidator, MinLengthValidator
from django.db import models
from django.db.models import Exists, OuterRef, Sum, Value, Count
from users.models import User


class IngredientQuerySet(models.QuerySet):
    """
    Менеджер для автоматического аннотирования рецепта в представлении списков
    покупок
    """
    def shopping_cart(self, user):
        return self.filter(recipe__shop_list__author=user).annotate(
            amount=Sum('recipe_ingredient__amount')
        ).select_related('units')


class RecipeQuerySet(models.QuerySet):
    """Выделенный QS с дополнительными аннотированными полями"""
    def opt_annotations(self, user):
        if user.is_anonymous:
            return self.annotate(
                is_favorited=Value(
                    False, output_field=models.BooleanField()
                ),
                is_in_shopping_cart=Value(
                    False, output_field=models.BooleanField()
                )
            )
        return self.annotate(
            is_favorited=Exists(FavorRecipes.objects.filter(
                author=user, recipes_id=OuterRef('pk')
            )),
            is_in_shopping_cart=Exists(ShoppingList.objects.filter(
                author=user, recipe_id=OuterRef('pk')
            ))
        )


class Ingredient(models.Model):
    name = models.CharField(
        max_length=200,
        verbose_name='Название'
    )
    units = models.CharField(
        max_length=16,
        verbose_name='Единица измерения'
    )

    objects = IngredientQuerySet.as_manager()

    class Meta:
        # Долго мучался, не мог понять где ошибка
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return f'{self.name}, {self.units}'


class Tag(models.Model):
    name = models.CharField(
        max_length=200,
        verbose_name='Тэг'
    )
    color = models.CharField(
        max_length=200,
        verbose_name='Цвет',
        null=True
    )
    slug = models.SlugField(
        unique=True,
        max_length=200,
        verbose_name='Короткое имя'
    )

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'

    def __str__(self):
        return self.slug


class Recipe(models.Model):
    name = models.CharField(max_length=200, verbose_name='Название')
    image = models.ImageField(
        upload_to='media/',
        blank=True, null=True,
        verbose_name='Картинка рецепта'
    )
    author = models.ForeignKey(
        User,
        related_name='recipes',
        verbose_name='Автор',
        on_delete=models.CASCADE
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name='Ингредиенты',
        through='RecipeComponent',
        blank=False
    )
    text = models.TextField(
        max_length=255,
        verbose_name='Текст',
        null=True
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Тэги'
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления',
        validators=[MinValueValidator(
            limit_value=0,
            message='Время приготовления - неотрицательное значение'
        )]
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )

    objects = RecipeQuerySet.as_manager()

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date', )

    def __str__(self):
        return self.name[:32]


class FollowQuerySet(models.Model):
    """Дополнительный QS, подтягивающий количество рецептов и признак подписки"""
    def opt_annotations(self, user):
        if user.is_anonymous:
            return self
        return self.objects.annotate(
            is_subscribed=Exists(Follow.objects.filter(
                author=user, user_id=OuterRef('pk'))
            ),
            recipes_count=Count(Recipe.objects.filter(author=user))
        )

class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчики'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Подписки'
    )

    objects = RecipeQuerySet.as_manager()

    class Meta:
        ordering = ('pk', )
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='follow_user_author_unique'
            ),
            models.CheckConstraint(
                check=models.Q(author=models.F('user')),
                name='follower_equal_following'
            ),
        ]



class ShoppingList(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='shop_list'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='author'
    )

    class Meta:
        verbose_name = 'Рецепт в корзине'
        verbose_name_plural = 'Рецепты в корзине'
        constraints = [
            models.UniqueConstraint(
                fields=['author', 'recipe'],
                name='shopping_author_recipe_unique'
            )
        ]

    def __str__(self):
        return f'{self.recipe} в избранном у {self.author}'


class FavorRecipes(models.Model):
    recipes = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Избранные рецепты',
        related_name='favorite_recipes',
        null=True
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='user_favorites',
        verbose_name='Пользователь'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                name='favorite_author_unique_recipes',
                fields=['author', 'recipes']
            )
        ]
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'


class RecipeComponent(models.Model):
    """
    Класс, описывающий Ингредиенты как часть рецепта
    """
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='recipe_ingredient',
        verbose_name='Ингредиенты'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='component_recipes',
        verbose_name='Рецепт'
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество',
        validators=[MinValueValidator(
            limit_value=1,
            message='Количество ингредиента не может быть меньше 1')]
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецепте'
        constraints = [
            models.UniqueConstraint(
                name='recipe_unique_component',
                fields=['ingredient', 'recipe']
            )
        ]

    def __str__(self):
        return self.ingredient.name
