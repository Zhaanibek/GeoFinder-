import csv
from django.core.management.base import BaseCommand

from GemFace import settings

class Command(BaseCommand):
        def handle(self, *args, **kwargs):
            datafile = settings.BASE_DIR / 'dataset' / 'almatyBostandyk.csv'
            with open(datafile, mode='r') as csvfile:
                reader = csv.DictReader(csvfile)
            for row in reader:
            store_location = StoreLocation(
                name=row['name'],
                latitude=float(row['latitude']),
                longitude=float(row['longitude']),
                rating=float(row['rating']),
                density=float(row['density']) if row['density'] else None,
                avg_neighbor_rating=float(row['avg_neighbor_rating']) if row['avg_neighbor_rating'] else None,
                predicted_score=float(row['predicted_score']) if row['predicted_score'] else None,
            )
            store_location.save()

# Вызовите эту функцию с путем к вашему CSV файлу
import_csv_to_db('dataset/almatyBostandyk.csv')
