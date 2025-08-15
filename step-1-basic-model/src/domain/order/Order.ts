import { OrderId } from './OrderId';
import { CustomerId } from '../customer/CustomerId';
import { ProductId } from './ProductId';
import { OrderItem } from './OrderItem';
import { Money } from '../shared/Money';

export enum OrderStatus {
  DRAFT = 'DRAFT',
  PLACED = 'PLACED',
  PAID = 'PAID',
  SHIPPED = 'SHIPPED',
  DELIVERED = 'DELIVERED',
  CANCELLED = 'CANCELLED',
}

/**
 * Order Aggregate Root
 * 注文集約のルートエンティティ
 */
export class Order {
  private readonly id: OrderId;
  private readonly customerId: CustomerId;
  private items: OrderItem[];
  private status: OrderStatus;
  private totalAmount: Money;
  private placedAt?: Date;
  private readonly maxItems: number = 100;

  constructor(id: OrderId, customerId: CustomerId) {
    this.id = id;
    this.customerId = customerId;
    this.items = [];
    this.status = OrderStatus.DRAFT;
    this.totalAmount = Money.zero();
  }

  static create(customerId: CustomerId): Order {
    return new Order(OrderId.generate(), customerId);
  }

  /**
   * 商品を追加（Aggregate Rootを通じてのみアクセス）
   */
  addItem(productId: ProductId, quantity: number, unitPrice: Money): void {
    this.ensureCanModify();
    
    if (this.items.length >= this.maxItems) {
      throw new Error(`注文には最大${this.maxItems}個まで追加可能です`);
    }
    
    const existingItem = this.items.find(item => item.hasProduct(productId));
    
    if (existingItem) {
      existingItem.changeQuantity(existingItem.getQuantity() + quantity);
    } else {
      const newItem = new OrderItem(productId, quantity, unitPrice);
      this.items.push(newItem);
    }
    
    this.recalculateTotal();
  }

  /**
   * 商品を削除
   */
  removeItem(productId: ProductId): void {
    this.ensureCanModify();
    
    const index = this.items.findIndex(item => item.hasProduct(productId));
    if (index === -1) {
      throw new Error('指定された商品が見つかりません');
    }
    
    this.items.splice(index, 1);
    this.recalculateTotal();
  }

  /**
   * 商品の数量を変更
   */
  changeItemQuantity(productId: ProductId, newQuantity: number): void {
    this.ensureCanModify();
    
    const item = this.items.find(item => item.hasProduct(productId));
    if (!item) {
      throw new Error('指定された商品が見つかりません');
    }
    
    item.changeQuantity(newQuantity);
    this.recalculateTotal();
  }

  /**
   * 注文を確定
   */
  place(): void {
    if (this.status !== OrderStatus.DRAFT) {
      throw new Error('下書き状態の注文のみ確定できます');
    }
    
    if (this.items.length === 0) {
      throw new Error('商品が選択されていません');
    }
    
    this.status = OrderStatus.PLACED;
    this.placedAt = new Date();
  }

  /**
   * 支払い完了
   */
  markAsPaid(): void {
    if (this.status !== OrderStatus.PLACED) {
      throw new Error('確定済みの注文のみ支払い可能です');
    }
    
    this.status = OrderStatus.PAID;
  }

  /**
   * 出荷
   */
  ship(): void {
    if (this.status !== OrderStatus.PAID) {
      throw new Error('支払い済みの注文のみ出荷可能です');
    }
    
    this.status = OrderStatus.SHIPPED;
  }

  /**
   * 配送完了
   */
  deliver(): void {
    if (this.status !== OrderStatus.SHIPPED) {
      throw new Error('出荷済みの注文のみ配送完了にできます');
    }
    
    this.status = OrderStatus.DELIVERED;
  }

  /**
   * キャンセル
   */
  cancel(): void {
    if (this.status === OrderStatus.SHIPPED || 
        this.status === OrderStatus.DELIVERED ||
        this.status === OrderStatus.CANCELLED) {
      throw new Error('この注文はキャンセルできません');
    }
    
    this.status = OrderStatus.CANCELLED;
  }

  /**
   * 合計金額の再計算（内部メソッド）
   */
  private recalculateTotal(): void {
    this.totalAmount = this.items.reduce(
      (sum, item) => sum.add(item.getSubtotal()),
      Money.zero()
    );
  }

  /**
   * 変更可能かチェック（内部メソッド）
   */
  private ensureCanModify(): void {
    if (this.status !== OrderStatus.DRAFT) {
      throw new Error('下書き状態の注文のみ変更可能です');
    }
  }

  // Getters（読み取り専用）
  getId(): OrderId {
    return this.id;
  }

  getCustomerId(): CustomerId {
    return this.customerId;
  }

  getStatus(): OrderStatus {
    return this.status;
  }

  getTotalAmount(): Money {
    return this.totalAmount;
  }

  getPlacedAt(): Date | undefined {
    return this.placedAt;
  }

  getItemCount(): number {
    return this.items.length;
  }

  /**
   * 注文明細のスナップショットを返す
   * （直接の参照を返さない）
   */
  getItems(): ReadonlyArray<{
    productId: ProductId;
    quantity: number;
    unitPrice: Money;
    subtotal: Money;
  }> {
    return this.items.map(item => ({
      productId: item.getProductId(),
      quantity: item.getQuantity(),
      unitPrice: item.getUnitPrice(),
      subtotal: item.getSubtotal(),
    }));
  }

  equals(other: Order): boolean {
    return this.id.equals(other.id);
  }
}