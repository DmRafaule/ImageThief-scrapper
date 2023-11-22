from enum import Enum
import json
import time

from bs4 import BeautifulSoup
import requests

import config as C
from Utils.utils import log


class LinkType(Enum):
    INTERNAL = 1
    EXTERNAL = 2


class WebCrawler:
    url = str
    domain = str

    def __init__(self, url: str, noisy: bool = True):
        start = time.time()
        self.url = url
        current = self.__dataGetCurrentLink()
        if current == 0:
            self.__crawlSitemap(url + "/" + "sitemap.xml")
            log(f"Ok: Found {len(self.__dataGetLinks(LinkType.INTERNAL))} internal links.", C.LOG_FILE)
        links = self.__dataGetLinks(LinkType.INTERNAL)
        length = len(links)
        if length == 0:
            self.__crawl(self.url)
        if not current >= length:
            self.__crawl(self.url + links[current]['url'])

        end = time.time()
        log(f"Result: Total internal links ({len(self.__dataGetLinks(LinkType.INTERNAL))})", C.LOG_FILE)
        log(f"Result: Total external links ({len(self.__dataGetLinks(LinkType.EXTERNAL))})", C.LOG_FILE)
        log(f"Result: Total crawling execution time ({end - start}) sec..", C.LOG_FILE)

    def __crawl(self, url: str):
        status = "Ok"
        try:
            if self.__crawlable(url):
                page = requests.get(url, headers=C.HEADERS, timeout=1)
            else:
                raise NotImplementedError
        except requests.exceptions.HTTPError as e:
            log(f"Error: {e.args[0]}.", C.LOG_FILE)
            status = "NotOk"
        except requests.exceptions.ReadTimeout:
            log("Error: Time out.", C.LOG_FILE)
            status = "NotOk"
        except requests.exceptions.ConnectionError as e:
            log(f"Error: Something wrong with connection. {e}", C.LOG_FILE)
            status = "NotOk"
        except requests.exceptions.RequestException as e:
            log(f"Error: While trying make request. {e}", C.LOG_FILE)
            status = "NotOk"
        except NotImplementedError:
            log("Error: Could parse file with such extention name.", C.LOG_FILE)
            status = "NotOk"
        else:
            soup = BeautifulSoup(page.text, 'lxml')
            for link in soup.find_all("a"):
                # Does our link even has 'href' attribute and it is not 'anchor' link
                if link.has_attr('href') and "#" not in link['href']:
                    if link['href'].startswith(('/')):
                        self.__dataLinkInsert(link['href'], LinkType.INTERNAL, page.status_code)
                    else:
                        if link['href'].startswith((self.url, self.url.replace("https", "http"), self.url.replace("http", "https"))):
                            self.__dataLinkInsert(link['href'].replace(self.url, ""), LinkType.INTERNAL, page.status_code)
                        else:
                            if link['href'].startswith(("https://", "http://")):
                                self.__dataLinkInsert(link['href'], LinkType.EXTERNAL, page.status_code)
        finally:
            self.__dataSetCurrentLink(self.__dataGetCurrentLink() + 1)
            current = self.__dataGetCurrentLink()
            links = self.__dataGetLinks(LinkType.INTERNAL)
            log(f"{status}: {current}/{self.__dataGetLinkNumber()} {url}", C.LOG_FILE)
            if not current >= self.__dataGetLinkNumber():
                self.__crawl(self.url + links[current]['url'])

    # Walk through sitemap file
    def __crawlSitemap(self, sitemap: str):
        status = "Ok"
        log("Status: Checking sitemap.", C.LOG_FILE)
        try:
            if self.__crawlable(sitemap):
                page = requests.get(url=sitemap, headers=C.HEADERS, timeout=1)
            else:
                # Maybe make your own Exception class
                raise NotImplementedError
        except requests.exceptions.HTTPError as e:
            log(f"Error: {e.args[0]}.", C.LOG_FILE)
            status = "NotOk"
        except requests.exceptions.ReadTimeout as e:
            log(f"Error: Time out. {e}", C.LOG_FILE)
            status = "NotOk"
        except requests.exceptions.ConnectionError as e:
            log(f"Error: Something wrong with connection. {e}", C.LOG_FILE)
            status = "NotOk"
        except requests.exceptions.RequestException as e:
            log(f"Error: While trying make request. {e}", C.LOG_FILE)
            status = "NotOk"
        except NotImplementedError:
            log("Error: Could parse file with such extention name.", C.LOG_FILE)
            status = "NotOk"
        else:
            soup = BeautifulSoup(page.text, 'xml')
            for sm in soup.find_all('loc'):
                if ".xml" in sm.text:
                    log(f"{status}: New sub sitemap ({sm.text})", C.LOG_FILE)
                    self.__crawlSitemap(sm.text)
                else:
                    self.__dataLinkInsert(sm.text.replace(self.url, ""), LinkType.INTERNAL, page.status_code)

    def __crawlable(self, url: str) -> bool:
        notcrawlable_ext = (
            ".zip",
            ".mp4",
            ".mp3",
            ".js",
            ".css",
            ".tar",
            ".7z",
            ".png",
            ".jpg",
            ".webp",
            ".svg",
            ".gz",
            ".ico",
            ".pdf",
            ".fp2",
            ".epub",
            ".txt",
        )
        if url.endswith(notcrawlable_ext):
            return False
        return True

    def __dataClenUpDuplicates(self):
        log("Ok: Remove duplicated urls.", C.LOG_FILE)
        with open(C.DATA_FILE, "r", encoding="utf-8") as F:
            links = json.load(F)
            # Remove duplicates by converting list to set and then back to list again
            links[self.__linkTypeToStr(LinkType.INTERNAL)] = list(set(links[self.__linkTypeToStr(LinkType.INTERNAL)]))
        with open(C.DATA_FILE, "w", encoding="utf-8") as F:
            json.dump(links, F, indent=2)

    def __dataIsEmpty(self) -> bool:
        type = self.__linkTypeToStr(LinkType.INTERNAL)
        with open(C.DATA_FILE, "r", encoding="utf-8") as F:
            data = json.load(F)
            if data[type]:
                log("Status: Data file is not empty", C.LOG_FILE)
                return False
            else:
                log("Status: Data file is empty", C.LOG_FILE)
                return True

    def __dataGetLinks(self, type: LinkType) -> []:
        type = self.__linkTypeToStr(type)
        with open(C.DATA_FILE, "r", encoding="utf-8") as F:
            data = json.load(F)
            return data[type]

    def __dataGetCurrentLink(self) -> int:
        with open(C.DATA_FILE, "r", encoding="utf-8") as F:
            data = json.load(F)
            return data["current_link_to_crawl"]

    def __dataSetCurrentLink(self, index: int):
        with open(C.DATA_FILE, "r", encoding="utf-8") as F:
            data = json.load(F)
            data["current_link_to_crawl"] = index
        with open(C.DATA_FILE, "w", encoding="utf-8") as F:
            json.dump(data, F, indent=2)

    def __dataGetLinkNumber(self) -> int:
        with open(C.DATA_FILE, "r", encoding="utf-8") as F:
            data = json.load(F)
            return data['links_number']

    def __dataLinkInsert(self, link: str, type: LinkType, status_code: int):
        # Before use type var. It is neccessary to convert it to string
        type = self.__linkTypeToStr(type)
        with open(C.DATA_FILE, "r", encoding="utf-8") as F:
            data = json.load(F)
            for dataLink in data[type]:
                if link == dataLink['url']:
                    break
            else:
                log(f"Ok: Found new link ({link})", C.LOG_FILE)
                if type == self.__linkTypeToStr(LinkType.INTERNAL):
                    data["links_number"] += 1
                data[type].append({
                    'url': link,
                })
                with open(C.DATA_FILE, "w", encoding="utf-8") as Fw:
                    # Make sure that data will be dumped. 
                    # Sometime Keyboard interruption break a data file
                    try:
                        json.dump(data, Fw, indent=2)
                    except Exception:
                        json.dump(data, Fw, indent=2)

    def __linkTypeToStr(self, ltype: LinkType) -> str:
        result = ""
        if LinkType.INTERNAL == ltype:
            result = "internal_links"
        else:
            result = "external_links"
        return result

    def getAllInternalLinks(self) -> dict:
        return self.__dataGetLinks(LinkType.INTERNAL)

    def getAllExternalLinks(self) -> dict:
        return self.__dataGetLinks(LinkType.EXTERNAL)
