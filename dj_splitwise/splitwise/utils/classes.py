from decimal import Decimal


class Transaction:
    def __init__(self, _from: int, to: int, amount: Decimal):
        self._from = _from
        self.to = to
        self.amount = amount

    def to_dict(self):
        return {
            '_from': self._from,
            'to': self.to,
            'amount': self.amount
        }

    def __str__(self):
        return f'Transaction[user(id={self._from}) -> user(id={self.to})] = {self.amount}'
