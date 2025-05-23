import unittest

import pytest
from sqlalchemy.orm import Session

from src.bank_bot_logic import BankBotLogic
from src.models import UserModel, TransactionModel
from src.session import setup_session


class SnakeGameTests(unittest.TestCase):
    _session: Session
    _logic: BankBotLogic

    @pytest.fixture(autouse=True)
    def before_each(self):
        self._session = setup_session()
        self._logic = BankBotLogic(self._session)
        self._logic.register_user("1", "User 1", 1)
        self._logic.register_user("2", "User 2", 2)

        yield

        self._session.close()

    def test_user_creation(self):
        self.assertTrue(self._logic.user_exists_by_tg_id(1))

    def test_user_balance(self):
        self.assertEqual(self._logic.get_balance(1), 0)

    def test_user_deposit(self):
        self._logic.deposit(1, 100)
        self.assertEqual(self._logic.get_balance(1), 100)

    def test_user_withdraw(self):
        self._logic.withdraw(1, 50)
        self.assertEqual(self._logic.get_balance(1), -50)

    def test_transaction_creation(self):
        self._logic.deposit(1, 100)
        self._logic.withdraw(1, 100)
        self.assertEqual(len(self._logic.get_transactions(1)), 2)

    def test_send_money(self):
        self._logic.deposit(1, 100)
        self._logic.send_money(1, "2", 50)
        self.assertEqual(self._logic.get_balance(1), 50)
        self.assertEqual(self._logic.get_balance(2), 50)

    def test_user_deletion(self):
        self._logic.delete_user(1)
        self.assertFalse(self._logic.user_exists_by_tg_id(1))


if __name__ == "__main__":
    unittest.main()
