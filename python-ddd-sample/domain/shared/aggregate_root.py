"""
Aggregate Root Base Class
集約ルートの基底クラス
"""
from typing import List
from domain.shared.domain_event import DomainEvent


class AggregateRoot:
    """
    集約ルートの基底クラス
    
    ドメインイベントの発行機能を提供する。
    すべての集約ルートはこのクラスを継承する。
    """
    
    def __init__(self):
        """初期化"""
        self._domain_events: List[DomainEvent] = []
    
    def add_domain_event(self, event: DomainEvent) -> None:
        """
        ドメインイベントを追加
        
        Args:
            event: 発生したドメインイベント
        """
        self._domain_events.append(event)
    
    def get_domain_events(self) -> List[DomainEvent]:
        """
        蓄積されたドメインイベントを取得
        
        Returns:
            ドメインイベントのリスト
        """
        return self._domain_events.copy()
    
    def clear_domain_events(self) -> None:
        """
        ドメインイベントをクリア
        
        通常はリポジトリが永続化後に呼び出す
        """
        self._domain_events.clear()
    
    def pull_domain_events(self) -> List[DomainEvent]:
        """
        ドメインイベントを取得してクリア
        
        Returns:
            ドメインイベントのリスト
        """
        events = self.get_domain_events()
        self.clear_domain_events()
        return events