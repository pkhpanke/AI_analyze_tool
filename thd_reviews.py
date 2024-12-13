import os,re
import urllib.request
import aiohttp
import asyncio
import json
import pandas as pd
from pyquery import PyQuery as pq
import winreg
import datetime
from PySide6.QtCore import QObject, Signal
# from bs4 import BeautifulSoup
import urllib
from aiohttp import TCPConnector
import requests
from yarl import URL
import logging
# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='[%(levelname)s] %(asctime)s - %(filename)s:%(funcName)s:%(lineno)d - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy()) 

##  old headers
# headers = {
#     "authority": "www.homedepot.com",
#     "accept": "*/*",
#     "accept-language": "zh-CN,zh;q=0.9",
#     "apollographql-client-name": "major-appliances",
#     "apollographql-client-version": "0.0.0",
#     "cache-control": "no-cache",
#     "content-type": "application/json",
#     "origin": "https://www.homedepot.com",
#     "pragma": "no-cache",
#     "sec-ch-ua": "\"Not.A/Brand\";v=\"8\", \"Chromium\";v=\"114\", \"Google Chrome\";v=\"114\"",
#     "sec-ch-ua-mobile": "?0",
#     "sec-ch-ua-platform": "\"Windows\"",
#     "sec-fetch-dest": "empty",
#     "sec-fetch-mode": "cors",
#     "sec-fetch-site": "same-origin",
#     "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
#     "x-api-cookies": "{}",
#     "x-debug": "false",
#     "x-experience-name": "major-appliances",
#     "x-hd-dc": "origin",
#     "x-thd-customer-token": ""
# }

# new headers
headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36', 
    'Accept-Encoding': 'gzip, deflate', 
    'accept': '*/*', 
    'Connection': 'keep-alive', 
    'authority': 'www.homedepot.com', 
    'accept-language': 'zh-CN,zh;q=0.9', 
    'apollographql-client-name': 'major-appliances', 
    'apollographql-client-version': '0.0.0', 
    'cache-control': 'no-cache', 
    'content-type': 'application/json', 
    'origin': 'https://www.homedepot.com', 
    'pragma': 'no-cache', 
    'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"', 
    'sec-ch-ua-mobile': '?0', 
    'sec-ch-ua-platform': '"Windows"', 
    'sec-fetch-dest': 'empty', 'sec-fetch-mode': 'cors', 
    'sec-fetch-site': 'same-origin', 
    'x-api-cookies': '{}', 
    'x-debug': 'false', 
    'x-experience-name': 'major-appliances', 
    'x-hd-dc': 'origin', 
    'x-thd-customer-token': ''
}
cookies = {

}
params = {
    "opname": "reviews"
}

