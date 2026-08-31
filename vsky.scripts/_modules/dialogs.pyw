# vsky.scripts\modules\dialogs.pyw

class ConsolePrinter:
    def __init__(self, prefix="[VSKY]"):
        self.prefix = prefix
        print(f"{self.prefix} Модули подключены, реально")

    def log(self, message):
        """Выводит сообщение в консоль Cinema 4D"""
        print(f"{self.prefix} {message}")