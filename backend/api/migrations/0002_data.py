import json

from django.db import migrations

def init_db(apps, schema_editor):
    """
    Creates Tag and Ingredient instances with given datasets
    """
    Ingredient = apps.get_model('api', 'Ingredient')
    Tag = apps.get_model('api', 'Tag')
    tags = [
        Tag(name='Завтрак', color='#FFB240', slug='breakfast'),
        Tag(name='Обед', color='#FF8040', slug='supper'),
        Tag(name='Ланч', color='#00AA72', slug='lunch'),
        Tag(name='Ужин', color='#4188D2', slug='dinner'),
    ]
    Tag.objects.bulk_create(tags)
    with open('./data/ingredients.json', encoding='utf-8') as f:
        json_data = json.load(f)
    for row in json_data:
        Ingredient.objects.create(
            name=row['title'],
            units=row['dimension']
        )


class Migration(migrations.Migration):
    """
    Load initial data
    """
    dependencies = [
        ('api', '0001_initial'),
    ]
    operations = [
        migrations.RunPython(init_db),
    ]
