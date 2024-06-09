"""Documentacion: Clase evento

Metodos relacionados a los códigos de las ciudades y paises

- codeCity():Metodo para asignarle el codigo de ciudad a un Evento
- codeCountry(): Método para asignarle el codigo de pais a un Evento

# Metodos relacionados a las imagenes

- check_url_image(): Chequear si el evento tiene imagen o no
- check_image(): Chequear si la imagen sirve o no
        Checkea las imagenes 10times.
        Si las imagenes son en blanco o no
- getting_standard_image(self): Metodo para traer imagen estandar dependiendo del pais
- write_image(path_image): Metodo para escrbir la imagen


# Funciones de ayudar que no se encuentran en la clase Evento:

- fill_country(boolean): Llena la base de datos de paises
- fill_cities(boolean): Llena la base de datos de ciudades

"""

# Librerias externas
import traceback
from enum import Enum
from io import BytesIO

from PIL import ImageFont, ImageDraw, Image
from web.models import Event, CityCode, CountryCode, Place
import numpy as np
import pandas as pd
from Levenshtein import distance
import pycountry
from urllib.request import urlopen
from tempfile import NamedTemporaryFile
import urllib.request

# Librerias internas
import os, random
import re
import logging

# Utilities
from web.management.commands.utilities import word_to_lowercase
from web.management.commands.utilities import find_string

# Get an instance of a logger
logger = logging.getLogger('django')

