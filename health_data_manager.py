import time
from datetime import datetime

import gspread
import utilities

class HealthDataManager:
    def __init__(self, config_file: str) -> None:
        self.users = []
        self.config = utilities.read_config(config_file)
        self.init_work_sheets()

    def init_work_sheets(self) -> None:
        credential_path = self.config["sheetCredentialPath"]
        book_title = self.config["workBook"]
        service_account = gspread.service_account(filename = credential_path)
        work_book = service_account.open(book_title)
        self.vital_sign_sheet = work_book.worksheet(self.config["vitalSignTab"])
        self.user_sheet = work_book.worksheet(self.config["userTab"])
        self.users = self.user_sheet.get_all_records()

    def request_to_vital_signs(self, request_args) -> list:
        # [user_name, heart_beat, blood_oxygen, body_temperature]
        user_id = request_args.get("uid")
        heart_beat = float(request_args.get("hb"))
        blood_oxygen = float(request_args.get("bo"))
        body_temperature = float(request_args.get("bt"))
        user_name = self.get_user_name(user_id)
        return [user_name, heart_beat,blood_oxygen, body_temperature]

    def insert_vital_signs(self, vital_signs: list) -> None:
        timestamp = time.time()
        str_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        vital_signs.extend([timestamp, str_datetime])
        self.vital_sign_sheet.insert_row(vital_signs, 2)

    def get_health_judge(self, vital_signs: list) -> str:
        # vital_signs[1] == 心跳    vital_signs[2] == 血氧    vital_signs[3] == 體溫
        if vital_signs[1] <= 0 or vital_signs[2] <= 0 or vital_signs[3] <= 0:
            return "" # 任一數據小於等於零代表無效數據，不做健康異常的警報

        judge = ""
        if vital_signs[1] > 120 or vital_signs[1] < 60:
            judge += f"\n每秒心跳{vital_signs[1]}下"
        if vital_signs[2] > 110 or vital_signs[2] < 90:
            judge += f"\n血氧濃度{vital_signs[2]}%"
        if vital_signs[3] > 38 or vital_signs[3] < 35:
            judge += f"\n體溫攝氏{vital_signs[3]}度"
        if judge:
            judge = "偵測到健康狀況異常：" + judge
        return judge

    def create_user(self, user_id: str, user_name: str) -> None:
        if self.user_exists(user_id):
            return
        try:
            self.user_sheet.insert_row([user_id, user_name], 2)
            self.users = self.user_sheet.get_all_records()
        except:
            raise Exception("無法新增使用者")

    def user_exists(self, user_id: str) -> bool:
        for user in self.users:
            if user["ID"] == user_id:
                return True
        return False

    def get_user_name(self, user_id: str) -> str:
        for user in self.users:
            if user["ID"] == user_id:
                return user["暱稱"]
        return "debug-user"

    def get_vital_sign(self, user_id: str, sign_type: str) -> float:
        cell = self.user_sheet.find(user_id)
        vital_signs = self.vital_sign_sheet.row_values(cell.row)
        if sign_type == "心跳":
            return vital_signs[1]
        elif sign_type == "血氧":
            return vital_signs[2]
        elif sign_type == "體溫":
            return vital_signs[3]
        else:
            return vital_signs
