import csv
import logging
import multiprocessing
import os
import time
import xml.etree.ElementTree as ET
from typing import Generator, Tuple


class Parser:
    logger = None
    return_queue = None
    parsed_set = set()

    datadir = None

    def __init__(
        self,
        return_queue: multiprocessing.Queue[ET.ElementTree],
        logger: logging.Logger,
        output_dir: str,
    ):
        self.return_queue = return_queue
        self.logger = logger
        self.datadir = output_dir

        self.csv_writer = csv.writer(
            open(
                os.path.join(self.datadir, "parsed_data.csv"),
                mode="w",
                newline="",
                encoding="utf-8",
            )
        )

    def init_csv(self, path: str, headers: list[str]):
        with open(path, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(headers)

    def append(self, path: str, data: dict[str, str]):
        if not os.path.exists(path):
            with open(path, mode="w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow([data.keys()])

        with open(path, mode="a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(data.values())

    def try_parse(self):
        while True:
            if self.return_queue.empty():
                time.sleep(0.2)
                continue

            xml_tree = self.return_queue.get()
            for appNum, metadata, abstract in self._datagen(xml_tree):
                if appNum in self.parsed_set:
                    continue
                self.parsed_set.add(appNum)

    def _datagen(
        self, xml: ET.ElementTree
    ) -> Generator[Tuple[str, dict, str], None, None]:
        root = xml.getroot()
        items = root.find("body").find("items")

        for item in items.findall("item"):
            application_number = item.findtext("applicationNumber")
            parsed_data = {
                "inventionTitle": item.findtext("inventionTitle"),
                "ipcNumber": item.findtext("ipcNumber"),
                "applicationDate": item.findtext("applicationDate"),
                "applicantName": item.findtext("applicantName"),
                "applicationDate": item.findtext("applicationDate"),
            }
            abstract = item.findtext("astrtCont", "")

            for k, v in parsed_data.items():
                if k in ["applicantName", "ipcNumber"]:
                    parsed_data[k] = v.split("|") if "|" in v else [v]

            yield application_number, parsed_data, abstract
