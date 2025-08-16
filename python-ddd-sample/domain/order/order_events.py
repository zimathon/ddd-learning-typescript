"""
Order Aggregate Domain Events
注文集約で発生するドメインイベント
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List
from datetime import datetime
from domain.shared.domain_event import DomainEvent


@dataclass(frozen=True)
class OrderCreatedEvent(DomainEvent):
    """注文作成イベント"""
    
    customer_id: str = ""
    
    def event_name(self) -> str:
        return "OrderCreated"
    
    def _get_event_data(self) -> Dict[str, Any]:
        return {
            'customer_id': self.customer_id
        }


@dataclass(frozen=True)
class OrderItemAddedEvent(DomainEvent):
    """注文商品追加イベント"""
    
    product_id: str = ""
    quantity: int = 0
    unit_price: int = 0
    
    def event_name(self) -> str:
        return "OrderItemAdded"
    
    def _get_event_data(self) -> Dict[str, Any]:
        return {
            'product_id': self.product_id,
            'quantity': self.quantity,
            'unit_price': self.unit_price
        }


@dataclass(frozen=True)
class OrderPlacedEvent(DomainEvent):
    """注文確定イベント"""
    
    customer_id: str = ""
    total_amount: int = 0
    items: List[Dict[str, Any]] = field(default_factory=list)
    placed_at: datetime = field(default_factory=datetime.now)
    
    def event_name(self) -> str:
        return "OrderPlaced"
    
    def _get_event_data(self) -> Dict[str, Any]:
        return {
            'customer_id': self.customer_id,
            'total_amount': self.total_amount,
            'items': self.items,
            'placed_at': self.placed_at.isoformat()
        }


@dataclass(frozen=True)
class OrderCancelledEvent(DomainEvent):
    """注文キャンセルイベント"""
    
    customer_id: str = ""
    reason: str = ""
    cancelled_at: datetime = field(default_factory=datetime.now)
    
    def event_name(self) -> str:
        return "OrderCancelled"
    
    def _get_event_data(self) -> Dict[str, Any]:
        return {
            'customer_id': self.customer_id,
            'reason': self.reason,
            'cancelled_at': self.cancelled_at.isoformat()
        }


@dataclass(frozen=True)
class OrderShippedEvent(DomainEvent):
    """注文出荷イベント"""
    
    tracking_number: str = ""
    shipped_at: datetime = field(default_factory=datetime.now)
    
    def event_name(self) -> str:
        return "OrderShipped"
    
    def _get_event_data(self) -> Dict[str, Any]:
        return {
            'tracking_number': self.tracking_number,
            'shipped_at': self.shipped_at.isoformat()
        }