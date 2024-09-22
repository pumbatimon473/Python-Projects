from functools import reduce
from rest_framework.exceptions import ValidationError

def build_balance_sheet(*user_expenses):
    """
    Builds a user to cumulative expense mapping
    :param user_expenses: A list of two-tuples: (user, expense)
    :return: a dict of user to balance mapping
    """
    balance = {}
    for user, expense in user_expenses:
        balance[user] = balance.setdefault(user, 0) + expense
    return balance


def validate_balance_sheet(balance_sheet: dict) -> bool:
    """
    Validates if the total paid amount is eq to the total shared amount.
    Raises ValidationError if the given balance_sheet is not valid.

    :param balance_sheet: A dict of user to balance mapping; -ve balance indicates owed (shared) amount
    :return: True if total_paid_amount = total_owed_amount
    """
    resultant_balance = reduce(lambda _sum, user_id: _sum + balance_sheet.get(user_id), balance_sheet.keys(), 0)
    is_valid = resultant_balance == 0
    if not is_valid:
        raise ValidationError('Invalid balance sheet! Total paid amount is not equal to the total owed amount')
    return is_valid


def is_smaller_balance(user_balance_1: tuple, user_balance_2: tuple) -> bool:
    """
    Accepts 2-tuples as arguments and compares them

    :param user_balance_1: (user_id_1, balance_1)
    :param user_balance_2: (user_id_2, balance_2)
    :return: True if balance_1 < balance_2
    """
    user_1, balance_1 = user_balance_1
    user_2, balance_2 = user_balance_2
    return balance_1 < balance_2


def is_smaller(item1, item2):
    return item1 < item2


def heapify(root: int, heap: list, comparator=is_smaller):
    """
    Recursively balances the min heap rooted at the given index

    :param root: represents the root index of a CBT
    :param heap: A list representing the CBT
    :param comparator: A callable which accepts two arguments and compares them; default=is_smaller
    :return: None
    """
    smallest = root
    left = 2 * root + 1
    right = left + 1
    N = len(heap)
    if left < N and is_smaller(heap[left], heap[smallest]):
        smallest = left
    if right < N and is_smaller(heap[right], heap[smallest]):
        smallest = right
    # swap if root is not the smallest
    if smallest != root:
        heap[smallest], heap[root] = heap[root], heap[smallest]
        heapify(smallest, heap)


def heap_push(user_balance: tuple, heap: list, comparator=is_smaller) -> None:
    N = len(heap)
    heap.append(user_balance)
    child = N  # the index at which the new item is inserted
    parent = (child - 1) // 2
    while parent >= 0 and is_smaller(heap[child], heap[parent]):
        heap[child], heap[parent] = heap[parent], heap[child]
        child = parent
        parent = (child - 1) // 2


def heap_pop(heap: list):
    N = len(heap)
    if N == 0:
        raise IndexError('Cannot pop from an empty heap!')
    heap[0], heap[N - 1] = heap[N - 1], heap[0]
    popped_item = heap.pop()
    heapify(0, heap)
    return popped_item
