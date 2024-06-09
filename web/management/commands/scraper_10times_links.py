# coding=utf-8
""" Modulo que contiene funciones helpers para scrapear links

¿Como usarlo?

Importas el modulo:
-> from scraper_links import scraper_links

Llamas a la funcion para crear el diccionario
-> dict_all_events = scraper_links()

El diccionario de listas contiene lo siguiente:
- keys = Nombre del pais
- values = Listas que incluyen todos los eventos por pais.
- Formato del diccionario: dict_all_events =
      {'/nombre_pais': [link_evento_1, ..., link_evento_n]...}


Copy&Paste lo siguiente para usarlo directamente:

from scraper_links import scraper_links

dict_all_events = scraper_links()
"""
import logging
import traceback
from bs4 import BeautifulSoup
import re

from datetime import datetime
import time

from web.management.commands.custom_ip_request import get as custom_ip_get
from web.models import EventLink

# Get an instance of a logger
logger = logging.getLogger('django')

def get_response(url: str):
    """ Función para obtener respuesta de cualquier url.

    Parametros
    ----------
    url : str
      URL de donde quiero obtener respuesta

    Return
    ------
    response : request object
    """

    headers = {'X-Requested-With': 'XMLHttpRequest'}
    try:
        print('request GET - url: ', url)
        response = custom_ip_get(url, headers=headers)
        if not response.ok:  # .status_code == 200:
            print(f'Code: {response.status_code}, url: {url}')
        return response
    except ConnectionError as ce:
        print(f'Connection aborted.', ce)
    except Exception as e:
        print(f'Error en get_response al tratar de traer la respuesta.')
        print(f'Exception {e}')
        print(traceback.print_exc())
    finally:
        time.sleep(5)


def get_countries(url_whereare_countries: str):
    """ Funcion para traer a los paises

    Parametros
    ----------
    url_whereare_countries : str
      URL donde se encuentran los paises.
      url = https://10times.com/events/by-country

    Return
    ------
    countries : list
      Lista con url de todos los paises.
      Formato de dato str = "/nombre_pais"
    """
    try:
        page_countries = get_response(url_whereare_countries)
        soup_countries = BeautifulSoup(page_countries.text, "lxml")
        # table = soup_countries.find_all('table', class_="tb-list")
        table = soup_countries.find_all('table', id = 'event-list')
        tr_table = table[0].find_all('tr')

        countries = []

        for tr in tr_table:
            link = tr.get('data-link')
            if link is not None:
                countries.append(link)

            # note: was like the following, changed on 13-09-2021
            # td = tr.find('td')
            # if td is not None:
            #     a = td.find('a').attrs.get('href')
            #     countries.append(a)

        return countries
    except Exception as e:
        print(f'Error en la funcon get_countries, {e}')
        print(traceback.print_exc())


def get_soup_by_country(response):
    """ Funcion para parsear html con atributos especificos "tr".

    Parametro
    ---------
    response : request Object
      Recibo una respuesta (response, objeto requests).

    Return
    ------
    soup_tr_country : soup Object
     Objeto BeautifulSoup parseado con atributos tr.
    """
    try:
        soup = BeautifulSoup(response.text, 'lxml')
        # TODO: seems that this changed... check it
        # soup_tr_country = soup.find_all('tr', class_='box')
        soup_tr_country = soup.find_all('tr', class_='row')
        return soup_tr_country
    except AttributeError as ae:
        print(f'Error en la funcion get_soup_by_country, {ae}')
        print(traceback.print_exc())
    except Exception as e:
        print(f'Error en la funcion get_soup_by_country, {e}')
        print(traceback.print_exc())


