"""
Event Handler Tests
イベントハンドラーのテスト
"""
import pytest
import asyncio
from datetime import datetime
from infrastructure.event_bus import InMemoryEventBus
from infrastructure.in_memory_order_repository import InMemoryOrderRepository
from application.handlers.order_placed_handler import (
    SendOrderConfirmationEmailHandler,
    NotifyInventorySystemHandler,
    UpdateAnalyticsHandler
)
from application.handlers.order_cancelled_handler import (
    ReleaseInventoryHandler,
    RefundPaymentHandler,
    SendCancellationEmailHandler
)
from domain.order.order import Order
from domain.order.product_id import ProductId
from domain.customer.customer_id import CustomerId
from domain.shared.money import Money


class TestEventBus:
    """イベントバスのテスト"""
    
    def setup_method(self):
        """各テストの前準備"""
        self.event_bus = InMemoryEventBus()
    
    def test_subscribe_and_publish_sync(self):
        """同期的なイベント購読と配信"""
        # ハンドラーを登録
        email_handler = SendOrderConfirmationEmailHandler()
        inventory_handler = NotifyInventorySystemHandler()
        
        self.event_bus.subscribe(email_handler)
        self.event_bus.subscribe(inventory_handler)
        
        # 注文を作成して確定
        order = Order.create(CustomerId.generate())
        order.add_item(ProductId('PROD001'), 2, Money.from_yen(1000))
        order.place()
        
        # イベントを取得して配信
        events = order.pull_domain_events()
        for event in events:
            self.event_bus.publish_sync(event)
        
        # イベント履歴を確認
        history = self.event_bus.get_event_history()
        assert len(history) == 2  # OrderCreated, OrderPlaced
    
    @pytest.mark.asyncio
    async def test_async_event_publishing(self):
        """非同期イベント配信"""
        # ハンドラーを登録
        analytics_handler = UpdateAnalyticsHandler()
        self.event_bus.subscribe(analytics_handler)
        
        # 注文を作成して確定
        order = Order.create(CustomerId.generate())
        order.add_item(ProductId('PROD001'), 1, Money.from_yen(5000))
        order.place()
        
        # イベントを非同期で配信
        events = order.pull_domain_events()
        for event in events:
            await self.event_bus.publish(event)
        
        # 処理が完了していることを確認
        history = self.event_bus.get_event_history()
        assert len(history) == 2
    
    def test_handler_count(self):
        """ハンドラー登録数の確認"""
        from domain.order.order_events import OrderPlacedEvent
        
        # 初期状態
        assert self.event_bus.get_handler_count(OrderPlacedEvent) == 0
        
        # ハンドラーを登録
        handler1 = SendOrderConfirmationEmailHandler()
        handler2 = NotifyInventorySystemHandler()
        
        self.event_bus.subscribe(handler1)
        assert self.event_bus.get_handler_count(OrderPlacedEvent) == 1
        
        self.event_bus.subscribe(handler2)
        assert self.event_bus.get_handler_count(OrderPlacedEvent) == 2
        
        # ハンドラーを解除
        self.event_bus.unsubscribe(handler1)
        assert self.event_bus.get_handler_count(OrderPlacedEvent) == 1


class TestOrderEventFlow:
    """注文イベントフローの統合テスト"""
    
    @pytest.mark.asyncio
    async def test_complete_order_flow_with_events(self):
        """イベント配信を含む完全な注文フロー"""
        # イベントバスとハンドラーをセットアップ
        event_bus = InMemoryEventBus()
        
        # OrderPlacedイベントのハンドラーを登録
        event_bus.subscribe(SendOrderConfirmationEmailHandler())
        event_bus.subscribe(NotifyInventorySystemHandler())
        event_bus.subscribe(UpdateAnalyticsHandler())
        
        # イベントバス付きリポジトリを作成
        repository = InMemoryOrderRepository(event_bus)
        
        # 注文を作成
        order = Order.create(CustomerId('CUST001'))
        order.add_item(ProductId('LAPTOP'), 1, Money.from_yen(150000))
        order.add_item(ProductId('MOUSE'), 2, Money.from_yen(3000))
        
        # 注文を保存（OrderCreatedイベントが配信される）
        await repository.save(order)
        
        # 注文を確定
        order.place()
        
        # 再度保存（OrderPlacedイベントが配信される）
        await repository.save(order)
        
        # イベント履歴を確認
        history = event_bus.get_event_history()
        assert len(history) == 3  # OrderCreated, OrderItemAdded, OrderPlaced
        
        # 最後のイベントがOrderPlacedであることを確認
        assert history[-1].event_name() == 'OrderPlaced'
    
    @pytest.mark.asyncio
    async def test_order_cancellation_flow(self):
        """注文キャンセルフローのテスト"""
        # イベントバスとハンドラーをセットアップ
        event_bus = InMemoryEventBus()
        
        # OrderCancelledイベントのハンドラーを登録
        event_bus.subscribe(ReleaseInventoryHandler())
        event_bus.subscribe(RefundPaymentHandler())
        event_bus.subscribe(SendCancellationEmailHandler())
        
        # イベントバス付きリポジトリを作成
        repository = InMemoryOrderRepository(event_bus)
        
        # 注文を作成して確定
        order = Order.create(CustomerId('CUST002'))
        order.add_item(ProductId('BOOK'), 3, Money.from_yen(1500))
        order.place()
        
        # 保存
        await repository.save(order)
        
        # 注文をキャンセル
        order.cancel("顧客都合によるキャンセル")
        
        # 再度保存（OrderCancelledイベントが配信される）
        await repository.save(order)
        
        # イベント履歴を確認
        history = event_bus.get_event_history()
        
        # 最後のイベントがOrderCancelledであることを確認
        assert history[-1].event_name() == 'OrderCancelled'
        assert history[-1]._get_event_data()['reason'] == "顧客都合によるキャンセル"


class TestEventHandlerIsolation:
    """イベントハンドラーの独立性テスト"""
    
    def test_handler_error_isolation(self):
        """一つのハンドラーのエラーが他に影響しないことを確認"""
        event_bus = InMemoryEventBus()
        
        # エラーを起こすハンドラーのモック
        class FailingHandler(SendOrderConfirmationEmailHandler):
            def handle(self, event):
                raise Exception("Simulated failure")
        
        # 正常なハンドラーと失敗するハンドラーを登録
        failing_handler = FailingHandler()
        normal_handler = NotifyInventorySystemHandler()
        
        event_bus.subscribe(failing_handler)
        event_bus.subscribe(normal_handler)
        
        # 注文を作成して確定
        order = Order.create(CustomerId.generate())
        order.add_item(ProductId('TEST'), 1, Money.from_yen(1000))
        order.place()
        
        # イベントを配信（エラーが起きても続行される）
        events = order.pull_domain_events()
        for event in events:
            event_bus.publish_sync(event)
        
        # イベント履歴には記録されている
        history = event_bus.get_event_history()
        assert len(history) == 2  # OrderCreated, OrderPlaced