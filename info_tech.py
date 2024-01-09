import random
from datetime import datetime
import gspread
import utilities

class MathGame:
    def __init__(self, config_file: str) -> None:
        self.operators = ['+', '-', '*', '/']
        self.config = utilities.read_config(config_file)
        credential_path = self.config["sheetCredentialPath"]
        book_title = self.config["workBook"]
        service_account = gspread.service_account(filename = credential_path)
        work_book = service_account.open(book_title)
        self.game_sheet = work_book.worksheet(self.config["gameTab"])
        self.log_sheet = work_book.worksheet(self.config["logTab"])

    def get_question(self) -> str:
        level = random.randint(1, 2)
        question = ""
        for i in range(level):
            num = random.randint(1, 99)
            op = random.choice(self.operators)
            question = question + str(num) + str(op)
        num = random.randint(1, 99)
        question += str(num)
        return question

    def get_reward(self, question, answer) -> int:
        value = round(eval(question), 2)
        value_text = str(value)
        if value_text != answer:
            return 0

        multiplier = 0
        for c in question:
            if c == '+':
                multiplier += 1
            elif c == '-':
                multiplier += 2
            elif c == '*':
                multiplier += 5
            elif c == '/':
                multiplier += 10
        return 100 * multiplier

    def draw_card(self, user: str) -> dict:
        all_cards = self.game_sheet.get_all_records()
        card = random.choice(all_cards)
        max_atk = card["最大攻擊力"]
        max_def = card["最大防禦力"]
        card["攻擊力"] = random.randint(max_atk // 2, max_atk)
        card["防禦力"] = random.randint(max_def // 2, max_def)
        self.insert_log(user, card)
        return card
    
    def insert_log(self, user: str, card: dict) -> None:
        log_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            log_text = f"{user} 抽到了攻擊力 {card['攻擊力']} 防禦力 {card['防禦力']} 的 {card['卡片名稱']}"
            self.log_sheet.insert_row([log_time, log_text], 2)
        except Exception as ex:
            print("failed to inse log: ", ex)