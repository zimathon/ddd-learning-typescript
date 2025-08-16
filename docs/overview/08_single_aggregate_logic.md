# 境界をまたがない処理の実装場所

## 基本原則：集約自身が責任を持つ

**単一集約内で完結する処理は、その集約（主にAggregate Root）に実装します。**

## 実装場所の判断フロー

```
処理が...
├─ 単一集約内で完結する？
│  └─ Yes → Aggregate（Entity）に実装
│  
├─ 複数集約にまたがる？
│  └─ Yes → Domain Serviceに実装
│  
├─ 技術的関心事を含む？
│  └─ Yes → Application Serviceに実装
│  
└─ 外部システムとの連携？
   └─ Yes → Application Service + Infrastructure層
```

## 具体例：どこに実装するか

### 1. Aggregate内に実装すべき処理

```typescript
// Order集約
class Order {
  private items: OrderItem[] = [];
  private status: OrderStatus;
  private totalAmount: Money;
  
  // ✅ 集約内で完結：Order自身に実装
  addItem(productId: ProductId, quantity: number, price: Money): void {
    // Order集約内のビジネスルール
    if (this.status !== OrderStatus.DRAFT) {
      throw new Error("確定済みの注文は変更できません");
    }
    
    if (this.items.length >= 100) {
      throw new Error("注文は最大100品目まで");
    }
    
    const item = new OrderItem(productId, quantity, price);
    this.items.push(item);
    this.recalculateTotal();
  }
  
  // ✅ 集約内で完結：Order自身に実装
  applyDiscount(discountRate: number): void {
    // Order集約内での割引適用
    if (discountRate < 0 || discountRate > 0.5) {
      throw new Error("割引率は0-50%の範囲");
    }
    
    this.totalAmount = this.totalAmount.multiply(1 - discountRate);
  }
  
  // ✅ 集約内で完結：Order自身に実装
  cancel(): void {
    // Order集約の状態遷移
    if (this.status === OrderStatus.SHIPPED) {
      throw new Error("出荷済みの注文はキャンセルできません");
    }
    
    this.status = OrderStatus.CANCELLED;
    this.addDomainEvent(new OrderCancelled(this.id));
  }
  
  // ✅ 集約内で完結：計算ロジック
  private recalculateTotal(): void {
    this.totalAmount = this.items.reduce(
      (sum, item) => sum.add(item.getSubtotal()),
      Money.zero()
    );
  }
}

// Customer集約
class Customer {
  private email: Email;
  private status: CustomerStatus;
  private loyaltyPoints: number;
  
  // ✅ 集約内で完結：Customer自身に実装
  changeEmail(newEmail: Email): void {
    // Customer集約内のビジネスルール
    if (this.email.equals(newEmail)) {
      return; // 同じメールアドレスなら何もしない
    }
    
    this.email = newEmail;
    this.addDomainEvent(new CustomerEmailChanged(this.id, newEmail));
  }
  
  // ✅ 集約内で完結：Customer自身に実装
  addLoyaltyPoints(points: number): void {
    // Customer集約内のポイント管理
    if (points <= 0) {
      throw new Error("ポイントは正の値である必要があります");
    }
    
    this.loyaltyPoints += points;
    
    // VIP昇格チェック
    if (this.loyaltyPoints >= 10000 && this.status !== CustomerStatus.VIP) {
      this.status = CustomerStatus.VIP;
      this.addDomainEvent(new CustomerUpgradedToVIP(this.id));
    }
  }
}
```

### 2. Domain Serviceに実装すべき処理

```typescript
// ❌ 間違い：複数集約にまたがる処理をEntityに実装
class Order {
  // Orderが他の集約を知っている（良くない）
  checkInventory(inventory: Inventory): boolean {
    // ...
  }
}

// ✅ 正解：Domain Serviceに実装
class OrderFulfillmentService {
  // 複数集約（Order + Inventory）にまたがる処理
  canFulfillOrder(order: Order, inventories: Inventory[]): boolean {
    for (const item of order.getItems()) {
      const inventory = inventories.find(i => i.productId.equals(item.productId));
      if (!inventory || !inventory.hasStock(item.quantity)) {
        return false;
      }
    }
    return true;
  }
}
```

