"""
CustomerId Value Object
顧客IDを表現する値オブジェクト
"""
import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class CustomerId:
    """不変の顧客ID値オブジェクト"""
    
    value: str
    
    def __post_init__(self):
        """生成時のバリデーション"""
        if not self.value or not self.value.strip():
            raise ValueError('CustomerIdは空にできません')
    
    @classmethod
    def generate(cls) -> 'CustomerId':
        """新しいIDを生成"""
        return cls(str(uuid.uuid4()))
    
    def __str__(self) -> str:
        return self.value