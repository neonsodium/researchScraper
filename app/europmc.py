import subprocess
import re
import urllib.parse
import scrapy
import argparse
import pandas as pd
import urllib
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

# Articals per Page
ArticlePerPage = 100
totalArticals = 0

# Excess Articals to crawl
# excessErrorArtical = 1000


# Define disallowed substrings and characters in emails
email_character_disallowed = [",", "/", ";", ":", "(", ")", "&", "%", "?", "[", "]", "  ", "+"]

email_id_disallowed = ["contact", "connect", "journals", "permission", "admin", "info"]


# Crawled Articles counters and crawled data extracted
Crawled_Articles_total = 0
Crawled_Articles_data = 0

# DataFrame to output the data
output_dataframe = pd.DataFrame()
def printProcessingData(artical_count):
    print("================================================================================================")
    print("Total articles crawled:" + str(Crawled_Articles_total))
    print("Total articles extracted:" + str(Crawled_Articles_data))
    print("Total number of articles to be crawled:" + str(artical_count))
    print("================================================================================================")

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

def process_email(email):
    """
    Process the given email address based on disallowed and required strings.

    Args:
        email (str): The email address to be processed.
        disallowed_strings (list): List of disallowed substrings.
        required_strings (list): List of required substrings.

    Returns:
        str: Result of processing the email address.
    """
    global email_character_disallowed
    global email_id_disallowed


    # Check for disallowed substrings
    for substring in email_character_disallowed:
        if substring in email:
            return False

    # Check if there are numbers before the @ symbol
    if re.match(r'^\d+@[\w.-]+\.\w+$', email):
        return False

    # Check for required substrings
    for substring in email_id_disallowed:
        if substring in email:
            return False

    return True


# Test the function
# result = process_email(test_email, disallowed, required)



#Extract email from affiliation
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


class PubMedSpider(scrapy.Spider):
    name = 'EuroPMC'

    def __init__(self, title=None, keyword=None, abstract=None, start_year=None, end_year=None, *args, **kwargs):
        super(PubMedSpider, self).__init__(*args, **kwargs)
        self.abstract = abstract
        self.keyword = keyword
        self.title = title
        self.totalArticalsFound = 0
        self.article_id = ''
        self.nextCursorMark = '*'
        self.NoOfArticles = ArticlePerPage
        self.start_year = start_year
        self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.199 Safari/537."}
        self.end_year = end_year
        self.page = 1
        self.start_urls = [self.get_start_url()]
        self.crawl_check = 0
        self.excessErrorArtical = 0

    def get_start_url(self):
        # Construct the start and consecutive URL/API using the provided parameters
            # date formate 1900-05-31
        print(self.nextCursorMark)
        return f'https://europepmc.org/api/get/articleApi?query=(TITLE:%22{self.title}%22%20AND%20%22{self.keyword}%22%20AND%20ABSTRACT:%22{self.abstract}%22)%20AND%20(FIRST_PDATE:%5B{self.start_year}%20TO%20{self.end_year}%5D)&cursorMark={self.nextCursorMark}&format=json&pageSize={self.NoOfArticles}&sort=Relevance&synonym=FALSE'
    def get_article_data(self):
        return f'https://europepmc.org/api/get/articleApi?query=(EXT_ID:{self.article_id})&format=json&resultType=core'

    def printCrawlExitStatement(self):
        print("================================================================================================")
        print(str(self.page) + " " + "No of pages where crawled" + '\n' + " No nextCursorMark was found on the page")
        print("================================================================================================")

    def parse(self, response):
        # articles ID from API JSON Response
        json_response = response.json()

        if self.page == 1:
            self.totalArticalsFound = json_response['hitCount']
            totalArticals = self.totalArticalsFound
            # self.excessErrorArtical = self.totalArticalsFound * 0.05
        else:
            printProcessingData(self.totalArticalsFound)

        if Crawled_Articles_total+self.excessErrorArtical > self.totalArticalsFound and self.page != 1:  # Used 'and' instead of '&&'
            self.printCrawlExitStatement()
            return
        try:
            articles_ids_json = json_response['resultList']['result']
        except:
            self.printCrawlExitStatement()
            return
        if not articles_ids_json:
            if self.page == 1:
                # No articles found on the first page, author not found
                self.printCrawlExitStatement()
                return
            else:
                self.printCrawlExitStatement()
                # No articles found on subsequent pages, search for the author
                # Exception handling =====INCOMPLETE=====
                return

        for article_id in articles_ids_json:
            self.article_id = article_id['id']
            yield response.follow(self.get_article_data(), self.parse_article, headers=self.headers)

        try:
            nextCursorMark = json_response['nextCursorMark']

            # self.nextCursorMark = nextCursorMark.replace("=","%3D")
            self.nextCursorMark = urllib.parse.quote(nextCursorMark)
            print(self.nextCursorMark)
        except:
            self.printCrawlExitStatement()
            return

        # Increment page number and send request for the next page
        self.page += 1
        self.NoOfArticles += ArticlePerPage
        # if self.page >= 999:
        #     self.page = 1
        yield response.follow(self.get_start_url(), self.parse, headers=self.headers)

    def parse_article(self, response):
        global output_dataframe
        global Crawled_Articles_total
        global Crawled_Articles_data
        Crawled_Articles_total += 1
        author_data_all = response.json()
        for author_items in author_data_all['resultList']['result']:
            article_title = author_items['title']
            # Check if affiliation exists and if it contains an email address and then Yield it
            for author_info in author_items['authorList']['author']:
                try:
                    affiliation = author_info['authorAffiliationDetailsList']['authorAffiliation']
                    affiliation = affiliation[0]['affiliation']
                    author_name = author_info['fullName']
                    if affiliation and '@' in affiliation:
                        Crawled_Articles_data += 1
                        author_data = []
                        email, affiliation = email_affiliation(affiliation)
                        if process_email(email) and not contains_high_unicode(author_name):
                            author_data.append({
                                'title': article_title,
                                'author_name': author_name,
                                'email': email,
                                'affiliation': affiliation,
                            })

                            # Add author_data(Dictionary) to a dataFrame and then Append/Concat it to the global output DataFrame
                            df_dictionary = pd.DataFrame(author_data)
                            # output.to_csv(output_path, mode='a', index=False)
                            output_dataframe = pd.concat([output_dataframe, df_dictionary], ignore_index=True)
                        else:
                            author_data.append({
                                'title': article_title,
                                'author_name': author_name,
                                'email': email,
                                'affiliation': affiliation,
                            })
                            print(author_data)
                except:
                    print(author_info)



