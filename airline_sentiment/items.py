# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html
import scrapy
from scrapy.item import Item, Field


class AirlineSentimentItem(Item):
    # define the fields for your item here like:
    url = Field()
    name = Field()
    reviews = Field()

class TripAdvisorReviewItem(Item):

    date = Field()
    title = Field()
    description = Field()
    stars = Field()
    helpful_votes = Field()
    user = Field()

