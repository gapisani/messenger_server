class Log:
    def __init__(self, message, chat_ = None):
        self.message = message
        self.chat_ = chat_
    def successfully(self):
        print(f"\033[32m[SUCCESSFULLY] {self.message}\033[0m")
    def log(self):
        print(f"[LOG] {self.message}")
    def warn(self):
        print(f"\033[33m[WARNING] {self.message}\033[0m")
    def error(self):
        print(f"\033[31m[ERROR] {self.message}\033[0m")
    def chat(self):
        print(f"[CHAT {self.chat_}] {self.message}")
