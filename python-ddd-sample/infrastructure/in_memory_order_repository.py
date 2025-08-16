"""
InMemoryOrderRepository
メモリ上で動作するリポジトリ実装（テスト・学習用）
"""
from typing import Dict, List, Optional
from domain.order.order import Order
from domain.order.order_id import OrderId
from domain.order.order_repository import OrderRepository
from domain.customer.customer_id import CustomerId


class InMemoryOrderRepository(OrderRepository):
    """インメモリ実装の注文リポジトリ"""
    
    def __init__(self, event_bus=None):
        self._orders: Dict[str, Order] = {}
        self._event_bus = event_bus  # イベントバスの注入
    
    async def save(self, order: Order) -> None:
        """注文を保存"""
        # 1. 集約を永続化
        self._orders[str(order.id)] = order
        
        # 2. 蓄積されたイベントを配信
        if self._event_bus:
            events = order.pull_domain_events()
            for event in events:
                await self._event_bus.publish(event)
    
    async def find_by_id(self, order_id: OrderId) -> Optional[Order]:
        """IDで注文を検索"""
        return self._orders.get(str(order_id))
    
    async def find_by_customer_id(self, customer_id: CustomerId) -> List[Order]:
        """顧客IDで注文を検索"""
        result = []
        for order in self._orders.values():
            if order.customer_id == customer_id:
                result.append(order)
        return result
    
    async def delete(self, order_id: OrderId) -> None:
        """注文を削除"""
        key = str(order_id)
        if key in self._orders:
            del self._orders[key]
    
    def clear(self) -> None:
        """全データをクリア（テスト用）"""
        self._orders.clear()
    
    def size(self) -> int:
        """保存されている注文数を返す（テスト用）"""
        return len(self._orders)