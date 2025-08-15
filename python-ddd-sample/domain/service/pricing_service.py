"""
PricingService Domain Service
価格計算に関するドメインサービス
複数の集約をまたぐビジネスロジックを実装
"""
from domain.order.order import Order
from domain.customer.customer import Customer
from domain.shared.money import Money


class PricingService:
    """価格計算ドメインサービス"""
    
    def calculate_discount(self, customer: Customer, order: Order) -> Money:
        """
        顧客と注文に基づいて割引を計算
        
        Args:
            customer: 顧客
            order: 注文
            
        Returns:
            割引金額
        """
        if not customer.is_active():
            return Money.zero()
        
        order_amount = order.total_amount
        loyalty_points = customer.loyalty_points
        
        # TODO(human): 割引計算ロジックを実装
        # ヒント：
        # - loyalty_pointsに基づいた割引率を計算
        # - order_amountの金額に応じた追加割引
        # - 最大割引率の制限（例：30%まで）
        
        discount_rate = 0.0
        
        # ここに実装を追加してください
        # Guidance: ロイヤリティポイントによる段階的な割引（例：1000ポイントで5%、2000ポイントで10%
        # ）、注文金額による追加割引（例：10000円以上で追加2%）、そして最大割引率の制限（例：30%まで
        # ）を考慮してください。計算結果はdiscount_rateとして0.0〜0.3の範囲の小数として表現し、最終
        # 的にorder_amount.multiply(discount_rate)で割引金額を返します。
        discount_rate = 0.0
        if loyalty_points >= 2000:
            discount_rate = 0.1
        elif loyalty_points >= 1000:
            discount_rate = 0.05
        if order_amount.greater_than_or_equal(Money.from_yen(10000)):
            discount_rate += 0.02
        if discount_rate > 0.3:
            discount_rate = 0.3

        return order_amount.multiply(discount_rate)
    
    def calculate_shipping_fee(self, order: Order) -> Money:
        """
        送料を計算
        
        Args:
            order: 注文
            
        Returns:
            送料
        """
        FREE_SHIPPING_THRESHOLD = Money.from_yen(5000)
        STANDARD_SHIPPING_FEE = Money.from_yen(500)
        
        if order.total_amount.greater_than_or_equal(FREE_SHIPPING_THRESHOLD):
            return Money.zero()
        
        return STANDARD_SHIPPING_FEE
    
    def calculate_final_amount(self, customer: Customer, order: Order) -> Money:
        """
        最終的な請求額を計算
        
        Args:
            customer: 顧客
            order: 注文
            
        Returns:
            最終請求額
        """
        subtotal = order.total_amount
        discount = self.calculate_discount(customer, order)
        shipping = self.calculate_shipping_fee(order)
        
        return subtotal.subtract(discount).add(shipping)