class Evento:
    """Clase evento """

    class CityMatchType(Enum):
        SMART = "smart"
        EXACT = "exact"

    def __init__(self, nombre, link_al_evento, fecha, fecha_final,
                 timing, sede, ciudad, pais, estado_del_evento,
                 tipo_del_evento, categorias, imagen_url, visitantes, expositores,
                 participantes, sitio_de_origen, sitio_web, image_mini_url,
                 is_online=False, country_code=None, latitude=None, longitude=None):
        """ Constructor clase Evento

        Atributos:
        ---------
        - name  # String
        - event_link  # String
        - date  # datetime
        - end_date  # datetime
        - timing  # String
        - place  # String
        - city  # String
        - country  # String
        - event_status  # String
        - event_type  # String
        - categories  # list -> String
        - image_url  # String
        - participants  # int
        - is_online  # bool
        - country_code  # String
        - latitude  # String
        - longitude  # string

        Metodos
        ---------
        - Codigos ciudades y paises
            - codeCity():Metodo para asignar el codigo de ciudad a un Evento
            - codeCountry(): Método para asignar el codigo del pais a un Evento
        - Imagenes
            - check_url_image(): Chequear si el evento tiene imagen o no
            - check_image(): Checkea las imagenes 10times. Si son blancas o no
            - getting_standard_image(self): Metodo para traer imagen estandar dependiendo del pais
            - write_image(path_font, path_image): Metodo para escrbir la imagen
        """
        self.nombre = nombre  # String
        self.link_al_evento = link_al_evento  # String
        self.fecha = fecha  # datetime
        self.fecha_final = fecha_final  # datetime
        self.timing = timing  # String
        self.sede = sede  # String
        self.ciudad = ciudad  # String
        if pais is not None:
            self.pais = pais.replace("of America", "") if pais not in ["USA", "EEUU"] else "United States"  # String
        else:
            self.pais = None
        self.estado_del_evento = estado_del_evento  # String
        self.tipo_del_evento = tipo_del_evento  # String
        self.categorias = categorias  # list -> String
        self.imagen_url = imagen_url  # String
        self.visitantes = visitantes  # String
        self.expositores = expositores  # String
        self.participantes = participantes  # int
        self.sitio_de_origen = sitio_de_origen  # String
        self.sitio_web = sitio_web  # String
        self.imagen_mini_url = image_mini_url  # String
        self.is_online = is_online
        self.country_code = country_code
        self.latitude = latitude
        self.longitude = longitude

    # Metodos relacionados a los códigos de las ciudades y paises

    def get_city_code(self):
        """ Metodo para asignarle el codigo de ciudad a un Evento"""
        if CityCode.objects.all().count() > 0:
            city_pag = self.ciudad
            code_country = self.get_country_code().countrycode if self.country_code is None else self.country_code
            print('--------------------')
            print('--- code_country ---')
            print('--------------------')
            print(code_country)
            # Obtengo el id del pais
            country_data = CountryCode.objects.filter(countrycode=code_country).first()

            # Get city using levenshtein
            # todo: use match type in required data (or save to DB and show it in admin)
            return get_city_smart(city_pag, country_data)

        else:
            logger.info('There are no cities, adding some, please wait')
            try:
                # todo: remove fill cities
                fill_cities(True)
            except Exception as e:
                logger.error(e)
                logger.error(traceback.print_exc())
            return Evento.get_city_code(self)

    def get_country_code(self):
        if self.country_code is not None:
            return CountryCode.objects.get(countrycode=self.country_code)
        try:
            """ Método para asignarle el codigo de pais a un Evento"""
            country_pag = self.pais
            print('-------------------')
            print('--- country_pag ---')
            print('-------------------')
            print(country_pag)

            # Comparo con los paises de la db
            countries_code = CountryCode.objects.all()
            if len(countries_code) != 0:
                return get_country_smart(country_pag)

            else:
                logger.info('There are no countries, adding some, please wait')
                try:
                    fill_country(True)
                except Exception as e:
                    logger.error(e)
                    logger.error(traceback.print_exc())
                return Evento.get_country_code(self)
        except Exception as e:
            logger.error(e)
            logger.error(traceback.print_exc())
            return None
  
    # Método para asignarle lat y long en base a place

    def lat_long(self):
        place = self.sede
        if place is not None:
            # todo: remove fill places (used for local developement)
            if Place.objects.all().count() == 0:
                fill_places(True)

            code_country = self.get_country_code().countrycode
            country_data = CountryCode.objects.filter(countrycode=code_country).first()
            # todo;: try to use event's matched city data instead of doing it again
            city_data, match_type = get_city_smart(self.ciudad, country_data)
            city_name = city_data.nombre if city_data is not None else self.ciudad
            place_data = Place.objects.filter(venue=place, nombreciudad=city_name).first()

            if place_data is not None:
                return place_data.latitud, place_data.longitud
            elif self.latitude is not None and self.longitude is not None:
                return self.latitude, self.longitude
            else:
                return None, None
        if self.latitude is not None and self.longitude is not None:
            return self.latitude, self.longitude
        else:
            return None, None

    # Metodos relacionados a las imagenes

    def check_url_image(self):
        """Chequear si el evento tiene imagen o no"""
        url_image = self.imagen_url
        if ((url_image == '') or (url_image is None) or (url_image == 'No image')):
            url_image_boolean = False
        else:
            url_image_boolean = True
        # Chequeo si tiene imagen mini    
        url_image_mini = self.imagen_mini_url
        if ((url_image_mini == '') or (url_image_mini is None) or (url_image_mini == 'No image')):
            url_image_mini_boolean = False
        else:
            url_image_mini_boolean = True

        return url_image_boolean, url_image_mini_boolean
    
    def check_image(self, url):
        """Chequear si la imagen sirve o no
        Checkea las imagenes 10times.
        Si las imagenes son en blanco o no"""
        image = url
        headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
        'Accept-Encoding': 'none',
        'Accept-Language': 'en-US,en;q=0.8',
        'Connection': 'keep-alive'}
        img_temp = NamedTemporaryFile(delete=True)
        request_ = urllib.request.Request(image,None,headers) #The assembled request
        response = urllib.request.urlopen(request_)# store the response
        # img_temp.write(urlopen(image).read())
        img_temp.write(response.read())
        img_temp.flush()
        img = Image.open(img_temp)
        data = np.asarray(img, dtype="int32")
        i = 0
        for pix in range(len(data.tolist())):
            if pix == 255:
                i = i + 1
        if i is len(data.tolist()):
            return False
        else:
            return True

    def getting_standard_image(self, image_type):
        """Metodo para traer imagen estandar dependiendo del pais"""
        if image_type == "cabecera":
            image_type_folder = 'photos_default'
        if image_type == "miniatura":
            image_type_folder = 'photos_default_mini'

        url_photos_default = f'media/{image_type_folder}'
        list_of_countries = os.listdir(url_photos_default)

        country = word_to_lowercase(self.pais)
        city = word_to_lowercase(self.ciudad)
        try:
            # Buscamos si el pais esta en la carpeta
            if country in list_of_countries:
                url_photos_in_country = f'{url_photos_default}/{country}'
                list_of_folder_in_country = os.listdir(url_photos_in_country)

                # Buscamos si la ciudad esta en la carpeta
                if city in list_of_folder_in_country:
                    url_photos_in_city = f'{url_photos_in_country}/{city}'
                    list_of_photos_in_city = os.listdir(url_photos_in_city)
                    random_photo_of_city = random.choice(list_of_photos_in_city)
                    url_random_photo_of_city = f'{url_photos_in_city}/{random_photo_of_city}'
                    return url_random_photo_of_city

                # Si no esta la ciudad seleccionamos la default por pais
                else:
                    url_photos_in_country_default = f'{url_photos_in_country}/{country}_default'
                    list_of_photos_in_city = os.listdir(url_photos_in_country_default)
                    random_photo_of_country_default = random.choice(list_of_photos_in_city)
                    url_random_photo_of_country_default = f'{url_photos_in_country_default}/{random_photo_of_country_default}'
                    return url_random_photo_of_country_default

            # Si no esta el pais seleccionamos la default general
            else:
                url_default = f'{url_photos_default}/default'
                list_of_photos_default = os.listdir(url_default)
                random_photo_default = random.choice(list_of_photos_default)
                url_random_photo_default = f'{url_default}/{random_photo_default}'
                return url_random_photo_default
        except Exception as e:
            logger.error(f'Error en getting_standard_image: {e}')
            logger.error(traceback.print_exc())

    def write_image_cabecera(self, path_image, event_aux, has_img_url_mini=None):
        try:
            event_pk = event_aux.pk
            """Metodo para escrbir la imagen de cabecera"""
            # imagen y fuente
            path_font = 'media/ArialBold.ttf'
            imagen = Image.open(path_image)

            # Datos del evento que se escribirán sobre la imagen.
            event_name = self.nombre
            event_date = self.fecha
            event_end_date = self.fecha_final
            event_city = self.ciudad
            event_country = self.pais
            event_category = self.categorias

            draw = ImageDraw.Draw(imagen)
            color = 'rgb(255, 255, 255)'  # white color

            # Event avatar
            # use avatar instead of first letter (if available)
            if has_img_url_mini and self.check_image(self.imagen_mini_url):
                logo = event_aux.get_remote_image_mini()
                logo_pil_image = Image.open(BytesIO(logo))
                logo_size = (182, 184)  # originally, 180 x 180, but we need to hide a small halo over the blue sqare
                logo_position = (169, 28)  # originally, 170 x 30, but we need to hide a small halo over the blue sqare
                logo_pil_image.thumbnail(logo_size, Image.ANTIALIAS)
                imagen.paste(logo_pil_image, logo_position)
            else:
                # Busco en el nombre del evento todos las palabras unicamente
                list_strings = re.findall("[a-zA-Z_]+", event_name)
                first_word = list_strings[0]
                avatar = first_word[0]

                (x, y) = (225, 65)  # El (x, y) = (0, 0) es el punto izquierdo superior
                font = ImageFont.truetype(font=path_font, size=80) # 80 pt ---> 106,6666 px
                draw.text((x, y), text=avatar, fill=color, font=font)

            # Event name
            font = ImageFont.truetype(font=path_font, size=29)
            if len(event_name) > 60:  # Si la cantidad de char supera 60
                list_place_of_space = find_string(event_name, ' ')
                # Busco el lugar del char espacio donde corto la frase.
                try:
                    number_place_of_space = min(list_place_of_space,
                                                key=lambda x: abs(x-55))
                except Exception as e:
                    number_place_of_space = 0

                event_name_part_1 = event_name[:number_place_of_space]
                event_name_part_2 = event_name[number_place_of_space+1:]

                (x1, y1) = (354, 30)
                (x2, y2) = (354, 30+40)

                draw.text((x1, y1), text=event_name_part_1, fill=color, font=font)
                draw.text((x2, y2), text=event_name_part_2, fill=color, font=font)

            else:
                (x, y) = (354, 30)
                draw.text((x, y), text=event_name, fill=color, font=font)

            # event_date, event_end_date
            if event_date is not None and event_end_date is not None:
                event_date = event_date.date().strftime("%Y-%m-%d")
                event_end_date = event_end_date.date().strftime("%Y-%m-%d")
                date = f'From {event_date} to {event_end_date}'
                font = ImageFont.truetype(font=path_font, size=20)
                (x, y) = (400, 124)
                draw.text((x, y), text=date, fill=color, font=font)
            elif event_date is not None:
                event_date = event_date.date().strftime("%Y-%m-%d")
                date = f'From {event_date}'
                font = ImageFont.truetype(font=path_font, size=20)
                (x, y) = (400, 124)
                draw.text((x, y), text=date, fill=color, font=font)

            # event_city, event_country
            place = f'{event_city}, {event_country}'
            font = ImageFont.truetype(font=path_font, size=20)
            (x, y) = (400, 165)
            draw.text((x, y), text=place, fill=color, font=font)

            # event_category
            font = ImageFont.truetype(font=path_font, size=14)
            (x, y) = (169, 302)
            categories = ' '
            categories = categories.join(event_category)

            if len(categories) > 70:  # Si la cantidad de char supera 60
                list_place_of_space = find_string(categories, ' ')
                # Busco el lugar del char espacio donde corto la frase.
                try:
                    number_place_of_space = min(list_place_of_space,
                                                key=lambda x: abs(x-70))
                except Exception as e:
                    number_place_of_space = 0
                categories_part_1 = categories[:number_place_of_space]
                categories_part_2 = categories[number_place_of_space+1:]

                (x1, y1) = (169, 302)
                (x2, y2) = (169, 302+16)

                draw.text((x1, y1), text=categories_part_1, fill=color, font=font)
                draw.text((x2, y2), text=categories_part_2, fill=color, font=font)

            else:
                (x, y) = (169, 302)
                draw.text((x, y), text=categories, fill=color, font=font)

            path_image_modified = f'media/photos_events'
            # image_name = f'{event_name[0:10]}-{event_date}-cabecera.jpg'
            # image_name = f'{event_name.replace("/", "-")}-{event_date.replace("/", "-")}-cabecera.jpg'
            # path_image_to_save = f'{path_image_modified}/{image_name}'
            path_image_to_save = f'{path_image_modified}/imagen-{event_pk}-cabecera.jpg'

            return path_image_to_save, imagen.save(path_image_to_save, 'jpeg')
        except Exception as e:
            logger.error('Error escribiendo la imagen de cabecera.')
            logger.error(e)
            logger.error(traceback.print_exc())
            raise e

    def write_image_miniatura(self, path_image, event_pk):
        """Metodo para escrbir la imagen miniatura"""
        # imagen y fuente
        path_font = 'media/ArialBold.ttf'
        imagen = Image.open(path_image)

        # Datos del evento que se escribirán sobre la imagen.
        event_name = self.nombre
        event_date = self.fecha
        event_end_date = self.fecha_final
        event_city = self.ciudad
        event_country = self.pais
        event_category = self.categorias

        draw = ImageDraw.Draw(imagen)
        color = 'rgb(255, 255, 255)'  # white color

        # Event avatar
        # Busco en el nombre del evento todos las palabras unicamente
        list_strings = re.findall("[a-zA-Z_]+", event_name)
        first_word = list_strings[0]
        avatar = first_word[0]

        (x, y) = (37, 29)  # El (x, y) = (0, 0) es el punto izquierdo superior
        font = ImageFont.truetype(font=path_font, size=45)
        draw.text((x, y), text=avatar, fill=color, font=font)

        # Event name
        font = ImageFont.truetype(font=path_font, size=13)
        if len(event_name) > 50:  # Si la cantidad de char supera 60
            list_place_of_space = find_string(event_name, ' ')
            # Busco el lugar del char espacio donde corto la frase.
            try:
                number_place_of_space = min(list_place_of_space,
                                            key=lambda x: abs(x-50))
            except Exception as e:
                number_place_of_space = 0

            event_name_part_1 = event_name[:number_place_of_space]
            event_name_part_2 = event_name[number_place_of_space+1:]

            (x1, y1) = (12, 99)
            (x2, y2) = (12, 99+15)

            draw.text((x1, y1), text=event_name_part_1, fill=color, font=font)
            draw.text((x2, y2), text=event_name_part_2, fill=color, font=font)

        else:
            (x, y) = (12, 99)
            draw.text((x, y), text=event_name, fill=color, font=font)

        # event_date, event_end_date
        if event_date is not None and event_end_date is not None:
            event_date = event_date.date().strftime("%Y-%m-%d")
            event_end_date = event_end_date.date().strftime("%Y-%m-%d")
            date = f'From {event_date} to {event_end_date}'
            font = ImageFont.truetype(font=path_font, size=10)
            (x, y) = (31, 135)
            draw.text((x, y), text=date, fill=color, font=font)
        elif event_date is not None:
            event_date = event_date.date().strftime("%Y-%m-%d")
            date = f'From {event_date}'
            font = ImageFont.truetype(font=path_font, size=10)
            (x, y) = (31, 135)
            draw.text((x, y), text=date, fill=color, font=font)

        # event_city, event_country
        place = f'{event_city}, {event_country}'
        font = ImageFont.truetype(font=path_font, size=10)
        (x, y) = (31, 152)
        draw.text((x, y), text=place, fill=color, font=font)

        # event_category
        font = ImageFont.truetype(font=path_font, size=8)
        (x, y) = (12, 172)
        categories = ' '
        categories = categories.join(event_category)

        if len(categories) > 70:  # Si la cantidad de char supera 60
            list_place_of_space = find_string(categories, ' ')
            # Busco el lugar del char espacio donde corto la frase.
            try:
                number_place_of_space = min(list_place_of_space,
                                            key=lambda x: abs(x-70))
            except Exception as e:
                number_place_of_space = 0
            categories_part_1 = categories[:number_place_of_space]
            categories_part_2 = categories[number_place_of_space+1:]

            (x1, y1) = (12, 172)
            (x2, y2) = (12, 172+8)

            draw.text((x1, y1), text=categories_part_1, fill=color, font=font)
            draw.text((x2, y2), text=categories_part_2, fill=color, font=font)

        else:
            (x, y) = (12, 172)
            draw.text((x, y), text=categories, fill=color, font=font)

        path_image_modified = f'media/photos_events'
        # image_name = f'{event_name[0:10]}-{event_date}-miniatura.jpg'
        # image_name = f'{event_name.replace("/", "-")}-{event_date.replace("/", "-")}-miniatura.jpg'
        # path_image_to_save = f'{path_image_modified}/{image_name}'
        path_image_to_save = f'{path_image_modified}/imagen-{event_pk}-miniatura.jpg'

        return path_image_to_save, imagen.save(path_image_to_save, 'jpeg')

