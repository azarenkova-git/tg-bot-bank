from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, BotCommand, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters, CallbackContext, \
    CallbackQueryHandler

from src.bank_bot_logic import BankBotLogic
from src.models import TransactionModel
from src.session import setup_session


def with_auth(func):
    """Декоратор, который проверяет, что пользователь зарегистрирован в системе"""

    async def wrapper(self, update: Update, ctx: ContextTypes):
        if self._logic.user_exists_by_tg_id(update.effective_user.id):
            await func(self, update, ctx)
        else:
            await self._reply_with_contact_request(update, ctx)

    return wrapper


class BankBot:
    def __init__(self, token: str, persist=False):
        self._session = setup_session(persist)
        self._logic = BankBotLogic(self._session)

        self._commands = [
            BotCommand("start", "Начать работу с ботом"),
            BotCommand("deposit", "<amount> Пополнить баланс"),
            BotCommand("balance", "Проверить баланс"),
            BotCommand("withdraw", "<amount> Снять деньги"),
            BotCommand("transactions", "Посмотреть список транзакций"),
            BotCommand("help", "Показать справку"),
        ]

        self._app = ApplicationBuilder().token(token).build()

        handlers = [
            CommandHandler("start", self._reply_with_contact_request),
            CommandHandler("deposit", self._make_deposit),
            CommandHandler("balance", self._show_balance),
            CommandHandler("withdraw", self._make_withdraw),
            CommandHandler("transactions", self._list_transactions),
            CommandHandler("help", self._show_help),
            CallbackQueryHandler(self._list_transactions),
            MessageHandler(filters.CONTACT, self._handle_received_contact),
        ]

        for handler in handlers:
            self._app.add_handler(handler)

    def start_bot(self):
        self._app.bot.set_my_commands(self._commands)
        print("Сервер запущен")
        self._app.run_polling(allowed_updates=Update.ALL_TYPES)
        print("Сервер остановлен")
        self._session.close()

    async def _reply_with_contact_request(self, update: Update, _: ContextTypes) -> None:
        """Запрос контактов пользователя"""

        contact_keyboard = KeyboardButton("Предоставьте номер телефона", request_contact=True)
        reply_markup = ReplyKeyboardMarkup([[contact_keyboard]], resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text("Пожалуйста, пройдите аутентификацию", reply_markup=reply_markup)

    async def _handle_received_contact(self, update: Update, _: ContextTypes) -> None:
        """Обработка полученных контактов пользователя"""

        contact = update.message.contact
        self._logic.find_or_register_user(contact.phone_number, contact.first_name, update.effective_user.id)
        await update.message.reply_text(f"Аутентификация пройдена")

    @with_auth
    async def _make_deposit(self, update: Update, context: CallbackContext) -> None:
        """Внесение депозита"""

        try:
            sum_arg = context.args[0] if context.args else None

            if sum_arg is None:
                await update.message.reply_text("Пожалуйста, введите сумму пополнения. Использование: /deposit <сумма>")
                return

            sum_value = int(sum_arg)

            if sum_value <= 0:
                await update.message.reply_text("Пожалуйста, введите положительное число для суммы.")
            else:
                await update.message.reply_text(f"Депозит в размере {sum_value} успешно принят.")

            self._logic.deposit(update.effective_user.id, sum_value)

        except (IndexError, ValueError):
            await update.message.reply_text("Пожалуйста, введите сумму пополнения. Использование: /deposit <сумма>")

    @with_auth
    async def _make_withdraw(self, update: Update, context: CallbackContext) -> None:
        """Вывод средств"""

        try:
            sum_arg = context.args[0] if context.args else None

            if sum_arg is None:
                await update.message.reply_text("Пожалуйста, введите сумму снятия. Использование: /withdraw <сумма>")
                return

            sum_value = int(sum_arg)

            if sum_value <= 0:
                await update.message.reply_text("Пожалуйста, введите положительное число для суммы.")
            else:
                await update.message.reply_text(f"Снятие в размере {sum_value} успешно принято.")

            self._logic.withdraw(update.effective_user.id, sum_value)

        except (IndexError, ValueError):
            await update.message.reply_text("Пожалуйста, введите сумму снятия. Использование: /withdraw <сумма>")

    @with_auth
    async def _show_balance(self, update: Update, _: ContextTypes) -> None:
        """Вывод баланса пользователя"""

        balance = self._logic.get_balance(update.effective_user.id)
        await update.message.reply_text(f"Ваш баланс: {balance}")

    def _paginate_transactions(self, transactions: list[TransactionModel], page: int, per_page=5):
        start = page * per_page
        end = start + per_page
        return transactions[start:end]

    @with_auth
    async def _list_transactions(self, update: Update, _: ContextTypes) -> None:
        """Вывод списка транзакций пользователя"""

        transactions = self._logic.get_transactions(update.effective_user.id)

        if update.callback_query:
            await update.callback_query.answer()

        page = int(update.callback_query.data) if update.callback_query and update.callback_query.data.isdigit() else 0
        items = self._paginate_transactions(transactions, page)

        message_text = "Нет транзакций" if len(transactions) == 0 else "\n".join([f"{item.date}: ${item.amount}" for item in items])

        keyboard = [
            [InlineKeyboardButton("Previous", callback_data=str(page - 1)),
             InlineKeyboardButton("Next", callback_data=str(page + 1))]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        if update.callback_query:
            await update.callback_query.edit_message_text(text=message_text, reply_markup=reply_markup)
        else:
            await update.message.reply_text(text=message_text, reply_markup=reply_markup)

    @with_auth
    async def _show_help(self, update: Update, _: ContextTypes) -> None:
        """Вывод справки"""

        help_text = "Доступные команды:\n"

        for command in self._commands:
            help_text += f"/{command.command} - {command.description}\n"

        await update.message.reply_text(help_text)
