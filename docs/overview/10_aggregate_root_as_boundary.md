# Aggregate Rootが境界のゲートキーパーである理由

## Aggregate Rootの本質：境界の守護者

Aggregate Rootは、集約の**唯一の入り口**として、データの整合性とビジネスルールを守る門番の役割を果たします。

## なぜAggregate Root経由でアクセスするのか

### 1. 整合性の保証

```typescript
// ❌ 悪い例：直接子Entityにアクセス
class OrderItemRepository {
  async updateQuantity(itemId: string, quantity: number) {
    const item = await this.findById(itemId);
    item.quantity = quantity;  // 直接変更
    await this.save(item);
    // ⚠️ Order全体の合計金額が狂う！
  }
}

// ✅ 良い例：Aggregate Root経由
class OrderRepository {
  async updateItemQuantity(orderId: string, itemId: string, quantity: number) {
    const order = await this.findById(orderId);  // Aggregate全体を取得
    order.updateItemQuantity(itemId, quantity);   // Root経由で変更
    await this.save(order);  // 整合性が保たれた状態で保存
  }
}

class Order {  // Aggregate Root
  private items: OrderItem[];
  private totalAmount: Money;
  
  updateItemQuantity(itemId: string, quantity: number): void {
    const item = this.items.find(i => i.id === itemId);
    item.updateQuantity(quantity);
    this.recalculateTotal();  // 整合性を保つ
    this.validateBusinessRules();  // ルールチェック
  }
}
```

### 2. カプセル化の実現

```typescript
// Aggregate内部構造を隠蔽
class Order {  // Aggregate Root
  private items: OrderItem[];
  private shipping: ShippingInfo;
  
  // 外部は内部構造を知らない
  ship(): void {
    // 内部でどう実装されているかは隠蔽
    if (!this.isPaid()) {
      throw new Error("未払いの注文は出荷できません");
    }
    
    this.shipping.markAsShipped();
    this.notifyCustomer();
  }
  
  // 必要な情報だけを公開
  getShippingStatus(): ShippingStatus {
    return this.shipping.getStatus();  // 読み取り専用
  }
}

// 外部からは
const order = await orderRepo.findById(orderId);
order.ship();  // 詳細を知らなくても使える
```

### 3. トランザクション境界の明確化

```typescript
class OrderService {
  async placeOrder(orderId: string) {
    // 1つのAggregate = 1つのトランザクション
    await this.transaction(async () => {
      const order = await this.orderRepo.findById(orderId);
      order.place();  // Aggregate Root経由
      await this.orderRepo.save(order);  // 全体を保存
    });
  }
}
```

## 境界づけられたコンテキスト間の連携

### Aggregate Rootが境界の接点となる

```typescript
// 販売コンテキスト
namespace SalesContext {
  class Order {  // Aggregate Root
    private id: OrderId;
    private customerId: CustomerId;
    private items: OrderItem[];
    
    // 他のコンテキストとの連携ポイント
    toShippingRequest(): ShippingRequest {
      return new ShippingRequest(
        this.id.value,
        this.getShippingAddress(),
        this.getItemSummary()
      );
    }
  }
}

// 配送コンテキスト
namespace ShippingContext {
  class Shipment {  // Aggregate Root
    static createFromOrder(request: ShippingRequest): Shipment {
      // 販売コンテキストのOrderとは直接やり取りしない
      // Aggregate Rootが提供するデータ経由
      return new Shipment(
        ShipmentId.generate(),
        request.orderId,
        request.address,
        request.items
      );
    }
  }
}

// コンテキスト間の連携
class ContextBridge {
  async createShipment(orderId: string) {
    // Sales Context のAggregate Root経由
    const order = await this.salesRepo.findOrderById(orderId);
    const shippingRequest = order.toShippingRequest();
    
    // Shipping Context のAggregate Root経由
    const shipment = Shipment.createFromOrder(shippingRequest);
    await this.shippingRepo.save(shipment);
  }
}
```

## Aggregate Rootのアクセスパターン

### 1. Repositoryパターン

```typescript
// RepositoryはAggregate Root単位で作る
interface OrderRepository {
  findById(id: OrderId): Promise<Order>;
  save(order: Order): Promise<void>;
  delete(id: OrderId): Promise<void>;
}

// ❌ 子Entity用のRepositoryは作らない
interface OrderItemRepository {  // これはアンチパターン
  findById(id: OrderItemId): Promise<OrderItem>;
}
```

### 2. Factoryパターン

```typescript
// Aggregate全体を生成
class OrderFactory {
  static createNewOrder(
    customerId: CustomerId,
    items: CreateOrderItemDto[]
  ): Order {
    const order = new Order(customerId);
    
    items.forEach(item => {
      order.addItem(item.productId, item.quantity, item.price);
    });
    
    return order;  // 整合性の取れたAggregate全体を返す
  }
}
```

### 3. Domain Serviceパターン

```typescript
class PricingService {
  // Aggregate Root同士の調整
  calculateDiscount(
    order: Order,      // Aggregate Root
    customer: Customer  // 別のAggregate Root
  ): Discount {
    const customerLevel = customer.getLoyaltyLevel();
    const orderAmount = order.getTotalAmount();
    
    // Aggregate Rootが提供する情報のみ使用
    return this.discountPolicy.calculate(customerLevel, orderAmount);
  }
}
```

## Aggregate Rootの責務

### 1. ゲートキーパー（門番）
```typescript
class Order {
  // すべての変更はRoot経由
  addItem(item: OrderItem): void {
    this.validateCanAddItem();  // 検証
    this.items.push(item);
    this.maintainInvariant();   // 不変条件維持
  }
}
```

### 2. コーディネーター（調整役）
```typescript
class Order {
  // 内部の調整
  cancel(): void {
    this.status = OrderStatus.CANCELLED;
    this.items.forEach(item => item.markAsCancelled());
    this.shipping?.cancel();
    this.raiseDomainEvent(new OrderCancelled(this.id));
  }
}
```

### 3. トランスレーター（翻訳者）
```typescript
class Order {
  // 外部向けのインターフェース
  toInvoice(): Invoice {
    return new Invoice(
      this.id,
      this.getCustomerInfo(),
      this.getItemDetails(),
      this.calculateTax()
    );
  }
}
```

## まとめ：Aggregate Rootの本質

### 境界の守護者として

1. **整合性の番人**：集約内のデータ整合性を保証
2. **ルールの執行者**：ビジネスルールを強制
3. **アクセスの管理者**：外部からの唯一の入り口
4. **コンテキストの接点**：他の境界との連携ポイント

### 設計の原則

```typescript
// 原則1：外部はAggregate Root経由でのみアクセス
const order = await orderRepo.findById(orderId);
order.doSomething();  // OK

// 原則2：子Entityへの直接アクセスは禁止
const item = order.getItem(itemId);  // NG（直接返さない）
order.updateItem(itemId, data);       // OK（Root経由）

// 原則3：Repository/FactoryはAggregate Root単位
class OrderRepository { }   // OK
class OrderItemRepository { }  // NG
```

Aggregate Rootは、DDDにおける境界管理の中核であり、システムの整合性と保守性を支える重要な概念です。