# Fin clase Evento


def fill_country(boolean):
    """
    Llena la base de datos de paises
    """
    try:
        if boolean is True:
            df_country = pd.read_csv('media/ih_pais.csv',
                                     names=['id',
                                            'country',
                                            'code'])
            for row in df_country.values:
                country_db = CountryCode.objects.filter(idpais=row[0]).values_list()
                if len(country_db) == 0:
                    CountryCode.objects.create(
                        # id=row[0],
                        # country=row[1],
                        # code=row[2])
                        idpais=row[0],
                        nombre=row[1],
                        countrycode=row[2])
                else:
                    pass
        else:
            pass
    except Exception as e:
        logger.error(e)
        logger.error(traceback.print_exc())


def fill_cities(boolean):
    """
    Llena la base de datos de ciudades
    """
    try:
        if boolean is True:
            df_city = pd.read_csv('media/ih_ciudad.csv',
                                  names=['id',
                                         'id_region',
                                         'id_provincia',
                                         'city',
                                         'code',
                                         'id_pais'])

            for row in df_city.values:
                country_db = CityCode.objects.filter(idciudad=row[0]).values_list()
                if len(country_db) == 0:
                    country = CountryCode.objects.get(idpais=row[5])
                    city = CityCode.objects.create(
                        # id=row[0],
                        # city=row[3],
                        # code=row[4],
                        # id_pais=country,
                        # id_region=row[1],
                        # id_provincia=row[2]
                        idciudad=row[0],
                        nombre=row[3],
                        citycode=row[4],
                        idpais=f'{country.idpais}',
                        idregion=row[1],
                        idprovincia=row[2]
                    )
                else:
                    pass
        else:
            pass
    except Exception as e:
        logger.error(e)
        logger.error(traceback.print_exc())


