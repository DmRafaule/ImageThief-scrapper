import os
import re
import json
import requests
import functools
import datetime
from config import VERBOSE


def initFile(filename: str) -> None:
    if not os.path.exists(filename):
        with open(filename, "w", encoding="utf-8") as F:
            pass
    else:
        with open(filename, "a", encoding="utf-8") as F:
            F.write(f"""

=== New session ({datetime.datetime.now().isoformat(sep='|',timespec='minutes') }) ===

                    """)


def initFolder(filename: str) -> None:
    if not os.path.exists(filename):
        os.mkdir(filename)


def initDataFile(data: any, filename: str) -> None:
    if not os.path.exists(filename):
        with open(filename, "w", encoding="utf-8") as F:
            json.dump(data, F, indent=2)


def checkURL(url: str) -> dict:
    # Check if url is valid
    code = requests.get(url)
    regex = '^((http|https)://)[-a-zA-Z0-9@:%._\\+~#?&//=]{2,256}\\.[a-z]{2,6}\\b([-a-zA-Z0-9@:%._\\+~#?&//=]*)$'
    r = re.compile(regex)
    if re.search(r, url) and code.status_code == 200:
        status = True
    else:
        status = False
    return status


def toMinimalURL(url: str) -> bool:
    # Remove from string any unneccesary strings
    end = url.find(".")
    end = url.find("/", end)
    if end == -1:
        end = len(url)
    url = url[:end]
    return url


def toDomainURL(url: str) -> str:
    end = url.find(".")
    end = url.find("/", end)
    if end == -1:
        end = len(url)
    return url[url.rindex('/') + 1:end]


if VERBOSE:
    def log(message: str, file: str = None):
        print(message)
        if file is not None:
            with open(file, "a", encoding="utf-8") as F:
                F.write(message)
                F.write("\n")

    def debug(message: str = "", file: str = None):
        def decorator_repeat(func):
            @functools.wraps(func)
            def wrapper_debug(*args, **kwargs):
                log(message, file)
                value = func(*args, **kwargs)
                return value
            return wrapper_debug
        return decorator_repeat
else:
    def log(message: str, file: str = None):
        if file is not None:
            with open(file, "a", encoding="utf-8") as F:
                F.write(message)
                F.write("\n")

    def debug(message="", file=None):
        def decorator_repeat(func):
            @functools.wraps(func)
            def wrapper_debug(*args, **kwargs):
                value = func(*args, **kwargs)
                return value
            return wrapper_debug
        return decorator_repeat
