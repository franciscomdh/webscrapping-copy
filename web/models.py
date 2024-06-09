"""Web data models
In this file we'll create a class (o more than one)
to manage events in django admin
"""

# Django
import logging

from django.db import models
from django.core.files import File
from rest_framework import serializers

# Utilities
from taggit.managers import TaggableManager
from tempfile import NamedTemporaryFile
from urllib.request import urlopen
from PIL import Image
import matplotlib.image as mpimg
from numpy import asarray
import urllib.request


# Get an instance of a logger
logger = logging.getLogger('django')


# Create your models here.


class EventLink(models.Model):
    site = models.CharField(max_length=100, default=None, blank=True, null=True)  # "10times" or "wca"
    scraped = models.BooleanField(blank=True, default=False)
    link = models.URLField(max_length=2000, null=True, blank=True)
    saved_date = models.DateTimeField(null=True, blank=True, auto_now_add=True)


class CountryCode(models.Model):
    idpais = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100, default=None, blank=True, null=True)
    countrycode = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return u'%s (%s)' % (self.nombre, self.countrycode)

    class Meta:
        managed = False
        db_table = "ih_pais"


class CityCode(models.Model):
    idciudad = models.AutoField(primary_key=True)
    idregion = models.IntegerField(default=0)
    idprovincia = models.IntegerField()
    nombre = models.CharField(max_length=200)
    citycode = models.CharField(max_length=3, blank=True, null=True)
    idpais = models.CharField(max_length=10, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'ih_ciudad'

    def __str__(self):
        return u'%s (%s) - %s' % (self.nombre, self.citycode, self.idpais)

    class Meta:
        managed = False
        db_table = "ih_ciudad"


class Place(models.Model):
    id = models.BigAutoField(primary_key=True)
    nombrepais = models.CharField(max_length=30, blank=True, null=True)
    nombreciudad = models.CharField(max_length=450, blank=True, null=True)
    venue = models.CharField(max_length=600, blank=True, null=True)
    latitud = models.CharField(max_length=60, null=True, blank=True)
    longitud = models.CharField(max_length=60, null=True, blank=True)

    class Meta:
        managed = False
        db_table = "ih_venues"


class Event(models.Model):
    """Event Models. Clase que se comunica con la DB.
    Guarda los atributos scrapeados en una variable
    para posterior utilizacion.
    """
    # Variables generales
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=150)
    pais = models.CharField(max_length=30)
    ciudad = models.CharField(max_length=100)
    estado_del_evento = models.CharField(max_length=30, null=True)
    tipo_del_evento = models.CharField(max_length=20)
    categorias = TaggableManager()
    fecha = models.DateTimeField()
    link_al_evento = models.CharField(max_length=255)
    # To now from what page the event is coming
    sitio_de_origen = models.CharField(max_length=40)
    # Imagen de cabecera
    imagen = models.ImageField(max_length=2000,
                               null=True,
                               upload_to="media/photos_events")
    imagen_url = models.URLField(max_length=2000, null=True, blank=True)
    # Imagen miniatura
    imagen_mini = models.ImageField(max_length=2000,
                                    null=True,
                                    upload_to="media/photos_events")
    imagen_mini_url = models.URLField(max_length=2000, null=True, blank=True)

    estado = models.CharField(null=True, max_length=100, blank=True)

    # Códigos de ciudad y pais
    # country_code_st = models.CharField(max_length=2, null=True, blank=True)
    # city_code_st= models.CharField(max_length=3, null=True, blank=True)

    # Códigos de ciudad y país (Foreign Keys)
    codigo_de_pais = models.ForeignKey(CountryCode, on_delete=models.PROTECT, null=True, blank=True)
    codigo_de_ciudad = models.ForeignKey(CityCode, on_delete=models.PROTECT, null=True, blank=True)
    codigo_de_ciudad_confirmado = models.BooleanField(blank=True, default=False)

    # Variables de world conference alerts
    fecha_final = models.DateTimeField(null=True, blank=True)

    # Variables de 10times
    sede = models.CharField(max_length=500, null=True, blank=True)
    timing = models.CharField(max_length=500, null=True, blank=True)
    visitantes = models.CharField(max_length=100, null=True, blank=True)
    expositores = models.CharField(max_length=100, null=True, blank=True)
    participantes = models.IntegerField(null=True, blank=True)

    # Variables para saber si fue enviado o modificado
    modificado = models.BooleanField(blank=True, default=False)
    enviado = models.BooleanField(blank=True, default=False)

    # Variable de lat y long en base a "place"
    latitud = models.FloatField(null=True, blank=True)
    longitud = models.FloatField(null=True, blank=True)

    # Atributo para guardar el website del evento
    sitio_web = models.URLField(max_length=2000, blank=True, null=True)

    # Add missing data (for filtering purposes)
    datos_requeridos_completos = models.BooleanField(default=True)

    #id de reservas en congreso
    id_api = models.IntegerField(blank=True, null=True)

    def add_remote_image(self):
        """Metodo para traer la imagen remota"""
        if self.imagen_url and not self.imagen:
            #img_temp = NamedTemporaryFile(delete=True)
            #img_temp.write(urlopen(self.image_url).read())
            #img_temp.flush()
            headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
            'Accept-Encoding': 'none',
            'Accept-Language': 'en-US,en;q=0.8',
            'Connection': 'keep-alive'}
            img_temp = NamedTemporaryFile(delete=True)
            request_ = urllib.request.Request(self.imagen_url, None, headers) #The assembled request
            response = urllib.request.urlopen(request_)# store the response
            img_temp.write(response.read())
            img_temp.flush()
            self.imagen.save(f"image_{self.pk}.jpg", File(img_temp))
            logger.info("Imagen descargada")
        # self.save()
        logger.info("Imagen guardada")

    def get_remote_image_mini(self):
        """Metodo para traer la imagen remota"""
        if self.imagen_mini_url and not self.imagen_mini:
            headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
            'Accept-Encoding': 'none',
            'Accept-Language': 'en-US,en;q=0.8',
            'Connection': 'keep-alive'}
            # img_temp = NamedTemporaryFile(delete=True)
            request_ = urllib.request.Request(self.imagen_mini_url, None, headers)  # The assembled request
            response = urllib.request.urlopen(request_)  # Store the response
            return response.read()
            # img_temp.write(response.read())
            # img_temp.flush()
            # return img_temp
            # self.imagen_mini.save(image_name if image_name is not None else f"image_mini_{self.pk}.jpg", File(img_temp))
            logger.info("Imagen mini descargada")
        # self.save()
        logger.info("Imagen mini guardada")
        return None

    def save_image(self, path):
        """Metodo para guardar la imagen de cabecera creada"""
        path = path.lstrip('media/')
        self.imagen = path
        self.save()
        logger.info('Imagen guardada')

    def save_image_mini(self, path):
        """Metodo para guardar la imagen miniatura creada"""
        path = path.lstrip('media/')
        self.imagen_mini = path
        self.save()
        logger.info('Imagen miniatura guardada')

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        logger.info(f'--- saving {self.id} ---')
        if self.sede is not None:
            # search place
            place = Place.objects.filter(venue=self.sede, nombreciudad=self.ciudad).first()
            if place is not None:
                # add lat and long to the event
                self.latitud = place.latitud
                self.longitud = place.longitud
        self.datos_requeridos_completos = \
            None not in [self.nombre, self.pais, self.ciudad, self.codigo_de_pais, self.codigo_de_ciudad] \
            and self.codigo_de_ciudad_confirmado is True
        if self.estado != 'New':
            self.estado = 'Changed'
        return super(Event, self).save(*args, **kwargs)


class CityCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CityCode
        fields = ('nombre','citycode')


class CountryCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CountryCode
        fields = ('nombre','countrycode')


class EventSerializer(serializers.ModelSerializer):
    country_code = CountryCodeSerializer(read_only=True)
    city_code = CityCodeSerializer(read_only=True)
    class Meta:
        model = Event
        fields = ('nombre','imagen','imagen_mini','imagen_url','imagen_mini_url','codigo_de_pais','codigo_de_ciudad','fecha','fecha_final','latitud','longitud')