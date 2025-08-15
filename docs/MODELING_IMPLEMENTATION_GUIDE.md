# DDD モデリング/実装ガイド - 実践的学習プラン

## 概要

このガイドは、モデリングから実装まで一貫したDDDの実践方法を学ぶための構成です。
特に日本の開発現場でよく遭遇する課題とその解決策に焦点を当てています。

## Part 1: ドメインモデリング編

### Chapter 1: ドメインモデリングの基礎

#### 1.1 モデリングセッションの実施方法

**イベントストーミング**
```typescript
// イベントストーミングの成果をコードに落とし込む
// オレンジ色の付箋：ドメインイベント
class OrderPlaced {
  constructor(
    public readonly orderId: string,
    public readonly occurredAt: Date
  ) {}
}

// 青色の付箋：コマンド
class PlaceOrder {
  constructor(
    public readonly customerId: string,
    public readonly items: OrderItem[]
  ) {}
}

// 黄色の付箋：アクター
enum Actor {
  Customer = "CUSTOMER",
  Admin = "ADMIN",
  System = "SYSTEM"
}

// ピンク色の付箋：外部システム
interface PaymentGateway {
  process(amount: Money): Promise<PaymentResult>;
}
```

#### 1.2 ユビキタス言語の構築

**用語集の管理**
```typescript
// ドメイン用語を型として表現
namespace DomainVocabulary {
  // 商品関連の用語
  export type SKU = string;           // 在庫管理単位
  export type ProductCode = string;   // 商品コード
  export type JAN = string;           // JANコード
  
  // 注文関連の用語
  export type BackOrder = Order & {   // 取り寄せ注文
    estimatedDeliveryDate: Date;
  };
  
  export type DropShipping = Order & { // 直送
    supplierId: string;
  };
}
```

#### 1.3 ドメインエキスパートとの協働

**実装例：ビジネスルールの明確化**
```typescript
// ドメインエキスパートとの対話から生まれたルール
class PricingRules {
  // 「大口割引は100個以上から適用」という業務知識
  static BULK_DISCOUNT_THRESHOLD = 100;
  static BULK_DISCOUNT_RATE = 0.1;
  
  // 「VIP会員は常に5%割引」
  static VIP_DISCOUNT_RATE = 0.05;
  
  // 「送料無料は5000円以上」
  static FREE_SHIPPING_THRESHOLD = new Money(5000, "JPY");
  
  calculateDiscount(
    quantity: number,
    customerType: CustomerType,
    subtotal: Money
  ): Money {
    let discountRate = 0;
    
    // ビジネスルールの実装
    if (quantity >= PricingRules.BULK_DISCOUNT_THRESHOLD) {
      discountRate += PricingRules.BULK_DISCOUNT_RATE;
    }
    
    if (customerType === CustomerType.VIP) {
      discountRate += PricingRules.VIP_DISCOUNT_RATE;
    }
    
    return subtotal.multiply(discountRate);
  }
}
```

### Chapter 2: 戦術的モデリング

#### 2.1 エンティティの設計

**実装例：ライフサイクルを持つエンティティ**
```typescript
// 商品のライフサイクル管理
class Product {
  private status: ProductStatus;
  private version: number = 0; // 楽観的ロック用
  
  constructor(
    private readonly id: ProductId,
    private name: string,
    private price: Money
  ) {
    this.status = ProductStatus.DRAFT;
  }
  
  // 状態遷移メソッド
  publish(): void {
    if (this.status !== ProductStatus.DRAFT) {
      throw new InvalidStateTransition(
        `Cannot publish product in ${this.status} status`
      );
    }
    
    this.validateForPublishing();
    this.status = ProductStatus.PUBLISHED;
    this.version++;
    
    // ドメインイベントの発行
    this.addDomainEvent(new ProductPublished(this.id));
  }
  
  private validateForPublishing(): void {
    if (!this.name || this.name.trim().length === 0) {
      throw new BusinessRuleViolation("Product name is required");
    }
    
    if (this.price.isNegative()) {
      throw new BusinessRuleViolation("Product price must be positive");
    }
  }
  
  discontinue(): void {
    if (this.status !== ProductStatus.PUBLISHED) {
      throw new InvalidStateTransition(
        `Cannot discontinue product in ${this.status} status`
      );
    }
    
    this.status = ProductStatus.DISCONTINUED;
    this.version++;
    this.addDomainEvent(new ProductDiscontinued(this.id));
  }
}
```

