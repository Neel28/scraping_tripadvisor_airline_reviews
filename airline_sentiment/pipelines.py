# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import csv
import os.path
class AirlineSentimentPipeline(object):

    def __init__(self):
        if not os.path.isfile('CONTENT_psysci.csv'):
            self.csvwriter = csv.writer(open('CONTENT.csv', 'a'))
            self.csvwriter.writerow(['name','url','date','title','review','star'])
        else:
            self.csvwriter = csv.writer(open('CONTENT.csv', 'a'))

    def process_item(self, item, spider):
        rev_val = item['reviews']
        for dictionary in rev_val:
            self.csvwriter.writerow([item['name'], item['url'],
                                 dictionary['date'],dictionary['title'],
                                 dictionary['description'],dictionary['stars']])
        return item
