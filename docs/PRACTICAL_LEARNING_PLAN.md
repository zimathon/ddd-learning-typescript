# DDD実践学習プラン - サンプルコード&FAQ版

## 概要

このプランは、実践的なサンプルコードとよくある質問（FAQ）を通じてDDDを学ぶための構成です。
理論と実装を交互に学び、実際の開発現場で直面する課題への対処法を習得します。

## 学習アプローチ

### ボトムアップDDD vs トップダウンDDD

#### ボトムアップDDD（このリポジトリのアプローチ）
1. **戦術的パターンから開始**
   - Value Object → Entity → Aggregate → Repository
   - 具体的な実装から抽象的な概念へ
   - 初学者に優しいアプローチ

2. **メリット**
   - すぐにコードが書ける
   - 具体的な成果物が見える
   - 段階的な理解が可能

#### トップダウンDDD（上級者向け）
1. **戦略的設計から開始**
   - ドメイン分析 → コンテキストマップ → 境界づけられたコンテキスト
   - 全体像から詳細へ

2. **メリット**
   - システム全体の設計が最適化される
   - 大規模プロジェクトに向いている

## 詳細学習プラン

### Phase 1: 基礎実装パターン（2-3週間）

#### Week 1: ドメインオブジェクトの基礎
**学習内容**
- Value Objectの実装パターン
- Entityの実装パターン
- 識別子の設計

**実装課題**
```typescript
// 1. 複雑なValue Objectの実装
class PhoneNumber {
  // 国番号、市外局番、加入者番号の分離
  // フォーマット変換
  // バリデーション
}

// 2. 識別子の実装パターン
class UserId {
  // UUID vs 連番
  // 型安全な識別子
}

// 3. Entityの状態管理
class User {
  // 状態遷移の実装
  // 不変条件の保護
}
```

**FAQ対応**
- Q: Value ObjectをEntityにしてしまう失敗を避けるには？
- Q: IDの生成タイミングはいつが適切？
- Q: プリミティブ型の執着を避けるには？

#### Week 2: 集約の設計
**学習内容**
- 集約境界の決定方法
- 集約ルートの責務
- トランザクション整合性と結果整合性

**実装課題**
```typescript
// ECサイトの注文集約
class Order {
  private items: OrderItem[];
  private shippingAddress: Address;
  
  // 集約内の不変条件
  addItem(productId: ProductId, quantity: Quantity): void {
    // 在庫確認は集約外
    // 価格計算は集約内
  }
  
  // 集約をまたぐ操作の分離
  cancel(): DomainEvent[] {
    // キャンセルイベントの発行
    // 在庫の復元は別集約の責務
  }
}
```

**FAQ対応**
- Q: 集約が大きくなりすぎた場合の分割方法は？
- Q: 複数集約の更新が必要な場合は？
- Q: 集約間の参照はIDのみにすべき？

### Phase 2: アプリケーション層の実装（2週間）

#### Week 3: リポジトリとファクトリ
**学習内容**
- リポジトリの抽象化
- ファクトリの使いどころ
- 永続化の詳細を隠蔽する方法

**実装課題**
```typescript
// 1. リポジトリインターフェース
interface OrderRepository {
  save(order: Order): Promise<void>;
  findById(id: OrderId): Promise<Order | null>;
  // 検索メソッドの設計
  findByCustomerId(customerId: CustomerId): Promise<Order[]>;
}

// 2. 仕様パターンの実装
class OrderSpecification {
  static pendingOrders(): Specification<Order> {
    return new PendingOrderSpec();
  }
}

// 3. ファクトリの実装
class OrderFactory {
  static createFromCart(
    cart: ShoppingCart,
    customer: Customer
  ): Order {
    // 複雑な生成ロジック
  }
}
```

**FAQ対応**
- Q: リポジトリのメソッドが増えすぎる問題の対処法は？
- Q: ORMとリポジトリの使い分けは？
- Q: テスト用のインメモリリポジトリの実装方法は？

#### Week 4: アプリケーションサービス
**学習内容**
- ユースケースの実装
- トランザクション管理
- エラーハンドリング

**実装課題**
```typescript
// 注文処理のユースケース
class PlaceOrderUseCase {
  constructor(
    private orderRepo: OrderRepository,
    private customerRepo: CustomerRepository,
    private inventoryService: InventoryService,
    private paymentService: PaymentService
  ) {}
  
  async execute(dto: PlaceOrderDto): Promise<OrderResult> {
    // 1. 顧客の取得と検証
    // 2. 在庫の確認
    // 3. 注文の生成
    // 4. 支払い処理
    // 5. 永続化
    // 6. イベント発行
  }
}
```

**FAQ対応**
- Q: ドメインサービスとアプリケーションサービスの違いは？
- Q: DTOとドメインオブジェクトの変換はどこで行う？
- Q: 分散トランザクションの扱い方は？

### Phase 3: イベント駆動アーキテクチャ（2週間）

#### Week 5: ドメインイベント
**学習内容**
- イベントの設計
- イベントストーミング
- イベントソーシングの基礎

**実装課題**
```typescript
// 1. イベントの定義
class OrderPlaced extends DomainEvent {
  constructor(
    public readonly orderId: OrderId,
    public readonly customerId: CustomerId,
    public readonly totalAmount: Money,
    public readonly placedAt: Date
  ) {
    super();
  }
}

// 2. イベントハンドラ
class InventoryUpdateHandler {
  async handle(event: OrderPlaced): Promise<void> {
    // 在庫の減算処理
  }
}

// 3. イベントバス
class EventBus {
  private handlers: Map<string, EventHandler[]>;
  
  publish(event: DomainEvent): Promise<void> {
    // 非同期でハンドラを実行
  }
}
```

