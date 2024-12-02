import re
import os
import scrapy
import argparse
import pandas as pd
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

output = pd.DataFrame()

# Helper function to extract the year parts from a given year string
def extract_year(given_year):
    # Split the given_year by "-"
    year_parts = given_year.split("-")

    # If there's only one year provided, append "3000" as the end year
    if len(year_parts) == 1:
        year_parts.append("3000")

    return year_parts


def email_affiliation(affiliation):
    email_pattern = r"(\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b)"
    email = re.findall(email_pattern, affiliation)
    email = ''.join(email)

    # Remove the email from the affiliation after extracting the email
    affiliation = affiliation.replace(str(email), "")

    # Remove "Electronic address:" from the affiliation
    remove = "Electronic address:"
    if remove in affiliation:
        affiliation = affiliation.replace(str(remove), "")

    # Remove trailing "." or " " from the affiliation
    if affiliation.endswith('.') or affiliation.endswith(' '):
        affiliation = affiliation[:len(affiliation) - 1]

    return email, affiliation

def contains_high_unicode(text):
    """
    Check if the given text contains any character with a Unicode value >= 132.

    Parameters:
    text (str): The text to check.

    Returns:
    bool: True if there is at least one character with a Unicode value >= 132, False otherwise.
    """
    for char in text:
        if ord(char) >= 132:
            return True
    return False


class PubMedSpider(scrapy.Spider):
    name = 'pubmed'

    def __init__(self, title=None, keyword=None, abstract=None, start_year=None, end_year=None, *args, **kwargs):
        super(PubMedSpider, self).__init__(*args, **kwargs)
        self.abstract = abstract
        self.keyword = keyword
        self.title = title
        self.start_year = start_year
        self.end_year = end_year
        self.page = 1
        self.output = output
        self.start_urls = [self.get_start_url()]

    def get_start_url(self):
        # Construct the start URL using the provided parameters
        return f'https://pubmed.ncbi.nlm.nih.gov/?term=((({self.keyword}) AND ({self.abstract}[Title/Abstract])) AND ({self.title}[Title])AND (("{self.start_year}"[Date - Publication] : "{self.end_year}"[Date - Publication]))&sort=&page={self.page}'

    def parse(self, response):
        articles = response.css('a.docsum-title')

        if not articles:
            if self.page == 1:
                # No articles found on the first page, author not found
                return
            else:
                # No articles found on subsequent pages, search for the author
                # Exception handling =====INCOMPLETE=====
                return

        for article in articles:
            link = article.css('a.docsum-title::attr(href)').get()
            yield response.follow(link, self.parse_article)

        # Increment page number and send request for the next page
        self.page += 1
        if self.page >= 999:
            self.page = 1
        yield response.follow(self.get_start_url(), self.parse)

    def parse_article(self, response):
        global output
        article_title = response.css('h1.heading-title::text').get()
        article_title = article_title.strip()  # strip extra white space characters
        author_data_all = response.css('span.authors-list-item')
        for author_item in author_data_all:
            author_name = author_item.css('a.full-name::text').get()
            affiliation = author_item.css('a.affiliation-link::attr(title)').get()

            # Check if affiliation exists and if it contains an email address and then Yield it
            if affiliation and '@' in affiliation and not contains_high_unicode(author_name):
                author_data = []
                email, affiliation = email_affiliation(affiliation)
                author_data.append({
                    'title': article_title,
                    'author_name': author_name,
                    'email': email,
                    'affiliation': affiliation,
                })

                # Add author_data(Dictionary) to a dataFrame and then Append/Concat it to the global output DataFrame
                df_dictionary = pd.DataFrame(author_data)
                output = pd.concat([output, df_dictionary], ignore_index=True)

def run_spider(article_title, article_keyword, article_abstract, start_date, end_date,file_name):
    process = CrawlerProcess(get_project_settings())
    process.crawl(PubMedSpider, title=article_title, keyword=article_keyword, abstract=article_abstract,
                  start_year=start_date, end_year=end_date)
    process.start()

    start_date = start_date.split('/')
    end_date = end_date.split('/')
    # output_path=f'PubMed_Output_{article_keyword}_{article_title}_{article_abstract}_{start_date[0]}_to_{end_date[0]}.csv'
    # f=open(output_path,'w')
    # output_path = f'PubMed_Output_{article_keyword}_{article_title}_{start_date[0]}_{start_date[1]}_{start_date[2]}_to_{end_date[0]}_{end_date[1]}_{end_date[2]}.csv'
    output_path = file_name
    output.to_csv(file_name, mode='a',index=False)


# def main(title, keyword, abstract, start_date, end_date):
#     print("Article Title:", title)
#     print("Article Keyword:", keyword)
#     print("Article Abstract:", abstract)
#     print("Start year:", start_date)
#     print("End year:", end_date)

if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser(description='Process article information.')
        parser.add_argument('title', type=str, help='Article Title')
        parser.add_argument('keyword', type=str, help='Article Keyword')
        parser.add_argument('abstract', type=str, help='Article Abstract')
        parser.add_argument('start_date', type=str, help='Start year')
        parser.add_argument('end_date', type=str, help='End year')
        parser.add_argument('file_name', type=str, help='File to append the data')
        args = parser.parse_args()
        run_spider(args.title, args.keyword, args.abstract, args.start_date, args.end_date, args.file_name)
        exit(0)

    except ValueError:
        print("Invalid input. Please enter valid year values.")
