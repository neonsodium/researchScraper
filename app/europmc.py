import logging
import subprocess
import urllib.parse
import scrapy
import pandas as pd
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from constants_europmc import (
    ARTICLE_PER_PAGE,
    EMAIL_CHARACTER_DISALLOWED,
    EMAIL_ID_DISALLOWED,
    HEADERS,
    OUTPUT_PATH_TEMPLATE,
)
from ulits_europmc import (
    print_processing_data,
    process_email,
    email_affiliation,
    contains_high_unicode,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("scraper.log"), logging.StreamHandler()],
)

logger = logging.getLogger(__name__)
output_dataframe = pd.DataFrame()


class PubMedSpider(scrapy.Spider):
    name = "EuroPMC"

    def __init__(
        self,
        title,
        keyword,
        abstract,
        start_year,
        end_year,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.abstract = abstract
        self.keyword = keyword
        self.Crawled_Articles_total = 0
        self.Crawled_Articles_data = 0
        self.title = title
        self.total_articles_found = 0
        self.article_id = ""
        self.next_cursor_mark = "*"
        self.no_of_articles = ARTICLE_PER_PAGE
        self.start_year = start_year
        self.end_year = end_year
        self.page = 1
        self.start_urls = [self.get_start_url()]
        logger.info(
            "Spider initialized with title: %s, keyword: %s, abstract: %s, "
            "start_year: %s, end_year: %s",
            title,
            keyword,
            abstract,
            start_year,
            end_year,
        )

    def get_start_url(self):
        url = (
            f"https://europepmc.org/api/get/articleApi?query="
            f"(TITLE:{self.title} AND {self.keyword} AND ABSTRACT:{self.abstract}) "
            f"AND (FIRST_PDATE:[{self.start_year} TO {self.end_year}])"
            f"&cursorMark={self.next_cursor_mark}&format=json&pageSize={self.no_of_articles}"
        )
        logger.info("Constructed start URL: %s", url)
        return url

    def get_start_url(self):
        # date formate 1900-05-31
        print(self.next_cursor_mark)
        return f"https://europepmc.org/api/get/articleApi?query=(TITLE:%22{self.title}%22%20AND%20%22{self.keyword}%22%20AND%20ABSTRACT:%22{self.abstract}%22)%20AND%20(FIRST_PDATE:%5B{self.start_year}%20TO%20{self.end_year}%5D)&cursorMark={self.next_cursor_mark}&format=json&pageSize={self.no_of_articles}&sort=Relevance&synonym=FALSE"

    def get_article_data(self):
        return f"https://europepmc.org/api/get/articleApi?query=(EXT_ID:{self.article_id})&format=json&resultType=core"

    def parse(self, response):
        try:
            logger.info("Parsing page %d", self.page)
            json_response = response.json()
            if self.page == 1:
                self.total_articles_found = json_response.get("hitCount", 0)
                logger.info("Total articles found: %d", self.total_articles_found)

            # Handle next cursor mark and articles parsing
            articles = json_response.get("resultList", {}).get("result", [])
            if not articles:
                logger.warning("No articles found on page %d", self.page)
                return

            for article_id in articles:
                self.article_id = article_id["id"]
                yield response.follow(
                    self.get_article_data(), self.parse_article, headers=HEADERS
                )

            # Update next cursor mark
            self.next_cursor_mark = json_response.get("nextCursorMark")
            if not self.next_cursor_mark:
                logger.info("No more pages to crawl")
                return

            # Continue crawling
            self.page += 1
            yield response.follow(self.get_start_url(), self.parse, headers=HEADERS)

        except Exception as e:
            logger.error("Error while parsing page %d: %s", self.page, e, exc_info=True)

    def parse_article(self, response):
        global output_dataframe
        self.Crawled_Articles_total += 1
        try:
            author_data_all = response.json()
            logger.info(
                "Processing article response, total articles crawled: %d",
                self.Crawled_Articles_total,
            )

            # Iterate over authors in the response
            for author_items in author_data_all.get("resultList", {}).get("result", []):
                article_title = author_items.get("title", "Unknown Title")
                logger.debug("Processing article: %s", article_title)

                # Check if affiliation exists and if it contains an email address
                for author_info in author_items.get("authorList", {}).get("author", []):
                    try:
                        affiliation_data = author_info.get(
                            "authorAffiliationDetailsList", {}
                        ).get("authorAffiliation", [])
                        if not affiliation_data:
                            logger.debug(
                                "No affiliation data found for author: %s",
                                author_info.get("fullName", "Unknown"),
                            )
                            continue

                        affiliation = affiliation_data[0].get("affiliation", "")
                        author_name = author_info.get("fullName", "Unknown Name")
                        if affiliation and "@" in affiliation:
                            self.Crawled_Articles_data += 1
                            logger.info(
                                "Valid affiliation with email found for author: %s",
                                author_name,
                            )

                            email, affiliation = email_affiliation(affiliation)
                            # print("=" * 80)
                            # print("affiliation:", affiliation)
                            # print("email:", email)
                            # print("=" * 80)
                            if process_email(
                                email, EMAIL_CHARACTER_DISALLOWED, EMAIL_ID_DISALLOWED
                            ) and not contains_high_unicode(author_name):
                                author_data = [
                                    {
                                        "title": article_title,
                                        "author_name": author_name,
                                        "email": email,
                                        "affiliation": affiliation,
                                    }
                                ]

                                # Add data to DataFrame
                                df_dictionary = pd.DataFrame(author_data)
                                output_dataframe = pd.concat(
                                    [output_dataframe, df_dictionary],
                                    ignore_index=True,
                                )
                                logger.info(
                                    "Added valid author data for: %s", author_name
                                )
                            else:
                                logger.warning(
                                    "Skipping invalid email or name for author: %s, email: %s",
                                    author_name,
                                    email,
                                )
                                author_data = [
                                    {
                                        "title": article_title,
                                        "author_name": author_name,
                                        "email": email,
                                        "affiliation": affiliation,
                                    }
                                ]
                                logger.debug("Invalid author data: %s", author_data)
                        else:
                            logger.debug(
                                "No valid email in affiliation for author: %s",
                                author_name,
                            )
                    except Exception as e:
                        logger.error(
                            "Error processing author info: %s, Error: %s",
                            author_info,
                            e,
                            exc_info=True,
                        )

        except Exception as e:
            logger.error("Error processing article response: %s", e, exc_info=True)


def run_spider(title, keyword, abstract, start_date, end_date):
    logger.info(
        "Starting spider with title: %s, keyword: %s, abstract: %s, start_date: %s, end_date: %s",
        title,
        keyword,
        abstract,
        start_date,
        end_date,
    )
    global output_dataframe
    try:
        process = CrawlerProcess(get_project_settings())
        process.crawl(
            PubMedSpider,
            title=title,
            keyword=keyword,
            abstract=abstract,
            start_year=start_date,
            end_year=end_date,
        )
        process.start()
        # Output path and execution of email sender
        output_path = OUTPUT_PATH_TEMPLATE.format(
            keyword=keyword,
            title=title,
            abstract=abstract,
            start_year=start_date.split("-")[0],
            end_year=end_date.split("-")[0],
        )
        output_dataframe.drop_duplicates().to_csv(output_path, mode="a", index=False)
        logger.info("Scraping completed. Output saved to: %s", output_path)
        # TODO
        # try:
        #     logger.info("Executing mailer script")
        #     subprocess.run(["python3", PYTHON_MAILER_SCRIPT, output_path], check=True)
        # except subprocess.CalledProcessError as e:
        #     logger.error("Mailer script failed with error: %s", e)
        # except Exception as e:
        #     logger.error("Error executing mailer: %s", e, exc_info=True)

    except Exception as e:
        logger.error("Error running spider: %s", e, exc_info=True)


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
