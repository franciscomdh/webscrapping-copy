""" Archivo inicial de scraper de 10times. 
Archivo encargado de llamar al scraper 10times especificamente.
"""
# Django
from django.core.management.base import BaseCommand

# Utilities
from web.management.commands.scraper_10times_info import start_scraper
# from web.management.commands.scraper_10times_links import scraper_links


class Command(BaseCommand):

    help = "collect jobs"

    def handle(self, *args, **options):
        # todo: remove hardcoded method and restore start_scraper()
        start_scraper()
        # scraper_links()
        self.stdout.write('job complete')
