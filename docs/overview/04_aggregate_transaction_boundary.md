# 集約の境界とトランザクション整合性

## 基本原則：1集約 = 1トランザクション

**集約の境界は、トランザクションで一貫性を保証する範囲**を定義します。

## 具体例で理解する

### ✅ 正しい設計：1つの集約を1トランザクションで更新

```typescript
// Order集約のみを更新
class PlaceOrderUseCase {
  async execute(orderId: string) {
    // 1トランザクション = 1集約
    await this.transaction(async () => {
      const order = await this.orderRepo.findById(orderId);
      order.place();  // 注文確定
      await this.orderRepo.save(order);
    });
    
    // 別のトランザクションで在庫を更新（別集約）
    await this.inventoryService.reserve(orderId);
  }
}
```

### ❌ 間違った設計：複数の集約を同一トランザクションで更新

```typescript
// アンチパターン：複数集約を同時更新
class PlaceOrderUseCase {
  async execute(orderId: string) {
    await this.transaction(async () => {
      // Order集約
      const order = await this.orderRepo.findById(orderId);
      order.place();
      await this.orderRepo.save(order);
      
      // Inventory集約（別集約！）
      const inventory = await this.inventoryRepo.findByProductId(productId);
      inventory.decrease(quantity);
      await this.inventoryRepo.save(inventory);  // ❌ 同一トランザクション
    });
  }
}
```

## なぜ1集約1トランザクションなのか

### 1. パフォーマンスの問題

```typescript
// 大きすぎる集約の例
class Customer {
  private orders: Order[] = [];  // 全注文履歴（1000件以上）
  
  // 顧客情報を更新するだけで全注文をロック
  updateEmail(email: Email) {
    this.email = email;
    // 1000件の注文も一緒にロックされる！
  }
}
```

### 2. 並行性の問題

```typescript
// 複数集約を同時更新すると...
async placeOrder() {
  await transaction(() => {
    order.place();      // 注文をロック
    inventory.reserve(); // 在庫をロック
    // 他のユーザーが在庫を見れない！
  });
}
```

## 集約境界の決め方

### 原則：「一緒に変更されるものは同じ集約」

```typescript
// ✅ 良い例：注文と注文明細は一緒に変更される
class Order {
  private items: OrderItem[] = [];  // 一緒に更新される
  
  addItem(product: Product, quantity: number) {
    this.items.push(new OrderItem(product, quantity));
    this.recalculateTotal();  // 同時に更新
  }
}

// ❌ 悪い例：顧客と注文は別々に変更される
class Customer {
  private orders: Order[] = [];  // 別々に更新されるべき
}
```

## 結果整合性 vs トランザクション整合性

### トランザクション整合性（集約内）
**即座に整合性を保証**

```typescript
class Order {
  private items: OrderItem[] = [];
  private totalAmount: Money;
  
  addItem(item: OrderItem) {
    this.items.push(item);
    this.totalAmount = this.calculateTotal();  // 即座に更新
    // この時点で整合性が保証される
  }
}
```

### 結果整合性（集約間）
**最終的に整合性を保証**

```typescript
// 注文確定後、イベントで在庫を更新
class OrderService {
  async placeOrder(order: Order) {
    // 1. 注文を確定（トランザクション1）
    await this.orderRepo.save(order);
    
    // 2. イベント発行
    await this.eventBus.publish(new OrderPlaced(order));
  }
}

// 別のハンドラで在庫を更新（トランザクション2）
class InventoryHandler {
  async handle(event: OrderPlaced) {
    // 非同期で在庫を減らす（結果整合性）
    const inventory = await this.inventoryRepo.find(event.productId);
    inventory.decrease(event.quantity);
    await this.inventoryRepo.save(inventory);
  }
}
```

## 実践的な判断基準

### 同じ集約にすべきケース

1. **不変条件を共有**
   - 「注文の合計 = 明細の合計」のような条件

2. **同時に作成・削除**
   - 注文を削除したら明細も削除

3. **強い整合性が必要**
   - 即座に整合性が必要な場合

### 別の集約にすべきケース

1. **独立したライフサイクル**
   - 顧客は注文がなくても存在する

2. **異なる更新頻度**
   - 商品情報は頻繁に更新、注文は一度確定したら不変

3. **スケーラビリティの要求**
   - 在庫は多くのユーザーが同時アクセス

## 実例：ECサイトの集約設計

```typescript
// 集約1：注文
class Order {
  private items: OrderItem[];      // 同じ集約
  private shippingAddress: Address; // 同じ集約
  private payment: PaymentMethod;   // 同じ集約
}

// 集約2：顧客
class Customer {
  private profile: Profile;          // 同じ集約
  private email: Email;              // 同じ集約
  // orders: Order[] ← 含めない（別集約）
}

// 集約3：商品
class Product {
  private price: Money;              // 同じ集約
  private description: string;       // 同じ集約
  // inventory: number ← 含めない（別集約）
}

// 集約4：在庫
class Inventory {
  private productId: ProductId;      // ID参照のみ
  private quantity: number;          // 同じ集約
  private reservations: Reservation[]; // 同じ集約
}
```

## まとめ

**集約の境界 = トランザクション整合性の境界**

- 集約内：**強い整合性**（同一トランザクション）
- 集約間：**結果整合性**（別トランザクション、イベント駆動）

これにより：
- パフォーマンスの向上
- 並行性の改善
- システムのスケーラビリティ確保

が実現できます。