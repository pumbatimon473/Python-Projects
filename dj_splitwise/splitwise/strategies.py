from typing import List
from .utils import Transaction
from .utils import heap_push, heap_pop, is_smaller_balance
from .utils import validate_balance_sheet


class NMinusOneSettlementStrategy:
    def settle_up(self, balance_sheet: dict) -> List[Transaction]:
        """
        Gives a list of transactions, when executed will settle-up every user participating
        in the shared expenses.
        It will always suggest (N - 1) transactions for a group of N users

        :param balance_sheet: A dict of user to balance mapping; -ve balance indicated expense owed
        :return: List[Transaction]
        """
        print(':: LOG :: NMinusOneSettlementStrategy | settle_up ::')
        validate_balance_sheet(balance_sheet)
        print(':: balance_sheet | before ::', balance_sheet)
        N = len(balance_sheet)  # num of users participating in the expenses
        user_ids = list(balance_sheet.keys())
        transactions = list()
        for n in range(N - 1):
            amount = balance_sheet.get(user_ids[n])
            amount_next = balance_sheet.get(user_ids[n + 1])
            if amount > 0:  # nth user should receive the amount from (n + 1)th user
                amount_next += amount
                balance_sheet[user_ids[n + 1]] = amount_next
                transaction = Transaction(_from=user_ids[n + 1], to=user_ids[n], amount=amount)
            elif amount < 0:  # nth user should pay the amount to the (n + 1)th user
                amount_next += amount  # amount is already -ve
                balance_sheet[user_ids[n + 1]] = amount_next
                transaction = Transaction(_from=user_ids[n], to=user_ids[n + 1], amount=-amount)
            else:  # nth user is already settled: No transaction
                pass
            # nth user will be settled
            balance_sheet[user_ids[n]] = 0
            if amount > 0 or amount < 0:
                transactions.append(transaction)
        else:
            balance_sheet[user_ids[-1]] = 0  # Last user will be settled itself if the first (N-1) users are settled
        print(':: balance_sheet | after ::', balance_sheet)
        print(':: Transactions ::', *transactions, sep='\n:: ')
        return transactions


class GreedySettlementStrategy:
    """
    Based on the idea: Settle bigger transactions first
    """
    def settle_up(self, balance_sheet: dict):
        """
        Gives a list of transactions based on greedy technique: settle-up bigger transactions first
        :param balance_sheet: A dict of user to balance amount mapping
        :return: List[Transaction]
        """
        print(':: LOG :: GreedySettlementStrategy | settle_up ::')
        validate_balance_sheet(balance_sheet)
        # step 1: split the balance sheet into two parts:
        # i) the users who paid
        # ii) the users who owed
        # The basic idea is: the money should flow from the user who owed to the user who paid
        group_paid = []
        group_owed = []
        for user_id, balance in balance_sheet.items():
            if balance > 0:  # paid
                heap_push((user_id, -balance), group_paid, comparator=is_smaller_balance)
            elif balance < 0:  # owed
                heap_push((user_id, balance), group_owed, comparator=is_smaller_balance)
        # step 2: settle-up bigger transactions
        transactions = list()
        while group_paid and group_owed:
            user_id_1, balance_paid = heap_pop(group_paid)
            user_id_2, balance_owed = heap_pop(group_owed)
            trn_amount = min(abs(balance_paid), abs(balance_owed))
            balance_owed += trn_amount
            balance_paid = -balance_paid - trn_amount  # Note: In max_heap, balance_paid was stored as -ve val
            if balance_paid > 0:
                heap_push((user_id_1, -balance_paid), group_paid, comparator=is_smaller_balance)
            if balance_owed < 0:
                heap_push((user_id_2, balance_owed), group_owed, comparator=is_smaller_balance)
            # prepare the transaction
            transactions.append(Transaction(user_id_2, user_id_1, trn_amount))
        print(':: Transactions ::', *transactions, sep='\n:: ')
        return transactions
