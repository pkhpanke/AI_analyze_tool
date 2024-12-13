
import logging
from urllib.parse import urlencode
import requests
from parsel import Selector
import json
import re
from threading import Thread
from queue import Queue

from PIL import Image
import math
import datetime

from PySide6.QtCore import QObject, Signal, QThread

# Setting up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

MAX_THREADS = 1
# qq
# API_KEY = '2f1e5a98-b97d-46d3-94eb-d22fb7ad029d'
# gmail
API_KEY = '53cb1231-0bab-425c-84ff-7fba116530b3'

def get_scrapeops_url(url, keep_headers=False):
    payload = {'api_key': API_KEY, 'url': url, 'keep_headers': keep_headers}
    proxy_url = 'https://proxy.scrapeops.io/v1/?' + urlencode(payload)
    return proxy_url


class ReviewSpiderThread(QThread):
    def __init__(self, ctrl_queue, asin, page, stars, retry_times=1, return_num_reviews=False):
        QThread.__init__(self)
        self.__ctrl_queue = ctrl_queue
        self.__asin = asin
        self.__page = page
        self.__stars = stars
        self.__return_num_reviews = return_num_reviews
        self.__retry_times = retry_times
        self.ret_review_ls = None
        self.ret_review_num = None

    def __request_retry(self, url, **kwargs):
        success_list = [200]
        for i in range(self.__retry_times):
            try:
                if i > 0:
                    logging.error(f'Retry {i+1} times')
                res = requests.post(get_scrapeops_url(url, True), **kwargs)
                if res.status_code in success_list:
                    ## Return response if successful
                    return res
            except requests.exceptions.ConnectionError as e:
                logging.error(e)
            except Exception as e:
                logging.error(e)
        logging.error('Retry times reach maximum.')
            
        return None

    def __get_one_review_page(self, return_num_reviews):
        """
        Returns:
            - If return_num_reviews is set to False, reviews information on one page is returned
            - When return_num_reviews is set to True, number of reviews filtered by certain conditions is also returned
        """
        post_data = {
            "sortBy": "recent",
            "reviewerType": "all_reviews",
            "formatType": "",
            "mediaType": "",
            "filterByStar": 5,
            "filterByAge": "",
            "pageNumber": 10,
            "filterByLanguage": "",
            "filterByKeyword": "",
            "shouldAppend": "undefined",
            "deviceType": "desktop",
            "canShowIntHeader": "undefined",
            "pageSize": 10,
            "asin": "",
            "scope": "reviewsAjax0"
        }
        # keywords to set
        post_data["pageNumber"] = self.__page,
        post_data["reftag"] = f"cm_cr_getr_d_paging_btm_next_{self.__page}",
        post_data["scope"] = f"reviewsAjax{self.__page}",
        post_data["asin"] = self.__asin
        post_data["filterByStar"] = self.__stars
        mapper = {1: "one_star", 2: "two_star", 3: 'three_star', 4: 'four_star', 5: 'five_star'}
        post_data["filterByStar"] = mapper[self.__stars]

        spiderurl=f'https://www.amazon.com/hz/reviews-render/ajax/reviews/get/ref=cm_cr_arp_d_paging_btm_next_{self.__page}'
        
        res = self.__request_retry(spiderurl, data=post_data)
        # try:
        #     res = requests.post(get_scrapeops_url(spiderurl, True),data=post_data)
        # except Exception as e:
        #     logging.info(e)
        #     return None
        try:
            if res is not None:
                res = res.content.decode('utf-8')
                contents = res.split('&&&')
                
                ret_ls = []
                ret_num = None

                for content in contents:
                    infos = content.split('","')
                    info = infos[-1].replace('"]','').replace('\\n','').replace('\\','')
                    # extract infomation
                    if 'data-hook="review"' in info:
                        sel = Selector(text=info)
                        data = {}
                        data['Reviewer'] = sel.xpath('//span[@class="a-profile-name"]/text()').extract_first() # username

                        stars_mapper = {'1.0 out of 5 stars': 1, '2.0 out of 5 stars': 2, '3.0 out of 5 stars': 3,
                                        '4.0 out of 5 stars': 4, '5.0 out of 5 stars': 5}
                        data['Stars'] = stars_mapper[sel.xpath('//span[@class="a-icon-alt"]/text()').extract_first()] # rating
                        long_date = sel.xpath('//span[@data-hook="review-date"]/text()').extract_first() # date
                        long_date = long_date.strip()
                        long_date_cpy = long_date
                        # find the position of third last space
                        pos_third = 0
                        for _ in range(3):
                            pos_tmp = long_date.rfind(' ')
                            acc = len(long_date) - pos_tmp  # the number of char
                            pos_third -= acc
                            long_date = long_date[:pos_tmp]
                        alpha_date = long_date_cpy[pos_third+1:]    # e.g. "June 7, 2018"
                        date_string = str(datetime.datetime.strptime(alpha_date, '%B %d, %Y').date())
                        data['Date'] = date_string
                        data['Title'] = sel.xpath('//a[@data-hook="review-title"]/span[2]/text()').extract_first() # title
                        data['Content'] = sel.xpath('//span[@data-hook="review-body"]/span/text()').extract_first() # details
                        # image = sel.xpath('div[@class="review-image-tile-section"]').extract_first()
                        # data['image'] = image if image else "not image" # picture
                        
                        ret_ls.append(data)

                    if return_num_reviews and 'data-hook="cr-filter-info-section"' in info:
                        # get the number of filtered reviews
                        sel = Selector(text=info)
                        txt = sel.xpath('//div/div[@data-hook="cr-filter-info-review-rating-count"]/text()').get()
                        txt = txt.replace(',', '')
                        ret_num = int(re.findall(r'\d+', txt)[1])
                        logging.info(f'Number of product {self.__asin}\'s {self.__stars} stars reviews: {ret_num}')
                    
                return ret_ls, ret_num
                
            else:
                logging.error(f'Post request for reviews failed! Response code: {res.status_code}')
                return None

        except Exception as e:
            logging.error(e)
            return None


    def run(self):
        try:
            ret_ls_num = self.__get_one_review_page(self.__return_num_reviews)
            if ret_ls_num is not None:
                self.ret_review_ls, self.ret_review_num = ret_ls_num      
                # self.__data_queue.put(ret_ls_num)   # submit the data    
        except Exception as e:
            logging.error(e)
        finally:
            logging.info(f'Task of {self.__stars} stars, page {self.__page} complete.')
            self.__ctrl_queue.get()
            self.__ctrl_queue.task_done()


