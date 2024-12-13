import logging
from urllib.parse import urlencode
import requests
from parsel import Selector
import json
import re
from threading import Thread
from queue import Queue
import time
import random

from PIL import Image
import math
import datetime

from PySide6.QtCore import QObject, Signal, QThread
import asyncio
import aiohttp
import js2py

MAX_CONCURRENT_REQUESTS = 5  # Adjust this value based on your requirements

headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
 'Accept-Language': 'en-US,en;q=0.9',
 'Accept-Encoding': 'gzip, deflate, br'}

headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
    # "Cache-Control": "max-age=0",
    "Priority": "u=0, i",
    "Sec-Ch-Ua": "\"Not/A)Brand\";v=\"8\", \"Chromium\";v=\"126\", \"Microsoft Edge\";v=\"126\"",
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": "\"Windows\"",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0",
    # "Referer": "https://www.lowes.com/pd/allen-roth-Merington-3-Light-Nickel-Transitional-Vanity-Light-Bar/4774575"
    # "Referer": "https://www.lowes.com/pd/Frigidaire-25-6-cu-ft-Side-by-Side-Refrigerator-with-Ice-Maker-Easycare-Stainless-Steel-ENERGY-STAR/5013537917"
    # "Referer": "https://www.lowes.com/pd/DEWALT-20V-MAX-5-0AH-2-Pk-W-Charger/5014688329"
}


