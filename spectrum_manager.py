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
        # [ts, v, b, g, y, o, r]
        dt = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        timestamp = request_args.get("ts")
        violet = float(request_args.get("v"))
        blue = float(request_args.get("b"))
        green = float(request_args.get("g"))
        yellow = float(request_args.get("y"))
        orange = float(request_args.get("o"))
        red = float(request_args.get("r"))
        return [dt, timestamp, violet, blue, green, yellow, orange, red]

    def insert_spectrum_record(self, spectrum_record: list) -> None:
        self.spectrum_sheet.append_row(spectrum_record)
