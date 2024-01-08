import random
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
        print(value_text, answer)

        if value_text != answer:
            return 0
        multiplier = 0
        for c in question:
            if c == '+':
                multiplier += 1
            elif c == '-':
                multiplier += 2
            elif c == '*':
                multiplier += 3
            elif c == '/':
                multiplier += 5
        return 100 * multiplier

    def draw_card(self) -> dict:
        all_cards = self.game_sheet.get_all_records()
        card = random.choice(all_cards)
        max_atk = card["最大攻擊力"]
        max_def = card["最大防禦力"]
        card["攻擊力"] = random.randint(max_atk//2, max_atk)
        card["防禦力"] = random.randint(max_def//2, max_def)
        return card