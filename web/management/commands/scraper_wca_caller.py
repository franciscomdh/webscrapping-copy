""" Archivo inicial de scraper de WCA. 
Archivo encargado de llamar al scraper WCA especificamente.
"""
from django.core.management.base import BaseCommand

from web.management.commands.scraper_wca import master_scrap


class Command(BaseCommand):

    help = "collect jobs"

    def handle(self, *args, **options):
        master_scrap()
        self.stdout.write('job complete')