class LowesScraper(QObject):
    logSignal = Signal(str)
    def __init__(self):
        super(LowesScraper, self).__init__()
        self.ls_review = []
        self.main_image_binary = None
    
    # @staticmethod
    def log_error(self,message):
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.logSignal.emit(f"[ERROR] {timestamp}: {message}")
    
    # @staticmethod
    def log_debug(self,message):
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        logging.debug(message)
        self.logSignal.emit(f"[DEBUG] {timestamp}: {message}")

    async def get_ten_reviews(self, semaphore, prod_id, offset, max_retries=3):
        if offset == 0:
            url = f"https://www.lowes.com/rnr/r/get-by-product/{prod_id}"
        else:
            url = f"https://www.lowes.com/rnr/r/get-by-product/{prod_id}" + "?" + "offset=" + str(offset)
        async with semaphore:
            retries = 0
            while retries < max_retries:
                try:
                    async with aiohttp.ClientSession(trust_env=True) as session:
                        async with session.get(url, headers=headers) as resp:
                            if resp.status == 200:
                                resp_str = await resp.text(encoding="utf-8")
                                obj = json.loads(resp_str)
                                # print(obj)
                                # print("=" * 100)
                                self.log_debug(f"success to get reviews for page [{int(offset/10)}].")
                                return obj
                            elif resp.status == 403:
                                logging.error(f"Received status 403 for page [{int(offset/10)}]. Retrying after delay...")
                                self.log_error(f"Received status 403 for page [{int(offset/10)}]. Retrying after delay...")
                                delay = 2 ** retries + random.uniform(0, 1)  # Exponential backoff with jitter
                                await asyncio.sleep(delay)
                            else:
                                logging.error(f"Got status {resp.status} for page [{int(offset/10)}]. Retrying...")
                                self.log_error(f"Got status {resp.status} for page [{int(offset/10)}]. Retrying...")
                except Exception as e:
                    logging.error(f"Error for page [{int(offset/10)}]. error: [{e}]")
                    self.log_error(e)
                retries += 1
                await asyncio.sleep(2 ** retries + random.uniform(0, 1))
            
        return None
    
    def get_prod_name(self, url:str):
        # the "/" before product name
        pos = -1
        for i in range(0, 4): 
            pos = url.find("/", pos + 1)
        if pos == -1:
            raise Exception("Cannot get product name.")
        # the "/" behind product name
        pos_post = -1
        pos_post = url.find("/", pos + 1)
        if pos_post == -1:
            raise Exception("Cannot get product name.")
        return url[pos+1:pos_post]
    
    def get_prod_id(self, url:str):
        pos = -1
        for i in range(0, 5): 
            pos = url.find("/", pos + 1)
        if pos == -1:
            raise Exception("Cannot get product id.")
        return url[pos+1:]

    async def get_review_statistics(self, prod_id):
        """
        Returns:
            - A dict
        The dict follow the following structure 
        {
            "averageOverallRating": ...,
            "RecommendCount": {
                "Yes": ...,
                "No": ...
            },
            "count_rating": ...,
            "tot_review_cnt": ...
        }
        """
        obj = await self.get_ten_reviews(asyncio.Semaphore(MAX_CONCURRENT_REQUESTS), prod_id, offset=0)
        if obj is None:
            self.log_error("failed to get review statistics.")
            return None
        ret = {}
        try:
            statistics = obj["reviewStatistics"]
            avg_rating = statistics["averageOverallRating"]
            not_recommend_cnt = statistics["notRecommendedCount"]
            recommend_cnt = statistics["recommendedCount"]
            tot_review_cnt = statistics["totalReviewCount"]
            count_rating = {}
            for entry in statistics["ratingDistribution"]:
                rating = entry["ratingValue"]
                review_cnt = entry["reviewCount"]
                count_rating[rating] = review_cnt
            ret["averageOverallRating"] = avg_rating
            ret["RecommendCount"] = {
                "Yes": recommend_cnt,
                "No": not_recommend_cnt
            }
            ret["count_rating"] = count_rating
            ret["tot_review_cnt"] = tot_review_cnt
            return ret
        except Exception as e:
            logging.error(e)
            self.log_error(e)
            return None
    
    async def get_reviews(self, prod_id, tot_review_cnt):
        pages = math.ceil(tot_review_cnt / 10)
        self.log_debug(f"found [{pages}] pages")
        semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
        tasks = []
        for i in range(pages):
            t = asyncio.create_task(self.get_ten_reviews(semaphore, prod_id, i*10))
            tasks.append(t)
            # Introduce a random delay after every batch of MAX_CONCURRENT_REQUESTS
            if (i + 1) % MAX_CONCURRENT_REQUESTS == 0:
                await asyncio.gather(*tasks[-MAX_CONCURRENT_REQUESTS:])
                random_delay = random.uniform(1.0, 3.0)  # Random delay between 1.0 and 5.0 seconds
                await asyncio.sleep(random_delay)
        done, pending = await asyncio.wait(tasks)
        for r in done:
            obj = r.result()
            results = obj["results"]
            for res in results:
                review_info = {}
                review_info["Date"] = res["submissionTime"][:19]
                review_info["Stars"] = res["rating"]
                review_info["Title"] = res["title"]
                review_info["Content"] = res["reviewText"]
                review_info["Reviewer"] = res["userNickname"]
                self.ls_review.append(review_info)
    
    def get_pic(self, url):
        sec = "https://www.lowes.com/_sec/verify?provider=interstitial"
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            # "Cache-Control": "max-age=0",
            "Priority": "u=0, i",
            "Sec-Ch-Ua": "\"Not/A)Brand\";v=\"8\", \"Chromium\";v=\"126\", \"Microsoft Edge\";v=\"126\"",
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": "\"Windows\"",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0",
            # "Referer": "https://www.lowes.com/pd/Frigidaire-25-6-cu-ft-Side-by-Side-Refrigerator-with-Ice-Maker-Easycare-Stainless-Steel-ENERGY-STAR/5013537917"
            # "Referer": "https://www.lowes.com/pd/DEWALT-20V-MAX-5-0AH-2-Pk-W-Charger/5014688329"
        }

        with requests.session() as sess:
            max_retries = 3
            retries = 0
            while retries < max_retries:
                try:
                    r = sess.get(url, headers=headers, timeout=2)
                    if r.status_code == 200:
                        break
                except Exception as e:
                    logging.error(e)
                    self.log_error(e)

                retries += 1
            if retries == max_retries:
                return None

            sel = Selector(text=r.content.decode())

            s1 = sel.xpath("/html/head/script[1]/text()").get()
            s4 = sel.xpath("/html/body/script/text()").get()

            context = js2py.EvalJs()

            context.execute(s1)
            j = context.j

            payload = {
            'bm-verify': re.search('"bm-verify"\s*:\s*"([^"]+)', s4)[1],
            'pow': j
            }
            # header for post
            headers1 = {
                    # "Access-Control-Allow-Credentials": "true",
                    "Accept": "*/*",
                    "Accept-Encoding": "gzip, deflate, br, zstd",
                    "Accept-Language": "zh-CN,zh;q=0.9",
                    "Content-Length": "373",
                    "Content-Type": "application/json",
                    "Origin": "https://www.lowes.com",
                    "Priority": "u=0, i",
                    "Referer": url,
                    "Sec-Ch-Ua": "\"Not/A)Brand\";v=\"8\", \"Chromium\";v=\"126\", \"Microsoft Edge\";v=\"126\"",
                    "Sec-Ch-Ua-Mobile": "?0",
                    "Sec-Ch-Ua-Platform": "\"Windows\"",
                    "Sec-Fetch-Dest": "empty",
                    "Sec-Fetch-Mode": "cors",
                    "Sec-Fetch-Site": "same-origin",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0",
                }

            retries = 0
            while retries < max_retries:
                try:
                    rr = sess.post(sec, data=json.dumps(payload), headers=headers1)
                    if rr.status_code == 200:
                        break
                except Exception as e:
                    logging.error(e)
                    self.log_error(e)

                retries += 1
            if retries == max_retries:
                return None

            headers2 = {
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                    "Accept-Encoding": "gzip, deflate, br, zstd",
                    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
                    # "Cache-Control": "max-age=0",
                    "Priority": "u=0, i",
                    "Referer": url,
                    "Sec-Ch-Ua": "\"Not/A)Brand\";v=\"8\", \"Chromium\";v=\"126\", \"Microsoft Edge\";v=\"126\"",
                    "Sec-Ch-Ua-Mobile": "?0",
                    "Sec-Ch-Ua-Platform": "\"Windows\"",
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Site": "same-origin",
                    "Upgrade-Insecure-Requests": "1",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0",
                    # "Referer": "https://www.lowes.com/pd/Frigidaire-25-6-cu-ft-Side-by-Side-Refrigerator-with-Ice-Maker-Easycare-Stainless-Steel-ENERGY-STAR/5013537917"
                    # "Referer": "https://www.lowes.com/pd/DEWALT-20V-MAX-5-0AH-2-Pk-W-Charger/5014688329"
                }
            retries = 0
            while retries < max_retries:
                try:
                    rrr = sess.get(url, headers=headers2)
                    if rrr.status_code == 200:
                        break
                except Exception as e:
                    logging.error(e)
                    self.log_error(e)

                retries += 1
            if retries == max_retries:
                return None

            sel = Selector(text=rrr.content.decode())

            src_portion = sel.xpath("/html/head/meta[@property='og:image']/@content").get()
            img_src = "https:"+ src_portion
            res = requests.get(img_src)
            self.main_image_binary = res.content   
                

    async def start_jobs(self, url):
        # get review statistics
        prod_name = self.get_prod_name(url)
        prod_id = self.get_prod_id(url)
        statistics = await self.get_review_statistics(prod_id)
        # get reviews
        if statistics is None:
            return
        await self.get_reviews(prod_id, tot_review_cnt=statistics["tot_review_cnt"])
        self.get_pic(url)

        self.ls_review.sort(key=lambda x: x["Date"],reverse=True)

        res = {
            "itemName": prod_name,
            "img": self.main_image_binary,
            "reviews": self.ls_review,
            "product_info": statistics
        }
        return res

    def fetch_reviews(self, url, ip_pool = False)->dict:
        """
        The main method to be called externally. Fetches reviews and product information for a given Amazon product URL.
        
        Parameters:
            - url (str): The URL of the Amazon product page from which to fetch reviews.
            - ip_pool (bool, optional): Indicates whether IP rotation should be used to prevent blocking. Defaults to True.

        Returns:
            - dict: A dictionary containing cleaned product name, product image URL,
                    a list of reviews (each a dict with details), and a product info dictionary.
        The returned dictionary has the following structure:
        {
            "itemName": "Cleaned product name",
            "img": "binary content for the product's main image",
            "reviews": [
                {
                    "Date": "Review submission date and time",
                    "Stars": "Review rating",
                    "Title": "Review title",
                    "Content": "Review text",
                    "Reviewer": "Username of the reviewer"
                },
                ...
            ],
            "product_info": {
                "additional": "Additional product information extracted from the page"
            }
        }
        """
        if ip_pool is True:
            logging.info("Lowes scraper with ip pool has not been implemented yet.")
            return None
        else:
            res = asyncio.run(self.start_jobs(url))
            return res



if __name__ == '__main__':
    scraper = LowesScraper()
    # https://www.lowes.com/pd/allen-roth-Merington-3-Light-Nickel-Transitional-Vanity-Light-Bar/4774575
    res = scraper.fetch_reviews("https://www.lowes.com/pd/allen-roth-Merington-3-Light-Nickel-Transitional-Vanity-Light-Bar/4774575",
                          ip_pool=False)
    # res = scraper.fetch_reviews("https://www.lowes.com/pd/KOHLER-Cimarron-White-WaterSense-Elongated-Comfort-Height-2-Piece-Toilet-12-in-Rough-In-Size-ADA-Compliant/5001954253",
    #                       ip_pool=False)
    print('finished')