def fill_places(boolean):
    """
    Llena la base de datos de paises
    """
    try:
        if boolean is True:
            df_places = pd.read_csv('media/venues.csv',
                                     names=['id',
                                            'nombreciudad',
                                            'venue',
                                            'lat',
                                            'long'])
            for row in df_places.values:                
                place = Place.objects.create(
                        # id=row[0],
                        # venue=row[1],
                        # lat=row[2],
                        # long=row[3])
                        idpais=row[0],
                        nombreciudad=row[1],
                        venue=row[2],
                        latitud=row[3],
                        longitud=row[4])
        else:
            pass
    except Exception as e:
        logger.error(e)
        logger.error(traceback.print_exc())


def get_city_smart(city_name, country_data):
    """
        If a match is found, returns a CityCode instance with an indicator of the matching type ("exact" or "smart").
        If no match is found, returns None and None.
    """
    same_code_countries = CountryCode.objects.filter(countrycode=country_data.countrycode)
    for country in same_code_countries:
        country_id = country.idpais
        cities = CityCode.objects.filter(nombre=city_name, idpais=f'{country_id}')
        city = cities.first()
        if city is not None:
            # NOTE: set match type to smart if more than 1 cities are found
            # (this solves an issue when receiving multiple cities with the same name in the same country)
            match_type = Evento.CityMatchType.EXACT if len(cities) == 1 else Evento.CityMatchType.SMART
            return city, match_type

        city = CityCode.objects.filter(nombre=f'{city_name} City', idpais=f'{country_id}').first()
        if city is not None:
            return city, Evento.CityMatchType.EXACT

        cities = CityCode.objects.filter(idpais=f'{country_id}')
        for city in cities:
            dif = distance(city.nombre, city_name)

            # NOTE: strict conditions, less sensitive and less prone to false positives (but still have)
            # if len(city_name) <= 10 and dif == 1:
            #     return city
            # elif ' ' not in city_name and len(city_name) > 10 and dif <= 2:
            #     return city
            # elif ' ' in city_name and len(city_name) > 7 and (
            #     max([len(name) for name in city_name.split(' ')]) > 4
            # ) and dif <= 3:
            #     # TODO: be careful with similar words that mean different things (ex: west, east)
            #     # city for names with " DF", " DC", "Saint Paul -> St Paul", etc.
            #     return city

            # NOTE: more sensitive conditions below (but prone to false positives)
            if len(city_name) <= 5 and dif == 1:
                return city, Evento.CityMatchType.SMART
            elif 5 < len(city_name) and dif <= 2:
                return city, Evento.CityMatchType.SMART
            elif ' ' in city_name and 8 <= len(city_name) and dif <= 3:
                return city, Evento.CityMatchType.SMART
            elif len(city_name) > 10 and dif <= 3:
                return city, Evento.CityMatchType.SMART

    return None, None


def get_country_smart(country_name):
    try:
        country_data = CountryCode.objects.get(nombre=country_name)
        return country_data
    except CountryCode.DoesNotExist:
        pass

    countries = CountryCode.objects.all()
    for country in countries:
        # print('=== country_name, country.nombre ===')
        # print(country_name, country.nombre)
        dif = distance(country_name, country.nombre)
        if len(country_name) <= 5 and dif == 1:
            return country
        elif len(country_name) <= 10 and dif <= 2:
            return country
        elif len(country_name) > 10 and dif <= 3:
            return country
    return None
