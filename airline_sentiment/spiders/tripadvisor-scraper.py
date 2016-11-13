import re
import time
import sys
from scrapy.spider import BaseSpider
from scrapy.selector import Selector
from scrapy.http import Request
import parsedatetime
from datetime import datetime
from airline_sentiment.items import *
from airline_sentiment.spiders.crawlerhelper import *

# Constants.
# Max reviews pages to crawl.
# Reviews collected are around: 5 * MAX_REVIEWS_PAGES
MAX_REVIEWS_PAGES = 500
cal = parsedatetime.Calendar()
now = datetime.now()
class TripAdvisorRestaurantBaseSpider(BaseSpider):
    name = "tripadvisor_airline"

    allowed_domains = ["tripadvisor.com"]
    base_uri = "http://www.tripadvisor.com"
    start_urls = [
        base_uri + "/Airlines"
    ]

    # Entry point for BaseSpider.
    # Page type: /RestaurantSearch
    def parse(self, response):
        tripadvisor_items = []

        sel = Selector(response)
        #//*[@id="LISTING_SECTION_A"]/div[2]/div[1]/div[1]
        #snode_airline = sel.xpath('//div[@id="taplc_airlines_index_main_0"]/div[@class="airlineData"]')
        #snode_restaurants = sel.xpath('//div[@id="EATERY_SEARCH_RESULTS"]/div[starts-with(@class, "listing")]')
        snode_airline = sel.xpath('//*[starts-with(@class, "listingSection")]/div[2]/div[starts-with(@class, "column")]/div[starts-with(@class, "airlineData")]')
        # Build item index.
        for snode_restaurant in snode_airline:
            tripadvisor_item =  AirlineSentimentItem()

            tripadvisor_item['url'] = self.base_uri + clean_parsed_string(get_parsed_string(snode_restaurant, 'div/a[1]/@href'))
            tripadvisor_item['name'] = clean_parsed_string(get_parsed_string(snode_restaurant, 'div/a[1]/div/text()'))

            #print(tripadvisor_item['url'])
            #print(tripadvisor_item['name'])

            yield Request(url=tripadvisor_item['url'], meta={'tripadvisor_item': tripadvisor_item}, callback=self.parse_search_page)

            tripadvisor_items.append(tripadvisor_item)

    def parse_search_page(self, response):

        tripadvisor_item = response.meta['tripadvisor_item']
        sel = Selector(response)

        tripadvisor_item['reviews'] = []

        # The default page contains the reviews but the reviews are shrink and need to click 'More' to view the complete content.
		# An alternate way is to click one of the reviews in the page to open the expanded reviews display page.
		# We're using this last solution to avoid AJAX here.
        expanded_review_url = clean_parsed_string(get_parsed_string(sel, '//div[contains(@class, "basic_review")]//a/@href'))

        if expanded_review_url:
			yield Request(url=self.base_uri + expanded_review_url, meta={'tripadvisor_item': tripadvisor_item, 'counter_page_review' : 0}, callback=self.parse_fetch_review)

    # If the page is not a basic review page, we can proceed with parsing the expanded reviews.
	# Page type: /ShowUserReviews
    def parse_fetch_review(self, response):

        tripadvisor_item = response.meta['tripadvisor_item']
        sel = Selector(response)
        counter_page_review = response.meta['counter_page_review']

        # Limit max reviews pages to crawl.
        #if counter_page_review < MAX_REVIEWS_PAGES:
        #    counter_page_review = counter_page_review + 1

        # TripAdvisor reviews for item.
        snode_reviews = sel.xpath('//div[@id="REVIEWS"]/div/div[contains(@class, "review")]/div[@class="col2of2"]/div[@class="innerBubble"]')

        # Reviews for item.
        for snode_review in snode_reviews:

            tripadvisor_review_item = TripAdvisorReviewItem()

            tripadvisor_review_item['title'] = clean_parsed_string(get_parsed_string(snode_review, 'div[@class="quote"]/text()'))
            # Review item description is a list of strings.
            # Strings in list are generated parsing user intentional newline. DOM: <br>
            tripadvisor_review_item['description'] = get_parsed_string_multiple(snode_review, 'div[@class="entry"]/p/text()')
            # Cleaning string and taking only the first part before whitespace.
            snode_review_item_stars = clean_parsed_string(get_parsed_string(snode_review, 'div[@class="rating reviewItemInline"]/span[starts-with(@class, "rate")]/img/@alt'))
            tripadvisor_review_item['stars'] = re.match(r'(\S+)', snode_review_item_stars).group()
            '''
            print('&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&')
            print(tripadvisor_review_item['title'])
            print(tripadvisor_review_item['description'])
            print(tripadvisor_review_item['stars'])
            print('&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&')
            '''
            snode_review_item_date = clean_parsed_string(get_parsed_string(snode_review, 'div[@class="rating reviewItemInline"]/span[@class="ratingDate"]/text()'))
            snode_review_item_date = str(snode_review_item_date)
            snode_review_item_date = re.sub(r'Reviewed ', '', snode_review_item_date, flags=re.IGNORECASE)
            #snode_review_item_date = time.strptime(snode_review_item_date, '%B %d, %Y') if snode_review_item_date else None
            #tripadvisor_review_item['date'] = time.strftime('%Y-%m-%d', snode_review_item_date) if snode_review_item_date else None
            da = cal.parseDT(snode_review_item_date, now)[0]
            tripadvisor_review_item['date'] = da.strftime('%m/%d/%Y')
            tripadvisor_item['reviews'].append(tripadvisor_review_item)


        # Find the next page link if available and go on.
        #next_page_url = clean_parsed_string(get_parsed_string(sel, '//a[starts-with(@class, "guiArw sprite-pageNext ")]/@href'))
        '''
        next_page_url = clean_parsed_string(get_parsed_string(sel, '//*[@id="REVIEWS"]/div[9]/div/a[2]/@href'))
        if next_page_url and len(next_page_url)==0:
            next_page_url = clean_parsed_string(get_parsed_string(sel, '//*[@id="REVIEWS"]/div[9]/div/a/@href'))

        if next_page_url and len(next_page_url) > 0:
            yield Request(url=self.base_uri + next_page_url, meta={'tripadvisor_item': tripadvisor_item, 'counter_page_review' : counter_page_review}, callback=self.parse_fetch_review)
        else:
            yield tripadvisor_item
        '''
        next_page_url = clean_parsed_string(get_parsed_string(sel, '//div[starts-with(@class,"unified pagination")]/a[starts-with(@class,"nav next")]/@href'))
        print('{}}}{}{}{}{}{}{}{}{}{}{}{}{}: ',next_page_url)
        if next_page_url and len(next_page_url) > 0:
            yield Request(url=self.base_uri + next_page_url, meta={'tripadvisor_item': tripadvisor_item, 'counter_page_review' : counter_page_review}, callback=self.parse_fetch_review)
        else:
            yield tripadvisor_item


















