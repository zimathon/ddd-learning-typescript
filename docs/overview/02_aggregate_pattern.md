# Aggregate（集約）パターンの解説

## Aggregateとは何か

Aggregate（集約）は、**関連するオブジェクトのまとまり**で、**データ変更の単位**として扱われます。
一言で言えば「**一緒に扱うべきオブジェクトのグループ**」です。

## なぜAggregateが必要か

### 問題：データの整合性
```typescript
// Aggregateを使わない場合の問題
class Order {
  items: OrderItem[];
  totalAmount: Money;
}

// 別の場所でOrderItemを直接変更
orderItem.changeQuantity(10);
// → Order.totalAmountと不整合が発生！
```

### 解決：Aggregateによる保護
```typescript
// Order Aggregateで整合性を保護
class Order {
  private items: OrderItem[];
  private totalAmount: Money;
  
  // Aggregateを通じてのみ変更可能
  changeItemQuantity(itemId: string, quantity: number) {
    const item = this.findItem(itemId);
    item.changeQuantity(quantity);
    this.recalculateTotal();  // 整合性を保つ
  }
}
```

## Order Aggregateの具体例

### 1. Aggregate Root（集約ルート）
```typescript
// OrderがAggregate Root
class Order {
  private readonly id: OrderId;
  private customerId: CustomerId;
  private items: OrderItem[] = [];  // 子エンティティ
  private shippingAddress: Address; // 値オブジェクト
  private totalAmount: Money;
  private status: OrderStatus;
  
  // 外部からはOrderを通じてのみアクセス
  addItem(productId: ProductId, quantity: number, price: Money) {
    // ビジネスルール：最大10種類まで
    if (this.items.length >= 10) {
      throw new Error("注文には最大10種類まで追加可能");
    }
    
    const item = new OrderItem(productId, quantity, price);
    this.items.push(item);
    this.recalculateTotal();
  }
}
```

### 2. 子エンティティ
```typescript
// OrderItemは単独では存在できない
class OrderItem {
  constructor(
    private productId: ProductId,
    private quantity: number,
    private unitPrice: Money
  ) {}
  
  // Orderの文脈でのみ意味を持つ
  getSubtotal(): Money {
    return this.unitPrice.multiply(this.quantity);
  }
}
```

## Aggregateの重要なルール

### 1. トランザクション境界
```typescript
// ✅ 良い例：1つのAggregateを1トランザクションで更新
async placeOrder(order: Order) {
  await this.orderRepository.save(order);
}

// ❌ 悪い例：複数のAggregateを同時に更新
async placeOrder(order: Order, inventory: Inventory) {
  await this.orderRepository.save(order);
  await this.inventoryRepository.save(inventory);  // 別Aggregate
}
```

### 2. 外部参照はIDのみ
```typescript
class Order {
  // ❌ 悪い例：別AggregateのEntityを直接保持
  private customer: Customer;
  
  // ✅ 良い例：IDのみを保持
  private customerId: CustomerId;
}
```

### 3. 不変条件の保護
```typescript
class Order {
  private items: OrderItem[] = [];
  private totalAmount: Money;
  
  // 不変条件：totalAmountは常にitemsの合計と一致
  private recalculateTotal() {
    this.totalAmount = this.items.reduce(
      (sum, item) => sum.add(item.getSubtotal()),
      Money.zero()
    );
  }
}
```

## Order Aggregateの境界設計

### 含めるべきもの
- **Order**（注文本体）
- **OrderItem**（注文明細）
- **ShippingAddress**（配送先）
- **PaymentMethod**（支払い方法）

### 含めるべきでないもの
- **Customer**（顧客） → 別Aggregate
- **Product**（商品） → 別Aggregate
- **Inventory**（在庫） → 別Aggregate

## 実装例：完全なOrder Aggregate

```typescript
// Aggregate Root
class Order {
  private readonly id: OrderId;
  private customerId: CustomerId;
  private items: OrderItem[] = [];
  private shippingAddress: Address;
  private status: OrderStatus;
  private totalAmount: Money;
  private placedAt?: Date;
  
  constructor(customerId: CustomerId, shippingAddress: Address) {
    this.id = OrderId.generate();
    this.customerId = customerId;
    this.shippingAddress = shippingAddress;
    this.status = OrderStatus.DRAFT;
    this.totalAmount = Money.zero();
  }
  
  // ビジネスメソッド
  addItem(productId: ProductId, quantity: number, unitPrice: Money): void {
    this.ensureCanModify();
    
    // 同じ商品は数量を増やす
    const existingItem = this.items.find(i => i.hasProduct(productId));
    if (existingItem) {
      existingItem.increaseQuantity(quantity);
    } else {
      this.items.push(new OrderItem(productId, quantity, unitPrice));
    }
    
    this.recalculateTotal();
  }
  
  removeItem(productId: ProductId): void {
    this.ensureCanModify();
    this.items = this.items.filter(i => !i.hasProduct(productId));
    this.recalculateTotal();
  }
  
  place(): void {
    if (this.status !== OrderStatus.DRAFT) {
      throw new Error("下書き状態の注文のみ確定できます");
    }
    
    if (this.items.length === 0) {
      throw new Error("商品が選択されていません");
    }
    
    this.status = OrderStatus.PLACED;
    this.placedAt = new Date();
  }
  
  cancel(): void {
    if (this.status !== OrderStatus.PLACED) {
      throw new Error("確定済みの注文のみキャンセル可能");
    }
    
    this.status = OrderStatus.CANCELLED;
  }
  
  // Helper methods
  private ensureCanModify(): void {
    if (this.status !== OrderStatus.DRAFT) {
      throw new Error("下書き状態の注文のみ変更可能");
    }
  }
  
  private recalculateTotal(): void {
    this.totalAmount = this.items.reduce(
      (sum, item) => sum.add(item.getSubtotal()),
      Money.zero()
    );
  }
  
  // Getters (読み取り専用)
  getId(): OrderId { return this.id; }
  getStatus(): OrderStatus { return this.status; }
  getTotalAmount(): Money { return this.totalAmount; }
  getItems(): ReadonlyArray<OrderItem> { return [...this.items]; }
}

// 子エンティティ
class OrderItem {
  constructor(
    private productId: ProductId,
    private quantity: number,
    private unitPrice: Money
  ) {
    if (quantity <= 0) {
      throw new Error("数量は1以上である必要があります");
    }
  }
  
  hasProduct(productId: ProductId): boolean {
    return this.productId.equals(productId);
  }
  
  increaseQuantity(amount: number): void {
    this.quantity += amount;
  }
  
  getSubtotal(): Money {
    return this.unitPrice.multiply(this.quantity);
  }
}

// 値オブジェクト
enum OrderStatus {
  DRAFT = "DRAFT",
  PLACED = "PLACED",
  PAID = "PAID",
  SHIPPED = "SHIPPED",
  DELIVERED = "DELIVERED",
  CANCELLED = "CANCELLED"
}
```

## Aggregateの利点

1. **整合性の保証**: データの不整合を防ぐ
2. **カプセル化**: ビジネスルールを一箇所に集約
3. **トランザクション管理**: 更新の単位が明確
4. **理解しやすさ**: 関連する概念がまとまっている

## まとめ

Order Aggregateは：
- **注文に関連するデータと振る舞いをまとめた単位**
- **注文の整合性を保護する境界**
- **ビジネスルールを実装する場所**

これにより、注文処理の複雑さを管理し、バグを防ぎ、ビジネスロジックを明確に表現できます。