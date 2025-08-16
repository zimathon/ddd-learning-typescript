# トランザクション整合性 vs 結果整合性

## 根本的な違い

### トランザクション整合性（強整合性）
**「今すぐ、完全に正しい状態」を保証**

```typescript
// 銀行の送金：絶対に即座に整合性が必要
class BankTransfer {
  async transfer(from: Account, to: Account, amount: Money) {
    await transaction(() => {
      from.withdraw(amount);  // 引き出し
      to.deposit(amount);     // 入金
      // この2つは必ず同時に成功or失敗する
    });
    // トランザクション完了時点で必ず整合性が取れている
  }
}
```

**特徴**：
- ACID特性（原子性・一貫性・独立性・永続性）
- 即座に整合性を保証
- 失敗したら全てロールバック
- 同期処理

### 結果整合性（最終整合性）
**「いずれ正しい状態になる」ことを保証**

```typescript
// ECサイトの注文と在庫：少しの遅延は許容できる
class OrderPlacement {
  async placeOrder(order: Order) {
    // 1. まず注文を確定（トランザクション1）
    await this.orderRepo.save(order);
    
    // 2. イベントを発行
    await this.eventBus.publish(new OrderPlaced(order));
    // この時点では在庫はまだ減っていない！
  }
}

// 別のプロセスで在庫を更新（トランザクション2）
class InventoryUpdater {
  async handleOrderPlaced(event: OrderPlaced) {
    // 数秒〜数分後に実行されるかも
    const inventory = await this.inventoryRepo.find(event.productId);
    inventory.decrease(event.quantity);
    await this.inventoryRepo.save(inventory);
    // ここでやっと在庫が減る
  }
}
```

**特徴**：
- BASE特性（基本的に利用可能・柔軟な状態・最終的な整合性）
- 一時的な不整合を許容
- 非同期処理
- 高可用性・高スケーラビリティ

## 具体例で見る違い

### シナリオ：商品を100個注文

#### トランザクション整合性の場合
```typescript
// すべてを1つのトランザクションで処理
async placeOrder() {
  await transaction(() => {
    order.place();           // 注文確定
    inventory.decrease(100); // 在庫を100減らす
    payment.charge();        // 支払い処理
  });
  // ✅ この時点ですべて完了・整合性OK
  // ❌ でも処理が重い、他のユーザーが待たされる
}
```

#### 結果整合性の場合
```typescript
// 段階的に処理
async placeOrder() {
  // Step 1: 注文だけ確定
  await order.place();
  // ⚠️ この時点では在庫はまだ100個のまま！
  
  // Step 2: 非同期で在庫更新（1秒後かも）
  eventBus.publish('OrderPlaced', { quantity: 100 });
  
  // Step 3: 別のサービスが在庫を減らす（2秒後かも）
  // inventory.decrease(100);
  
  // ✅ 最終的には整合性が取れる
  // ✅ 高速、他のユーザーを待たせない
  // ❌ 一時的に在庫数が正しくない
}
```

## いつどちらを使うか

### トランザクション整合性を使うべき場合

| ケース | 理由 | 例 |
|--------|------|-----|
| **金銭処理** | 1円のズレも許されない | 銀行送金、決済処理 |
| **在庫の最後の1個** | 重複販売を防ぐ | 限定商品、座席予約 |
| **重要な状態遷移** | 中途半端な状態は危険 | 契約締結、承認フロー |

### 結果整合性を使うべき場合

| ケース | 理由 | 例 |
|--------|------|-----|
| **大量データ処理** | 全部待つと遅すぎる | アクセスログ集計 |
| **通知・メール** | 少し遅れても問題ない | 注文確認メール |
| **レコメンド更新** | 完璧でなくても機能する | おすすめ商品 |
| **在庫の目安表示** | 「残りわずか」程度でOK | 在庫インジケーター |

## DDDにおける使い分け

### 集約内 = トランザクション整合性
```typescript
class Order {
  private items: OrderItem[];
  private total: Money;
  
  addItem(item: OrderItem) {
    this.items.push(item);
    this.total = this.calculateTotal();
    // 必ず同時に更新される（トランザクション整合性）
  }
}
```

### 集約間 = 結果整合性
```typescript
// Order集約とInventory集約の連携
class OrderService {
  async placeOrder(order: Order) {
    await this.orderRepo.save(order);  // まず注文を保存
    
    // 非同期でイベント発行（結果整合性）
    await this.eventBus.publish(new OrderPlaced(order));
    // 在庫はいずれ減る（すぐではない）
  }
}
```

## よくある誤解

### 誤解1：結果整合性は「いい加減」
**違います**。最終的には必ず正しい状態になることを保証します。

### 誤解2：トランザクション整合性が常に優れている
**違います**。パフォーマンスと可用性を犠牲にします。

### 誤解3：結果整合性は実装が簡単
**違います**。補償処理、冪等性、順序保証など考慮事項が多い。

## 実装時の注意点

### 結果整合性の実装で必要なこと

```typescript
class EventHandler {
  async handle(event: OrderPlaced) {
    // 1. 冪等性の保証（同じイベントを2回処理しても大丈夫）
    if (await this.isAlreadyProcessed(event.id)) {
      return;
    }
    
    // 2. エラー時のリトライ
    try {
      await this.updateInventory(event);
    } catch (error) {
      await this.scheduleRetry(event);
    }
    
    // 3. 補償処理（取り消し処理）
    if (event.isCancelled) {
      await this.compensate(event);
    }
  }
}
```

## まとめ

- **トランザクション整合性**：即座に完全な整合性（同期・ACID）
- **結果整合性**：最終的な整合性（非同期・BASE）

これらは**トレードオフの関係**：
- 整合性 vs パフォーマンス
- 正確性 vs 可用性
- シンプルさ vs スケーラビリティ

ビジネス要件に応じて適切に選択することが重要です。