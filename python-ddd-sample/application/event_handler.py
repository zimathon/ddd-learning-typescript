"""
Event Handler Interface
イベントハンドラーのインターフェース
"""
from abc import ABC, abstractmethod
from typing import Type, List
from domain.shared.domain_event import DomainEvent


class EventHandler(ABC):
    """
    イベントハンドラーの基底クラス
    
    すべてのイベントハンドラーはこのクラスを継承する。
    """
    
    @abstractmethod
    def handle(self, event: DomainEvent) -> None:
        """
        イベントを処理する
        
        Args:
            event: 処理するドメインイベント
        """
        pass
    
    @abstractmethod
    def handles_event(self) -> Type[DomainEvent]:
        """
        このハンドラーが処理するイベントタイプを返す
        
        Returns:
            処理するイベントのクラス
        """
        pass