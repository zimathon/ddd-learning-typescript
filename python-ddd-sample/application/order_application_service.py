"""
OrderApplicationService
注文に関するアプリケーションサービス（ユースケース層）
"""
from typing import Optional
from dataclasses import dataclass
from domain.order.order import Order
from domain.order.order_id import OrderId
from domain.order.product_id import ProductId
from domain.order.order_repository import OrderRepository
from domain.customer.customer import Customer
from domain.customer.customer_id import CustomerId
from domain.customer.email import Email
from domain.service.pricing_service import PricingService
from domain.shared.money import Money


@dataclass
class PlaceOrderCommand:
    """注文確定コマンド"""
    order_id: str
    

@dataclass
class CreateOrderCommand:
    """注文作成コマンド"""
    customer_id: str
    items: list[dict]  # [{'product_id': str, 'quantity': int, 'unit_price': int}]


class OrderApplicationService:
    """注文アプリケーションサービス"""
    
    def __init__(
        self,
        order_repository: OrderRepository,
        pricing_service: PricingService
    ):
        self._order_repository = order_repository
        self._pricing_service = pricing_service
    
    async def create_order(self, command: CreateOrderCommand) -> str:
        """
        新規注文を作成
        
        Args:
            command: 注文作成コマンド
            
        Returns:
            作成された注文ID
        """
        # 注文を作成
        customer_id = CustomerId(command.customer_id)
        order = Order.create(customer_id)
        
        # 商品を追加
        for item in command.items:
            product_id = ProductId(item['product_id'])
            quantity = item['quantity']
            unit_price = Money.from_yen(item['unit_price'])
            order.add_item(product_id, quantity, unit_price)
        
        # 保存
        await self._order_repository.save(order)
        
        return str(order.id)
    
    async def place_order(self, command: PlaceOrderCommand) -> None:
        """
        注文を確定（Use Case: 注文確定の流れを管理）
        
        Args:
            command: 注文確定コマンド
        """
        # 1. 注文を取得
        order_id = OrderId(command.order_id)
        order = await self._order_repository.find_by_id(order_id)
        
        if not order:
            raise ValueError(f'注文が見つかりません: {command.order_id}')
        
        # 2. 注文を確定（ドメインロジック）
        order.place()
        
        # 3. 保存
        await self._order_repository.save(order)
        
        # 4. 後続処理（実際のシステムでは以下のような処理）
        # - 在庫の確保
        # - 支払い処理の開始
        # - 確認メールの送信
        # - イベントの発行
    
    async def get_order_summary(self, order_id: str) -> Optional[dict]:
        """
        注文サマリーを取得
        
        Args:
            order_id: 注文ID
            
        Returns:
            注文サマリー
        """
        order = await self._order_repository.find_by_id(OrderId(order_id))
        
        if not order:
            return None
        
        return {
            'order_id': str(order.id),
            'customer_id': str(order.customer_id),
            'status': order.status.value,
            'total_amount': order.total_amount.format(),
            'item_count': order.item_count,
            'items': order.get_items(),
            'placed_at': order.placed_at.isoformat() if order.placed_at else None
        }
    
    async def cancel_order(self, order_id: str) -> None:
        """
        注文をキャンセル
        
        Args:
            order_id: 注文ID
        """
        order = await self._order_repository.find_by_id(OrderId(order_id))
        
        if not order:
            raise ValueError(f'注文が見つかりません: {order_id}')
        
        # ドメインロジック
        order.cancel()
        
        # 保存
        await self._order_repository.save(order)
        
        # 後続処理
        # - 在庫の復元
        # - 支払いのキャンセル
        # - キャンセル通知メール