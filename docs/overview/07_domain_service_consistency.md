# Domain Serviceと整合性モデル

## Domain Serviceの本質

Domain Serviceは「**複数の集約にまたがるビジネスロジック**」を表現する場所であり、
整合性モデル（トランザクション/結果整合性）とは**独立した概念**です。

## Domain Service ≠ 整合性の決定

### Domain Serviceの責務
```typescript
// Domain Service：ビジネスルールを表現
interface PricingService {
  // 「価格計算のルール」を定義（HOW TO実装は知らない）
  calculatePrice(
    product: Product,
    customer: Customer,
    quantity: number
  ): Money;
}
```

### 整合性は実装層で決定

```typescript
// 実装1：同期的に計算（トランザクション整合性）
class SyncPricingService implements PricingService {
  calculatePrice(product: Product, customer: Customer, quantity: number): Money {
    const basePrice = product.getPrice();
    const discount = customer.getDiscountRate();
    return basePrice.multiply(quantity).applyDiscount(discount);
    // 即座に結果を返す
  }
}

// 実装2：非同期で計算（結果整合性）
class AsyncPricingService implements PricingService {
  async calculatePrice(
    product: Product, 
    customer: Customer, 
    quantity: number
  ): Promise<Money> {
    // イベント発行して後で計算
    await this.eventBus.publish(new PriceCalculationRequested(
      product.id,
      customer.id,
      quantity
    ));
    // 一旦仮の価格を返す
    return product.getPrice().multiply(quantity);
  }
}
```

## 具体例：在庫確認サービス

### Domain Service定義（ビジネスロジックのみ）
```typescript
// ドメイン層：純粋なビジネスルール
class InventoryCheckService {
  // ビジネスルール：在庫確認のロジック
  canFulfillOrder(
    order: Order,
    inventories: Map<ProductId, Inventory>
  ): boolean {
    for (const item of order.getItems()) {
      const inventory = inventories.get(item.productId);
      if (!inventory || !inventory.hasStock(item.quantity)) {
        return false;
      }
    }
    return true;
  }
  
  // ビジネスルール：予約可能かの判定
  canReserve(
    product: Product,
    inventory: Inventory,
    quantity: number
  ): ReservationResult {
    if (inventory.availableQuantity < quantity) {
      return ReservationResult.insufficient();
    }
    
    if (product.isDiscontinued()) {
      return ReservationResult.productUnavailable();
    }
    
    return ReservationResult.available();
  }
}
```

### Application Serviceで整合性を選択

```typescript
// アプリケーション層：整合性モデルを決定

// パターン1：トランザクション整合性で実装
class TransactionalOrderService {
  constructor(
    private inventoryCheckService: InventoryCheckService,
    private db: Database
  ) {}
  
  async placeOrder(orderId: string): Promise<void> {
    await this.db.transaction(async (trx) => {
      const order = await this.orderRepo.find(orderId, trx);
      const inventories = await this.inventoryRepo.findByProducts(
        order.getProductIds(),
        trx
      );
      
      // Domain Serviceでビジネスルール適用
      if (!this.inventoryCheckService.canFulfillOrder(order, inventories)) {
        throw new InsufficientInventoryError();
      }
      
      // 同一トランザクションで更新
      for (const [productId, inventory] of inventories) {
        inventory.reserve(order.getQuantityFor(productId));
        await this.inventoryRepo.save(inventory, trx);
      }
      
      order.confirm();
      await this.orderRepo.save(order, trx);
    });
  }
}

// パターン2：結果整合性で実装
class EventualOrderService {
  constructor(
    private inventoryCheckService: InventoryCheckService,
    private eventBus: EventBus
  ) {}
  
  async placeOrder(orderId: string): Promise<void> {
    // まず注文を確定
    const order = await this.orderRepo.find(orderId);
    order.confirm();
    await this.orderRepo.save(order);
    
    // 在庫確認は非同期で実行
    await this.eventBus.publish(new OrderPlaced(order));
  }
  
  // 別のハンドラで在庫確認
  async handleOrderPlaced(event: OrderPlaced): Promise<void> {
    const order = await this.orderRepo.find(event.orderId);
    const inventories = await this.inventoryRepo.findByProducts(
      event.productIds
    );
    
    // Domain Serviceでビジネスルール適用（同じロジック）
    if (!this.inventoryCheckService.canFulfillOrder(order, inventories)) {
      // 補償処理
      await this.eventBus.publish(new OrderCancelled(event.orderId));
      return;
    }
    
    // 非同期で在庫を更新
    for (const [productId, inventory] of inventories) {
      await this.eventBus.publish(new ReserveInventory(productId, quantity));
    }
  }
}
```

