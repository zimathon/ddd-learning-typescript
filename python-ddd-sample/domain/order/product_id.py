"""
ProductId Value Object
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class ProductId:
    """不変の商品ID値オブジェクト"""
    
    value: str
    
    def __post_init__(self):
        if not self.value or not self.value.strip():
            raise ValueError('ProductIdは空にできません')
    
    def __str__(self) -> str:
        return self.value