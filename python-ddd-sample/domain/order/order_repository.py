"""
OrderRepository Interface
Aggregate Root単位でRepositoryを定義
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from .order import Order
from .order_id import OrderId
from ..customer.customer_id import CustomerId


class OrderRepository(ABC):
    """注文リポジトリのインターフェース"""
    
    @abstractmethod
    async def save(self, order: Order) -> None:
        """注文を保存"""
        pass
    
    @abstractmethod
    async def find_by_id(self, order_id: OrderId) -> Optional[Order]:
        """IDで注文を検索"""
        pass
    
    @abstractmethod
    async def find_by_customer_id(self, customer_id: CustomerId) -> List[Order]:
        """顧客IDで注文を検索"""
        pass
    
    @abstractmethod
    async def delete(self, order_id: OrderId) -> None:
        """注文を削除"""
        pass