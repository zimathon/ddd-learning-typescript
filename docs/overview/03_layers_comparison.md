# AggregateとUse Case層の違い

## レイヤーアーキテクチャにおける位置づけ

```
┌─────────────────────────────────────┐
│   Presentation層（Controller）       │
├─────────────────────────────────────┤
│   Application層（Use Case）          │ ← ユースケース層
├─────────────────────────────────────┤
│   Domain層（Entity, Aggregate）      │ ← Aggregateはここ
├─────────────────────────────────────┤
│   Infrastructure層（DB, API）        │
└─────────────────────────────────────┘
```

## それぞれの役割と責務

### Domain層：Aggregate（Order）
**ビジネスルールとデータの整合性を守る**

```typescript
// Domain層：Order Aggregate
class Order {
  private items: OrderItem[] = [];
  private totalAmount: Money;
  
  // ビジネスルール：注文には最低1つの商品が必要
  addItem(productId: ProductId, quantity: number, price: Money): void {
    if (quantity <= 0) {
      throw new Error("数量は1以上である必要があります");
    }
    
    const item = new OrderItem(productId, quantity, price);
    this.items.push(item);
    this.recalculateTotal();  // 整合性を保つ
  }
  
  // ビジネスルール：下書き状態のみ確定可能
  place(): void {
    if (this.status !== OrderStatus.DRAFT) {
      throw new Error("下書き状態の注文のみ確定できます");
    }
    if (this.items.length === 0) {
      throw new Error("商品が選択されていません");
    }
    this.status = OrderStatus.PLACED;
  }
}
```

**特徴**：
- ビジネスルールの実装
- データの整合性保証
- 状態管理
- 技術的な詳細を知らない（DBやAPIを知らない）

### Application層：Use Case
**ユーザーの操作を実現する流れを管理**

```typescript
// Application層：注文確定のユースケース
class PlaceOrderUseCase {
  constructor(
    private orderRepository: OrderRepository,
    private inventoryService: InventoryService,
    private paymentService: PaymentService,
    private emailService: EmailService
  ) {}
  
  async execute(dto: PlaceOrderDto): Promise<OrderResult> {
    // 1. 注文を取得
    const order = await this.orderRepository.findById(dto.orderId);
    if (!order) throw new OrderNotFound();
    
    // 2. 在庫を確認
    for (const item of order.getItems()) {
      const available = await this.inventoryService.checkStock(
        item.productId, 
        item.quantity
      );
      if (!available) throw new InsufficientStock();
    }
    
    // 3. 支払い処理
    const payment = await this.paymentService.process(
      order.getTotalAmount(),
      dto.paymentMethod
    );
    
    // 4. 注文を確定（ドメインロジック）
    order.place();  // Aggregateのメソッドを呼ぶ
    
    // 5. 保存
    await this.orderRepository.save(order);
    
    // 6. 在庫を減らす
    await this.inventoryService.reserve(order);
    
    // 7. 確認メール送信
    await this.emailService.sendOrderConfirmation(order);
    
    return OrderResult.from(order);
  }
}
```

**特徴**：
- 複数のドメインオブジェクトを協調させる
- 外部サービスとの連携
- トランザクション管理
- ユースケースの流れを制御

## 具体例で理解する

### シナリオ：「商品をカートに追加する」

#### Domain層（Aggregate）の責務
```typescript
class ShoppingCart {  // Aggregate
  private items: CartItem[] = [];
  
  // ビジネスルール：カートには最大20個まで
  addItem(productId: ProductId, quantity: number): void {
    if (this.items.length >= 20) {
      throw new CartLimitExceeded("カートには最大20個まで");
    }
    
    const existing = this.findItem(productId);
    if (existing) {
      existing.increaseQuantity(quantity);
    } else {
      this.items.push(new CartItem(productId, quantity));
    }
  }
}
```
**関心事**：「カートのルール」だけ

#### Application層（Use Case）の責務
```typescript
class AddToCartUseCase {
  async execute(dto: AddToCartDto): Promise<void> {
    // 1. 商品が存在するか確認
    const product = await this.productRepo.findById(dto.productId);
    if (!product) throw new ProductNotFound();
    
    // 2. 在庫があるか確認
    const hasStock = await this.inventoryService.check(
      dto.productId, 
      dto.quantity
    );
    if (!hasStock) throw new OutOfStock();
    
    // 3. カートを取得（なければ作成）
    let cart = await this.cartRepo.findByCustomerId(dto.customerId);
    if (!cart) {
      cart = new ShoppingCart(dto.customerId);
    }
    
    // 4. カートに追加（ドメインロジック）
    cart.addItem(dto.productId, dto.quantity);
    
    // 5. 保存
    await this.cartRepo.save(cart);
    
    // 6. レコメンド更新（副作用）
    await this.recommendService.updateBasedOnCart(cart);
  }
}
```
**関心事**：「ユーザー操作の全体的な流れ」

## まとめ：役割の違い

| 観点 | Aggregate（Domain層） | Use Case（Application層） |
|------|---------------------|------------------------|
| **責務** | ビジネスルールの実装 | ユースケースの実現 |
| **関心事** | データの整合性・不変条件 | 処理の流れ・外部連携 |
| **依存** | 何にも依存しない | Domain層・Infrastructure層に依存 |
| **例** | 「注文には商品が必要」 | 「注文確定時は在庫確認→支払い→メール送信」 |
| **変更理由** | ビジネスルールが変わった時 | 業務フローが変わった時 |

### 簡単に言うと

- **Aggregate**：「注文とは何か」「注文のルール」を定義（What）
- **Use Case**：「注文をどう処理するか」の手順を定義（How）

AggregateはUse Caseに**使われる**側で、ビジネスの核となるルールを守る役割です。