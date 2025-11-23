import requests


import logging
import multiprocessing
import os
import time
import xml.etree.ElementTree as ET


KIPRIS_BASE_URL = "https://plus.kipris.or.kr"
KIPRIS_PATH = "kipo-api/kipi/patUtiModInfoSearchSevice/getAdvancedSearch"

PARAM_AVAIL = [
    "word",
    "astrtCont",
    "inventionTitle",
    "ipcNumber",
    "patent",
    "utility",
    "lastvalue",
    "applicationDate",
    "ServiceKey",
]

PAGE_SIZE = 500


class Fetcher:
    params = {}
    page_index = 1
    service_key = ""
    return_queue = None
    logger = None

    target_end = 1

    def __init__(
        self,
        ServiceKey: str,
        return_queue: multiprocessing.Queue[ET.ElementTree],
        logger: logging.Logger,
        **kwargs,
    ):
        self.service_key = ServiceKey
        self.return_queue = return_queue
        self.logger = logger
        self.set_params(**kwargs)

    def try_fetch(self):
        while self.page_index < self.target_end:
            if self.return_queue.full():
                time.sleep(0.2)
                continue

            self.logger.info("Starting fetch operation")
            self.logger.info(f"PAGE: {self.params.get('pageNo', 1)}")
            self.params["ServiceKey"] = self.service_key
            try:
                res = requests.get(
                    os.path.join(KIPRIS_BASE_URL, KIPRIS_PATH),
                    params={
                        **self.params,
                        "pageNo": self.page_index,
                        "numOfRows": PAGE_SIZE,
                    },
                    timeout=30,
                )
                res.raise_for_status()
            except Exception as e:
                self.logger.error(f"HTTP error occurred: {e}")
                raise

            xml = ET.fromstring(res.text)

            if xml.find("header").find("successYN").text != "Y":
                resultMSG = xml.find("header").find("resultMsg").text
                raise Exception(f"KIPRIS API request failed: {resultMSG}")

            self.page_index += 1
            self.return_queue.put(ET.ElementTree(xml))

    def set_params(self, **kwargs):
        for k, v in kwargs.items():
            if k not in PARAM_AVAIL:
                continue
            self.params[k] = v

        self.logger.info(f"Parameters set: {self.params}")
        self.init_process()

    def set_page(self, page: int):
        self.params["pageNo"] = page
        self.logger.info(f"Page set to: {page}")
        self.init_process()

    def set_end(self, end: int):
        self.target_end = end
        self.logger.info(f"End page set to: {end}")

    def init_process(self):
        if self.process.is_alive():
            self.process.terminate()
        self.process = multiprocessing.Process(target=self.try_fetch, daemon=True)

    def run(self):
        self.process.start()
        self.process.join()
