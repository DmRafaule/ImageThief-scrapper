import os
import time
import random
import string
import json
from zipfile import ZipFile, ZIP_DEFLATED

from bs4 import BeautifulSoup
import requests

import config as C
from Utils.utils import toDomainURL, log


def GetRandomString(length: int) -> str:
    letters = string.ascii_letters
    random_string = ''.join(random.choice(letters) for i in range(length))
    return random_string


class ImgScrapper:
    url = str
    domain = str

    def __init__(self, url: str, noisy: bool = True):
        self.url = url
        self.domain = toDomainURL(url)

    def scrape(self, *urls):
        start = time.time()
        status = "Ok"

        with open(C.DATA_FILE, "r", encoding="utf-8") as F:
            data = json.load(F)
            data["links_number"] = len(urls)
            data["internal_links"] = urls
        with open(C.DATA_FILE, "w", encoding="utf-8") as F:
            json.dump(data, F, indent=2)

        log("Status: Start collecting images.", C.LOG_FILE)
        length = len(urls)
        for link in urls[self.__dataGetCurrentLink():]:
            if type(link) is not str:
                l_url = link["url"]
            else:
                l_url = link
            current = self.__dataGetCurrentLink()
            try:
                if type(link) is not str:
                    page = requests.get(self.url + l_url, headers=C.HEADERS)
                else:
                    page = requests.get(l_url, headers=C.HEADERS)
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
            else:
                log(f"{status}: Scraped {current}/{length} ({l_url})", C.LOG_FILE)
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
        log(f"Result: Total scraping execution time ({end - start}) sec..", C.LOG_FILE)
        log(f"Result: Total scrapped images {self.__dataGetImgsNumber()} in {self.__dataGetPageNumber()} pages", C.LOG_FILE)
        self.__dataSetCurrentLink(0)

    def download(self):
        log("Status: Start downloading images.", C.LOG_FILE)
        # Make a slice of list of images
        imgs = self.__dataGetImgs()[self.__dataGetCurrentImg():]
        for img_path in imgs:
            try:
                img = requests.get(img_path, headers=C.HEADERS)
                status = "OK"
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
            else:
                current = self.__dataGetCurrentImg()
                length = self.__dataGetImgsNumber()
                filename = img_path[img_path.rfind("/"):]
                with open(C.IMAGES_FOLDER + "/" + filename, "wb") as F:
                    log(f"{status}: Saved {current}/{length}  {filename}", C.LOG_FILE)
                    F.write(img.content)
                    self.__dataSetCurrentImg(current + 1)

    def zip(self) -> None:
        log("Status: Start archiving.", C.LOG_FILE)
        filenames = next(os.walk(C.IMAGES_FOLDER), (None, None, []))[2]
        with ZipFile(C.RESULT_FOLDER + "/" + self.domain + ".zip", "w", ZIP_DEFLATED) as Z:
            for file in filenames:
                full_filename = "./" + C.IMAGES_FOLDER + "/" + file
                log(f"Ok: Archived {full_filename}", C.LOG_FILE)
                Z.write(full_filename)

    def getImgs(self) -> []:
        return self.__dataGetImgs()

    def __dataGetPageNumber(self) -> int:
        with open(C.DATA_FILE, "r", encoding="utf-8") as F:
            data = json.load(F)
            return data['links_number']

    def __dataGetImgsNumber(self) -> int:
        with open(C.DATA_FILE, "r", encoding="utf-8") as F:
            data = json.load(F)
            return data['imgs_number']

    def __dataGetImgs(self) -> []:
        with open(C.DATA_FILE, "r", encoding="utf-8") as F:
            data = json.load(F)
            return data['imgs']

    def __dataGetCurrentImg(self) -> int:
        with open(C.DATA_FILE, "r", encoding="utf-8") as F:
            data = json.load(F)
            return data["current_img"]

    def __dataSetCurrentImg(self, index: int):
        with open(C.DATA_FILE, "r", encoding="utf-8") as F:
            data = json.load(F)
            data["current_img"] = index
        with open(C.DATA_FILE, "w", encoding="utf-8") as F:
            json.dump(data, F, indent=2)

    def __dataGetCurrentLink(self) -> int:
        with open(C.DATA_FILE, "r", encoding="utf-8") as F:
            data = json.load(F)
            return data["current_link_to_scrape"]

    def __dataSetCurrentLink(self, index: int):
        with open(C.DATA_FILE, "r", encoding="utf-8") as F:
            data = json.load(F)
            data["current_link_to_scrape"] = index
        with open(C.DATA_FILE, "w", encoding="utf-8") as F:
            json.dump(data, F, indent=2)

    def __dataImgInsert(self, link: str, status_code: int):
        with open(C.DATA_FILE, "r", encoding="utf-8") as F:
            data = json.load(F)
            for dataLink in data["imgs"]:
                if link == dataLink:
                    break
            else:
                log(f"Ok: Found new img ({link})", C.LOG_FILE)
                data["imgs_number"] = data["imgs_number"] + 1
                data["imgs"].append(link)
                with open(C.DATA_FILE, "w", encoding="utf-8") as Fw:
                    # Make sure that data will be dumped.
                    # Sometime Keyboard interruption break a data file
                    try:
                        json.dump(data, Fw, indent=2)
                    except Exception:
                        json.dump(data, Fw, indent=2)
