import { Order } from '../order/Order';
import { Customer } from '../customer/Customer';
import { Money } from '../shared/Money';

/**
 * PricingService Domain Service
 * 価格計算に関するドメインサービス
 * 複数の集約をまたぐビジネスロジックを実装
 */
export class PricingService {
  
  /**
   * 顧客と注文に基づいて割引を計算
   */
  calculateDiscount(customer: Customer, order: Order): Money {
    if (!customer.isActive()) {
      return Money.zero();
    }
    
    const orderAmount = order.getTotalAmount();
    const loyaltyPoints = customer.getLoyaltyPoints();
    
    // TODO(human): 割引計算ロジックを実装
    // ヒント：
    // - loyaltyPointsに基づいた割引率を計算
    // - orderAmountの金額に応じた追加割引
    // - 最大割引率の制限（例：30%まで）
    
    let discountRate = 0;
    
    // ここに実装を追加してください
    
    return orderAmount.multiply(discountRate);
  }
  
  /**
   * 送料を計算
   */
  calculateShippingFee(order: Order): Money {
    const FREE_SHIPPING_THRESHOLD = Money.fromYen(5000);
    const STANDARD_SHIPPING_FEE = Money.fromYen(500);
    
    if (order.getTotalAmount().greaterThan(FREE_SHIPPING_THRESHOLD)) {
      return Money.zero();
    }
    
    return STANDARD_SHIPPING_FEE;
  }
  
  /**
   * 最終的な請求額を計算
   */
  calculateFinalAmount(customer: Customer, order: Order): Money {
    const subtotal = order.getTotalAmount();
    const discount = this.calculateDiscount(customer, order);
    const shipping = this.calculateShippingFee(order);
    
    return subtotal.subtract(discount).add(shipping);
  }
}