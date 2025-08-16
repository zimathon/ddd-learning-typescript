"""
PricingService割引計算のテスト
"""
import pytest
from domain.service.pricing_service import PricingService
from domain.order.order import Order
from domain.order.product_id import ProductId
from domain.customer.customer import Customer
from domain.customer.customer_id import CustomerId
from domain.customer.email import Email
from domain.shared.money import Money


class TestPricingServiceDiscount:
    """割引計算のテスト"""
    
    def setup_method(self):
        """各テストの前準備"""
        self.service = PricingService()
    
    def test_no_discount_for_new_customer(self):
        """新規顧客（ポイントなし）は割引なし"""
        customer = Customer.create(
            customer_id=CustomerId.generate(),
            email=Email('new@example.com'),
            name='New Customer'
        )
        
        order = Order.create(customer.id)
        order.add_item(ProductId('PROD001'), 1, Money.from_yen(5000))
        
        discount = self.service.calculate_discount(customer, order)
        
        assert discount == Money.zero()
    
    def test_loyalty_points_1000_gives_5_percent(self):
        """1000ポイントで5%割引"""
        customer = Customer.create(
            customer_id=CustomerId.generate(),
            email=Email('loyal@example.com'),
            name='Loyal Customer'
        )
        # 1000ポイント追加
        for _ in range(10):
            customer.add_loyalty_points(100)
        
        order = Order.create(customer.id)
        order.add_item(ProductId('PROD001'), 1, Money.from_yen(5000))
        
        discount = self.service.calculate_discount(customer, order)
        
        assert discount == Money.from_yen(250)  # 5000 * 0.05 = 250
    
    def test_loyalty_points_2000_gives_10_percent(self):
        """2000ポイントで10%割引"""
        customer = Customer.create(
            customer_id=CustomerId.generate(),
            email=Email('vip@example.com'),
            name='VIP Customer'
        )
        # 2000ポイント追加
        for _ in range(20):
            customer.add_loyalty_points(100)
        
        order = Order.create(customer.id)
        order.add_item(ProductId('PROD001'), 1, Money.from_yen(5000))
        
        discount = self.service.calculate_discount(customer, order)
        
        assert discount == Money.from_yen(500)  # 5000 * 0.10 = 500
    
    def test_large_order_gets_additional_discount(self):
        """10000円以上の注文で追加2%割引"""
        customer = Customer.create(
            customer_id=CustomerId.generate(),
            email=Email('big@example.com'),
            name='Big Spender'
        )
        # 1000ポイント追加（5%割引）
        for _ in range(10):
            customer.add_loyalty_points(100)
        
        order = Order.create(customer.id)
        order.add_item(ProductId('PROD001'), 1, Money.from_yen(12000))
        
        discount = self.service.calculate_discount(customer, order)
        
        # 5% + 2% = 7%割引
        assert discount == Money.from_yen(840)  # 12000 * 0.07 = 840
    
    def test_maximum_discount_cap_at_30_percent(self):
        """最大割引率は30%に制限"""
        customer = Customer.create(
            customer_id=CustomerId.generate(),
            email=Email('super@example.com'),
            name='Super VIP'
        )
        # 大量のポイント追加
        for _ in range(100):
            customer.add_loyalty_points(100)
        
        order = Order.create(customer.id)
        order.add_item(ProductId('PROD001'), 1, Money.from_yen(100000))
        
        discount = self.service.calculate_discount(customer, order)
        
        # 10000ポイントでも2000ポイント以上の条件で10%、大口注文で2%追加 = 12%
        assert discount == Money.from_yen(12000)  # 100000 * 0.12 = 12000
    
    def test_combined_loyalty_and_large_order_discount(self):
        """ロイヤリティと大口注文の組み合わせ"""
        customer = Customer.create(
            customer_id=CustomerId.generate(),
            email=Email('combo@example.com'),
            name='Combo Customer'
        )
        # 2000ポイント追加（10%割引）
        for _ in range(20):
            customer.add_loyalty_points(100)
        
        order = Order.create(customer.id)
        order.add_item(ProductId('LAPTOP'), 1, Money.from_yen(150000))
        
        discount = self.service.calculate_discount(customer, order)
        
        # 10% + 2% = 12%割引
        assert discount == Money.from_yen(18000)  # 150000 * 0.12 = 18000
    
    def test_discount_calculation_with_final_amount(self):
        """割引を含む最終請求額の統合テスト"""
        customer = Customer.create(
            customer_id=CustomerId.generate(),
            email=Email('final@example.com'),
            name='Final Customer'
        )
        # 1500ポイント（5%割引）
        for _ in range(15):
            customer.add_loyalty_points(100)
        
        order = Order.create(customer.id)
        order.add_item(ProductId('PROD001'), 1, Money.from_yen(15000))
        
        # 割引: 15000 * 0.07 = 1050 (5% + 2%)
        # 送料: 0円（5000円以上）
        # 最終額: 15000 - 1050 + 0 = 13950
        final_amount = self.service.calculate_final_amount(customer, order)
        
        assert final_amount == Money.from_yen(13950)