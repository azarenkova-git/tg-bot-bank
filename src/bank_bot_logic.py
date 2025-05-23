from datetime import datetime

from sqlalchemy import desc
from sqlalchemy.orm import Session

from src.models import UserModel, TransactionModel


class BankBotLogic:
    """Класс, реализующий логику ("бекенд") бота"""

    _session: Session

    def __init__(self, session: Session):
        self._session = session

    def register_user(self, phone_number: str, name: str, tg_user_id: str) -> UserModel:
        """
        Находит и возвращает пользователя по номеру телефона, либо регистрирует нового пользователя
        """

        user = UserModel(phone_number=phone_number, name=name, tg_user_id=tg_user_id)
        self._session.add(user)
        self._session.commit()

        return user

    def find_user_by_tg_id(self, tg_user_id: str) -> UserModel:
        """Находит пользователя по tg_id"""

        return self._session.query(UserModel).filter(UserModel.tg_user_id == tg_user_id).first()

    def find_user_by_phone_number(self, phone_number: str) -> UserModel:
        """Находит пользователя по номеру телефона"""

        return self._session.query(UserModel).filter(UserModel.phone_number == phone_number).first()

    def user_exists_by_tg_id(self, tg_user_id: str) -> bool:
        """Проверка, что пользователь зарегистрирован в системе"""

        return self.find_user_by_tg_id(tg_user_id) is not None

    def deposit(self, tg_user_id: int, amount: int) -> None:
        """Пополнение баланса пользователя"""

        user = self.find_user_by_tg_id(tg_user_id)
        user.balance += amount

        transaction = TransactionModel(amount=amount, user_id=user.id, date=datetime.now())
        self._session.add(transaction)

        self._session.commit()

    def withdraw(self, tg_user_id: int, amount: int) -> None:
        """Снятие денег со счета пользователя"""

        user = self.find_user_by_tg_id(tg_user_id)
        user.balance -= amount

        transaction = TransactionModel(amount=-amount, user_id=user.id, date=datetime.now())
        self._session.add(transaction)

        self._session.commit()

    def send_money(self, sender_tg_user_id: int, recipient_phone_number: str, amount: int) -> None:
        """Перевод денег от одного пользователя другому"""

        sender = self.find_user_by_tg_id(sender_tg_user_id)
        recipient = self.find_user_by_phone_number(recipient_phone_number)

        sender.balance -= amount
        recipient.balance += amount

        transaction = TransactionModel(amount=-amount, user_id=sender.id, date=datetime.now())
        self._session.add(transaction)

        transaction = TransactionModel(amount=amount, user_id=recipient.id, date=datetime.now())
        self._session.add(transaction)

        self._session.commit()

    def get_balance(self, tg_user_id: int) -> int:
        """Возвращает баланс пользователя"""

        user = self.find_user_by_tg_id(tg_user_id)
        return user.balance

    def get_transactions(self, tg_user_id: int) -> list[TransactionModel]:
        """Возвращает список транзакций пользователя"""

        user = self.find_user_by_tg_id(tg_user_id)

        return self._session.query(TransactionModel) \
            .filter(TransactionModel.user_id == user.id) \
            .order_by(desc(TransactionModel.date)) \
            .all()

    def delete_user(self, tg_user_id: int) -> None:
        """Удаляет пользователя из системы"""

        user = self.find_user_by_tg_id(tg_user_id)
        self._session.delete(user)
        self._session.commit()
