"""
OrderItem Entity (Aggregate内の子Entity)
注文明細を表現するエンティティ
"""
from .product_id import ProductId
from ..shared.money import Money


class OrderItem:
    """注文明細エンティティ（Aggregate内の子Entity）"""
    
    def __init__(self, product_id: ProductId, quantity: int, unit_price: Money):
        """
        注文明細を生成
        
        Args:
            product_id: 商品ID
            quantity: 数量
            unit_price: 単価
        """
        if quantity <= 0:
            raise ValueError('数量は1以上である必要があります')
        
        self._product_id = product_id
        self._quantity = quantity
        self._unit_price = unit_price
    
    def change_quantity(self, new_quantity: int) -> None:
        """数量を変更"""
        if new_quantity <= 0:
            raise ValueError('数量は1以上である必要があります')
        self._quantity = new_quantity
    
    def get_subtotal(self) -> Money:
        """小計を計算"""
        return self._unit_price.multiply(self._quantity)
    
    def has_product(self, product_id: ProductId) -> bool:
        """指定された商品かチェック"""
        return self._product_id == product_id
    
    @property
    def product_id(self) -> ProductId:
        return self._product_id
    
    @property
    def quantity(self) -> int:
        return self._quantity
    
    @property
    def unit_price(self) -> Money:
        return self._unit_price