class THDReviews(QObject):
    logSignal = Signal(str)
    def __init__(self):
        super(THDReviews, self).__init__()
        self.data =[]
        self.itemName = ""
        self.itemUrl = ""
        self.image_content = None
        self.img_link = ""
        self.product_info_dict = {}
        self.proxy = None

    def check_webpage_access(self, url, proxies=None, timeout=5):
        """
        Check if a webpage is accessible using a HEAD request.
        
        Parameters:
        url (str): The URL of the webpage to check.
        timeout (int): The timeout for the request in seconds. Default is 5 seconds.
        
        Returns:
        bool: True if the webpage is accessible, False otherwise.
        """
        try:
            response = requests.head(url, proxies=proxies, timeout=timeout)
            # Check if the status code indicates a successful response
            if response.status_code == 200:
                return True
            else:
                self.log_debug(f"failed to access {url}, reason: [{response.status_code}]")
                return False
        except Exception as e:
            self.log_error(f"failed to access {url}, reason: [{e}], please make sure the VPN is disabled")
            # If there is any request exception, return False
            return False

    def config_proxy(self):
        '''
        proxy_settings = self.get_proxy_settings_windows()
        logging.info(proxy_settings)
        if proxy_settings:
            # self.proxy = "http://127.0.0.1:9981"
            if "http" in proxy_settings or "https" in proxy_settings:
                # Split the input string by semicolon
                parts = proxy_settings.split(';')

                # Search for the part that starts with "http="
                http_part  = next((part for part in parts if part.startswith("http=")), None)
                self.proxy = http_part.replace("=", "://")
            else:
                self.proxy = "http://"+proxy_settings
            self.log_debug(f"Current System Proxy is {proxy_settings}, configure APP to use Proxy Server: {self.proxy}")
        else:
            self.proxy = None
            self.log_debug("No proxy is enabled.")
        '''

        # set proxy environment parameters
        # remember to let coroutine trust environment parameters
        system_proxies = urllib.request.getproxies()
        logging.info(system_proxies)

        if "http" in system_proxies:
            os.environ["http_proxy"] = system_proxies["http"]
            # self.proxy = system_proxies["http"]

        '''
        if self.proxy is not None:
            unset_proxy = False
            try:
                self.log_debug("Testing connectivity to homedepot.com...")
                # resp = requests.get("https://www.homedepot.com/", headers=headers, cookies=cookies,
                #             proxies = system_proxies)
                # if resp.status_code != 200:
                #     unset_proxy = True
                resp = self.check_webpage_access("https://www.homedepot.com/", proxies = system_proxies, timeout = 2)
                if resp:
                    unset_proxy = True
            except Exception as e:
                unset_proxy = True
            if unset_proxy:
                self.proxy = None
                self.log_debug("Proxy can not be used by being passed as a get/post argument.")
        '''

    # @staticmethod
    def log_error(self,message):
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        logging.error(message)
        self.logSignal.emit(f"[ERROR] {timestamp}: {message}")
    
    # @staticmethod
    def log_debug(self,message):
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        logging.debug(message)
        self.logSignal.emit(f"[DEBUG] {timestamp}: {message}")
    def get_proxy_settings_windows(self):
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 'Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings') as key:
                proxy_enabled = winreg.QueryValueEx(key, 'ProxyEnable')[0]
                if proxy_enabled:
                    proxy_server = winreg.QueryValueEx(key, 'ProxyServer')[0]
                    return proxy_server
        except Exception as e:
            pass

    async def do_request_detail(self,session:aiohttp.ClientSession, url, max_retries=3):
        """

        :param session:  aiohttp.ClientSession()
        :param url:  商品详情页url
        :param max_retries:  最大重试次数
        :return:
        """
        retries = 0
        while retries <= max_retries:
            try:
                async with session.get(url, headers=headers, cookies=cookies,
                                    proxy = self.proxy
                                    ) as response:
                    if response.status == 200:
                        response = await response.read()
                        # with open("1.html","w",encoding="utf-8") as f:
                        #     f.write(response.decode())
                        return response
                    else:
                        print(await response.text())
                        self.log_debug(f"Got status {response.status} for url {url}. Retrying...")
            except Exception as e:
                self.log_error(f"An error occurred while fetching url {url} error_info: {e}. Retrying...")

            retries += 1

        self.log_error(f"Failed to fetch url {url} after {max_retries} retries.")
        return None  # 或者你可以返回一个特殊值或异常来表示获取页面失败


    async def get_detail(self,url):
        try:
            """获取商品详情页内容"""
            async with aiohttp.ClientSession(trust_env=True,
                                            #  connector=TCPConnector(ssl=False)
                                            ) as session:
                response = await self.do_request_detail(session, url)
                if response is None:
                    # Split the URL by '/'
                    parts = url.split('/')

                    # Get the second-to-last part
                    product_name = parts[-2]
                    return product_name,None
                doc = pq(response)
                itemName = doc("title").text().replace("The Home Depot Logo AccountIcons", "").strip()  # 商品名称
                # soup = BeautifulSoup(response, 'html.parser')
                # # Extract the title
                # itemName = soup.find('title')
                print("itemName: "+ itemName)
                # Extract the image link from the link tag with id 'thd-helmet__link--preloadImg'
                image_url = doc('link#thd-helmet__link--preloadImg').attr('href')
                return itemName, image_url
        except Exception as e:
            logging.error(e)


    async def do_request_list(self,session, itemId, starRatings=None, page=1, max_retries=5):
        """

        :param session:  aiohttp.ClientSession()
        :param itemId:  商品id
        :param starRatings:  评论星级
        :param page:  页码
        :param max_retries:  最大重试次数
        :return:
        """
        retries = 0
        startIndex = (page - 1) * 10 + 1
        while retries <= max_retries:
            try:
                url = "https://www.homedepot.com/federation-gateway/graphql"
                data = {
                    "operationName": "reviews",
                    "variables": {
                        "filters": {
                            "isVerifiedPurchase": False,
                            "prosCons": None,
                            "starRatings": starRatings
                        },
                        "itemId": itemId,
                        "pagesize": "10",
                        "recfirstpage": "10",
                        "searchTerm": None,
                        "sortBy": "photoreview",
                        "startIndex": startIndex
                    },
                    "query": "query reviews($itemId: String!, $searchTerm: String, $sortBy: String, $startIndex: Int, $recfirstpage: String, $pagesize: String, $filters: ReviewsFilterInput) {\n  reviews(itemId: $itemId, searchTerm: $searchTerm, sortBy: $sortBy, startIndex: $startIndex, recfirstpage: $recfirstpage, pagesize: $pagesize, filters: $filters) {\n    Results {\n      AuthorId\n      Badges {\n        DIY {\n          BadgeType\n          __typename\n        }\n        top250Contributor {\n          BadgeType\n          __typename\n        }\n        IncentivizedReview {\n          BadgeType\n          __typename\n        }\n        EarlyReviewerIncentive {\n          BadgeType\n          __typename\n        }\n        top1000Contributor {\n          BadgeType\n          __typename\n        }\n        VerifiedPurchaser {\n          BadgeType\n          __typename\n        }\n        __typename\n      }\n      BadgesOrder\n      CampaignId\n      ContextDataValues {\n        Age {\n          Value\n          __typename\n        }\n        VerifiedPurchaser {\n          Value\n          __typename\n        }\n        __typename\n      }\n      ContextDataValuesOrder\n      Id\n      IsRecommended\n      IsSyndicated\n      Photos {\n        Id\n        Sizes {\n          normal {\n            Url\n            __typename\n          }\n          thumbnail {\n            Url\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      ProductId\n      SubmissionTime\n      TagDimensions {\n        Pro {\n          Values\n          __typename\n        }\n        Con {\n          Values\n          __typename\n        }\n        __typename\n      }\n      Title\n      TotalNegativeFeedbackCount\n      TotalPositiveFeedbackCount\n      ClientResponses {\n        Response\n        Date\n        Department\n        __typename\n      }\n      Rating\n      RatingRange\n      ReviewText\n      SecondaryRatings {\n        Quality {\n          Label\n          Value\n          __typename\n        }\n        Value {\n          Label\n          Value\n          __typename\n        }\n        EnergyEfficiency {\n          Label\n          Value\n          __typename\n        }\n        Features {\n          Label\n          Value\n          __typename\n        }\n        Appearance {\n          Label\n          Value\n          __typename\n        }\n        EaseOfInstallation {\n          Label\n          Value\n          __typename\n        }\n        EaseOfUse {\n          Label\n          Value\n          __typename\n        }\n        __typename\n      }\n      SecondaryRatingsOrder\n      SyndicationSource {\n        LogoImageUrl\n        Name\n        __typename\n      }\n      UserNickname\n      UserLocation\n      Videos {\n        VideoId\n        VideoThumbnailUrl\n        VideoUrl\n        __typename\n      }\n      __typename\n    }\n    Includes {\n      Products {\n        store {\n          Id\n          FilteredReviewStatistics {\n            AverageOverallRating\n            TotalReviewCount\n            TotalRecommendedCount\n            RecommendedCount\n            NotRecommendedCount\n            SecondaryRatingsAveragesOrder\n            RatingDistribution {\n              RatingValue\n              Count\n              __typename\n            }\n            ContextDataDistribution {\n              Age {\n                Values {\n                  Value\n                  Count\n                  __typename\n                }\n                __typename\n              }\n              Gender {\n                Values {\n                  Value\n                  Count\n                  __typename\n                }\n                __typename\n              }\n              Expertise {\n                Values {\n                  Value\n                  __typename\n                }\n                __typename\n              }\n              HomeGoodsProfile {\n                Values {\n                  Value\n                  Count\n                  __typename\n                }\n                __typename\n              }\n              VerifiedPurchaser {\n                Values {\n                  Value\n                  Count\n                  __typename\n                }\n                __typename\n              }\n              __typename\n            }\n            __typename\n          }\n          __typename\n        }\n        items {\n          Id\n          FilteredReviewStatistics {\n            AverageOverallRating\n            TotalReviewCount\n            TotalRecommendedCount\n            RecommendedCount\n            NotRecommendedCount\n            SecondaryRatingsAveragesOrder\n            RatingDistribution {\n              RatingValue\n              Count\n              __typename\n            }\n            ContextDataDistribution {\n              Age {\n                Values {\n                  Value\n                  Count\n                  __typename\n                }\n                __typename\n              }\n              Gender {\n                Values {\n                  Value\n                  Count\n                  __typename\n                }\n                __typename\n              }\n              Expertise {\n                Values {\n                  Value\n                  __typename\n                }\n                __typename\n              }\n              HomeGoodsProfile {\n                Values {\n                  Value\n                  Count\n                  __typename\n                }\n                __typename\n              }\n              VerifiedPurchaser {\n                Values {\n                  Value\n                  Count\n                  __typename\n                }\n                __typename\n              }\n              __typename\n            }\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    FilterSelected {\n      StarRatings {\n        is5Star\n        is4Star\n        is3Star\n        is2Star\n        is1Star\n        __typename\n      }\n      VerifiedPurchaser\n      SearchText\n      __typename\n    }\n    pagination {\n      previousPage {\n        label\n        isNextPage\n        isPreviousPage\n        isSelectedPage\n        __typename\n      }\n      pages {\n        label\n        isNextPage\n        isPreviousPage\n        isSelectedPage\n        __typename\n      }\n      nextPage {\n        label\n        isNextPage\n        isPreviousPage\n        isSelectedPage\n        __typename\n      }\n      __typename\n    }\n    SortBy {\n      mosthelpfull\n      newest\n      oldest\n      highestrating\n      lowestrating\n      photoreview\n      __typename\n    }\n    TotalResults\n    __typename\n  }\n}\n"
                }
                data = json.dumps(data, separators=(',', ':'))
                async with session.post(url, headers=headers, cookies=cookies, params=params, data=data, 
                                        proxy=self.proxy
                                        ) as response:  # post请求
                    if response.status == 200:
                        response = await response.read()
                        self.log_debug(f"---success to get reviews for page {page}")
                        return response
                    else:
                        print(await response.text())
                        self.log_error(f"Got status {response.status} for page {page}. Retrying...")
            except Exception as e:
                self.log_error(f"An error occurred while fetching page {page}: {e}. Retrying...")

            retries += 1

        self.log_error(f"Failed to fetch page {page} after {max_retries} retries.")
        return None

    def consolidate_ages(self, data):
        # Define new age groups and their corresponding keys in the original dictionary
        new_age_groups = {
            "18to34": ["18to24", "25to34"],
            "35to54": ["35to44", "45to54"],
            "55orover": ["55to64", "65orOver"]
        }

        # Initialize a new dictionary to store the consolidated data
        consolidated_data = {}

        # Iterate through the new age groups, summing and assigning as appropriate
        for new_key, old_keys in new_age_groups.items():
            # Sum the values of the old keys from the original dictionary
            sum_values = sum(data[old_key] for old_key in old_keys if old_key in data)
            # Assign this sum to the corresponding new key in the consolidated dictionary
            consolidated_data[new_key] = sum_values

        return consolidated_data

    async def get_total_pages(self,itemId, starRatings):
        """获取评论条数 starRatings为列表，如[5,4,3]，None则是全部评论"""
        async with aiohttp.ClientSession(trust_env=True) as session:
            response = await self.do_request_list(session, itemId, starRatings)
            if response is None:
                return 0
            # ["data"]["reviews"]["TotalResults"]
            # 获取总页数
            response = json.loads(response)
            TotalResults = response["data"]["reviews"]["TotalResults"]
            self.product_info_dict["TotalResults"] = TotalResults
            # print("TotalResults: "+ str(TotalResults))
            averageOverallRating = response["data"]["reviews"]["Includes"]["Products"]["store"]["FilteredReviewStatistics"]["AverageOverallRating"]
            self.product_info_dict["averageOverallRating"] = averageOverallRating
            # print("averageOverallRating: "+ str(averageOverallRating))
            recommendedCount = response["data"]["reviews"]["Includes"]["Products"]["store"]["FilteredReviewStatistics"]["RecommendedCount"]
            # self.product_info_dict["recommendedCount"] = recommendedCount
            # print("recommendedCount: "+ str(recommendedCount))

            notRecommendedCount = response["data"]["reviews"]["Includes"]["Products"]["store"]["FilteredReviewStatistics"]["NotRecommendedCount"]
            # self.product_info_dict["notRecommendedCount"] = notRecommendedCount
            self.product_info_dict["RecommendCount"] = {'Recom':recommendedCount,'notRecom':notRecommendedCount}
            # print("notRecommendedCount: "+ str(notRecommendedCount))
            count_rating5 = response["data"]["reviews"]["Includes"]["Products"]["store"]["FilteredReviewStatistics"]["RatingDistribution"][0]["Count"]
            count_rating4 = response["data"]["reviews"]["Includes"]["Products"]["store"]["FilteredReviewStatistics"]["RatingDistribution"][1]["Count"]
            count_rating3 = response["data"]["reviews"]["Includes"]["Products"]["store"]["FilteredReviewStatistics"]["RatingDistribution"][2]["Count"]
            count_rating2 = response["data"]["reviews"]["Includes"]["Products"]["store"]["FilteredReviewStatistics"]["RatingDistribution"][3]["Count"]
            count_rating1 = response["data"]["reviews"]["Includes"]["Products"]["store"]["FilteredReviewStatistics"]["RatingDistribution"][4]["Count"]
            self.product_info_dict["count_rating"] = {"rating5": count_rating5, "rating4": count_rating4, "rating3": count_rating3, "rating2": count_rating2, "rating1": count_rating1}
            # print("count_rating5: "+ str(count_rating5))
            # print("count_rating4: "+ str(count_rating4))
            # print("count_rating3: "+ str(count_rating3))
            # print("count_rating2: "+ str(count_rating2))
            # print("count_rating1: "+ str(count_rating1))


            count_DIYer = response["data"]["reviews"]["Includes"]["Products"]["store"]["FilteredReviewStatistics"]["ContextDataDistribution"]["HomeGoodsProfile"]["Values"][0]["Count"]
            count_Professional = response["data"]["reviews"]["Includes"]["Products"]["store"]["FilteredReviewStatistics"]["ContextDataDistribution"]["HomeGoodsProfile"]["Values"][1]["Count"]
            self.product_info_dict["count_buyer"] = {'DIYer': int(count_DIYer), 'Pro': int(count_Professional)}                                                   
            # print("count_DIYer: "+ str(count_DIYer))
            # print("count_Professional: "+ str(count_Professional))
            
            try:
                count_VerifiedPurchaser = response["data"]["reviews"]["Includes"]["Products"]["store"]["FilteredReviewStatistics"]["ContextDataDistribution"]["VerifiedPurchaser"]["Values"][0]["Count"]
                self.product_info_dict["count_VerifiedPurchaser"] = count_VerifiedPurchaser
                # print("count_VerifiedPurchaser: "+ str(count_VerifiedPurchaser))
            except Exception as e:
                print(f"Unexpected error to get count_VerifiedPurchaser: {e}")
                self.log_error(f"Unexpected error to get count_VerifiedPurchaser: {e}")

            # Parse age distribution
            age_distribution_list = {entry["Value"] : int(entry["Count"]) for entry in response["data"]["reviews"]["Includes"]["Products"]["store"]["FilteredReviewStatistics"]["ContextDataDistribution"]["Age"]["Values"]}
            # self.product_info_dict["age_distribution_list"] = age_distribution_list
            self.product_info_dict["age_distribution_list"] = self.consolidate_ages(age_distribution_list)
            # print(age_distribution_list)

            # Parse gender distribution
            gender_distribution_list = {entry["Value"]: int(entry["Count"]) for entry in response["data"]["reviews"]["Includes"]["Products"]["store"]["FilteredReviewStatistics"]["ContextDataDistribution"]["Gender"]["Values"]}
            self.product_info_dict["gender_distribution_list"] = gender_distribution_list
            # print(gender_distribution_list)
            print("product_info:",self.product_info_dict)

            pages = TotalResults // 10 + 1
            if pages >= 51:
                pages = 51
            return pages


    async def get_reviews(self, itemId, pages, starRatings):
        """获取当前页评论 starRatings为列表，如[5,4,3]，None则是全部评论"""
        """"""
        async with aiohttp.ClientSession(trust_env=True) as session:
            # session, itemId, starRatings=None, page=1, max_retries=5
            tasks = [self.do_request_list(session, itemId, starRatings, page) for page in range(1, pages + 1)]  # 生成任务列表
            pages_content = await asyncio.gather(*tasks)
            print("len",len(pages_content),"type",type(pages_content))

            # 解析每一页的内容并保存数据
            data = []
            for index, content in enumerate(pages_content):
                if content is not None:
                    content = json.loads(content)
                    Results = content["data"]["reviews"]["Results"]
                    if Results:
                        data.extend(Results)
                        # self.log_debug(f"---success to get the reivew in page index: {index}")
                    else:
                        self.log_error(f"fail to get the reivew in page index: {index}")
                else:
                    self.log_error(f"fail to get the reivew since page is empty in page index: {index}")
            return data


    async def get_all_reviews(self,itemId, starRatings=None):
        """获取所有评论 starRatings为列表，如[5,4,3]，None则是全部评论"""
        """"""
        total_pages = await self.get_total_pages(itemId, starRatings)
        if total_pages == 0:
            return None
        self.log_debug(f"itemId {itemId}  Has  {total_pages} pages found.")
        data = await self.get_reviews(itemId, total_pages, starRatings)
        self.log_debug(f"finished to get all reviews, total {len(data)} items")
        return data


    async def save_reviews(self,reviews, save_csv_path):
        """保存评论到excel 标题，内容，评分，时间，作者 商品id"""
        #  Title ReviewText Rating SubmissionTime UserNickname ProductId
        new_data = []
        for review in reviews:
            new_data.append(
                [review["Title"], review["ReviewText"], review["Rating"], review["SubmissionTime"], review["UserNickname"],
                review["ProductId"], review["itemName"]])
        if not new_data:
            return None
        df = pd.DataFrame(new_data, columns=["标题", "内容", "评分", "时间", "作者", "商品id", "商品名称"])
        df.to_csv(save_csv_path, index=False, encoding="utf_8_sig", mode="a", header=not os.path.exists(save_csv_path))
    # def fetch_product_img(self,img_link):
    #     if img_link:
    #         # Use requests to get the content of the image
    #         response = requests.get(image_url)

    #         # Check if the request was successful (status code 200 means OK)
    #         if response.status_code == 200:
    #             # Open a file in binary write mode and save the image content
    #             with open("downloaded_image.jpg", "wb") as file:
    #                 file.write(response.content)
    #         else:
    #             print("Failed to retrieve the image.")
    #     else:
    #         print("Image URL not found.")

    async def fetch_product_img(self,img_link):
        try:
            if img_link:
                async with aiohttp.ClientSession(trust_env=True) as session:
                    async with session.get(img_link, 
                                        proxy=self.proxy
                                        ) as response:
                        if response.status == 200:
                            self.image_content = await response.read()

                            # Open a file in binary write mode and save the image content
                            # with open("downloaded_image.jpg", "wb") as file:
                            #     file.write(self.image_content)

                            # print("Image saved as 'downloaded_image.jpg'.")
                        else:
                            self.log_error("Failed to retrieve the image.")
            else:
                self.log_error("Image URL not found.")
        except Exception as e:
            logging.error(e)
            self.image_content = None

    async def start_job(self,url,starRatings=None):
        save_csv_path = "data.csv"
        self.itemUrl = url
        itemId = self.itemUrl.split("/")[-1]
        # starRatings = None  # 评论星级 这里指定1星评论 你可以指定多个星级 [1,2,3,4,5] ,指定为None则是全部评论
        self.log_debug("start scrap job")
        # parse review pages while scraping details page
        # task_get_reviews = self.get_all_reviews(itemId, starRatings)
        # task_get_details = self.get_detail(self.itemUrl)
        # result_reviews, result_details = await asyncio.gather(task_get_reviews, task_get_details)
        # self.data = result_reviews
        # self.itemName, self.img_link = result_details

        self.data = await self.get_all_reviews(itemId, starRatings)
        self.itemName, self.img_link = await self.get_detail(self.itemUrl)

        # self.itemName = "smart"

    def fetch_reviews(self,itemUrl):
        # loop = asyncio.get_event_loop()
        # loop.run_until_complete(self.start_job(itemUrl))
        # self.config_proxy()
        # self.log_debug("Testing connectivity to homedepot.com...")
        # access = self.check_webpage_access("https://www.homedepot.com/", timeout = 5)
        # if not access:
        #     return None
        
        asyncio.run(self.start_job(itemUrl))
        try:
            asyncio.run(self.fetch_product_img(self.img_link))
        except Exception as e:
            logging.error(e)
            return None
        if not self.data:
            return None
        new_data = []
        for review in self.data:
            item = {
                    "Date": review["SubmissionTime"].split(".")[0],
                    "Stars": review["Rating"],
                    "Title": review["Title"],
                    "Content": review["ReviewText"],
                    "Reviewer": review["UserNickname"]
                }
            new_data.append(item)  
            # new_data.append(
            #     [review["Title"], review["ReviewText"], review["Rating"], review["SubmissionTime"], review["UserNickname"],
            #     review["ProductId"], review["itemName"]])
        if not new_data:
            return None
        # print(new_data)
        # Clean the product name for it to be filename-friendly
        cleaned_product_name = re.sub(r'[\\/*?:"<>|]', '', self.itemName)
        ret_data = {
            "itemName": cleaned_product_name,
            "img": self.image_content,
            "reviews": new_data,
            "product_info": self.product_info_dict
        }

        return ret_data


    async def main(self):
        save_csv_path = "data.csv"
        itemUrl = "https://www.homedepot.com/p/LG-1-8-cu-ft-30-in-W-Smart-Over-the-Range-Microwave-Oven-with-EasyClean-in-PrintProof-Stainless-Steel-1000-Watt-MVEM1825F/321666159"
        itemId = itemUrl.split("/")[-1]
        starRatings = None  # 评论星级 这里指定1星评论 你可以指定多个星级 [1,2,3,4,5] ,指定为None则是全部评论
        self.data = await self.get_all_reviews(itemId, starRatings)
        self.itemName = await self.get_detail(itemUrl)
        if self.data is not None:
            for i in self.data:
                i["itemName"] = self.itemName
        await self.save_reviews(self.data, save_csv_path)


if __name__ == '__main__':
#     loop = asyncio.get_event_loop()
#     loop.run_until_complete(main())

    scraper = THDReviews()
    scraper.fetch_reviews("https://www.homedepot.com/p/LG-1-8-cu-ft-30-in-W-Smart-Over-the-Range-Microwave-Oven-with-EasyClean-in-PrintProof-Stainless-Steel-1000-Watt-MVEM1825F/321666159")
