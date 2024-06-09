"""Scraper de la info de Word Conference Alert"""
# Librerias externas
import traceback

import requests
from bs4 import BeautifulSoup
from mechanize import Browser
import time
import datetime
import logging

# Get an instance of a logger
logger = logging.getLogger('django')

# Librerias internas
from web.models import Event, EventLink
from web.management.commands.evento import Evento, get_city_smart, get_country_smart
from web.management.commands.database_controller import all_registers_query
from web.management.commands.database_controller import check_existing_event
from web.models import CountryCode, CityCode

# ---------------------///////////////////////------------------------- #
# Extraigo la informacion desde el link propio del evento.     


def det_event(url):
    URL = url
    mech = Browser()
    mech.set_handle_robots(False)
    mech.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]
    page = mech.open(URL)
    html = page.read()
    soup = BeautifulSoup(html, 'lxml')

    # Busco la tabla donde salen los datos
    table = soup.find("table", border=0, class_='table')

    for row in table.findAll('img'):
        image = row.get('content')
        image_url = row.get('src')
    if image == 'conference.jpg':
        return True, ''
    else: 
        return False, image_url

def scrap_events(url):            
    URL = url
    mech = Browser()
    mech.set_handle_robots(False)
    mech.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]
    page = mech.open(URL)
    html = page.read()
    soup = BeautifulSoup(html, 'lxml')

    # Busco la tabla donde salen los datos
    table = soup.find("table", border=0, class_='table')    

    # Metodo para chequear si existen los eventos para no repetir
    existing_events = all_registers_query()

    # Scrapeo el nombre del evento
    for row in table.findAll('tr')[1:]:
        a = row.find('h1', {'itemprop': 'name'})
        if(a is not None):
            b = a.getText(strip=True)
            name = ''
            for l in b: 
                if l != '(':
                    name = name + l
                else:
                    break
    logger.info(f'Url event: {url}')

    # Determino si el evento es tipo a (con imagen) o b (sin imagen)
    class_event, image_url = det_event(url)

    if class_event is True:
        # Scrapeo la fecha de inicio
        start_date = 0
        for row in soup.select('div')[1:]:
            a = row.find('p', {'itemprop': 'startDate'})
            if(a is not None):
                start_date = a.get('content')
                start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
                break
        # Scrapeo la fecha de finalizacion
        end_date = 0
        for row in soup.select('div')[1:]:
            a = row.find('p', {'itemprop': 'endDate'})
            if(a is not None):
                end_date = a.get('content')
                end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')
                break
    else:
        start_date = 0
        for row in table.findAll('tr')[1:]:
            a = row.find('span', {'itemprop': 'startDate'})
            if(a is not None):
                start_date = a.get('content')
                start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
                break
        end_date = 0
        for row in table.findAll('tr')[1:]:
            a = row.findAll('span',{'class':'btn btn-default cnt_btn'})
            if a: #Chequeo si esta vacio
                end_date = (a[1]).getText(strip=True)
                end_date = end_date[0:2] + end_date[4:]
                end_date = datetime.datetime.strptime(end_date, '%d %b %Y')                      

    # Scrapeo la ciudad
    for row in table.findAll('tr')[1:]:
        venue_title = row.find('span', {'class': 'ev_mn'})
        if not venue_title or venue_title is None or venue_title.find("Venue") == -1:
            continue
        a = row.find('h2')
        if(a is not None):
            city = a
            city = city.getText(strip=True)
            place = None
            if len(city.split(',')) > 3:
                place = city.split(',')[0]
                city = city.split(',')[1]
                city = city.strip()
                place = place.strip()
                if place == city:
                    place = None 
                    city = city.split(',')[0]
                else:
                    pass
            elif len(city.split(',')) == 3:
                place = city.split(',')[1]
                city = city.split(',')[0]
                city = city.strip()
                place = place.strip()
                if place == city:
                    place = None 
                    city = city.split(',')[0]
                else:
                    pass
            else:
                city = city.split(',')[0]      
    # Scrapeo el pais
    country = ""
    for row in table.findAll('tr')[1:]:
        a = row.find('span', {'itemprop': 'country'})
        if a is not None:
            country = a.getText(strip=True)

    city_data_has_country_code = CountryCode.objects.filter(countrycode=city).count() > 0 or get_capitalyzed_initials(country) == city
    city_is_missing = CityCode.objects.filter(nombre=city).count() == 0
    place_has_city = city_is_missing and CityCode.objects.filter(nombre=place).count() > 0
    if city_is_missing and not place_has_city and city is not None and place is not None:
        country_db_data = get_country_smart(country)
        if country_db_data is not None:
            city_smart_with_city, _ = get_city_smart(city, country_db_data)
            city_smart_with_place, _ = get_city_smart(place, country_db_data)
            place_has_city = city_smart_with_city is None and city_smart_with_place is not None

    # if (city == country or city_data_has_country_code) and place is not None:
    if (city == country and city_is_missing) or city_data_has_country_code or place_has_city:
        city_backup = city
        city = place
        place = city_backup if city_backup is not None and city_backup.lower().find("online") else None
    
    # Scrapeo el tipo de evento
    for row in soup.select('div.panel-heading')[1:]:
        a = row.find('h5')
        if a is not None:
            event_type = a.getText()
            event_type = event_type.lstrip('Event Type - ')

    # Scrapeo el codigo del evento, este codigo se usa para no repetir
    for row in table.findAll('tr')[1:]:
        a = row.find('span', {'itemprop': 'Event-id'})
        if (a is not None):
            serial = a.get_text(strip=True)
            serial = serial.lstrip('Event Serial No.-')

    if (event_type == 'Virtual Event') or (event_type == 'Virtual') or (event_type == 'Online') or (event_type == 'Online Event'):
        city = ''
        place = ''
    
    # Scrapeo los topicos
    topic = []
    for row in table.findAll('tr')[1:]:
        a = row.find('span', {'class': 'ev_mn'})
        if(a is not None):
            b = a.findAll('a', {'target': '_blank'})
            for i in range(len(b)):
                topic1 = b[i].get_text(strip=True)
                topic.append(topic1)

    # Scrapeo el website
    for row in table.findAll('tr')[1:]:
        a = row.find('a', {'itemprop':'url'})
        if (a is not None):
            website = a.get('href')

    timing = None
    event_status = 'Available'
    # image_url = 'https://img.10times.com/event/cefe330eb249f35fb8d07af22ca6c96/1522294253697/1685.jpg?imgeng=/w_160/h_160/m_stretch/cmpr_30/f_jpg'
    # image_url = ''
    participants = None
    page = 'WCA'
    visitors = ""
    exhibitors = ""
    image_url_mini = ''

    # Creo una instancia de Evento y lo guardo
    event = Evento(name, url, start_date, end_date, timing, place, city,
                   country, event_status, event_type, topic, image_url, visitors, exhibitors,
                   participants, page, website, image_url_mini)

    # Método para chequear si existe el evento o no
    ## ------------------ Guardo en DB ----------------------------##
    check_existing_event(event, existing_events)
    return event