def run_spider(article_title, article_keyword, article_abstract, start_date, end_date):
    process = CrawlerProcess(get_project_settings())
    process.crawl(PubMedSpider, title=article_title, keyword=article_keyword, abstract=article_abstract,
                  start_year=start_date, end_year=end_date)
    process.start()

    start_date = start_date.split('-')
    end_date = end_date.split('-')
    output_path = f'/var/www/html/output/EuroPMC_Output_{article_keyword}_{article_title}_{article_abstract}_{start_date[0]}_to_{end_date[0]}.csv'
    # output_filename = f'/Users/vedanths/PycharmProjects/Bankinglabs/scraping_server/output/EuroPMC_Output_{article_keyword}_{article_title}_{article_abstract}_{start_date[0]}_to_{end_date[0]}.csv'
    # f=open(output_path,'w')
    # output_path = f'PubMed_Output_{article_keyword}_{article_title}_{start_date[0]}_{start_date[1]}_{start_date[2]}_to_{end_date[0]}_{end_date[1]}_{end_date[2]}.csv'
    output_dataframe.drop_duplicates().to_csv(output_path, mode='a', index=False)
    python_mailer = "/var/www/html/main/Mailer/mailer_4.py"
    # python_mailer = "/Users/vedanths/PycharmProjects/Bankinglabs/scraping_server/main/Mailer/mailer_4.py"
    try:
        # Execute the Python file
        subprocess.run(["python3", python_mailer,output_filename])
    except subprocess.CalledProcessError as e:
        print(f"Error executing the Python file: {e}")
    except FileNotFoundError as e:
        print(f"Python interpreter not found: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

    
    print("================================================================================================")
    print("Total articles found:" + str(totalArticals))
    print("Total articles crawled:" + str(Crawled_Articles_total))
    print("Total articles extracted:" + str(Crawled_Articles_data))
    print("================================================================================================")




# def main():
#     title = input("title:")
#     keyword = input("keyword:")
#     abstract = input("abstract:")
#     start_date = input("start_year:")
#     end_date = input("end_year:")
#     # file_name = input("file_name:")
#     run_spider(title, keyword, abstract, start_date, end_date)
#
# main()

if __name__ == "__main__":
    try:
        title = input("title:")
        keyword = input("keyword:")
        abstract = input("abstract:")
        start_date = input("start_year(1900):")
        end_date = input("end_year(1900):")
        # file_name = input("file_name:")
        run_spider(title, keyword, abstract, start_date, end_date)
        exit(0)

    except ValueError:
        print("Invalid input. Please enter valid year values.")

# if __name__ == "__main__":
#     try:
#         parser = argparse.ArgumentParser(description='Process article information.')
#         parser.add_argument('title', type=str, help='Article Title')
#         parser.add_argument('keyword', type=str, help='Article Keyword')
#         parser.add_argument('abstract', type=str, help='Article Abstract')
#         parser.add_argument('start_date', type=str, help='Start year')
#         parser.add_argument('end_date', type=str, help='End year')
#         parser.add_argument('file_name', type=str, help='File to append the data')
#         args = parser.parse_args()
#         run_spider(args.title, args.keyword, args.abstract, args.start_date, args.end_date, args.file_name)
#         exit(0)
#
#     except ValueError:
#         print("Invalid input. Please enter valid year values.")
