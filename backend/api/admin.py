from django.contrib import admin
from django.db.models import Count
from django.urls import reverse
from django.utils.html import mark_safe
from django.utils.translation import gettext_lazy as _

from api.models import FavorRecipes, Follow, Ingredient, Recipe, Tag


class RecipeComponentAdmin(admin.TabularInline):
    model = Recipe.ingredients.through
    extra = 0
    min_num = 1  # From Django 1.7 :)


class RecipeAdmin(admin.ModelAdmin):
    inlines = (RecipeComponentAdmin,)
    list_display = ('pk', 'name', 'author_link', 'favorite_count', 'tag_list')
    list_display_links = ('pk', 'name', )
    search_fields = ('author', 'name')
    list_filter = ('tags', )

    def author_link(self, obj):
        url = reverse('admin:users_user_change', args=[obj.author.id])
        return mark_safe('<a href="%s">%s</a>' % (url, obj.author.username))

    def favorite_count(self, obj):
        return obj.favorite_count

    def tag_list(self, obj):
        s = list(obj.tags.values('name'))
        return ', '.join(i["name"] for i in s)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.prefetch_related('tags', 'ingredients')
        queryset = queryset.prefetch_related('favorite_recipes').annotate(
            favorite_count=Count('favorite_recipes')
        )
        return queryset

    favorite_count.short_description = ('В избранном')


class TagAdmin(admin.ModelAdmin):
    list_display = ('name', )


class IngridientAdmin(admin.ModelAdmin):
    list_display = ('name', 'units')


class FollowAdmin(admin.ModelAdmin):
    list_display = ('author', 'user')


class FavorAdmin(admin.ModelAdmin):
    list_display = ('author', 'recipes')


admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Ingredient, IngridientAdmin)
admin.site.register(Follow, FollowAdmin)
admin.site.register(FavorRecipes, FavorAdmin)
