import requests


import logging
import os
import time
import xml.etree.ElementTree as ET


KIPRIS_URL = "http://plus.kipris.or.kr/kipo-api/kipi/patUtiModInfoSearchSevice/getAdvancedSearch"

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

PAGE_SIZE = 10


class Fetcher:
    params = {}
    page_index = 1
    service_key = ""
    logger = None

    def __init__(
        self,
        ServiceKey: str,
        logger: logging.Logger,
        **kwargs,
    ):
        self.service_key = ServiceKey
        self.logger = logger

        self.set_params(**kwargs)

    def fetch(self) -> ET.ElementTree:
        self.logger.info("Starting fetch operation")
        self.logger.info(f"PAGE: {self.page_index}")
        self.params["ServiceKey"] = self.service_key
        try:
            res = requests.get(
                KIPRIS_URL,
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

        # print(res.text)
        xml = ET.fromstring(res.text)

        if xml.find("header").find("successYN").text != "Y":
            resultMSG = xml.find("header").find("resultMsg").text
            raise Exception(f"KIPRIS API request failed: {resultMSG}")

        self.page_index += 1
        return ET.ElementTree(xml)

    def set_params(self, **kwargs):
        for k, v in kwargs.items():
            if k not in PARAM_AVAIL:
                continue
            self.params[k] = v

        self.logger.info(f"Parameters set: {self.params}")
        self.page_index = 1

    def reset(self):
        self.page_index = 1
