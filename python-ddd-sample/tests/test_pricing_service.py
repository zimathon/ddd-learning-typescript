"""
PricingService Domain Serviceのテスト
"""
import pytest
from domain.service.pricing_service import PricingService
from domain.order.order import Order
from domain.order.product_id import ProductId
from domain.customer.customer import Customer
from domain.customer.customer_id import CustomerId
from domain.customer.email import Email
from domain.shared.money import Money


class TestPricingService:
    """価格計算ドメインサービスのテスト"""
    
    def setup_method(self):
        """各テストの前準備"""
        self.service = PricingService()
    
    def test_calculate_shipping_fee_for_small_order(self):
        """小額注文の送料計算"""
        order = Order.create(CustomerId.generate())
        order.add_item(ProductId('PROD001'), 1, Money.from_yen(3000))
        
        shipping_fee = self.service.calculate_shipping_fee(order)
        
        assert shipping_fee == Money.from_yen(500)
    
    def test_calculate_shipping_fee_for_large_order(self):
        """送料無料条件を満たす注文"""
        order = Order.create(CustomerId.generate())
        order.add_item(ProductId('PROD001'), 1, Money.from_yen(6000))
        
        shipping_fee = self.service.calculate_shipping_fee(order)
        
        assert shipping_fee == Money.zero()
    
    def test_calculate_shipping_fee_boundary(self):
        """送料無料の境界値テスト"""
        # ちょうど5000円
        order = Order.create(CustomerId.generate())
        order.add_item(ProductId('PROD001'), 1, Money.from_yen(5000))
        
        shipping_fee = self.service.calculate_shipping_fee(order)
        assert shipping_fee == Money.zero()
        
        # 5001円
        order2 = Order.create(CustomerId.generate())
        order2.add_item(ProductId('PROD001'), 1, Money.from_yen(5001))
        
        shipping_fee2 = self.service.calculate_shipping_fee(order2)
        assert shipping_fee2 == Money.zero()
        
        # 4999円
        order3 = Order.create(CustomerId.generate())
        order3.add_item(ProductId('PROD001'), 1, Money.from_yen(4999))
        
        shipping_fee3 = self.service.calculate_shipping_fee(order3)
        assert shipping_fee3 == Money.from_yen(500)
    
    def test_calculate_discount_for_inactive_customer(self):
        """非アクティブ顧客の割引計算"""
        # 非アクティブな顧客を作成
        customer = Customer.create(
            customer_id=CustomerId.generate(),
            email=Email('test@example.com'),
            name='Test Customer'
        )
        customer.deactivate()  # 非アクティブ化
        
        order = Order.create(customer.id)
        order.add_item(ProductId('PROD001'), 1, Money.from_yen(10000))
        
        discount = self.service.calculate_discount(customer, order)
        
        assert discount == Money.zero()
    
    def test_calculate_final_amount_simple(self):
        """最終請求額の計算（シンプルケース）"""
        customer = Customer.create(
            customer_id=CustomerId.generate(),
            email=Email('test@example.com'),
            name='Test Customer'
        )
        
        order = Order.create(customer.id)
        order.add_item(ProductId('PROD001'), 1, Money.from_yen(3000))
        
        # 割引なし、送料500円
        final_amount = self.service.calculate_final_amount(customer, order)
        
        assert final_amount == Money.from_yen(3500)  # 3000 + 500
    
    def test_calculate_final_amount_with_free_shipping(self):
        """送料無料での最終請求額"""
        customer = Customer.create(
            customer_id=CustomerId.generate(),
            email=Email('test@example.com'),
            name='Test Customer'
        )
        
        order = Order.create(customer.id)
        order.add_item(ProductId('PROD001'), 1, Money.from_yen(10000))
        
        # 10000円以上で2%割引、送料無料
        final_amount = self.service.calculate_final_amount(customer, order)
        
        assert final_amount == Money.from_yen(9800)  # 10000 - 200(2%割引) + 0(送料無料)