class AMZ_Scrapper(QObject):
    def __init__(self):
        pass
    

    def __get_all_reviews(self, asin: str):
        """
        Returns:
            - A list of review infomation including Date, Stars, Title, Content, Reviewer
            - The number of filtered reviews 
        """
        ls_all_reviews = []
        ## First round: scrape 5 pages with different stars to get the number of reviews filtered by these 5 conditions
        control_queue = Queue(MAX_THREADS)
        self.thd_ls = []
        for stars in range(1, 6):
            # 1, 2, 3, 4, 5
            thd = ReviewSpiderThread(control_queue, asin, 1, stars, retry_times=3, return_num_reviews=True)
            # This element, used to fill the queue, will be poped by the spider thread
            control_queue.put(stars)
            thd.start()
            self.thd_ls.append(thd)
        
        # Receive data from spider threads
        control_queue.join()
        dic_review_num = { stars: 0 for stars in range(1, 6) }
        for idx, thd in enumerate(self.thd_ls, 1):
            # 1, 2, 3, 4, 5
            thd.wait()
            review_num = thd.ret_review_num
            review_ls = thd.ret_review_ls
            if review_num is not None:
                dic_review_num[idx] = review_num
            if review_ls is not None:
                ls_all_reviews.extend(review_ls)

        # Second round: scrape the remaining pages
        self.thd_ls = []
        for stars in range(1, 6):
            if stars not in dic_review_num:
                continue
            review_num =  dic_review_num[stars]
            num_pages =  math.ceil(review_num / 10)
            logging.info(f'Reviews with {stars} stars: {num_pages} pages')
            if num_pages > 1: 
                num_pages = min(num_pages, 10)
                for page in range(2, num_pages + 1):
                    thd = ReviewSpiderThread(control_queue, asin, page, stars, retry_times=3)
                    # This element, used to fill the queue, will be poped by the spider thread
                    control_queue.put(stars)
                    thd.start()
                    self.thd_ls.append(thd)
                    
        # Receive data from spider threads
        control_queue.join()
        for thd in self.thd_ls:
            thd.wait()
            review_ls = thd.ret_review_ls
            if review_ls is not None:
                ls_all_reviews.extend(review_ls)
        
        logging.info(f'All scraping tasks complete, number of reviews: {len(ls_all_reviews)}')
        return ls_all_reviews
            


    def __get_product_page_info(self, url):
        """
        Returns:
            - A dict like:
        {
            "itemName": "Cleaned product name",
            "img": "binary content for the product's main image",
            "feature_bullets": "A List of feature bullets(About this item)"
        }
        """
        logging.info('Start scraping product page')
        ## Get product page info
        url = url.split("?")[0]
        asin = url.split("/")[5]
        print(asin)
        success = False
        # Retry 3 times
        for i in range(3):
            logging.info(f'Try to get product page the {i+1} times...')
            try: 
                res = requests.get(get_scrapeops_url(url))  # Send URL To ScrapeOps Instead of Amazon  
            except Exception as e:
                logging.info(e)
                continue
            if res.status_code == 200:
                success = True
                break
            else:
                continue
        if success:
            logging.info(f'Get request for product page return 200')
            # Parse html elements
            sel = Selector(text=res.text)
            name = sel.css("#productTitle::text").get("").strip()       # Product name
            feature_bullets = [bullet.strip() for bullet in sel.css("#feature-bullets li ::text").getall()]     # About this item
            main_image_src = sel.css("#imgTagWrapperId img::attr(src)").get()   # Main image src
            res = requests.get(main_image_src)
            main_image_binary = res.content     # main image binary
            avg_rating = float(sel.css("i[data-hook=average-star-rating] ::text").get("").strip().split(" ")[0])    # average rating

            rating_pertcent = {}
            # #histogramTable tbody tr:nth-child(1) td:nth-child(3) a
            all_stars_from_5 = list(range(1, 6))
            all_stars_from_5.reverse()
            for row, stars in enumerate(all_stars_from_5, 1):
                # rating_pertcent[str(stars)] = sel.css(f"#histogramTable tbody tr:nth-child({row}) td:nth-child(3) ::text").get("")
                percent_str = sel.css(f"#histogramTable tr:nth-child({row}) ::text").getall()[1]
                percent = float(percent_str.replace("%", ""))
                rating_pertcent[str(stars)] = percent
            return {
                "itemName": name,
                "img": main_image_binary,
                "product_info": {
                    "feature_bullets": feature_bullets,
                    "averageOverallRating": avg_rating,
                    "count_rating": rating_pertcent,
                },
                "asin": asin
            }
        else:
            logging.info('Maximum retry limit has been reached')
            return None


    def fetch_reviews(self, url, ip_pool = True)->dict:
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
        if ip_pool:
            product_info = self.__get_product_page_info(url)
            if product_info is not None:
                ls_reviews = self.__get_all_reviews(product_info["asin"])
                product_info["reviews"] = ls_reviews
            return product_info
                
        else:
            logging.info('Please set ip_pool to True.')
            return None
                

       


