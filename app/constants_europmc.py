from config import get_config
import os

EMAIL_CHARACTER_DISALLOWED = [
    ",",
    "/",
    ";",
    ":",
    "(",
    ")",
    "&",
    "%",
    "?",
    "[",
    "]",
    "  ",
    "+",
]
EMAIL_ID_DISALLOWED = ["contact", "connect", "journals", "permission", "admin", "info"]

# Scrapy Default Configurations
ARTICLE_PER_PAGE = 100
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.199 Safari/537."
}

OUTPUT_PATH_TEMPLATE = "/Users/vedanths/Projects/researchScraper/output/EuroPMC_Output_{keyword}_{title}_{abstract}_{start_year}_to_{end_year}.csv"