def find_pattern(response):
    """ Funcion que busca en el enlace ajax
    si lo que se muestra son eventos pasados.

    - Tipo de enlace en el que busca =
      f"https://10times.com/ajax?for=scroll&path={country}&ajax=1&page={number_page}
    - El patron son palabras claves.

    Parametro
    ---------
    response : request Object
      Recibo una respuesta (response, objeto requests).

    Return
    ------
    pattern_found : bool
      Bandera que me indica si encontro el patron o no.
    """
    try:
        pattern_found = False

        soup = get_soup_by_country(response)

        # Buscando texto en atributos tr de objeto soup
        first_list = []
        for tr in soup:
            text = tr.text
            first_list.append(text)

        # Eliminando saltos de lineas para cada elemento de texto en la lista
        second_list = []
        for text in first_list:
            list_importants_word = text.splitlines()
            second_list.append(list_importants_word)

        # Eliminando elementos vacios para cada lista
        third_list = []
        for every_list in second_list:
            new_list = list(filter(None, every_list))
            third_list.append(new_list)

        # Convirtiendo cada lista nuevamente en un string
        # para buscar las palabras claves
        keywords = ['No', 'upcoming', 'past', 'events']
        for every_list in third_list:
            text = str(every_list).strip('[]')
            if all(word in text for word in keywords):
                pattern_found = True  # Si lo encontre
                break  # Salgo y me quedo con ese true
            else:
                pattern_found = False

        return pattern_found

    except Exception as e:
        print(f'Error en la funcion find_pattern, {e}')
        print(traceback.print_exc())


def get_number_events_by_country(country: str):
    """ Funcion que me permite obtener el numero de eventos por pais.

    Parametro
    ---------
    country: str
      Pais del cual quiero obtener el numero de eventos.
      Formato del str = "/nombre_pais".

    Return
    ------
    events_in_country : int
      Numero de eventos en el pais.
    """
    try:
        url = f'https://10times.com{country}'
        response = get_response(url)
        soup = BeautifulSoup(response.text, 'lxml')
        events_by_country = soup.find(
                                'div',
                                attrs={
                                  'class': 'by-country'
                                  })
        number_events = events_by_country.find_all(
                                          'small',
                                          attrs={
                                            # TODO: this changes frequently... got fixed?
                                            # 'class': 'text-muted pull-right'
                                            # 'class': 'text-muted float-end'
                                            'class': 'text-blue fw-500 ms-2'
                                            })

        events_in_country = int(number_events[0].text)
        return events_in_country
    except Exception as e:
        print(f'Error en la funcion get_number_events_by_country, {e}')
        print(traceback.print_exc())


def get_links_events_no_dates(country: str):
    """ Funcion para obtener los links de los eventos iniciales,
    no incluye url con fecha.

    Parametro
    ---------
    country: str
      Pais del cual quiero obtener los links de los eventos.
      Formato del str = "/nombre_pais".

    Return
    ------
    links_events : list
      Lista con links de eventos
    max_date : str
      La fecha futura mayor de los eventos. Formato del str = "%Y-%m-%d".
    """
    number_page = 1

    exit = True

    datas_end_date_list = []  # Lista para guardar fechas de los eventos
    links_events = []

    try:
        # Loop para recorrer todos los enlaces
        while exit is True:
            url = f"https://10times.com/ajax?for=scroll&path={country}&ajax=1&page={number_page}"
            print('extracting page ' + url)
            logger.warning('extracting page ' + url)

            response = get_response(url)

            soup = get_soup_by_country(response)

            data_content = {}

            if response.ok:
                # response.ok == (response.status_code == 200):

                for tr in soup:
                    is_past = len(tr.findAll(text=re.compile('some of the past events'))) > 0
                    if is_past:
                        exit = False
                        break
                    try:
                        # si esta fila es una fecha del feed de anuncios (no de la lista), la paso por alto
                        is_default_date = tr.find('div', class_="eventTime").attrs.get('data-date-format') == "default"
                        if not is_default_date:
                            continue
                    except Exception:
                        pass

                    # Extraigo links
                    try:
                        a = tr.find('a').attrs.get('href')
                        if a is not None and a not in links_events:
                            EventLink.objects.create(
                                scraped=False,
                                site="10times",
                                link=a
                            )
                            links_events.append(a)
                    except AttributeError as ae:
                        print(f'Link no capturado. {ae}')
                    except Exception as e:
                        print('Error en get_links_events_no_dates.')
                        print(f'Exception {e}')
                    # Extraigo fechas
                    try:
                        # data_content = dict(tr.find("span").attrs)
                        data_end_date = tr.find('div', class_="eventTime").attrs.get('data-start-date')
                        # Extraigo fecha de finalizacion de evento
                        # data_end_date = data_content['data-end-date']
                        datas_end_date_list.append(data_end_date)
                    except Exception as e:
                        print('No se puedo extraer la fecha de finalización del evento.'.encode('utf-8'))
                        print('En la función get_links_events_no_dates.'.encode('utf-8'))
                        # print(f'Exception {e}')

                number_page += 1
            else:
                exit = False

        # Obtengo la fecha futura mayor de los eventos
        max_date = max(
                      datas_end_date_list,
                      # old date format was '%Y-%m-%d'
                      key=lambda d: datetime.strptime(d, '%Y/%m/%d')
                    )

        return links_events, max_date

    except Exception as e:
        print(f'Error en la funcion get_link_events_no_date, {e}')