# ---------------------///////////////////////------------------------- #
# Scrapeo "horizontal" las paginas que contienen los links de los ss.


def scrap_links():
    # Remove all event links from DB
    EventLink.objects.filter(site="wca").delete()

    url = 'https://www.worldconferencealerts.com/conference-alerts.php'
    mech = Browser()
    mech.set_handle_robots(False)
    mech.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]
    page = mech.open(url)
    html = page.read()
    soup = BeautifulSoup(html, 'lxml')

            # Guardo la cantidad de paginas que contienen links
    cant = soup.select('a.page-link')
    link = cant[len(cant)-1].get('href')
    cant_pag = int(link.lstrip('?page='))
    # Hago un list para guardarlos y despues repasarlos uno por uno
    links = []
    # Guardo la primer pagina
    links.append(url)
    for i in range(cant_pag):
        # No guardo ni la 0 porque no existe, ni la primera porque ya se guardo
        # anteriormente
        if i == 0 or i == 1:
            a = ''
        else:
            links.append(url+'?page='+str(i))
    return links


# ---------------------///////////////////////------------------------- #
# Scrapeo "vertical" las paginas que contienen los links de los eventos.


def scrap_pages(link):
    print('Scrap pages')
    url = link
    mech = Browser()
    mech.set_handle_robots(False)
    mech.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]
    page = mech.open(url)
    html = page.read()
    soup = BeautifulSoup(html, 'lxml')

    link_event = soup.select('a.conflist')
    links = []
    for link in link_event:
        links.append(link.get('href'))

    return links

# ---------------------///////////////////////------------------------- #
# Metodo para recorrer todos los links de todos los eventos.


def master_scrap():
    if EventLink.objects.filter(site='wca').count() > 0:
        return scrap_events_from_db(10000)

    links_pages = scrap_links()
    links_events = []
    i = 0
    cant_pages = 0
    for link in links_pages:
        # Descomentar la siguiente línea e indentar para limitar los eventos scrapeados
        # if(cant_pages < 1):  # Esto debe sacarse para scrapear todos los eventos
        if(i < 6):
            try:
                links_events.append(scrap_pages(link))
            except Exception as e:
                print('Could not get events page from link ' + link)
                print(e)
            i = i + 1
            cant_pages = cant_pages + 1
        else:
            print('Pagina: ', link)
            time.sleep(5)
            i = 0
        # Descomentar la siguiente línea e indentar hasta aquí para limitar los eventos scrapeados
        # else:
        #     break

    for link in links_events:
        for i in link:
            # save event link
            EventLink.objects.create(
                scraped=False,
                site='wca',
                link=i
            )


def scrap_events_from_db(limit=0):
    #  TODO: split this method and create a parent method that calls both... then copy login from scraper_10times_info
    logger.info('Scrapping events...')
    all_links = EventLink.objects.filter(site="wca")
    logger.info(len(all_links))
    #  events = []
    i = 0
    t = 0
    try:
        for link_data in all_links:
            if i is not 0 and i >= limit:
                break

            if t < 7:
                try:
                    scrap_events(link_data.link)
                    #  events.append(scrap_events(link))
                except Exception as e:
                    logger.error(f'Exception scraping event {link_data.link}')
                    logger.error(e)
                finally:
                    EventLink.objects.filter(link=link_data.link).delete()

                t = t + 1
            else:
                time.sleep(6)
                t = 0

            i = i + 1

    except Exception as e:
        logger.error('Hay una excepcion al tratar de scrapear eventos en scarp_events_from_db')
        logger.error(e)
        logger.error(traceback.print_exc())
    #  Imprimo la cantidad de eventos que scrapee
    #  print('Events: ', len(events))

    return 'All events scrapped'


def get_capitalyzed_initials(country_name):
    name_list = country_name.split()

    initials = ""

    for name in name_list:  # go through each name
        initials += name[0].upper()  # append the initial

    return initials