## よくある間違いと修正

### アンチパターン1：貧血症ドメインモデル

```typescript
// ❌ 悪い例：ロジックがない（貧血症）
class Order {
  items: OrderItem[];
  totalAmount: Money;
  status: OrderStatus;
  // セッターゲッターだけ...
}

// ロジックが外部に漏れている
class OrderService {
  addItemToOrder(order: Order, item: OrderItem) {
    if (order.status !== OrderStatus.DRAFT) {
      throw new Error("...");
    }
    order.items.push(item);
    order.totalAmount = this.calculateTotal(order.items);
  }
}
```

### 修正後：リッチなドメインモデル

```typescript
// ✅ 良い例：ロジックを持つ
class Order {
  private items: OrderItem[] = [];
  private totalAmount: Money;
  private status: OrderStatus;
  
  // ビジネスロジックは集約内に
  addItem(productId: ProductId, quantity: number, price: Money): void {
    this.validateCanAddItem();
    const item = new OrderItem(productId, quantity, price);
    this.items.push(item);
    this.recalculateTotal();
  }
  
  private validateCanAddItem(): void {
    if (this.status !== OrderStatus.DRAFT) {
      throw new Error("確定済みの注文は変更できません");
    }
  }
  
  private recalculateTotal(): void {
    this.totalAmount = this.items.reduce(
      (sum, item) => sum.add(item.getSubtotal()),
      Money.zero()
    );
  }
}
```

### アンチパターン2：過度に大きな集約

```typescript
// ❌ 悪い例：関係ないロジックまで含んでいる
class Order {
  // 注文の責務
  addItem() { }
  cancel() { }
  
  // これらは別の場所に置くべき
  sendEmail() { }          // → Infrastructure層
  calculateTax() { }        // → Domain Service（税制は複雑）
  checkCreditCard() { }     // → Application Service
  generateInvoicePDF() { }  // → Infrastructure層
}
```

### 修正後：適切な責務分離

```typescript
// ✅ 良い例：Order集約は注文の責務のみ
class Order {
  // 注文の核心的な責務のみ
  addItem(productId: ProductId, quantity: number, price: Money): void { }
  cancel(): void { }
  place(): void { }
  
  // 他の責務は適切な場所へ
}

// 税計算は別のDomain Serviceで
class TaxCalculationService {
  calculate(order: Order, taxRate: TaxRate): Money { }
}

// メール送信はInfrastructure層で
class EmailService {
  sendOrderConfirmation(order: Order): void { }
}
```

## 実装場所の早見表

| 処理内容 | 実装場所 | 例 |
|---------|----------|-----|
| **単一集約の状態変更** | Aggregate | `order.cancel()` |
| **単一集約内の計算** | Aggregate | `order.calculateTotal()` |
| **単一集約のバリデーション** | Aggregate | `order.validateItems()` |
| **複数集約の調整** | Domain Service | `pricingService.calculate(order, customer)` |
| **複雑な業務ルール** | Domain Service | `creditCheckService.evaluate()` |
| **外部システム連携** | Application Service | `paymentService.process()` |
| **トランザクション管理** | Application Service | `orderUseCase.placeOrder()` |
| **技術的な処理** | Infrastructure | `emailSender.send()` |

## まとめ

### 基本方針

1. **まずAggregate内に実装できないか考える**
   - 単一集約で完結するならAggregate内に

2. **複数集約にまたがるならDomain Service**
   - ただし純粋なビジネスロジックのみ

3. **技術的関心事はApplication Service以下**
   - DB、API、メール送信など

### コードの匂い（Code Smell）

- Aggregateが貧血症 → ロジックを集約内に移動
- Aggregateが肥大化 → Domain Serviceに分離を検討
- Domain Serviceが技術詳細を知っている → Application Serviceに移動

適切な場所に適切なロジックを置くことで、保守性の高いコードになります。