"""
Domain Event Base Class
ドメインイベントの基底クラス
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict
import uuid


@dataclass(frozen=True)
class DomainEvent(ABC):
    """
    ドメインイベントの基底クラス
    
    すべてのドメインイベントはこのクラスを継承する。
    イベントは不変（immutable）であり、過去に起きたことを表現する。
    """
    
    # イベントの一意識別子
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # イベント発生時刻
    occurred_at: datetime = field(default_factory=datetime.now)
    
    # イベントを発生させた集約のID
    aggregate_id: str = field(default="")
    
    @abstractmethod
    def event_name(self) -> str:
        """イベント名を返す"""
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """イベントを辞書形式に変換"""
        return {
            'event_id': self.event_id,
            'event_name': self.event_name(),
            'occurred_at': self.occurred_at.isoformat(),
            'aggregate_id': self.aggregate_id,
            'data': self._get_event_data()
        }
    
    @abstractmethod
    def _get_event_data(self) -> Dict[str, Any]:
        """イベント固有のデータを返す"""
        pass