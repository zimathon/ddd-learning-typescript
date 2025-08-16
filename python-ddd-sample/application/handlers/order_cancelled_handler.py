"""
Order Cancelled Event Handler
注文キャンセルイベントのハンドラー
"""
from typing import Type
from application.event_handler import EventHandler
from domain.shared.domain_event import DomainEvent
from domain.order.order_events import OrderCancelledEvent


class ReleaseInventoryHandler(EventHandler):
    """
    在庫解放ハンドラー
    
    OrderCancelledEventを受け取って、予約していた在庫を解放する。
    """
    
    def __init__(self, inventory_service=None):
        """
        初期化
        
        Args:
            inventory_service: 在庫管理サービス
        """
        self._inventory_service = inventory_service
    
    def handle(self, event: OrderCancelledEvent) -> None:
        """
        予約在庫を解放
        
        Args:
            event: 注文キャンセルイベント
        """
        print(f"🔓 Releasing inventory for cancelled Order {event.aggregate_id}")
        
        # 実際のシステムでは、ここで在庫解放処理を実行
        if self._inventory_service:
            self._inventory_service.release_reservation(event.aggregate_id)
        else:
            # デモ用の出力
            print(f"   Order ID: {event.aggregate_id}")
            print(f"   Reason: {event.reason if event.reason else 'No reason provided'}")
    
    def handles_event(self) -> Type[DomainEvent]:
        """処理するイベントタイプ"""
        return OrderCancelledEvent


class RefundPaymentHandler(EventHandler):
    """
    返金処理ハンドラー
    
    OrderCancelledEventを受け取って、支払い済みの場合は返金処理を開始する。
    """
    
    def __init__(self, payment_service=None):
        """
        初期化
        
        Args:
            payment_service: 決済サービス
        """
        self._payment_service = payment_service
    
    def handle(self, event: OrderCancelledEvent) -> None:
        """
        返金処理を開始
        
        Args:
            event: 注文キャンセルイベント
        """
        print(f"💰 Processing refund for cancelled Order {event.aggregate_id}")
        
        # 実際のシステムでは、ここで返金処理を実行
        if self._payment_service:
            self._payment_service.initiate_refund(
                order_id=event.aggregate_id,
                customer_id=event.customer_id
            )
        else:
            # デモ用の出力
            print(f"   Customer: {event.customer_id}")
            print(f"   Cancelled at: {event.cancelled_at.isoformat()}")
    
    def handles_event(self) -> Type[DomainEvent]:
        """処理するイベントタイプ"""
        return OrderCancelledEvent


class SendCancellationEmailHandler(EventHandler):
    """
    キャンセル通知メール送信ハンドラー
    
    OrderCancelledEventを受け取って、顧客にキャンセル通知メールを送信する。
    """
    
    def __init__(self, email_service=None):
        """
        初期化
        
        Args:
            email_service: メール送信サービス
        """
        self._email_service = email_service
    
    def handle(self, event: OrderCancelledEvent) -> None:
        """
        キャンセル通知メールを送信
        
        Args:
            event: 注文キャンセルイベント
        """
        print(f"📧 Sending cancellation email for Order {event.aggregate_id}")
        
        # 実際のシステムでは、ここでメール送信処理を実行
        if self._email_service:
            self._email_service.send_cancellation_notice(
                order_id=event.aggregate_id,
                customer_id=event.customer_id,
                reason=event.reason,
                cancelled_at=event.cancelled_at
            )
        else:
            # デモ用の出力
            print(f"   To: Customer {event.customer_id}")
            print(f"   Order ID: {event.aggregate_id}")
            if event.reason:
                print(f"   Reason: {event.reason}")
    
    def handles_event(self) -> Type[DomainEvent]:
        """処理するイベントタイプ"""
        return OrderCancelledEvent