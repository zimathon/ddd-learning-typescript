import { ProductId } from './ProductId';
import { Money } from '../shared/Money';

/**
 * OrderItem Entity (Aggregate内の子Entity)
 * 注文明細を表現するエンティティ
 */
export class OrderItem {
  private readonly productId: ProductId;
  private quantity: number;
  private readonly unitPrice: Money;

  constructor(productId: ProductId, quantity: number, unitPrice: Money) {
    if (quantity <= 0) {
      throw new Error('数量は1以上である必要があります');
    }
    
    this.productId = productId;
    this.quantity = quantity;
    this.unitPrice = unitPrice;
  }

  changeQuantity(newQuantity: number): void {
    if (newQuantity <= 0) {
      throw new Error('数量は1以上である必要があります');
    }
    this.quantity = newQuantity;
  }

  getSubtotal(): Money {
    return this.unitPrice.multiply(this.quantity);
  }

  hasProduct(productId: ProductId): boolean {
    return this.productId.equals(productId);
  }

  getProductId(): ProductId {
    return this.productId;
  }

  getQuantity(): number {
    return this.quantity;
  }

  getUnitPrice(): Money {
    return this.unitPrice;
  }
}