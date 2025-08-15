"""
Money Value Object
お金を表現する値オブジェクト
"""
from dataclasses import dataclass
from typing import Self


@dataclass(frozen=True)
class Money:
    """不変の金額値オブジェクト"""
    
    amount: int
    currency: str = 'JPY'
    
    def __post_init__(self):
        """生成時のバリデーション"""
        if self.amount < 0:
            raise ValueError('金額は0以上である必要があります')
        
        if not self.currency or len(self.currency) != 3:
            raise ValueError('通貨コードは3文字である必要があります')
    
    @classmethod
    def zero(cls, currency: str = 'JPY') -> 'Money':
        """ゼロ金額を生成"""
        return cls(0, currency)
    
    @classmethod
    def from_yen(cls, amount: int) -> 'Money':
        """円で金額を生成"""
        return cls(amount, 'JPY')
    
    def add(self, other: 'Money') -> 'Money':
        """金額を加算"""
        self._assert_same_currency(other)
        return Money(self.amount + other.amount, self.currency)
    
    def subtract(self, other: 'Money') -> 'Money':
        """金額を減算"""
        self._assert_same_currency(other)
        result = self.amount - other.amount
        if result < 0:
            raise ValueError('計算結果が負の値になります')
        return Money(result, self.currency)
    
    def multiply(self, multiplier: float) -> 'Money':
        """金額に乗数をかける"""
        if multiplier < 0:
            raise ValueError('乗数は0以上である必要があります')
        return Money(int(self.amount * multiplier), self.currency)
    
    def greater_than(self, other: 'Money') -> bool:
        """金額を比較"""
        self._assert_same_currency(other)
        return self.amount > other.amount
    
    def less_than(self, other: 'Money') -> bool:
        """他の金額より小さいか判定"""
        self._assert_same_currency(other)
        return self.amount < other.amount
    
    def greater_than_or_equal(self, other: 'Money') -> bool:
        """他の金額以上か判定"""
        self._assert_same_currency(other)
        return self.amount >= other.amount
    
    def less_than_or_equal(self, other: 'Money') -> bool:
        """他の金額以下か判定"""
        self._assert_same_currency(other)
        return self.amount <= other.amount
    
    def is_zero(self) -> bool:
        """ゼロかチェック"""
        return self.amount == 0
    
    def format(self) -> str:
        """フォーマット済み文字列を返す"""
        if self.currency == 'JPY':
            return f'¥{self.amount:,}'
        return f'{self.currency} {self.amount:,}'
    
    def _assert_same_currency(self, other: 'Money') -> None:
        """同じ通貨かチェック"""
        if self.currency != other.currency:
            raise ValueError(f'異なる通貨の計算はできません: {self.currency} != {other.currency}')