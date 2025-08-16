"""
Event Bus Implementation
イベントバスの実装
"""
from typing import Dict, List, Type
import asyncio
from collections import defaultdict
from domain.shared.domain_event import DomainEvent
from application.event_handler import EventHandler


class InMemoryEventBus:
    """
    インメモリ実装のイベントバス
    
    イベントの購読と配信を管理する。
    同期・非同期の両方の処理をサポート。
    """
    
    def __init__(self):
        """初期化"""
        # イベントタイプごとのハンドラーを管理
        self._handlers: Dict[Type[DomainEvent], List[EventHandler]] = defaultdict(list)
        
        # イベント履歴（デバッグ・テスト用）
        self._event_history: List[DomainEvent] = []
        
        # 非同期処理用のキュー
        self._async_queue: asyncio.Queue = None
    
    def subscribe(self, handler: EventHandler) -> None:
        """
        イベントハンドラーを登録
        
        Args:
            handler: 登録するイベントハンドラー
        """
        event_type = handler.handles_event()
        self._handlers[event_type].append(handler)
        print(f"✅ Subscribed {handler.__class__.__name__} to {event_type.__name__}")
    
    def unsubscribe(self, handler: EventHandler) -> None:
        """
        イベントハンドラーの登録を解除
        
        Args:
            handler: 解除するイベントハンドラー
        """
        event_type = handler.handles_event()
        if handler in self._handlers[event_type]:
            self._handlers[event_type].remove(handler)
            print(f"❌ Unsubscribed {handler.__class__.__name__} from {event_type.__name__}")
    
    async def publish(self, event: DomainEvent) -> None:
        """
        イベントを配信（非同期）
        
        Args:
            event: 配信するドメインイベント
        """
        # イベント履歴に追加
        self._event_history.append(event)
        
        # 該当するハンドラーを取得
        event_type = type(event)
        handlers = self._handlers.get(event_type, [])
        
        print(f"📤 Publishing {event.event_name()} to {len(handlers)} handlers")
        
        # 各ハンドラーで処理（並列実行）
        tasks = []
        for handler in handlers:
            task = self._handle_event_async(handler, event)
            tasks.append(task)
        
        # すべてのハンドラーの処理を待つ
        if tasks:
            await asyncio.gather(*tasks)
    
    def publish_sync(self, event: DomainEvent) -> None:
        """
        イベントを配信（同期）
        
        Args:
            event: 配信するドメインイベント
        """
        # イベント履歴に追加
        self._event_history.append(event)
        
        # 該当するハンドラーを取得
        event_type = type(event)
        handlers = self._handlers.get(event_type, [])
        
        print(f"📤 Publishing {event.event_name()} to {len(handlers)} handlers (sync)")
        
        # 各ハンドラーで処理（順次実行）
        for handler in handlers:
            try:
                handler.handle(event)
                print(f"   ✅ {handler.__class__.__name__} processed")
            except Exception as e:
                print(f"   ❌ {handler.__class__.__name__} failed: {e}")
                # エラーをログに記録（本番環境では適切なロギング）
                self._handle_error(handler, event, e)
    
    async def _handle_event_async(self, handler: EventHandler, event: DomainEvent) -> None:
        """
        非同期でイベントを処理
        
        Args:
            handler: イベントハンドラー
            event: ドメインイベント
        """
        try:
            # ハンドラーがasyncメソッドを持っているか確認
            if hasattr(handler, 'handle_async'):
                await handler.handle_async(event)
            else:
                # 同期メソッドを非同期で実行
                await asyncio.to_thread(handler.handle, event)
            
            print(f"   ✅ {handler.__class__.__name__} processed")
        except Exception as e:
            print(f"   ❌ {handler.__class__.__name__} failed: {e}")
            self._handle_error(handler, event, e)
    
    def _handle_error(self, handler: EventHandler, event: DomainEvent, error: Exception) -> None:
        """
        エラー処理
        
        Args:
            handler: エラーが発生したハンドラー
            event: 処理中のイベント
            error: 発生したエラー
        """
        # 実際のシステムでは、ここでエラーログを記録
        # 必要に応じてリトライやDLQ（Dead Letter Queue）への送信を実装
        error_info = {
            'handler': handler.__class__.__name__,
            'event': event.to_dict(),
            'error': str(error)
        }
        print(f"🚨 Error logged: {error_info}")
    
    def get_event_history(self) -> List[DomainEvent]:
        """
        イベント履歴を取得（テスト用）
        
        Returns:
            イベントのリスト
        """
        return self._event_history.copy()
    
    def clear_history(self) -> None:
        """イベント履歴をクリア（テスト用）"""
        self._event_history.clear()
    
    def get_handler_count(self, event_type: Type[DomainEvent]) -> int:
        """
        特定のイベントタイプに登録されたハンドラー数を取得
        
        Args:
            event_type: イベントタイプ
            
        Returns:
            ハンドラー数
        """
        return len(self._handlers.get(event_type, []))