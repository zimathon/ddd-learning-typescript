"""
Order Placed Event Handler
注文確定イベントのハンドラー
"""
from typing import Type
from application.event_handler import EventHandler
from domain.shared.domain_event import DomainEvent
from domain.order.order_events import OrderPlacedEvent


class SendOrderConfirmationEmailHandler(EventHandler):
    """
    注文確認メール送信ハンドラー
    
    OrderPlacedEventを受け取って、顧客に確認メールを送信する。
    """
    
    def __init__(self, email_service=None):
        """
        初期化
        
        Args:
            email_service: メール送信サービス（本番環境では実際のサービスを注入）
        """
        self._email_service = email_service
    
    def handle(self, event: OrderPlacedEvent) -> None:
        """
        注文確認メールを送信
        
        Args:
            event: 注文確定イベント
        """
        print(f"📧 Sending order confirmation email for Order {event.aggregate_id}")
        
        # 実際のシステムでは、ここでメール送信処理を実行
        if self._email_service:
            self._email_service.send_confirmation(
                order_id=event.aggregate_id,
                customer_id=event.customer_id,
                total_amount=event.total_amount,
                items=event.items
            )
        else:
            # デモ用の出力
            print(f"   To: Customer {event.customer_id}")
            print(f"   Order ID: {event.aggregate_id}")
            print(f"   Total: ¥{event.total_amount:,}")
            print(f"   Items: {len(event.items)} item(s)")
    
    def handles_event(self) -> Type[DomainEvent]:
        """処理するイベントタイプ"""
        return OrderPlacedEvent


class NotifyInventorySystemHandler(EventHandler):
    """
    在庫システム通知ハンドラー
    
    OrderPlacedEventを受け取って、在庫システムに通知する。
    """
    
    def __init__(self, inventory_service=None):
        """
        初期化
        
        Args:
            inventory_service: 在庫管理サービス
        """
        self._inventory_service = inventory_service
    
    def handle(self, event: OrderPlacedEvent) -> None:
        """
        在庫システムに注文を通知
        
        Args:
            event: 注文確定イベント
        """
        print(f"📦 Notifying inventory system for Order {event.aggregate_id}")
        
        # 実際のシステムでは、ここで在庫予約処理を実行
        if self._inventory_service:
            for item in event.items:
                self._inventory_service.reserve_stock(
                    product_id=item['product_id'],
                    quantity=item['quantity']
                )
        else:
            # デモ用の出力
            for item in event.items:
                print(f"   Reserve: {item['product_id']} x {item['quantity']}")
    
    def handles_event(self) -> Type[DomainEvent]:
        """処理するイベントタイプ"""
        return OrderPlacedEvent


class UpdateAnalyticsHandler(EventHandler):
    """
    分析データ更新ハンドラー
    
    OrderPlacedEventを受け取って、分析データを更新する。
    """
    
    def __init__(self, analytics_service=None):
        """
        初期化
        
        Args:
            analytics_service: 分析サービス
        """
        self._analytics_service = analytics_service
    
    async def handle_async(self, event: OrderPlacedEvent) -> None:
        """
        分析データを非同期で更新
        
        Args:
            event: 注文確定イベント
        """
        print(f"📊 Updating analytics for Order {event.aggregate_id}")
        
        # 実際のシステムでは、ここで分析データを更新
        if self._analytics_service:
            await self._analytics_service.record_order(
                order_id=event.aggregate_id,
                customer_id=event.customer_id,
                total_amount=event.total_amount,
                placed_at=event.placed_at
            )
        else:
            # デモ用の出力（非同期処理のシミュレーション）
            import asyncio
            await asyncio.sleep(0.1)  # 処理時間のシミュレーション
            print(f"   Analytics updated for amount: ¥{event.total_amount:,}")
    
    def handle(self, event: OrderPlacedEvent) -> None:
        """
        同期版のhandle（互換性のため）
        
        Args:
            event: 注文確定イベント
        """
        print(f"📊 Updating analytics for Order {event.aggregate_id} (sync)")
        
        if self._analytics_service:
            self._analytics_service.record_order_sync(
                order_id=event.aggregate_id,
                customer_id=event.customer_id,
                total_amount=event.total_amount,
                placed_at=event.placed_at
            )
        else:
            print(f"   Analytics updated for amount: ¥{event.total_amount:,}")
    
    def handles_event(self) -> Type[DomainEvent]:
        """処理するイベントタイプ"""
        return OrderPlacedEvent