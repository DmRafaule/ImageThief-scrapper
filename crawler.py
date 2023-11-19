from enum import Enum
import os
import json
import time

from bs4 import BeautifulSoup
import requests

from config import HEADERS, VERSION


class LinkType(Enum):
    INTERNAL = 1
    EXTERNAL = 2


class WebCrawler:
    url = str
    domain = str
    _dataFile = "data.json"
    _logFile = "log.txt"
    _workDirectory = "WebCrawler_"

    def __init__(self, url: str):
        start = time.time()
        self.url = url
        self.__initWorkDirectory()
        self._dataFile = self._workDirectory + "/" + self._dataFile
        self._logFile = self._workDirectory + "/" + self._logFile
        self.__initLogFile()
        if not os.path.exists(self._dataFile):
            self.__initDataFile()
        # Get first, root one links, if database is empty
        if self.__dataIsEmpty():
            self.__crawlSitemap(url + "/" + "sitemap.xml")
            self.__log(f"Status: Found {len(self.__dataGetLinks(LinkType.INTERNAL))} internal links.")
            links = self.__dataGetLinks(LinkType.INTERNAL)
            current = self.__dataGetCurrentLink()
            self.__crawl(self.url + links[current])
        # Otherwise load data from database and continue
        else:
            links = self.__dataGetLinks(LinkType.INTERNAL)
            current = self.__dataGetCurrentLink()
            if not current >= len(links):
                self.__crawl(self.url + links[current])

        end = time.time()
        self.__log(f"Status: Total internal links ({len(self.__dataGetLinks(LinkType.INTERNAL))})")
        self.__log(f"Status: Total external links ({len(self.__dataGetLinks(LinkType.EXTERNAL))})")
        self.__log(f"Status: Total crawling execution time ({end - start}) sec..")

    def __crawl(self, url: str):
        page = requests.get(url=url, headers=HEADERS, timeout=5)
        soup = BeautifulSoup(page.text, 'lxml')
        for link in soup.find_all("a"):
            if link.has_attr('href'):
                if link['href'].startswith(('/')):
                    self.__dataLinkInsert(link['href'], LinkType.INTERNAL)
                else:
                    if link['href'].startswith((self.url, self.url.replace("https", "http"), self.url.replace("http", "https"))):
                        self.__dataLinkInsert(link['href'].replace(self.url, ""), LinkType.INTERNAL)
                    else:
                        if link['href'].startswith(("https://", "http://")):
                            self.__dataLinkInsert(link['href'], LinkType.EXTERNAL)
        self.__dataSetCurrentLink(self.__dataGetCurrentLink() + 1)
        current = self.__dataGetCurrentLink()
        links = self.__dataGetLinks(LinkType.INTERNAL)
        self.__log(f"Ok: {current}/{len(links)} {url}")
        if not current >= len(links):
            self.__crawl(self.url + links[current])

    # Walk through sitemap file
    def __crawlSitemap(self, sitemap: str):
        self.__log("Status: Checking sitemap.")
        page = requests.get(url=sitemap, headers=HEADERS)
        soup = BeautifulSoup(page.text, 'xml')
        for sm in soup.find_all('loc'):
            if ".xml" in sm.text:
                self.__log(f"Status: Found new sub sitemap ({sm.text})")
                self.__crawlSitemap(sm.text)
            else:
                self.__dataLinkInsert(sm.text.replace(self.url, ""), LinkType.INTERNAL)

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

    def __dataLinkInsert(self, link: str, type: LinkType):
        # Before use type var. It is neccessary to convert it to string
        type = self.__linkTypeToStr(type)
        with open(self._dataFile, "r", encoding="utf-8") as F:
            data = json.load(F)
            if link not in data[type]:
                self.__log(f"Status: Found new link ({link})")
                data[type].append(link)
                with open(self._dataFile, "w", encoding="utf-8") as Fw:
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

    def getAllInternalLinks(self):
        return self.__dataGetLinks(LinkType.INTERNAL)

    def getAllExternalLinks(self):
        return self.__dataGetLinks(LinkType.EXTERNAL)
