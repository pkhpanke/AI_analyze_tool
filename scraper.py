import time
import os
import datetime
import json
import textwrap
from collections import OrderedDict
import csv
import sys
import urllib

from flask import session
# import matplotlib.pyplot as plt
# from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

# # Local application/library specific imports
# from thd_reviews import THDReviews
# from remote_analysis import ReviewAnalysisClient
# from amz_scrapper import AMZ_Scrapper
# from lowes_scrapper import LowesScraper
import logging

def urltest(product_link):
    brand='None'
    if "homedepot" in product_link:
            brand = 'HomeDepot'
    elif "amazon" in product_link:
           brand = 'Amazon'
    elif "lowes" in product_link:
           brand = 'Lowe\'s'
        

