"""
OrderApplicationServiceの統合テスト
"""
import pytest
import asyncio
from application.order_application_service import (
    OrderApplicationService,
    CreateOrderCommand,
    PlaceOrderCommand
)
from infrastructure.in_memory_order_repository import InMemoryOrderRepository
from domain.service.pricing_service import PricingService
from domain.order.order_id import OrderId
from domain.order.order import OrderStatus


class TestOrderApplicationService:
    """注文アプリケーションサービスの統合テスト"""
    
    def setup_method(self):
        """各テストの前準備"""
        self.repository = InMemoryOrderRepository()
        self.pricing_service = PricingService()
        self.service = OrderApplicationService(
            order_repository=self.repository,
            pricing_service=self.pricing_service
        )
    
    @pytest.mark.asyncio
    async def test_create_order(self):
        """注文作成のユースケース"""
        # コマンドを準備
        command = CreateOrderCommand(
            customer_id='CUST001',
            items=[
                {
                    'product_id': 'PROD001',
                    'quantity': 2,
                    'unit_price': 1000
                },
                {
                    'product_id': 'PROD002',
                    'quantity': 1,
                    'unit_price': 2000
                }
            ]
        )
        
        # 実行
        order_id = await self.service.create_order(command)
        
        # 検証
        assert order_id is not None
        assert self.repository.size() == 1
        
        # 保存された注文を確認
        saved_order = await self.repository.find_by_id(OrderId(order_id))
        assert saved_order is not None
        assert saved_order.item_count == 2
        assert saved_order.total_amount.amount == 4000  # 2*1000 + 1*2000
    
    @pytest.mark.asyncio
    async def test_place_order(self):
        """注文確定のユースケース"""
        # まず注文を作成
        create_command = CreateOrderCommand(
            customer_id='CUST001',
            items=[
                {
                    'product_id': 'PROD001',
                    'quantity': 1,
                    'unit_price': 5000
                }
            ]
        )
        order_id = await self.service.create_order(create_command)
        
        # 注文を確定
        place_command = PlaceOrderCommand(order_id=order_id)
        await self.service.place_order(place_command)
        
        # 検証
        order = await self.repository.find_by_id(OrderId(order_id))
        assert order.status == OrderStatus.PLACED
        assert order.placed_at is not None
    
    @pytest.mark.asyncio
    async def test_place_nonexistent_order_raises_error(self):
        """存在しない注文の確定はエラー"""
        command = PlaceOrderCommand(order_id='NONEXISTENT')
        
        with pytest.raises(ValueError, match='注文が見つかりません'):
            await self.service.place_order(command)
    
    @pytest.mark.asyncio
    async def test_get_order_summary(self):
        """注文サマリーの取得"""
        # 注文を作成
        create_command = CreateOrderCommand(
            customer_id='CUST001',
            items=[
                {
                    'product_id': 'PROD001',
                    'quantity': 2,
                    'unit_price': 1500
                }
            ]
        )
        order_id = await self.service.create_order(create_command)
        
        # サマリーを取得
        summary = await self.service.get_order_summary(order_id)
        
        # 検証
        assert summary is not None
        assert summary['order_id'] == order_id
        assert summary['customer_id'] == 'CUST001'
        assert summary['status'] == 'DRAFT'
        assert summary['total_amount'] == '¥3,000'
        assert summary['item_count'] == 1
        assert len(summary['items']) == 1
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_order_summary_returns_none(self):
        """存在しない注文のサマリーはNone"""
        summary = await self.service.get_order_summary('NONEXISTENT')
        assert summary is None
    
    @pytest.mark.asyncio
    async def test_cancel_order(self):
        """注文キャンセルのユースケース"""
        # 注文を作成して確定
        create_command = CreateOrderCommand(
            customer_id='CUST001',
            items=[
                {
                    'product_id': 'PROD001',
                    'quantity': 1,
                    'unit_price': 3000
                }
            ]
        )
        order_id = await self.service.create_order(create_command)
        
        place_command = PlaceOrderCommand(order_id=order_id)
        await self.service.place_order(place_command)
        
        # キャンセル
        await self.service.cancel_order(order_id)
        
        # 検証
        order = await self.repository.find_by_id(OrderId(order_id))
        assert order.status == OrderStatus.CANCELLED
    
    @pytest.mark.asyncio
    async def test_cancel_nonexistent_order_raises_error(self):
        """存在しない注文のキャンセルはエラー"""
        with pytest.raises(ValueError, match='注文が見つかりません'):
            await self.service.cancel_order('NONEXISTENT')
    
    @pytest.mark.asyncio
    async def test_complete_order_flow(self):
        """完全な注文フローのテスト"""
        # 1. 注文作成
        create_command = CreateOrderCommand(
            customer_id='CUST001',
            items=[
                {
                    'product_id': 'LAPTOP001',
                    'quantity': 1,
                    'unit_price': 120000
                },
                {
                    'product_id': 'MOUSE001',
                    'quantity': 2,
                    'unit_price': 3000
                }
            ]
        )
        order_id = await self.service.create_order(create_command)
        
        # 2. 注文内容確認
        summary = await self.service.get_order_summary(order_id)
        assert summary['total_amount'] == '¥126,000'
        assert summary['item_count'] == 2
        
        # 3. 注文確定
        place_command = PlaceOrderCommand(order_id=order_id)
        await self.service.place_order(place_command)
        
        # 4. 確定後の状態確認
        order = await self.repository.find_by_id(OrderId(order_id))
        assert order.status == OrderStatus.PLACED
        assert order.total_amount.amount == 126000