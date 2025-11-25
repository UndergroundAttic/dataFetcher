import csv
import json
import logging
import os
import xml.etree.ElementTree as ET
from typing import Generator, Tuple

CSV_COLUMNS = ["applicationNumber", "abstractContent"]
METADATA_KEYS = [
    "inventionTitle",
    "ipcNumber",
    "applicationDate",
    "applicantName",
    "query",
]


class Parser:
    logger = None
    parsed_set = set()

    metadata: dict = {}
    csv_path: str | None = None
    json_path: str | None = None

    countCutoff: int | None = None

    def __init__(
        self,
        logger: logging.Logger,
        output_dir: str,
    ):
        self.logger = logger
        self.output_dir = output_dir

    def set_name(self, name: str):
        self.parsed_set = set()
        self.csv_path = os.path.join(self.output_dir, f"{name}.csv")
        self.json_path = os.path.join(self.output_dir, f"{name}_metadata.json")
        self.metadata = (
            json.load(open(self.json_path, "r", encoding="utf-8"))
            if os.path.exists(self.json_path)
            else {}
        )
        for k in self.metadata.keys():
            self.parsed_set.add(k)

    def init_csv(self, headers: list[str]):
        with open(self.csv_path, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(headers)

    def parse(self, xml_tree: ET.ElementTree) -> bool:
        """Parse XML and return True if cutoff is met, False otherwise"""
        # Check if cutoff is already met before parsing
        if self.check_cutoff():
            self.logger.info("Cutoff already met before parsing, skipping")
            return True

        if not os.path.exists(self.csv_path):
            self.init_csv(CSV_COLUMNS)

        with open(self.csv_path, "a", encoding="utf-8", newline="") as csv_file:
            csv_writer = csv.writer(csv_file)

            has_data = False
            for appNum, metadata, abstract in self._datagen(xml_tree):
                has_data = True

                if appNum in self.parsed_set:
                    print(f"Skipping duplicate: {appNum}")
                    continue

                # Check if cutoff is met before adding record
                if self.check_cutoff():
                    with open(self.json_path, "w", encoding="utf-8") as json_file:
                        json.dump(
                            self.metadata, json_file, ensure_ascii=False, indent=4
                        )
                    return True

                csv_writer.writerow([appNum, abstract])
                self.metadata[appNum] = metadata
                self.parsed_set.add(appNum)
                print(appNum)

        with open(self.json_path, "w", encoding="utf-8") as json_file:
            json.dump(self.metadata, json_file, ensure_ascii=False, indent=4)

        # If no data was processed, treat as cutoff met
        if not has_data:
            self.logger.info("No data in fetch result, treating as cutoff met")
            return True

        return False

    def _datagen(
        self, xml: ET.ElementTree
    ) -> Generator[Tuple[str, dict, str], None, None]:
        root = xml.getroot()
        items = root.find("body").find("items")

        for item in items.findall("item"):
            application_number = item.findtext("applicationNumber")
            parsed_data = {key: item.findtext(key) for key in METADATA_KEYS}
            abstract = item.findtext("astrtCont", "")

            for k, v in parsed_data.items():
                if k in ["applicantName", "ipcNumber"]:
                    parsed_data[k] = v.split("|") if "|" in v else [v]

            yield application_number, parsed_data, abstract

    def set_cutoff(self, countCutoff: int | None):
        self.countCutoff = countCutoff
        self.logger.info(f"Cutoff set - countCutoff: {countCutoff}")

    def check_cutoff(self) -> bool:
        """Check if any cutoff condition is met"""
        # Check count cutoff
        if self.countCutoff is not None:
            if len(self.parsed_set) >= self.countCutoff:
                self.logger.info(
                    f"Count cutoff reached: {len(self.parsed_set)} records"
                )
                return True

        return False


class QueryParser(Parser):
    def parse(self, json_data: dict) -> bool:
        """Parse JSON and return True if cutoff is met, False otherwise"""
        # Check if cutoff is already met before parsing
        if self.check_cutoff():
            self.logger.info("Cutoff already met before parsing, skipping")
            return True

        if not os.path.exists(self.csv_path):
            self.init_csv(CSV_COLUMNS)

        with open(self.csv_path, "a", encoding="utf-8", newline="") as csv_file:
            csv_writer = csv.writer(csv_file)

            has_data = False
            for appNum, metadata, abstract in self._datagen(json_data):
                has_data = True

                if appNum in self.parsed_set:
                    print(f"Skipping duplicate: {appNum}")
                    continue

                # Check if cutoff is met before adding record
                if self.check_cutoff():
                    with open(self.json_path, "w", encoding="utf-8") as json_file:
                        json.dump(
                            self.metadata, json_file, ensure_ascii=False, indent=4
                        )
                    return True

                csv_writer.writerow([appNum, abstract])
                self.metadata[appNum] = metadata
                self.parsed_set.add(appNum)
                # print(appNum)

        with open(self.json_path, "w", encoding="utf-8") as json_file:
            json.dump(self.metadata, json_file, ensure_ascii=False, indent=4)

        # If no data was processed, treat as cutoff met
        if not has_data:
            self.logger.info("No data in fetch result, treating as cutoff met")
            return True

        return False

    def rm_tags(self, text: str) -> str:
        """Remove HTML tags from text"""
        import re

        clean = re.compile("<.*?>")
        return re.sub(clean, "", text)

    def _datagen(self, json_data: dict) -> Generator[Tuple[str, dict, str], None, None]:
        items: list[dict[str, str]] = json_data.get("resultList", [])

        for item in items:
            application_number = item.get("DOCID", "")
            parsed_data = {
                "inventionTitle": self.rm_tags(item.get("TLE", "")),
                "ipcNumber": item.get("IPC", "").split("|"),
                "applicationDate": item.get("AD", "").replace("-", ""),
                "applicantName": item.get("AP", "").split("|"),
                "backwardCitationCount": int(item.get("BCTC", "0")),
            }
            abstract = self.rm_tags(item.get("AB", ""))

            yield application_number, parsed_data, abstract
