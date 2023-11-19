from bs4 import BeautifulSoup
from config import URL, HEADERS, LOG_FILE
from requests import get
import re

from crawler import WebCrawler


def downloadAllImagesFromSite(url: str = None) -> bool:
    spider = WebCrawler(url=url)


def requestWebsiteUrl() -> dict:
    # Check if url is valid
    url = input("Enter valid URL of website: ")
    code = get(url=url, headers=HEADERS)
    regex = '^((http|https)://)[-a-zA-Z0-9@:%._\\+~#?&//=]{2,256}\\.[a-z]{2,6}\\b([-a-zA-Z0-9@:%._\\+~#?&//=]*)$'
    r = re.compile(regex)
    if re.search(r, url) and code.status_code == 200:
        log(f"Ok: {url} is valid.")
        return {"isValid": True, "url": url}
    else:
        log(f"Error: {url} is not valid.")
        return {"isValid": False, "url": url}


def initScrappingWebsite(url: str) -> None:
    # Remove from string any unneccesary strings
    end = url.find(".")
    end = url.find("/", end)
    if end == -1:
        end = len(url)
    url = url[:end]
    global URL
    URL = url


def initLoggerFile(filename: str) -> None:
    with open(filename, "w", encoding="utf-8") as F:
        F.write("#INIT LOGGER FILE#")
        F.write("\n")


def log(message: str):
    print(message)
    with open(LOG_FILE, "a", encoding="utf-8") as F:
        F.write(message)
        F.write("\n")


if __name__ == "__main__":
    initLoggerFile(LOG_FILE)
    #rwu = requestWebsiteUrl()
    #if rwu["isValid"]:
    if True:
        initScrappingWebsite(URL)
        if downloadAllImagesFromSite(url=URL):
            log(f"Ok: Successfully scrapped all images from website: {URL}.")
        else:
            log(f"Error(downloadAllImagesFromSite(rwu['url'])): Could not load images from {URL}.")
    else:
        log(f"Error(if rwu['isValid']:): This url, {rwu['url']}, is invalid.")
