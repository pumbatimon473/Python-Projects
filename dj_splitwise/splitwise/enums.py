from enum import Enum


class Query(Enum):
    ALL = 'all'
    USER_EXPENSE = 'user_expense'
    GROUP_EXPENSE = 'group_expense'


class SettlementType(Enum):
    N_MINUS_1 = 'n_minus_1'
    GREEDY = 'greedy'