def get_links_events_by_dates(country: str, max_date: str, links_events: list):
    """ Funcion para obtener los links de los eventos a partir de una fecha.

    Parametro
    ---------
    country: str
      Pais del cual quiero obtener los links de los eventos.
      Formato del str = "/nombre_pais".
    max_date : str
      La fecha futura mayor de los eventos. Formato del str = "%Y-%m-%d".
    links_events : list
      Lista con links de eventos

    Return
    ------
    links_events : list
      Lista con links de eventos
    max_date : str
      La fecha futura mayor de los eventos. Formato del str = "%Y-%m-%d".
    """

    date_end = max_date
    number_page = 1
    pattern_found = False
    exit = True

    links_events = list(set(links_events))
    datas_start_date_list = []
    datas_end_date_list = []

    try:
        while exit is True:
            url_by_dates = f"https://10times.com/ajax?for=scroll&path={country}&ajax=1&page={number_page}&datefrom={date_end}"
            response = get_response(url_by_dates)
            print('extracting page ' + url_by_dates)
            logger.warning('extracting page ' + url_by_dates)

            soup = get_soup_by_country(response)

            data_content = {}

            if response.ok:
                # response.ok == (response.status_code == 200):

                for tr in soup:
                    is_past = len(tr.findAll(text=re.compile('some of the past events'))) > 0
                    if is_past:
                        exit = False
                        break
                    try:
                        # si esta fila es una fecha del feed de anuncios (no de la lista), la paso por alto
                        is_default_date = tr.find('div', class_="eventTime").attrs.get('data-date-format') == "default"
                        if not is_default_date:
                            continue
                    except Exception:
                        pass

                    # Extraigo links
                    try:
                        a = tr.find('a').attrs.get('href')
                        # save event link
                        if a is not None and a not in links_events:
                            EventLink.objects.create(
                                scraped=False,
                                site="10times",
                                link=a
                            )
                            links_events.append(a)
                    except AttributeError as ae:
                        print(f'Link no capturado. {ae}')
                        # print(traceback.print_exc())
                    except Exception as e:
                        print('Error en get_links_events_by_dates')
                        print(f'Exception {e}')
                        print(traceback.print_exc())
                    # Extraigo fechas
                    try:
                        # data_content = dict(tr.find("span").attrs)
                        # Extraigo fecha de finalizacion de evento
                        # data_end_date = data_content['data-end-date']
                        data_start_date = tr.find('div', class_="eventTime").attrs.get('data-start-date')
                        datas_start_date_list.append(data_start_date)
                        data_end_date = tr.find('div', class_="eventTime").attrs.get('data-end-date')
                        datas_end_date_list.append(data_end_date)
                    except Exception as e:
                        # print('------ tr -------')
                        # print(tr)
                        print('No se puedo extraer la fecha de finalización del evento.'.encode('utf-8'))
                        # print('Atributo "span" de extraccion de fecha.')
                        print('En la función get_links_events_by_dates.'.encode('utf-8'))
                        # print(f'Exception {e}')
                        # print(traceback.print_exc())

                number_page += 1
            else:
                exit = False

        # old date format was '%Y-%m-%d'
        max_start_date = max(datas_start_date_list, key=lambda d: datetime.strptime(d, '%Y/%m/%d'))
        max_end_date = max(datas_end_date_list, key=lambda d: datetime.strptime(d, '%Y/%m/%d'))

        return links_events, max_start_date, max_end_date

    except Exception as e:
        print(f'Error en la funcion get_links_events_by_dates, {e}')
        print(traceback.print_exc())


