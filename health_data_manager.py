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

    def get_vital_signs(self, request_args) -> list:
        # [user_name, heart_beat, blood_oxygen, body_temperature]
        user_id = request_args.get("uid")
        heart_beat = float(request_args.get("hb"))
        blood_oxygen = float(request_args.get("bo"))
        body_temperature = float(request_args.get("bt"))
        user_name = self.get_user_name(user_id)
        return [user_name, heart_beat,blood_oxygen, body_temperature]

    def append_vital_signs(self, vital_signs: list) -> None:
        try:
            self.worksheet.append_row(vital_signs)
        except Exception as ex:
            print("failed to append health data: ", ex)

    def get_health_judge(self, vital_signs: list) -> str:
        judge = ""
        if vital_signs[1] > 120 or vital_signs[1] < 80:
            judge += f"\n每秒心跳{vital_signs[1]}下"
        if vital_signs[2] > 110 or vital_signs[2] < 90:
            judge += f"\n血氧濃度{vital_signs[1]}%"
        if vital_signs[3] > 38 or vital_signs[3] < 35:
            judge += f"\n體溫攝氏{vital_signs[1]}度"
        if judge:
            judge = "偵測到健康狀況異常：" + judge
        return judge
    
    def create_user(self, user_id: str, user_name: str) -> None:
        if self.user_exists(user_id):
            return
        try:   
            self.user_sheet.append_row([user_id, user_name])
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
