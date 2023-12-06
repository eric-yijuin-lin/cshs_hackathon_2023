import utilities
import gspread

class HealthDataManager:
    def __init__(self, config_file: str) -> None:
        self.config = utilities.read_config(config_file)
        self.init_work_sheet()

    def init_work_sheet(self) -> None:
        print("aaa", self.config)
        credential_path = self.config["sheetCredentialPath"]
        book_name = self.config["workBookName"]
        tab_name = self.config["sheetTabName"]
        service_account = gspread.service_account(filename = credential_path)
        work_book = service_account.open(book_name)
        self.worksheet = work_book.worksheet(tab_name)

    def append_health_row(self, data_row: list) -> None:
        try:
            # [user_name, heart_beat, blood_oxygen, body_temperature]
            self.worksheet.append_row([
                data_row[0],
                float(data_row[1]),
                float(data_row[2]),
                float(data_row[3]),
            ])
        except Exception as ex:
            print("failed to append health data: ", ex)

    def get_user_name(self, user_id: str) -> str:
        return "debug-user"
