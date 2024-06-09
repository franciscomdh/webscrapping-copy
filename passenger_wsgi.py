import sys, os

INTERP = "/home/aibm/congress-scrapper/env/bin/python"
if sys.executable != INTERP: os.execl(INTERP, INTERP, *sys.argv)

from congressscrapper.wsgi import application