from enum import Enum
import os
import json
import time
from datetime import date

from bs4 import BeautifulSoup
import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Encoding": "identify",
    "DNT": "1",
    "Connection": "keep-alive",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
}
VERSION = "05"


class LinkType(Enum):
    INTERNAL = 1
    EXTERNAL = 2


class WebCrawler:
    url = str
    domain = str
    _scanTime = int
    _dataFile = "data.json"
    _logFile = "log.txt"
    _workDirectory = "WebCrawler_"

    def __init__(self, url: str, noisy: bool = True):
        if not noisy:
            self.__log = self.__log_q
        start = time.time()
        self.url = url
        self.__initWorkDirectory()
        self._dataFile = self._workDirectory + "/" + self._dataFile
        self._logFile = self._workDirectory + "/" + self._logFile
        self._scanTime = str(date.today())
        self.__initLogFile()
        if not os.path.exists(self._dataFile):
            self.__initDataFile()
        current = self.__dataGetCurrentLink()
        if current == 0:
            self.__crawlSitemap(url + "/" + "sitemap.xml")
            self.__log(f"Status: Found {len(self.__dataGetLinks(LinkType.INTERNAL))} internal links.")
        links = self.__dataGetLinks(LinkType.INTERNAL)
        if not current >= len(links):
            self.__crawl(self.url + links[current]['url'])

        end = time.time()
        self.__log(f"Result: Total internal links ({len(self.__dataGetLinks(LinkType.INTERNAL))})")
        self.__log(f"Result: Total external links ({len(self.__dataGetLinks(LinkType.EXTERNAL))})")
        self.__log(f"Result: Total crawling execution time ({end - start}) sec..")

    def __crawl(self, url: str):
        status = "Ok"
        try:
            if self.__crawlable(url):
                page = requests.get(url=url, headers=HEADERS, timeout=1)
            else:
                raise NotImplementedError
        except requests.exceptions.HTTPError as e:
            self.__log(f"Error: {e.args[0]}.")
            status = "NotOk"
        except requests.exceptions.ReadTimeout:
            self.__log("Error: Time out.")
            status = "NotOk"
        except requests.exceptions.ConnectionError as e:
            self.__log(f"Error: Something wrong with connection. {e}")
            status = "NotOk"
        except requests.exceptions.RequestException as e:
            self.__log(f"Error: While trying make request. {e}")
            status = "NotOk"
        except NotImplementedError:
            self.__log("Error: Could parse file with such extention name.")
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
            self.__log_a(f"{status}: {current}/{self.__dataGetLinkNumber()} {url}")
            if not current >= self.__dataGetLinkNumber():
                self.__crawl(self.url + links[current]['url'])

    # Walk through sitemap file
    def __crawlSitemap(self, sitemap: str):
        status = "Ok"
        self.__log("Status: Checking sitemap.")
        try:
            if self.__crawlable(sitemap):
                page = requests.get(url=sitemap, headers=HEADERS, timeout=1)
            else:
                # Maybe make your own Exception class
                raise NotImplementedError
        except requests.exceptions.HTTPError as e:
            self.__log(f"Error: {e.args[0]}.")
            status = "NotOk"
        except requests.exceptions.ReadTimeout as e:
            self.__log(f"Error: Time out. {e}")
            status = "NotOk"
        except requests.exceptions.ConnectionError as e:
            self.__log(f"Error: Something wrong with connection. {e}")
            status = "NotOk"
        except requests.exceptions.RequestException as e:
            self.__log(f"Error: While trying make request. {e}")
            status = "NotOk"
        except NotImplementedError:
            self.__log("Error: Could parse file with such extention name.")
            status = "NotOk"
        else:
            soup = BeautifulSoup(page.text, 'xml')
            for sm in soup.find_all('loc'):
                if ".xml" in sm.text:
                    self.__log(f"{status}: New sub sitemap ({sm.text})")
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
        )
        if url.endswith(notcrawlable_ext):
            return False
        return True

    def __dataClenUpDuplicates(self):
        self.__log("Ok: Remove duplicated urls.")
        with open(self._dataFile, "r", encoding="utf-8") as F:
            links = json.load(F)
            # Remove duplicates by converting list to set and then back to list again
            links[self.__linkTypeToStr(LinkType.INTERNAL)] = list(set(links[self.__linkTypeToStr(LinkType.INTERNAL)]))
        with open(self._dataFile, "w", encoding="utf-8") as F:
            json.dump(links, F, indent=2)

    def __dataIsEmpty(self) -> bool:
        type = self.__linkTypeToStr(LinkType.INTERNAL)
        with open(self._dataFile, "r", encoding="utf-8") as F:
            data = json.load(F)
            if data[type]:
                self.__log("Status: Data file is not empty")
                return False
            else:
                self.__log("Status: Data file is empty")
                return True

    def __dataGetLinks(self, type: LinkType) -> []:
        type = self.__linkTypeToStr(type)
        with open(self._dataFile, "r", encoding="utf-8") as F:
            data = json.load(F)
            return data[type]

    def __dataGetCurrentLink(self) -> int:
        with open(self._dataFile, "r", encoding="utf-8") as F:
            data = json.load(F)
            return data["current_link"]

    def __dataSetCurrentLink(self, index: int):
        with open(self._dataFile, "r", encoding="utf-8") as F:
            data = json.load(F)
            data["current_link"] = index
        with open(self._dataFile, "w", encoding="utf-8") as F:
            json.dump(data, F, indent=2)

    def __dataGetLinkNumber(self) -> int:
        with open(self._dataFile, "r", encoding="utf-8") as F:
            data = json.load(F)
            return data['link_number']

    def __dataLinkInsert(self, link: str, type: LinkType, status_code: int):
        # Before use type var. It is neccessary to convert it to string
        type = self.__linkTypeToStr(type)
        with open(self._dataFile, "r", encoding="utf-8") as F:
            data = json.load(F)
            for dataLink in data[type]:
                if link == dataLink['url']:
                    break
            else:
                self.__log(f"Status: Found new link ({link})")
                if type == self.__linkTypeToStr(LinkType.INTERNAL):
                    data["link_number"] += 1
                data[type].append({'url': link, 'status': status_code, 'scan_date': self._scanTime})
                with open(self._dataFile, "w", encoding="utf-8") as Fw:
                    # Make sure that data will be dumped. 
                    # Sometime Keyboard interruption break a data file
                    try:
                        json.dump(data, Fw, indent=2)
                    except Exception:
                        json.dump(data, Fw, indent=2)

    def __initWorkDirectory(self):
        end = self.url.find(".")
        end = self.url.find("/", end)
        if end == -1:
            end = len(self.url)
        self.domain = self.url[self.url.rindex('/') + 1:end]
        self._workDirectory += self.domain
        try:
            os.mkdir(self._workDirectory)
            self.__log(f"Target:{self.domain}\n", False)
            self.__log(f"Ok: Directory {self._workDirectory} created.", False)
        except OSError:
            self.__log(f"Error(__initWorkDirectory): Directory by name {self._workDirectory} already exist.", False)

    def __initLogFile(self):
        print(f"Ok: Init log file ({self._logFile})")
        with open(self._logFile, "w", encoding="utf-8") as F:
            F.write("LOG FILE. WEBCRAWLER")
            F.write("\n")

    def __initDataFile(self):
        self.__log(f"Ok: Init data file ({self._dataFile})")
        with open(self._dataFile, "w", encoding="utf-8") as F:
            json.dump({
                "version": "#WEBCRAWLER_" + VERSION + "#",
                "domain": self.domain,
                "link_number": 0,
                "current_link": 0,
                "external_links": [],
                "internal_links": [],
            }, F, indent=2)

    def __linkTypeToStr(self, ltype: LinkType) -> str:
        result = ""
        if LinkType.INTERNAL == ltype:
            result = "internal_links"
        else:
            result = "external_links"
        return result

    def __log(self, message: str, toConsole: bool = True):
        if toConsole:
            print(message)
        with open(self._logFile, "a", encoding="utf-8") as F:
            F.write(message)
            F.write("\n")

    def __log_a(self, message: str):
        print(message)

    def __log_q(self, message: str, toConsole: bool = True):
        pass

    def getAllInternalLinks(self) -> dict:
        return self.__dataGetLinks(LinkType.INTERNAL)

    def getAllExternalLinks(self) -> dict:
        return self.__dataGetLinks(LinkType.EXTERNAL)