**FAQ対応**
- Q: イベントの粒度はどう決める？
- Q: イベントの順序保証は必要？
- Q: 失敗したイベント処理のリトライは？

#### Week 6: Sagaパターンと補償処理
**学習内容**
- 長時間実行プロセスの管理
- 補償トランザクション
- 状態機械の実装

**実装課題**
```typescript
// 注文処理Saga
class OrderProcessingSaga {
  private state: SagaState;
  
  async handle(event: DomainEvent): Promise<void> {
    switch(this.state) {
      case 'PAYMENT_PENDING':
        // 支払い処理
        break;
      case 'INVENTORY_RESERVED':
        // 在庫確保
        break;
      case 'SHIPPING_ARRANGED':
        // 配送手配
        break;
    }
  }
  
  async compensate(): Promise<void> {
    // ロールバック処理
  }
}
```

**FAQ対応**
- Q: Sagaの状態はどこに保存する？
- Q: タイムアウト処理はどう実装する？
- Q: 並行実行される複数のSagaの管理は？

### Phase 4: 戦略的設計（2週間）

#### Week 7: 境界づけられたコンテキスト
**学習内容**
- コンテキストマップの作成
- 統合パターン
- チーム間の調整

**実装課題**
```typescript
// 販売コンテキストと配送コンテキストの統合
namespace SalesContext {
  class Order {
    // 販売の観点での注文
  }
}

namespace ShippingContext {
  class Shipment {
    // 配送の観点での注文
  }
  
  // 腐敗防止層
  class OrderTranslator {
    static toShipment(order: SalesContext.Order): Shipment {
      // コンテキスト間の変換
    }
  }
}
```

**FAQ対応**
- Q: マイクロサービスとコンテキストの関係は？
- Q: 共有カーネルの管理方法は？
- Q: レガシーシステムとの統合は？

#### Week 8: 統合パターンの実装
**学習内容**
- 腐敗防止層
- 公開ホストサービス
- イベント駆動統合

**実装課題**
```typescript
// REST APIによる公開ホストサービス
class OrderAPI {
  // 外部システム向けのインターフェース
  async createOrder(request: CreateOrderRequest): Promise<OrderResponse> {
    // DTOからドメインモデルへの変換
    // ユースケースの実行
    // レスポンスの生成
  }
}

// 腐敗防止層の実装
class LegacySystemAdapter {
  // レガシーシステムのデータモデルを
  // ドメインモデルに変換
}
```

### Phase 5: 実践プロジェクト（3-4週間）

#### 実装する機能
1. **商品カタログ管理**
   - 商品の登録・更新
   - カテゴリ管理
   - 在庫管理

2. **注文処理**
   - カート機能
   - 注文確定
   - 支払い処理

3. **配送管理**
   - 配送スケジュール
   - 配送状況追跡

4. **顧客管理**
   - 会員登録
   - ポイント管理
   - 購入履歴

#### アーキテクチャ要件
- クリーンアーキテクチャの適用
- CQRSパターンの実装
- イベントソーシング（一部）
- テスト駆動開発

## よくある実装の課題と解決策

### 1. パフォーマンス問題
**課題**: 集約の読み込みが重い
**解決策**: 
- 遅延読み込みの実装
- CQRSによる読み取り専用モデル
- キャッシング戦略

### 2. トランザクション管理
**課題**: 複数集約の更新
**解決策**:
- イベント駆動による結果整合性
- Sagaパターン
- 2フェーズコミット（最終手段）

### 3. テスタビリティ
**課題**: ドメインロジックのテストが困難
**解決策**:
- 依存性注入の徹底
- インメモリ実装の提供
- ドメインイベントによる副作用の分離

## 学習リソース

### 必読書
- エリック・エヴァンス『ドメイン駆動設計』
- ヴァーノン・ヴォーン『実践ドメイン駆動設計』
- 松岡幸一郎『ドメイン駆動設計サンプルコード&FAQ』

### 参考実装
- [ddd-forum](https://github.com/stemmlerjs/ddd-forum) - TypeScript実装例
- [modular-monolith-with-ddd](https://github.com/kgrzybek/modular-monolith-with-ddd) - C#実装例

### コミュニティ
- DDD Community Japan
- Domain-Driven Design Europe

## 評価基準

各フェーズ完了時のチェックリスト：

### Phase 1 完了基準
- [ ] Value ObjectとEntityの違いを説明できる
- [ ] 集約の境界を適切に設計できる
- [ ] 基本的なドメインモデルを実装できる

### Phase 2 完了基準
- [ ] リポジトリパターンを実装できる
- [ ] ユースケースをアプリケーションサービスとして実装できる
- [ ] レイヤー間の依存関係を適切に管理できる

### Phase 3 完了基準
- [ ] ドメインイベントを設計・実装できる
- [ ] Sagaパターンを理解し実装できる
- [ ] 非同期処理を適切に扱える

### Phase 4 完了基準
- [ ] 境界づけられたコンテキストを識別できる
- [ ] コンテキスト間の統合パターンを選択できる
- [ ] 腐敗防止層を実装できる

### Phase 5 完了基準
- [ ] 実際に動作するアプリケーションを構築できる
- [ ] DDDのパターンを適切に適用できる
- [ ] チームでDDDを実践する準備ができている