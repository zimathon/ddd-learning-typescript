"""
Order Aggregateのテスト
"""
import pytest
from datetime import datetime
from domain.order.order import Order, OrderStatus
from domain.order.order_id import OrderId
from domain.order.product_id import ProductId
from domain.customer.customer_id import CustomerId
from domain.shared.money import Money


class TestOrder:
    """Order集約のテスト"""
    
    def test_create_order(self):
        """注文の作成"""
        customer_id = CustomerId.generate()
        order = Order.create(customer_id)
        
        assert order.customer_id == customer_id
        assert order.status == OrderStatus.DRAFT
        assert order.total_amount == Money.zero()
        assert order.item_count == 0
    
    def test_add_item(self):
        """商品の追加"""
        order = Order.create(CustomerId.generate())
        product_id = ProductId('PROD001')
        
        order.add_item(product_id, 2, Money.from_yen(1000))
        
        assert order.item_count == 1
        assert order.total_amount == Money.from_yen(2000)
    
    def test_add_same_product_increases_quantity(self):
        """同じ商品を追加すると数量が増える"""
        order = Order.create(CustomerId.generate())
        product_id = ProductId('PROD001')
        
        order.add_item(product_id, 2, Money.from_yen(1000))
        order.add_item(product_id, 3, Money.from_yen(1000))
        
        assert order.item_count == 1  # 商品種類は1つ
        assert order.total_amount == Money.from_yen(5000)  # 5個分
    
    def test_remove_item(self):
        """商品の削除"""
        order = Order.create(CustomerId.generate())
        product_id = ProductId('PROD001')
        
        order.add_item(product_id, 2, Money.from_yen(1000))
        order.remove_item(product_id)
        
        assert order.item_count == 0
        assert order.total_amount == Money.zero()
    
    def test_change_item_quantity(self):
        """商品数量の変更"""
        order = Order.create(CustomerId.generate())
        product_id = ProductId('PROD001')
        
        order.add_item(product_id, 2, Money.from_yen(1000))
        order.change_item_quantity(product_id, 5)
        
        assert order.total_amount == Money.from_yen(5000)
    
    def test_max_items_limit(self):
        """最大商品数の制限"""
        order = Order.create(CustomerId.generate())
        
        # 最大数まで追加
        for i in range(Order.MAX_ITEMS):
            order.add_item(ProductId(f'PROD{i:03d}'), 1, Money.from_yen(100))
        
        # 追加でエラー
        with pytest.raises(ValueError, match='最大'):
            order.add_item(ProductId('EXTRA'), 1, Money.from_yen(100))
    
    def test_place_order(self):
        """注文の確定"""
        order = Order.create(CustomerId.generate())
        order.add_item(ProductId('PROD001'), 1, Money.from_yen(1000))
        
        order.place()
        
        assert order.status == OrderStatus.PLACED
        assert order.placed_at is not None
        assert isinstance(order.placed_at, datetime)
    
    def test_cannot_place_empty_order(self):
        """空の注文は確定できない"""
        order = Order.create(CustomerId.generate())
        
        with pytest.raises(ValueError, match='商品が選択されていません'):
            order.place()
    
    def test_cannot_modify_placed_order(self):
        """確定済み注文は変更できない"""
        order = Order.create(CustomerId.generate())
        order.add_item(ProductId('PROD001'), 1, Money.from_yen(1000))
        order.place()
        
        # 商品追加不可
        with pytest.raises(ValueError, match='変更可能'):
            order.add_item(ProductId('PROD002'), 1, Money.from_yen(500))
        
        # 商品削除不可
        with pytest.raises(ValueError, match='変更可能'):
            order.remove_item(ProductId('PROD001'))
    
    def test_order_status_transitions(self):
        """注文ステータスの遷移"""
        order = Order.create(CustomerId.generate())
        order.add_item(ProductId('PROD001'), 1, Money.from_yen(1000))
        
        # DRAFT -> PLACED
        order.place()
        assert order.status == OrderStatus.PLACED
        
        # PLACED -> PAID
        order.mark_as_paid()
        assert order.status == OrderStatus.PAID
        
        # PAID -> SHIPPED
        order.ship()
        assert order.status == OrderStatus.SHIPPED
        
        # SHIPPED -> DELIVERED
        order.deliver()
        assert order.status == OrderStatus.DELIVERED
    
    def test_cancel_order(self):
        """注文のキャンセル"""
        order = Order.create(CustomerId.generate())
        order.add_item(ProductId('PROD001'), 1, Money.from_yen(1000))
        order.place()
        
        order.cancel()
        assert order.status == OrderStatus.CANCELLED
    
    def test_cannot_cancel_shipped_order(self):
        """出荷済み注文はキャンセルできない"""
        order = Order.create(CustomerId.generate())
        order.add_item(ProductId('PROD001'), 1, Money.from_yen(1000))
        order.place()
        order.mark_as_paid()
        order.ship()
        
        with pytest.raises(ValueError, match='キャンセルできません'):
            order.cancel()
    
    def test_get_items_returns_snapshot(self):
        """商品リストはスナップショットを返す"""
        order = Order.create(CustomerId.generate())
        product_id = ProductId('PROD001')
        order.add_item(product_id, 2, Money.from_yen(1000))
        
        items = order.get_items()
        
        # スナップショットなので変更しても影響なし
        assert len(items) == 1
        assert items[0]['quantity'] == 2
        assert items[0]['subtotal'] == Money.from_yen(2000)