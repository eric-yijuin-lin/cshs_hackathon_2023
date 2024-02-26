import time
from datetime import datetime
from math import sqrt

import gspread
import utilities

class SpectrumDataManager:
    def __init__(self, config_file: str) -> None:
        self.users = []
        self.hospitals = []
        self.config = utilities.read_config(config_file)
        self.init_work_sheets()

    def init_work_sheets(self) -> None:
        credential_path = self.config["sheetCredentialPath"]
        book_title = self.config["workBook"]
        service_account = gspread.service_account(filename = credential_path)
        work_book = service_account.open(book_title)
        self.spectrum_sheet = work_book.worksheet(self.config["spectrumTab"])

    def spectrum_from_request(self, request_args) -> list:
        dt = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        spectrum_text = request_args.get("s")
        spectrum_list = []
        for text in spectrum_text.split(";"):
            if not text:
                continue
            values = text.split(",")
            spectrum_list.append([
                dt,             # server datetime
                int(values[0]), # time stamp
                float(values[1]), # violet
                float(values[2]), # blue
                float(values[3]), # green
                float(values[4]), # yellow
                float(values[5]), # orange
                float(values[6])  # red
            ])
        return spectrum_list

    def insert_spectrum_record(self, spectrum_record: list) -> None:
        self.spectrum_sheet.append_rows(spectrum_record)