#### 2.2 値オブジェクトの設計

**実装例：複雑な値オブジェクト**
```typescript
// 住所の値オブジェクト（日本の住所体系に対応）
class JapaneseAddress {
  constructor(
    private readonly postalCode: PostalCode,
    private readonly prefecture: Prefecture,
    private readonly city: string,
    private readonly street: string,
    private readonly building?: string
  ) {
    this.validate();
  }
  
  private validate(): void {
    // 郵便番号と都道府県の整合性チェック
    if (!this.postalCode.matchesPrefecture(this.prefecture)) {
      throw new Error("郵便番号と都道府県が一致しません");
    }
  }
  
  // フォーマット済み住所の取得
  getFullAddress(): string {
    const parts = [
      `〒${this.postalCode.format()}`,
      this.prefecture.getName(),
      this.city,
      this.street
    ];
    
    if (this.building) {
      parts.push(this.building);
    }
    
    return parts.join(" ");
  }
  
  // 配送可能エリアかチェック
  isDeliverable(): boolean {
    // 離島や配送不可地域のチェック
    return !DeliveryBlacklist.includes(this.postalCode.toString());
  }
}

// 郵便番号の値オブジェクト
class PostalCode {
  private readonly value: string;
  
  constructor(value: string) {
    // ハイフンありなし両方に対応
    const normalized = value.replace(/[-－\s]/g, "");
    
    if (!/^\d{7}$/.test(normalized)) {
      throw new Error("郵便番号は7桁の数字である必要があります");
    }
    
    this.value = normalized;
  }
  
  format(): string {
    return `${this.value.slice(0, 3)}-${this.value.slice(3)}`;
  }
  
  matchesPrefecture(prefecture: Prefecture): boolean {
    // 郵便番号データベースとの照合（簡略化）
    const prefectureCode = this.value.slice(0, 2);
    return PostalCodeDatabase.getPrefecture(prefectureCode) === prefecture;
  }
}
```

#### 2.3 集約の設計

**実装例：適切な集約境界**
```typescript
// ショッピングカート集約
class ShoppingCart {
  private items: CartItem[] = [];
  private readonly maxItems = 100;
  
  constructor(
    private readonly id: CartId,
    private readonly customerId: CustomerId
  ) {}
  
  // 集約内の不変条件を守る
  addItem(productId: ProductId, quantity: number): void {
    // ビジネスルール：カートには最大100種類まで
    if (this.items.length >= this.maxItems) {
      throw new CartLimitExceeded();
    }
    
    // ビジネスルール：同一商品は数量を増やす
    const existingItem = this.items.find(
      item => item.productId.equals(productId)
    );
    
    if (existingItem) {
      existingItem.increaseQuantity(quantity);
    } else {
      this.items.push(new CartItem(productId, quantity));
    }
    
    // イベント発行
    this.addDomainEvent(
      new ItemAddedToCart(this.id, productId, quantity)
    );
  }
  
  // 集約をまたぐ操作は避ける
  // NG: checkout(inventory: Inventory, payment: Payment)
  // OK: checkout(): Order（別の集約を返す）
  checkout(): CheckoutCommand {
    if (this.items.length === 0) {
      throw new EmptyCartError();
    }
    
    // チェックアウトコマンドを返す（実際の処理は別の場所で）
    return new CheckoutCommand(
      this.customerId,
      this.items.map(item => item.toOrderItem())
    );
  }
  
  // 集約内の計算
  calculateTotal(priceList: PriceList): Money {
    return this.items.reduce(
      (total, item) => {
        const price = priceList.getPrice(item.productId);
        return total.add(price.multiply(item.quantity));
      },
      Money.zero("JPY")
    );
  }
}
```

### Chapter 3: 戦略的モデリング

#### 3.1 境界づけられたコンテキストの識別

