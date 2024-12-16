import re

import pandas as pd


def print_processing_data(total, crawled, extracted):
    print("=" * 80)
    print(f"Total articles crawled: {crawled}")
    print(f"Total articles extracted: {extracted}")
    print(f"Total number of articles to be crawled: {total}")
    print("=" * 80)


def contains_high_unicode(text):
    return any(ord(char) >= 132 for char in text)


def process_email(email, disallowed_chars, disallowed_ids):
    for char in disallowed_chars:
        if char in email:
            return False

    if re.match(r"^\d+@[\w.-]+\.\w+$", email):
        return False

    for id_filter in disallowed_ids:
        if id_filter in email:
            return False

    return True


def email_affiliation(affiliation):
    email_pattern = r"(\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b)"
    email = re.findall(email_pattern, affiliation)
    email = "".join(email)

    # Remove the email from the affiliation
    affiliation = affiliation.replace(email, "").strip()

    # Remove specific phrases
    affiliation = affiliation.replace("Electronic address:", "").strip()

    # Remove trailing punctuation
    if affiliation.endswith("."):
        affiliation = affiliation[:-1]

    return email, affiliation
