import os
import time
import random
import string
import json
from zipfile import ZipFile, ZIP_DEFLATED
from datetime import date

from bs4 import BeautifulSoup
import requests

VERSION = "05"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Encoding": "identify",
    "DNT": "1",
    "Connection": "keep-alive",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
}


def GetRandomString(length: int) -> str:
    letters = string.ascii_letters
    random_string = ''.join(random.choice(letters) for i in range(length))
    return random_string


class ImgScrapper:
    url = str
    domain = str
    _scanTime = int
    _dataFile = "data.json"
    _logFile = "log.txt"
    _workDirectory = "ImgScrapper_result_"

    def __init__(self, url: str, noisy: bool = True):
        if not noisy:
            self.__log = self.__log_q
        self.url = url
        end = self.url.find(".")
        end = self.url.find("/", end)
        if end == -1:
            end = len(self.url)
        self.domain = self.url[self.url.rindex('/') + 1:end]
        self.__initWorkDirectory(self.domain)
        self.__initLogFile()
        self._dataFile = self._workDirectory + "/" + self._dataFile
        self._logFile = self._workDirectory + "/" + self._logFile
        self._scanTime = str(date.today())
        self.__initDataFile()

    def scrape(self, url: str, *urls):
        start = time.time()
        status = "Ok"

        with open(self._dataFile, "r", encoding="utf-8") as F:
            data = json.load(F)
            data["page_number"] = len(urls)
            data["page_links"] = urls
        with open(self._dataFile, "w", encoding="utf-8") as F:
            json.dump(data, F, indent=2)

        self.__log("Status: Start collecting images.")
        length = len(urls)
        for link in urls[self.__dataGetCurrentLink():]:
            current = self.__dataGetCurrentLink()
            try:
                page = requests.get(self.url + link["url"], headers=HEADERS)
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
            else:
                self.__log_a(f"{status}: {current}/{length} ({link['url']})")
                soup = BeautifulSoup(page.text, 'lxml')
                for img_tag in soup.find_all('img'):
                    if img_tag.has_attr('src'):
                        if img_tag['src'].startswith(("http")):
                            img_path = img_tag['src']
                        else:
                            img_path = self.url + img_tag['src']

                        for img_one in self.__dataGetImgs():
                            if img_tag['src'] in img_one:
                                break
                        else:
                            self.__dataImgInsert(img_path, 200)
                self.__dataSetCurrentLink(self.__dataGetCurrentLink() + 1)
        end = time.time()
        self.__log(f"Result: Total scraping execution time ({end - start}) sec..")
        self.__log(f"Result: Total scrapped images {self.__dataGetImgsNumber()} in {self.__dataGetPageNumber()} pages")

    def download(self):
        self.__log("Status: Start downloading images.")
        # Make a slice of list of images
        imgs = self.__dataGetImgs()[self.__dataGetCurrentImg():]
        for img_path in imgs:
            try:
                img = requests.get(img_path["url"], headers=HEADERS)
                status = "Saved"
            except requests.exceptions.HTTPError as e:
                self.__log(f"Error: {e.args[0]}.")
                status = "Not saved"
            except requests.exceptions.ReadTimeout:
                self.__log("Error: Time out.")
                status = "Not saved"
            except requests.exceptions.ConnectionError as e:
                self.__log(f"Error: Something wrong with connection. {e}")
                status = "Not saved"
            except requests.exceptions.RequestException as e:
                self.__log(f"Error: While trying make request. {e}")
                status = "Not saved"
            else:
                current = self.__dataGetCurrentImg()
                length = self.__dataGetImgsNumber()
                filename = img_path["url"][img_path["url"].rfind("/"):]
                with open(self._workDirectory + "/" + filename, "wb") as F:
                    self.__log_a(f"{status}: {current}/{length}  ({filename})")
                    F.write(img.content)
                    self.__dataSetCurrentImg(current + 1)

    def zip(self) -> None:
        self.__log("Status: Start archiving.")
        filenames = next(os.walk(self._workDirectory), (None, None, []))[2]
        with ZipFile(self.domain + ".zip", "w", ZIP_DEFLATED) as Z:
            for file in filenames:
                full_filename = "./" + self._workDirectory + "/" + file
                self.__log(f"Ok: Archived {full_filename}")
                Z.write(full_filename)

    def __dataGetPageNumber(self) -> int:
        with open(self._dataFile, "r", encoding="utf-8") as F:
            data = json.load(F)
            return data['page_number']

    def __dataGetImgsNumber(self) -> int:
        with open(self._dataFile, "r", encoding="utf-8") as F:
            data = json.load(F)
            return data['imgs_number']

    def __dataGetImgs(self) -> []:
        with open(self._dataFile, "r", encoding="utf-8") as F:
            data = json.load(F)
            return data['imgs']

    def __dataGetCurrentImg(self) -> int:
        with open(self._dataFile, "r", encoding="utf-8") as F:
            data = json.load(F)
            return data["current_img"]

    def __dataSetCurrentImg(self, index: int):
        with open(self._dataFile, "r", encoding="utf-8") as F:
            data = json.load(F)
            data["current_img"] = index
        with open(self._dataFile, "w", encoding="utf-8") as F:
            json.dump(data, F, indent=2)

    def __dataGetCurrentLink(self) -> int:
        with open(self._dataFile, "r", encoding="utf-8") as F:
            data = json.load(F)
            return data["current_page"]

    def __dataSetCurrentLink(self, index: int):
        with open(self._dataFile, "r", encoding="utf-8") as F:
            data = json.load(F)
            data["current_page"] = index
        with open(self._dataFile, "w", encoding="utf-8") as F:
            json.dump(data, F, indent=2)

    def __dataImgInsert(self, link: str, status_code: int):
        with open(self._dataFile, "r", encoding="utf-8") as F:
            data = json.load(F)
            for dataLink in data["imgs"]:
                if link == dataLink['url']:
                    break
            else:
                self.__log(f"Status: Found new img ({link})")
                data["imgs_number"] = data["imgs_number"] + 1
                data["imgs"].append({'url': link, 'status': status_code, 'scan_date': self._scanTime})
                with open(self._dataFile, "w", encoding="utf-8") as Fw:
                    # Make sure that data will be dumped. 
                    # Sometime Keyboard interruption break a data file
                    try:
                        json.dump(data, Fw, indent=2)
                    except Exception:
                        json.dump(data, Fw, indent=2)

    def __initWorkDirectory(self, name: str = None):
        if name is None:
            self._workDirectory += GetRandomString(10)
        else:
            self._workDirectory += name
        try:
            os.mkdir(self._workDirectory)
            self.__log(f"Target:{self._workDirectory}\n", False)
            self.__log(f"Ok: Directory {self._workDirectory} created.", False)
        except OSError:
            self.__log(f"Error(__initWorkDirectory): Directory by name {self._workDirectory} already exist.", False)

    def __initLogFile(self):
        print(f"Ok: Init log file ({self._logFile})")
        with open(self._logFile, "w", encoding="utf-8") as F:
            F.write("LOG FILE. IMGSCRAPPER")
            F.write("\n")

    def __initDataFile(self):
        if not os.path.exists(self._dataFile):
            self.__log(f"Ok: Init data file ({self._dataFile})")
            with open(self._dataFile, "w", encoding="utf-8") as F:
                json.dump({
                    "version": "#IMGSCRAPPER_" + VERSION + "#",
                    "current_page": 0,
                    "page_number": 0,
                    "page_links": [],
                    "current_img": 0,
                    "imgs_number": 0,
                    "imgs": [],
                }, F, indent=2)

    def __log(self, message: str, toConsole: bool = True):
        if toConsole:
            print(message)
        with open(self._logFile, "a", encoding="utf-8") as F:
            F.write(message)
            F.write("\n")

    def __log_q(self, message: str, toConsole: bool = True):
        pass

    def __log_a(self, message: str):
        print(message)