**実装例：コンテキストの分離**
```typescript
// 販売コンテキスト
namespace SalesContext {
  // 販売視点での商品
  export class Product {
    constructor(
      private readonly id: ProductId,
      private name: string,
      private price: Money,
      private category: Category
    ) {}
    
    // 販売に関するメソッド
    canBeSold(): boolean {
      return this.price.isPositive();
    }
  }
  
  // 販売視点での顧客
  export class Customer {
    constructor(
      private readonly id: CustomerId,
      private loyaltyPoints: number,
      private purchaseHistory: Purchase[]
    ) {}
    
    getDiscount(): Discount {
      // ロイヤリティプログラムに基づく割引
      return DiscountCalculator.calculate(this.loyaltyPoints);
    }
  }
}

// 在庫コンテキスト
namespace InventoryContext {
  // 在庫視点での商品
  export class StockItem {
    constructor(
      private readonly sku: SKU,
      private quantity: number,
      private location: WarehouseLocation,
      private reorderPoint: number
    ) {}
    
    // 在庫に関するメソッド
    needsReorder(): boolean {
      return this.quantity <= this.reorderPoint;
    }
    
    reserve(quantity: number): Reservation {
      if (this.quantity < quantity) {
        throw new InsufficientStockError();
      }
      
      this.quantity -= quantity;
      return new Reservation(this.sku, quantity);
    }
  }
}

// 配送コンテキスト
namespace ShippingContext {
  // 配送視点での注文
  export class Shipment {
    constructor(
      private readonly trackingNumber: TrackingNumber,
      private items: ShipmentItem[],
      private destination: Address,
      private carrier: Carrier
    ) {}
    
    // 配送に関するメソッド
    estimateDeliveryDate(): Date {
      return this.carrier.estimateDelivery(
        this.destination,
        this.getTotalWeight()
      );
    }
    
    private getTotalWeight(): Weight {
      return this.items.reduce(
        (total, item) => total.add(item.weight),
        Weight.zero()
      );
    }
  }
}
```

#### 3.2 コンテキストマップ

**実装例：コンテキスト間の関係**
```typescript
// コンテキスト間の統合
class ContextIntegration {
  // 販売 → 在庫：顧客/供給者関係
  async reserveInventory(
    order: SalesContext.Order
  ): Promise<InventoryContext.Reservation[]> {
    const reservations: InventoryContext.Reservation[] = [];
    
    for (const item of order.getItems()) {
      // 販売コンテキストのProductIdを在庫コンテキストのSKUに変換
      const sku = this.productIdToSKU(item.productId);
      
      // 在庫サービスを呼び出し
      const reservation = await this.inventoryService.reserve(
        sku,
        item.quantity
      );
      
      reservations.push(reservation);
    }
    
    return reservations;
  }
  
  // 販売 → 配送：公開ホストサービス
  async createShipment(
    order: SalesContext.Order
  ): Promise<ShippingContext.Shipment> {
    // 注文を配送リクエストに変換
    const shippingRequest = this.orderToShippingRequest(order);
    
    // 配送サービスのAPIを呼び出し
    return await this.shippingAPI.createShipment(shippingRequest);
  }
  
  // マッピング関数
  private productIdToSKU(productId: ProductId): SKU {
    // 変換ロジック
    return this.mappingService.getSKU(productId);
  }
  
  private orderToShippingRequest(
    order: SalesContext.Order
  ): ShippingRequest {
    return {
      items: order.getItems().map(item => ({
        sku: this.productIdToSKU(item.productId),
        quantity: item.quantity
      })),
      destination: order.getShippingAddress(),
      priority: order.getShippingPriority()
    };
  }
}
```

## Part 2: 実装パターン編

### Chapter 4: レイヤードアーキテクチャ

