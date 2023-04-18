import csv
import os

from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = (
        'This command helps you to fill CSV data into db. '
        'To perform CSV data migration type the following command: '
        '>>> python manage.py importcsv '
        '--filename "<filename>.csv" '
        '--model_name "<model_name>" '
        '--app_name "<app_name>"'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--filename',
            type=str,
            help='file name (with ".csv" extension)'
        )
        parser.add_argument(
            '--model_name',
            type=str,
            help='model name that is used with this ".csv" file'
        )
        parser.add_argument(
            '--app_name',
            type=str,
            help='django app name'
        )

    def get_csv_file(self, filename):
        file_path = os.path.join(
            settings.BASE_DIR,
            'data',
            filename
        )
        return file_path

    def handle(self, *args, **options):
        filename = options['filename']
        app_name = options['app_name']
        model_name = options['model_name']
        file_path = self.get_csv_file(filename)
        self.stdout.write(self.style.SUCCESS(f'Reading: {file_path}'))
        _model = apps.get_model(app_name, model_name)
        _model.objects.all().delete()
        try:
            with open(file_path, 'r', encoding='utf-8') as csv_file:
                reader = csv.reader(csv_file, delimiter=',')
                bulk_create_data = (
                    _model(name=row[0], measurement_unit=row[1])
                    for row in reader
                )
                if 'tags.csv' in filename:
                    bulk_create_data = (
                        _model(name=row[0], color=row[1], slug=row[2])
                        for row in reader
                    )
                _model.objects.bulk_create(bulk_create_data)
                line_count = _model.objects.count()
            self.stdout.write(
                self.style.SUCCESS(
                    f'{line_count} entries added to {model_name}'
                )
            )
        except FileNotFoundError:
            raise CommandError(f'File {file_path} does not exist')