## Domain Serviceの設計指針

### 1. 整合性に依存しない設計

```typescript
// ❌ 悪い例：整合性を前提とした設計
class BadTransferService {
  async transfer(from: Account, to: Account, amount: Money) {
    await this.db.transaction(async () => {
      // トランザクションに依存した実装
      from.withdraw(amount);
      to.deposit(amount);
    });
  }
}

// ✅ 良い例：純粋なビジネスロジック
class GoodTransferService {
  // ビジネスルールのみ
  validateTransfer(from: Account, to: Account, amount: Money): ValidationResult {
    if (from.balance.lessThan(amount)) {
      return ValidationResult.insufficientFunds();
    }
    
    if (to.isBlocked()) {
      return ValidationResult.accountBlocked();
    }
    
    return ValidationResult.valid();
  }
  
  // 実行方法は呼び出し側が決める
  prepareTransfer(from: Account, to: Account, amount: Money): TransferCommand {
    return new TransferCommand(from.id, to.id, amount);
  }
}
```

### 2. ステートレスな設計

```typescript
// Domain Serviceはステートレス
class ShippingCostCalculator {
  // 純粋関数：入力から出力を計算
  calculate(
    destination: Address,
    weight: Weight,
    shippingMethod: ShippingMethod
  ): Money {
    // ビジネスルールに基づいて計算
    const baseRate = this.getBaseRate(shippingMethod);
    const distanceMultiplier = this.calculateDistance(destination);
    const weightMultiplier = this.calculateWeightFactor(weight);
    
    return baseRate
      .multiply(distanceMultiplier)
      .multiply(weightMultiplier);
  }
}
```

## 整合性選択の判断基準

```typescript
class ConsistencyDecisionMatrix {
  // Domain Serviceを使う際の整合性選択
  chooseConsistencyModel(context: BusinessContext): ConsistencyModel {
    
    // Domain Serviceの種類は関係ない
    // ビジネス要件で判断
    
    if (context.requiresImmediate) {
      // 即座に結果が必要 → トランザクション
      return 'TRANSACTIONAL';
    }
    
    if (context.canTolerateDelay) {
      // 遅延OK → 結果整合性
      return 'EVENTUAL';
    }
    
    if (context.hasCompensation) {
      // 補償可能 → 結果整合性
      return 'EVENTUAL';
    }
    
    // デフォルトは結果整合性（スケーラビリティ優先）
    return 'EVENTUAL';
  }
}
```

## まとめ

### Domain Serviceの役割
- **ビジネスロジック**の表現
- **複数集約**にまたがる処理の調整
- **ドメイン知識**のカプセル化

### 整合性の選択
- Domain Serviceとは**独立**した判断
- **ビジネス要件**に基づいて決定
- **実装時**（Application Service）で選択

### 推奨アプローチ

1. **Domain Service**：純粋なビジネスロジックとして設計
2. **Application Service**：整合性モデルを選択して実装
3. **デフォルト**：結果整合性を優先
4. **例外**：ビジネス上必要な場合のみトランザクション整合性

```typescript
// 理想的な構造
class OrderProcessing {
  // Domain層：ビジネスルール
  private domainService = new OrderValidationService();
  
  // Application層：整合性の選択
  async process(order: Order) {
    // ビジネスルールの適用
    const validation = this.domainService.validate(order);
    
    if (validation.requiresImmediateConsistency) {
      // トランザクション整合性
      await this.processWithTransaction(order);
    } else {
      // 結果整合性（デフォルト）
      await this.processWithEventualConsistency(order);
    }
  }
}
```