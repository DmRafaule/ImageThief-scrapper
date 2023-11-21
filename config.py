from enum import Enum


class ScrappingMode(Enum):
    # Scrape full website, without exceptions
    FULL = 0,
    # First scrape fill be like in FULL mode,
    # But in next iterations will be check hash sums
    # And scrape only different ones
    MONITORE = 1,
    # Scrape only single page
    SINGLE_PAGE = 2,


# Target URL
URL = "https://www.historiesofhumanity.com"
# Mode in which this script gonna work
MODE = ScrappingMode.FULL
# Is program gonna make a lot of output to terminal ?
VERBOSE = True
# Headers for parser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Encoding": "identify",
    "DNT": "1",
    "Connection": "keep-alive",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
}
# Where results will be found
RESULT_FOLDER = "Results"
# Folder for Images
IMAGES_FOLDER = "imgs"
# Where logs stored,
LOG_FILE = "log.txt"
# Where all data stored
DATA_FILE = "data.json"
# Name of program
NAME = "ImageStealer"
# Version of program
VERSION = "07"
# Creator of this program
AUTHOR = "Tim the Webmaster"
# Where it can be found
SOURCE_WEBSITE = "https://timthewebmaster.com"
# Template to init when creating DATA_FILE
DATA_JSON_TEMPLATE = {
    "version": VERSION,
    "target": URL,
    "current_link_to_crawl": 0,
    "links_number": 0,
    "external_links": [],
    "internal_links": [],
    "current_link_to_scrape": 0,
    "current_img": 0,
    "imgs_number": 0,
    "imgs": [],
}
