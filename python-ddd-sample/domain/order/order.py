"""
Order Aggregate Root
注文集約のルートエンティティ
"""
from enum import Enum
from datetime import datetime
from typing import List, Optional, Dict
from .order_id import OrderId
from .product_id import ProductId
from .order_item import OrderItem
from ..customer.customer_id import CustomerId
from ..shared.money import Money


class OrderStatus(Enum):
    """注文ステータス"""
    DRAFT = 'DRAFT'
    PLACED = 'PLACED'
    PAID = 'PAID'
    SHIPPED = 'SHIPPED'
    DELIVERED = 'DELIVERED'
    CANCELLED = 'CANCELLED'


class Order:
    """注文集約のルートエンティティ"""
    
    MAX_ITEMS = 100
    
    def __init__(self, order_id: OrderId, customer_id: CustomerId):
        """
        注文を生成
        
        Args:
            order_id: 注文ID
            customer_id: 顧客ID
        """
        self._id = order_id
        self._customer_id = customer_id
        self._items: List[OrderItem] = []
        self._status = OrderStatus.DRAFT
        self._total_amount = Money.zero()
        self._placed_at: Optional[datetime] = None
    
    @classmethod
    def create(cls, customer_id: CustomerId) -> 'Order':
        """新規注文を作成"""
        return cls(OrderId.generate(), customer_id)
    
    def add_item(self, product_id: ProductId, quantity: int, unit_price: Money) -> None:
        """
        商品を追加（Aggregate Rootを通じてのみアクセス）
        
        Args:
            product_id: 商品ID
            quantity: 数量
            unit_price: 単価
        """
        self._ensure_can_modify()
        
        if len(self._items) >= self.MAX_ITEMS:
            raise ValueError(f'注文には最大{self.MAX_ITEMS}個まで追加可能です')
        
        # 既存商品の数量を増やす
        existing_item = self._find_item(product_id)
        if existing_item:
            existing_item.change_quantity(existing_item.quantity + quantity)
        else:
            new_item = OrderItem(product_id, quantity, unit_price)
            self._items.append(new_item)
        
        self._recalculate_total()
    
    def remove_item(self, product_id: ProductId) -> None:
        """商品を削除"""
        self._ensure_can_modify()
        
        item_index = self._find_item_index(product_id)
        if item_index == -1:
            raise ValueError('指定された商品が見つかりません')
        
        self._items.pop(item_index)
        self._recalculate_total()
    
    def change_item_quantity(self, product_id: ProductId, new_quantity: int) -> None:
        """商品の数量を変更"""
        self._ensure_can_modify()
        
        item = self._find_item(product_id)
        if not item:
            raise ValueError('指定された商品が見つかりません')
        
        item.change_quantity(new_quantity)
        self._recalculate_total()
    
    def place(self) -> None:
        """注文を確定"""
        if self._status != OrderStatus.DRAFT:
            raise ValueError('下書き状態の注文のみ確定できます')
        
        if len(self._items) == 0:
            raise ValueError('商品が選択されていません')
        
        self._status = OrderStatus.PLACED
        self._placed_at = datetime.now()
    
    def mark_as_paid(self) -> None:
        """支払い完了"""
        if self._status != OrderStatus.PLACED:
            raise ValueError('確定済みの注文のみ支払い可能です')
        
        self._status = OrderStatus.PAID
    
    def ship(self) -> None:
        """出荷"""
        if self._status != OrderStatus.PAID:
            raise ValueError('支払い済みの注文のみ出荷可能です')
        
        self._status = OrderStatus.SHIPPED
    
    def deliver(self) -> None:
        """配送完了"""
        if self._status != OrderStatus.SHIPPED:
            raise ValueError('出荷済みの注文のみ配送完了にできます')
        
        self._status = OrderStatus.DELIVERED
    
    def cancel(self) -> None:
        """キャンセル"""
        if self._status in [OrderStatus.SHIPPED, OrderStatus.DELIVERED, OrderStatus.CANCELLED]:
            raise ValueError('この注文はキャンセルできません')
        
        self._status = OrderStatus.CANCELLED
    
    def _find_item(self, product_id: ProductId) -> Optional[OrderItem]:
        """商品を検索（内部メソッド）"""
        for item in self._items:
            if item.has_product(product_id):
                return item
        return None
    
    def _find_item_index(self, product_id: ProductId) -> int:
        """商品のインデックスを検索（内部メソッド）"""
        for i, item in enumerate(self._items):
            if item.has_product(product_id):
                return i
        return -1
    
    def _recalculate_total(self) -> None:
        """合計金額の再計算（内部メソッド）"""
        total = Money.zero()
        for item in self._items:
            total = total.add(item.get_subtotal())
        self._total_amount = total
    
    def _ensure_can_modify(self) -> None:
        """変更可能かチェック（内部メソッド）"""
        if self._status != OrderStatus.DRAFT:
            raise ValueError('下書き状態の注文のみ変更可能です')
    
    @property
    def id(self) -> OrderId:
        return self._id
    
    @property
    def customer_id(self) -> CustomerId:
        return self._customer_id
    
    @property
    def status(self) -> OrderStatus:
        return self._status
    
    @property
    def total_amount(self) -> Money:
        return self._total_amount
    
    @property
    def placed_at(self) -> Optional[datetime]:
        return self._placed_at
    
    @property
    def item_count(self) -> int:
        return len(self._items)
    
    def get_items(self) -> List[Dict]:
        """
        注文明細のスナップショットを返す
        （直接の参照を返さない）
        """
        return [
            {
                'product_id': item.product_id,
                'quantity': item.quantity,
                'unit_price': item.unit_price,
                'subtotal': item.get_subtotal()
            }
            for item in self._items
        ]
    
    def __eq__(self, other: object) -> bool:
        """IDによる等価性判定"""
        if not isinstance(other, Order):
            return False
        return self._id == other._id