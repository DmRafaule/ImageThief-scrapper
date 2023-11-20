from config import HEADERS, LOG_FILE
import requests
import re

from crawler import WebCrawler
from scrapper import ImgScrapper


def downloadAllImagesFromSite(
        url: str = None,
        noisy: bool = True) -> None:

    spider = WebCrawler(url, noisy)
    links_to_scrapp = spider.getAllInternalLinks()

    scrapper = ImgScrapper(url, noisy)
    scrapper.scrape(*links_to_scrapp)
    scrapper.download()
    scrapper.zip()


def requestWebsiteUrl() -> dict:
    # Check if url is valid
    url = input("Enter valid URL of website: ")
    code = requests.get(url=url, headers=HEADERS)
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
    return url


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
    rwu = requestWebsiteUrl()
    if rwu["isValid"]:
        downloadAllImagesFromSite(initScrappingWebsite(rwu['url']), noisy=True)
    else:
        log(f"Error(if rwu['isValid']:): This url, {rwu['url']}, is invalid.")
