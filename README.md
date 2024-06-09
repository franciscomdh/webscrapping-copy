- [Congress scrapper](#congress-scrapper)
  - [Set up DOCKER](#set-up-docker)
  - [Commands DOCKER](#commands-docker)
    - [Build web container (first time)](#build-web-container-first-time)
    - [Make and apply migrations](#make-and-apply-migrations)
    - [Create super user](#create-super-user)
    - [Run the app](#run-the-app)
    - [Run linter](#run-linter)
  - [Scrapers](#scrapers)
    - [Scraper 10times](#scraper-10times)
    - [Scraper World Conference Alerts](#scraper-world-conference-alerts)
# Congress scrapper

## Set up DOCKER

- Make suren that docker and docker-compose are installed on your system
  
- Copy .envs/mysql-example.env to .envs/mysql.env and update the environment variables values
  
## Commands DOCKER

### Build web container (first time)

`docker-compose -f docker-compose.yml build`
### Make and apply migrations

`docker-compose -f docker-compose.yml run --rm web python manage.py makemigrations`

`docker-compose -f docker-compose.yml run --rm web python manage.py migrate`
### Create super user

`docker-compose -f docker-compose.yml run --rm web python manage.py createsuperuser`
### Run the app

`docker-compose up`
### Run linter

`bash lint.sh` (from the project root)

## Scrapers

This commands are to scrape [10times](https://10times.com) and [World Conference Alerts](https://www.worldconferencealerts.com/)

### Scraper 10times

`python3 manage.py scraper_10times`

### Scraper World Conference Alerts

`python3 manage.py scraper_wca_caller`

## Common errors

### Django can't connect to DB when raising the project for the first time

Comment out the prod credentials in the settings.py file and use the docker ones instead.

### Can create DB migrations, but not run them

- get into the db server running `docker compose exec db sh`
- get into mysql CLI mysql -u root -p
- check the character set with the command `SELECT default_character_set_name FROM information_schema.SCHEMATA S WHERE schema_name = "congressscrapper";`
- if it's latin1 (default), change it to utf8 running `ALTER DATABASE congressscrapper CHARACTER SET utf8 COLLATE utf8_general_ci;`

The migrations should run fine now.