#  cannot lint the whole project parent folder because of a known issue of pylint
#  https://github.com/PyCQA/pylint/issues/352
#  todo: fix when issue is solved
DJANGO_SETTINGS_MODULE=.congressscrapper.settings pylint --load-plugins pylint_django ./web
