
def test_scraper_thread():
    # 测试链接，这里以HomeDepot的产品链接为例
    test_link = "https://www.homedepot.com/p/Stanley-Bostitch-BR1525-25-Gauge-1-2-in-Bulk-Finishing-Nailer-BR1525KIT/301506960"

    # 创建ScraperThread实例
    scraper_thread = ScraperThread(test_link)

    # 启动线程
    scraper_thread.start()

    # 等待线程结束
    scraper_thread.join()

    # 打印抓取结果
    if scraper_thread.scrap_success:
        print("抓取成功！")
        print("产品名称：", scraper_thread.productname)
        print("产品信息：", scraper_thread.product_info)
        print("评论列表：", scraper_thread.reviews)
        if scraper_thread.product_image_file_path:
            print("产品图片保存路径：", scraper_thread.product_image_file_path)
    else:
        print("抓取失败！")

if __name__ == "__main__":
    test_scraper_thread()