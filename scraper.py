import time
import os
import datetime
import json
import textwrap
from collections import OrderedDict
import csv
import sys
import urllib
import threading
from flask import session
import logging
from thd_reviews import THDReviews
reviews_list = []
def urltest(product_link):
       brand='None'
       if "homedepot" in product_link:
              brand = 'HomeDepot'
       elif "amazon" in product_link:
              brand = 'Amazon'
       elif "lowes" in product_link:
              brand = 'Lowe\'s'
       else :
              brand='wrong'
       return brand
        
class ScraperThread(threading.Thread):

    def __init__(self, link):
        super(ScraperThread, self).__init__()
        self.link = link
        self.productname = None
        self.product_image_file_path = None
        self.product_info = {}
        self.scrap_success = False
        self.reviews= {}
    

    def save_image(self, image_content):
        folder_path = os.path.join(os.path.expanduser('~'), 'Pictures', 'thd_img')
        os.makedirs(folder_path, exist_ok=True)
        image_file_path = os.path.join(folder_path, self.productname + '.jpg')
        try:
            with open(image_file_path, "wb") as file:
                file.write(image_content)
            return image_file_path
        except Exception as e:
            self.logMessage.emit(f"Error saving image: {e}")
            return None

    def convert_to_percentage(self,data):

        try:
            # Check if data is a dictionary
            if not isinstance(data, dict):
                raise ValueError("Input must be a dictionary")

            for key, inner_dict in data.items():
                # print(f"\nkey: {key}\ninner_dict: {inner_dict}\ntype:{type(inner_dict)}\n\n")
                # Check if inner items are also dictionaries
                if not isinstance(inner_dict, dict):
                    continue

                # Calculate the total sum for each inner dictionary
                total = sum(inner_dict.values())

                # Handle the case where the total is 0
                if total == 0:
                    # Assign 0% to all items if the total is 0, as there's no basis for division
                    for inner_key in inner_dict:
                        inner_dict[inner_key] = 0
                    continue  # Move on to the next inner dictionary

                # Calculate percentage and update the inner dictionary
                for inner_key, value in inner_dict.items():
                    # Ensure the values are numeric
                    if not isinstance(value, (int, float)):
                        raise ValueError(f"All counts must be numeric, problem at {inner_key}")

                    # Calculate percentage and round it off
                    percentage = (value / total) * 100
                    inner_dict[inner_key] = round(percentage)  # round to nearest whole number

            return data

        except ValueError as e:
            # Handle specific error with a message
            print(f"ValueError: {e}")
        except Exception as e:
            # Catch all other errors
            print(f"An unexpected error occurred: {e}")

    def run(self):
        global reviews_list
        if "homedepot.com" in self.link:
            scraper = THDReviews()
            scraper.fetch_reviews(self.link)  # Connect signals
        # elif "amazon.com" in self.link:
        #     scraper = AMZ_Scrapper()
        # elif "lowes.com" in self.link:
        #     scraper = LowesScraper()
        #     scraper.fetch_reviews(self.link)  # Connect signals
        else:
            print("wrong")
        print("start scraping :" + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
        # ret_data = {
        #     "itemName": self.itemName,
        #     "img": self.image_content,
        #     "reviews": new_data
        # }
        reviews_list.clear()
        try:
            data = scraper.fetch_reviews(self.link)
            if not data:
                logging.info("no reviews")
                print("fail to get reviews, potential issue to access the web")
                self.scrap_success = False
                return
        except Exception as e:
            logging.info(f"Scraping failed: {e}")
            print(str(e))
            self.scrap_success = False
            return 
        
        self.productname = data['itemName']
        reviews_list = data['reviews']
        # self.product_info = data['product_info']
        if "homedepot.com" in self.link:
            product_info = self.convert_to_percentage(data['product_info'])
        elif "amazon.com" in self.link:
            product_info = data['product_info']
        elif "lowes.com" in self.link:
            product_info = self.convert_to_percentage(data['product_info'])
        self.product_info = product_info
        if 'img' in data and data['img']:
            self.product_image_file_path = self.save_image(data['img'])
            if self.product_image_file_path:
                print(f"Image saved at {self.product_image_file_path}")
        else:
            print("No image content available.")
        self.reviews=reviews_list
        print("finish scraping :" + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
        self.scrap_success = True