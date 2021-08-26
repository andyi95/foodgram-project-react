from django.core.cache import cache
from django.core.cache.backends import locmem
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from api.models import Ingredient, Recipe


@receiver(post_delete, sender=Recipe, dispatch_uid='recipe_deleted')
def obj_post_delete_handler(sender, **kwargs):
    cache.delete('recipe_objects')

@receiver(post_save, sender=Recipe, dispatch_uid='recipe_updated')
def obj_post_save_handler(sender, **kwargs):
    cache.delete('recipe_objects')

@receiver(post_save, sender=Ingredient, dispatch_uid='ingredient_updated')
def obj_post_save_handler(sender, **kwargs):
    cache.delete('ingredient_objects')