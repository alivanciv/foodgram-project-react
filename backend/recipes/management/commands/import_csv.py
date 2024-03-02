import csv

from django.conf import settings
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from recipes.models import Ingredient
from api.serializers import IngredientSerializer

User = get_user_model()


class Command(BaseCommand):
    help = 'Импорт CSV data'

    def handle(self, *args, **options):
        self.import_simple_csv(
            'ingredients.csv',
            Ingredient,
            IngredientSerializer
        )
        print('Все файлы были успешно импрортированы.')

    def import_simple_csv(self, filename, model, serializer=None):
        csv_file = settings.CSV_FILES / filename

        with open(csv_file, 'r', encoding='utf-8') as f:
            fieldnames = [
                field.name for field in model._meta.get_fields()
                if not field.is_relation
            ]
            reader = csv.reader(f, delimiter=',')
            id = model.objects.all().count()
            data = {}
            for row in reader:
                id += 1
                data['id'] = id
                data['name'], data['measurement_unit'] = row
                model_instance = model()
                for attr in fieldnames:
                    setattr(model_instance, attr, data.get(attr))
                if serializer:
                    serializer_instance = serializer(data=data)
                    serializer_instance.is_valid(raise_exception=True)
                model_instance.save()
