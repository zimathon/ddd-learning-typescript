"""
OrderId Value Object
"""
import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class OrderId:
    """不変の注文ID値オブジェクト"""
    
    value: str
    
    def __post_init__(self):
        if not self.value or not self.value.strip():
            raise ValueError('OrderIdは空にできません')
    
    @classmethod
    def generate(cls) -> 'OrderId':
        """新しいIDを生成"""
        return cls(str(uuid.uuid4()))
    
    def __str__(self) -> str:
        return self.value