if __name__ == '__main__':
    scrapper = AMZ_Scrapper()
    # https://www.amazon.com/MUSETEX-Pre-Installed-Support-Tempered-Computer/dp/B0CP7TNPG1/ref=sr_1_3?dib=eyJ2IjoiMSJ9.Yq8YmLzaaKlosoBJY4IxsGBuVEXpYBdJtEWIozJiY_5s_otco-C2_4ntn8Ifxc1orHv5pLCt6tFufjILT5jIUO5bZbjTTXf6NdSCTQGN2Z3Kgr3CoJ86bCxIL5zsRbJMeNn2E8AOUkAdwIxFB9qoAkAvctNPh8bGUb3c7XJAPT2j2AO8L1A6vM2MrSoKHoDjz_P4-yqBHBCeCXKB3wQzUBkNqg-5YoYreGH_qmFnC7k.hnHU0tXugnfSHvAHPAtfxa1ocuurZdYaE9-df6Rg-Qc&dib_tag=se&keywords=%E6%9C%BA%E7%AE%B1&qid=1713344804&sr=8-3
    # result = scrapper.fetch_reviews('https://www.amazon.com/MUSETEX-Pre-Installed-Support-Tempered-Computer/dp/B0CP7TNPG1/ref=sr_1_3?dib=eyJ2IjoiMSJ9.Yq8YmLzaaKlosoBJY4IxsGBuVEXpYBdJtEWIozJiY_5s_otco-C2_4ntn8Ifxc1orHv5pLCt6tFufjILT5jIUO5bZbjTTXf6NdSCTQGN2Z3Kgr3CoJ86bCxIL5zsRbJMeNn2E8AOUkAdwIxFB9qoAkAvctNPh8bGUb3c7XJAPT2j2AO8L1A6vM2MrSoKHoDjz_P4-yqBHBCeCXKB3wQzUBkNqg-5YoYreGH_qmFnC7k.hnHU0tXugnfSHvAHPAtfxa1ocuurZdYaE9-df6Rg-Qc&dib_tag=se&keywords=%E6%9C%BA%E7%AE%B1&qid=1713344804&sr=8-3')
    # https://www.amazon.com/Talking-Dad-Joke-Stocking-Stuffer/dp/B0CF4L3STL/ref=sxin_16_pa_sp_search_thematic_sspa?content-id=amzn1.sym.739a72f6-6e4d-4318-b008-5d7cb86f8006%3Aamzn1.sym.739a72f6-6e4d-4318-b008-5d7cb86f8006&crid=RG13GSGVN0KQ&cv_ct_cx=father%27s%2Bday%2Bgifts&dib=eyJ2IjoiMSJ9.Y-LmrLXWEUOtFsx5NAHVYbILw9wP3adc_2zcdeV_nTRTjo4QeYnRljndqSwW_SFRF8CuE0fxYLcQusb0E8fvBw.w8Te2XU54SuA-iLDfsfASMMhCfW2EVTKI5SO9_NTLgM&dib_tag=se&keywords=father%27s%2Bday%2Bgifts&pd_rd_i=B0CF4L3STL&pd_rd_r=2794f899-fb52-4b14-901c-e871d98d6846&pd_rd_w=WORfE&pd_rd_wg=bL2ZV&pf_rd_p=739a72f6-6e4d-4318-b008-5d7cb86f8006&pf_rd_r=ES2VA4Z6E8PC0MK9XYXE&qid=1718085015&sbo=RZvfv%2F%2FHxDF%2BO5021pAnSA%3D%3D&sprefix=%2Caps%2C567&sr=1-5-7efdef4d-9875-47e1-927f-8c2c1c47ed49-spons&sp_csd=d2lkZ2V0TmFtZT1zcF9zZWFyY2hfdGhlbWF0aWM&th=1
    # https://www.amazon.com/Apple-iPhone-XR-Fully-Unlocked/dp/B07P6Y7954/ref=sr_1_1?keywords=iphone+xr&qid=1566312515&s=gateway&sr=8-1
    result = scrapper.fetch_reviews('https://www.amazon.com/Talking-Dad-Joke-Stocking-Stuffer/dp/B0CF4L3STL/ref=sxin_16_pa_sp_search_thematic_sspa?content-id=amzn1.sym.739a72f6-6e4d-4318-b008-5d7cb86f8006%3Aamzn1.sym.739a72f6-6e4d-4318-b008-5d7cb86f8006&crid=RG13GSGVN0KQ&cv_ct_cx=father%27s%2Bday%2Bgifts&dib=eyJ2IjoiMSJ9.Y-LmrLXWEUOtFsx5NAHVYbILw9wP3adc_2zcdeV_nTRTjo4QeYnRljndqSwW_SFRF8CuE0fxYLcQusb0E8fvBw.w8Te2XU54SuA-iLDfsfASMMhCfW2EVTKI5SO9_NTLgM&dib_tag=se&keywords=father%27s%2Bday%2Bgifts&pd_rd_i=B0CF4L3STL&pd_rd_r=2794f899-fb52-4b14-901c-e871d98d6846&pd_rd_w=WORfE&pd_rd_wg=bL2ZV&pf_rd_p=739a72f6-6e4d-4318-b008-5d7cb86f8006&pf_rd_r=ES2VA4Z6E8PC0MK9XYXE&qid=1718085015&sbo=RZvfv%2F%2FHxDF%2BO5021pAnSA%3D%3D&sprefix=%2Caps%2C567&sr=1-5-7efdef4d-9875-47e1-927f-8c2c1c47ed49-spons&sp_csd=d2lkZ2V0TmFtZT1zcF9zZWFyY2hfdGhlbWF0aWM&th=1')
    logging.info(result)

    thd = Thread()
    thd.is_alive