**実装例：レイヤー構成**
```typescript
// プレゼンテーション層
class OrderController {
  constructor(
    private orderService: OrderApplicationService
  ) {}
  
  async createOrder(req: Request, res: Response) {
    try {
      const dto = this.validateRequest(req.body);
      const result = await this.orderService.placeOrder(dto);
      res.json(this.toResponse(result));
    } catch (error) {
      this.handleError(error, res);
    }
  }
}

// アプリケーション層
class OrderApplicationService {
  constructor(
    private orderRepo: OrderRepository,
    private customerRepo: CustomerRepository,
    private inventoryService: InventoryService,
    private eventBus: EventBus
  ) {}
  
  async placeOrder(dto: PlaceOrderDto): Promise<OrderResult> {
    // トランザクション開始
    return await this.transactionManager.execute(async () => {
      // ドメインロジックの実行
      const customer = await this.customerRepo.findById(dto.customerId);
      if (!customer) throw new CustomerNotFound();
      
      const order = Order.place(customer, dto.items);
      
      // 在庫の確認と確保
      await this.inventoryService.reserve(order);
      
      // 永続化
      await this.orderRepo.save(order);
      
      // イベント発行
      await this.eventBus.publish(order.getEvents());
      
      return OrderResult.from(order);
    });
  }
}

// ドメイン層
class Order {
  static place(customer: Customer, items: OrderItemDto[]): Order {
    // ドメインロジック
    const order = new Order(
      OrderId.generate(),
      customer.getId(),
      OrderStatus.PENDING
    );
    
    items.forEach(item => {
      order.addItem(item.productId, item.quantity, item.price);
    });
    
    order.applyDiscount(customer.getDiscount());
    order.calculateTotal();
    
    return order;
  }
}

// インフラストラクチャ層
class OrderRepositoryImpl implements OrderRepository {
  constructor(private db: Database) {}
  
  async save(order: Order): Promise<void> {
    const data = this.toPersistence(order);
    await this.db.orders.upsert(data);
  }
  
  async findById(id: OrderId): Promise<Order | null> {
    const data = await this.db.orders.findOne({ id: id.value });
    return data ? this.toDomain(data) : null;
  }
}
```

### Chapter 5: CQRS実装

**実装例：コマンドとクエリの分離**
```typescript
// コマンド側
class OrderCommandHandler {
  async handle(command: PlaceOrderCommand): Promise<void> {
    const order = Order.place(
      command.customerId,
      command.items
    );
    
    await this.orderRepository.save(order);
    await this.eventStore.save(order.getEvents());
  }
}

// クエリ側（読み取り専用モデル）
class OrderQueryService {
  async getOrderSummary(orderId: string): Promise<OrderSummaryView> {
    // 非正規化されたビューから直接取得
    return await this.readDB.orderSummaries.findOne({ orderId });
  }
  
  async searchOrders(criteria: SearchCriteria): Promise<OrderListView[]> {
    // Elasticsearchなどから検索
    return await this.searchEngine.search(criteria);
  }
}

// イベントハンドラ（読み取りモデルの更新）
class OrderProjection {
  async on(event: OrderPlaced): Promise<void> {
    // 読み取り用DBを更新
    await this.readDB.orderSummaries.insert({
      orderId: event.orderId,
      customerId: event.customerId,
      totalAmount: event.totalAmount,
      placedAt: event.occurredAt,
      status: 'PENDING'
    });
    
    // 検索エンジンにもインデックス
    await this.searchEngine.index({
      type: 'order',
      id: event.orderId,
      data: event
    });
  }
}
```

## Part 3: 実装の課題と解決策

### よくある実装課題

#### 課題1: 巨大な集約
**問題**: 集約が大きくなりすぎてパフォーマンスが悪化
**解決策**: 
```typescript
// Before: 巨大な集約
class Order {
  private items: OrderItem[] = [];  // 1000件以上になることも
  private history: OrderHistory[];  // 全履歴を保持
  private comments: Comment[];      // 全コメント
}

// After: 適切に分割
class Order {
  private items: OrderItem[] = [];  // 基本情報のみ
}

class OrderHistory {  // 別集約として分離
  constructor(
    private orderId: OrderId,
    private events: HistoryEvent[]
  ) {}
}

class OrderComments {  // 別集約として分離
  constructor(
    private orderId: OrderId,
    private comments: Comment[]
  ) {}
}
```

#### 課題2: トランザクション境界
**問題**: 複数集約の更新が必要
**解決策**: Sagaパターンまたはプロセスマネージャー

#### 課題3: 永続化の複雑さ
**問題**: ORマッパーとの不整合
**解決策**: 永続化専用のモデルを用意

## 学習の進め方

1. **理論編（1週間）**: Part 1を読み、モデリング手法を理解
2. **実装編（2週間）**: Part 2を実装し、各パターンを習得
3. **実践編（2週間）**: Part 3の課題を解決しながら理解を深める
4. **プロジェクト（3週間）**: 実際のアプリケーションを構築

このガイドに従って学習を進めることで、モデリングから実装まで一貫したDDDのスキルを身につけることができます。