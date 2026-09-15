from enum import Enum


class Locale(Enum):
    """
    Defines supported locales / domains for job sources.
    Used to determine request structure and parsing logic.
    """

    CANADA_ENGLISH = 1
    CANADA_FRENCH = 2
    USA_ENGLISH = 3
    UK_ENGLISH = 4
    FRANCE_FRENCH = 5
    GERMANY_GERMAN = 6


class JobStatus(Enum):
    """
    Job lifecycle statuses.
    NOTE: these are the only valid values for entries in 'status' in CSV exports.
    """

    UNKNOWN = 1
    NEW = 2
    ARCHIVE = 3
    INTERVIEWING = 4
    INTERVIEWED = 5
    REJECTED = 6
    ACCEPTED = 7
    DELETE = 8
    INTERESTED = 9
    APPLIED = 10
    APPLY = 11
    OLD = 12


class JobField(Enum):
    """
    Canonical job fields used across scrapers, filters, and storage.
    """

    TITLE = 0
    COMPANY = 1
    LOCATION = 2
    DESCRIPTION = 3
    KEY_ID = 4
    URL = 5
    LOCALE = 6
    QUERY = 7
    PROVIDER = 8
    STATUS = 9
    SCRAPE_DATE = 10
    SHORT_DESCRIPTION = 11
    POST_DATE = 12
    RAW = 13
    TAGS = 14
    WAGE = 15
    REMOTENESS = 16


class Remoteness(Enum):
    """
    Defines the level of remoteness for a job.
    """

    UNKNOWN = 1  # invalid / not determined
    IN_PERSON = 2
    TEMPORARILY_REMOTE = 3
    PARTIALLY_REMOTE = 4
    FULLY_REMOTE = 5
    ANY = 6


class DuplicateType(Enum):
    """
    Defines how a job is considered a duplicate.
    Used to determine deduplication behavior.
    """

    KEY_ID = 0
    EXISTING_TFIDF = 1
    NEW_TFIDF = 2


class Provider(Enum):
    """
    Job source providers.
    """

    INDEED = 1
    GLASSDOOR = 2
    MONSTER = 3


class DelayAlgorithm(Enum):
    """
    Delay algorithms for human-like behavior.
    """

    CONSTANT = 1
    SIGMOID = 2
    LINEAR = 3


class ScrapeStatus(Enum):
    """
    Status of a scraping run.
    Used by runners, scrapers, and UI.
    """

    OK = "ok"
    CAPTCHA = "captcha"
    ERROR = "error"
    STOPPED = "stopped"
