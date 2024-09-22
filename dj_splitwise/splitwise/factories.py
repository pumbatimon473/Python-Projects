from .strategies import NMinusOneSettlementStrategy, GreedySettlementStrategy
from .enums import SettlementType


class SettlementStrategyFactory:
    @classmethod
    def get_by_name(cls, name: str):
        name = name.strip().lower()
        settlement_type = SettlementType(name)
        if settlement_type == SettlementType.N_MINUS_1:
            return NMinusOneSettlementStrategy()
        elif settlement_type == SettlementType.GREEDY:
            return GreedySettlementStrategy()