def scraper_links_by_country(country: str):
    """ Scraper de los links por cada pais.

    Parametro
    ---------
    country: str
      Pais del cual quiero scrapear los links de los eventos. Formato del str = "/nombre_pais".

    Return
    ------
    links_events : list
      Lista con links de eventos
    """
    links_events = []
    try:
        # todo: fix 10times scraper... it stops before scraping with dates
        links_events, max_start_date = get_links_events_no_dates(country)
        print('[START] Events before date ' + max_start_date + ': ' + str(len(links_events)))
        logger.warning('[START] Events before date ' + max_start_date + ': ' + str(len(links_events)))

        # taking number of events
        eventos_unicos = get_number_events_by_country(country)
        fin = 0
        fin_anterior = 0

        while fin <= eventos_unicos:
            links_events, new_max_start_date, max_end_date = get_links_events_by_dates(
                                        country,
                                        max_start_date,
                                        links_events)
            fin = len(links_events)
            print('Events after date ' + max_start_date + ': ' + str(len(links_events)))
            logger.warning('Events after date ' + max_start_date + ': ' + str(len(links_events)))
            if new_max_start_date == max_start_date:
                # if last max start date is equal to the new one,
                # start from end date: to avoid repeating events and prevent early exit
                max_start_date = max_end_date
                # todo: improve "fin" related variables names and implementation
            else:
                max_start_date = new_max_start_date
            if fin == fin_anterior:  # Salida del scraper si se vuelve infinito
                print('Finishing country scraping to avoid infinite loop...')
                logger.warning('Finishing country scraping to avoid infinite loop...')
                # todo: possible fail... what if this date fills the whole page?
                break
            fin_anterior = fin

    except Exception as e:
        logger.error(f'Error en la funcion scraper_links_by_country, {e}')
        logger.error(traceback.print_exc())

    return links_events


def scraper_links():
    """ Funcion para scrapear los links de todos los eventos por pais.

    - No recibe ningun argumento

    Return
    ------
    dict_all_events : dictionary
      Diccionario de listas.
      - keys = Nombre del pais
      - values = Listas que incluyen todos los eventos por pais.
      - Formato del diccionario: dict_all_events =
          {'/nombre_pais': [link_evento_1, ..., link_evento_n]...}
    """
    url_countries = "https://10times.com/events/by-country"
    dict_all_events = {}

    # Remove all event links from DB
    EventLink.objects.filter(site="10times").delete()

    count = 0  # Variable es para limitar la paises que scrapeamos
    try:
        countries = EventLink.objects.filter(site="10times_country")
        if len(countries) == 0:
            countries_links = get_countries(url_countries)
            for country_link in countries_links:
                EventLink.objects.create(
                    scraped=False,
                    site="10times_country",
                    link=country_link
                )
            countries = EventLink.objects.filter(site="10times_country")
        for country_data in countries:
            # if count >= 100 and count < 102:
            # print('count is greater that 100 and less than 102')
            print(country_data.link)
            time.sleep(1)
            # Obteniendo cantidad de eventos por pais.
            list_events = scraper_links_by_country(country_data.link)
            dict_all_events[country_data.link] = list_events
            # save all event links to DB
            # events were saved here... uncomment block to do it again
            # for event_link in list_events:
            #     # save event link
            #     EventLink.objects.create(
            #         scraped=False,
            #         site="10times",
            #         link=event_link
            #     )

            # indent unitl here and uncomment if to limit countries
            count += 1
            EventLink.objects.filter(link=country_data.link, site="10times_country").delete()
    except Exception as e:
        print(f'Error en la funcion scraper_links, {e}')
        print(traceback.print_exc())

    return dict_all_events
