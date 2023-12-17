import asyncio

from src.bank_bot import BankBot

# Токен бота. Аналогичный можно получить у @BotFather
TOKEN = "6962534079:AAEVMfyQYwFk1PjGhgyjAlmPu_fqdw94sPs"


def main() -> None:
    bot = BankBot(TOKEN)
    bot.start_bot()


if __name__ == '__main__':
    main()
