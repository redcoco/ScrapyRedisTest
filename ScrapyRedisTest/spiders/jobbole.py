# -*- coding: utf-8 -*-
from scrapy.http import Request
from urllib import parse
from scrapy_redis.spiders import RedisSpider


class JobboleSpider(RedisSpider):
    name = 'jobbole'
    allowed_domains = ["blog.jobbole.com"]
    # start_urls = ['http://blog.jobbole.com/all-posts/page/550/']
    redis_key = 'jobbole:start_urls'


    # 用户自定义settings
    custom_settings = {
        "DOWNLOAD_DELAY": 0.4,
        "ROBOTSTXT_OBEY": False,
        # Enables scheduling storing requests queue in redis.
        "SCHEDULER ":"scrapy_redis.scheduler.Scheduler",
        # Ensure all spiders share same duplicates filter through redis.
        "DUPEFILTER_CLASS ":"scrapy_redis.dupefilter.RFPDupeFilter",
        # Store scraped item in redis for post-processing.
        "ITEM_PIPELINES ":{
    'scrapy_redis.pipelines.RedisPipeline': 300
        },
    }

    def parse(self, response):
        """
        1. 获取文章列表页中的文章url并交给scrapy下载后并进行解析
        2. 获取下一页的url并交给scrapy进行下载， 下载完成后交给parse
        """
        # 解析列表页中的所有文章url并交给scrapy下载后并进行解析
        if response.status == 404:
            self.fail_urls.append(response.url)
            self.crawler.stats.inc_value("failed_url")

        post_nodes = response.css("#archive .floated-thumb .post-thumb a")
        for post_node in post_nodes:
            image_url = post_node.css("img::attr(src)").extract_first("")
            post_url = post_node.css("::attr(href)").extract_first("")
            yield Request(url=parse.urljoin(response.url, post_url), meta={"front_image_url": image_url},
                          callback=self.parse_detail)

        # 提取下一页并交给scrapy进行下载
        next_url = response.css(".next.page-numbers::attr(href)").extract_first("")
        if next_url:
            yield Request(url=parse.urljoin(response.url, post_url), callback=self.parse)

    def parse_detail(self, response):
        front_image_url = response.meta.get("front_image_url")
        yield {"front_image_url":front_image_url}
