import requests


import logging
import xml.etree.ElementTree as ET


KIPRIS_URL = (
    "http://plus.kipris.or.kr/kipo-api/kipi/patUtiModInfoSearchSevice/getAdvancedSearch"
)

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
    "query",
]

PAGE_SIZE = 500


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


class QueryFetcher(Fetcher):
    def fetch(self) -> dict:
        self.logger.info("Starting fetch operation")
        self.logger.info(f"PAGE: {self.page_index}")

        query = self.params.get("query", "")
        patent = self.params.get("patent", True)
        utility = self.params.get("utility", False)
        lastvalue = self.params.get("lastvalue", "R")

        clsExpression = "((P<IN>CLS))" if patent and not utility else None
        lstExpression = f"(({lastvalue}<IN>LST))"

        prefixExpression = ""
        if clsExpression:
            prefixExpression += clsExpression
            prefixExpression += "*"

        prefixExpression += lstExpression

        try:
            res = requests.post(
                "https://www.kipris.or.kr/kpat/resulta.do",
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
                    "Referer": "https://www.kipris.or.kr/search/searchResult.do",
                    "Origin": "https://www.kipris.or.kr",
                },
                data={
                    "expression": query,
                    "queryText": query,
                    "numPerPage": PAGE_SIZE,
                    "numPageLinks": "2",
                    "currentPage": self.page_index,
                    "sortField": "RANK",
                    "sortState": "Desc",
                    "prefixExpression": prefixExpression,
                },
            )
            res.raise_for_status()
        except Exception as e:
            self.logger.error(f"HTTP error occurred: {e}")
            raise

        if res.json().get("resultCode", "") != "00":
            raise Exception(f"KIPRIS API request failed")

        self.page_index += 1
        return res.json()
