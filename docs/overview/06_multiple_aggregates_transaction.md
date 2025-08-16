# 複数集約のトランザクション更新 - 理想と現実

## DDDの理想論

**原則：1トランザクション = 1集約**

しかし、現実には複数集約を同一トランザクションで更新する必要があるケースが存在します。

## 複数集約を同一トランザクションで更新する現実的なケース

### ケース1：強い整合性が絶対必要な場合

#### 在庫の最後の1個問題
```typescript
// 現実的な実装：複数集約を同一トランザクションで更新
class ReserveLastItemUseCase {
  async execute(orderId: string, productId: string) {
    await this.db.transaction(async (trx) => {
      // Inventory集約
      const inventory = await this.inventoryRepo.findById(productId, trx);
      if (inventory.quantity !== 1) {
        throw new Error("最後の1個ではない");
      }
      inventory.reserve();
      await this.inventoryRepo.save(inventory, trx);
      
      // Order集約も同時に更新
      const order = await this.orderRepo.findById(orderId, trx);
      order.confirmItem(productId);
      await this.orderRepo.save(order, trx);
      
      // 両方成功 or 両方失敗
    });
  }
}
```

**理由**：結果整合性では「売り越し」のリスクがある

#### 会計処理での仕訳
```typescript
// 複式簿記：借方と貸方は必ず同時
class AccountingEntry {
  async record(entry: JournalEntry) {
    await this.db.transaction(async (trx) => {
      // Debit集約
      const debitAccount = await this.accountRepo.find(entry.debitId, trx);
      debitAccount.debit(entry.amount);
      await this.accountRepo.save(debitAccount, trx);
      
      // Credit集約
      const creditAccount = await this.accountRepo.find(entry.creditId, trx);
      creditAccount.credit(entry.amount);
      await this.accountRepo.save(creditAccount, trx);
      
      // 法的に両方同時でないといけない
    });
  }
}
```

**理由**：法的要件、監査要件

### ケース2：パフォーマンスの最適化

```typescript
// 現実的な判断：小さな集約なら一緒に更新
class QuickCheckoutUseCase {
  async execute(cartId: string, customerId: string) {
    await this.db.transaction(async (trx) => {
      // Cart集約
      const cart = await this.cartRepo.find(cartId, trx);
      const order = cart.checkout();
      
      // Order集約（新規作成）
      await this.orderRepo.save(order, trx);
      
      // Cart集約（削除）
      await this.cartRepo.delete(cartId, trx);
      
      // Customer集約（ポイント更新）
      const customer = await this.customerRepo.find(customerId, trx);
      customer.addPoints(order.getPoints());
      await this.customerRepo.save(customer, trx);
    });
    
    // 後で非同期処理
    await this.eventBus.publish(new OrderPlaced(order));
  }
}
```

**理由**：
- ユーザー体験（即座にフィードバック）
- ネットワークラウンドトリップの削減
- 実装のシンプルさ

### ケース3：レガシーシステムの制約

```typescript
// レガシーDBの制約で分離できない
class LegacyOrderSystem {
  async createOrder(orderData: any) {
    // レガシーDBは巨大なトランザクション前提
    await this.legacyDb.transaction(async (trx) => {
      // 注文マスタ、注文明細、在庫、顧客情報...
      // 全部同時に更新する設計になっている
      await trx.execute('CALL CREATE_ORDER_PROC(?, ?, ?)', params);
    });
  }
}
```

## 現実的な設計判断の基準

### 複数集約の同時更新を許容する判断基準

```typescript
class TransactionBoundaryDecision {
  shouldUseSingleTransaction(): boolean {
    // 1. ビジネス上の強い整合性要求
    if (this.requiresStrongConsistency()) {
      return true; // 例：決済、在庫の最後の1個
    }
    
    // 2. パフォーマンス要件
    if (this.isHighFrequencyOperation() && this.isSmallAggregates()) {
      return true; // 例：軽量な更新の組み合わせ
    }
    
    // 3. 技術的制約
    if (this.hasLegacyConstraints() || this.hasDistributedSystemLimitations()) {
      return true; // 例：既存システムの制約
    }
    
    // 4. コストベネフィット
    if (this.eventualConsistencyCost() > this.transactionCost()) {
      return true; // 例：実装コストが高すぎる
    }
    
    return false; // 基本は結果整合性
  }
}
```

## プラグマティックなアプローチ

### 段階的な移行戦略

```typescript
// Step 1: まずは動くものを作る（複数集約OK）
class OrderServiceV1 {
  async placeOrder() {
    await this.db.transaction(async () => {
      // Order, Inventory, Customer を全部更新
    });
  }
}

// Step 2: 重要な部分から分離
class OrderServiceV2 {
  async placeOrder() {
    // コア処理（Order集約のみ）
    await this.db.transaction(async () => {
      await this.orderRepo.save(order);
    });
    
    // 在庫は非同期に
    await this.eventBus.publish(new OrderPlaced());
  }
}

// Step 3: 完全な分離（理想形）
class OrderServiceV3 {
  async placeOrder() {
    // Sagaパターンで完全に分離
    await this.sagaManager.start(new OrderSaga());
  }
}
```

## ドメインエキスパートとの対話

```typescript
// ビジネス要件を明確にする
class BusinessRequirements {
  // 「在庫が合わないのは絶対ダメ？」
  isInventoryConsistencyCritical(): boolean {
    // ECサイト：多少のズレはOK → false
    // 医薬品管理：絶対ダメ → true
  }
  
  // 「注文確定まで何秒待てる？」
  getAcceptableLatency(): number {
    // B2C：1秒以内
    // B2B：10秒OK
  }
  
  // 「一時的な不整合は許容できる？」
  canTolerateTemporaryInconsistency(): boolean {
    // SNSのいいね数：OK → true
    // 銀行残高：NG → false
  }
}
```

## 実装パターン

### パターン1：必要最小限の複数集約更新

```typescript
class MinimalMultiAggregateUpdate {
  async execute() {
    // 本当に同時でないといけない部分だけ
    await this.db.transaction(async () => {
      await this.criticalUpdate1();
      await this.criticalUpdate2();
    });
    
    // それ以外は非同期
    await this.eventBus.publish(new NonCriticalUpdates());
  }
}
```

### パターン2：楽観的ロックで擬似的な整合性

```typescript
class OptimisticLockingApproach {
  async execute() {
    // 別々のトランザクションだが、バージョンチェック
    const order = await this.orderRepo.findById(id);
    const inventory = await this.inventoryRepo.findById(id);
    
    if (inventory.canReserve(order.quantity)) {
      // Order更新
      order.confirm();
      await this.orderRepo.save(order);
      
      try {
        // Inventory更新（失敗したら補償）
        inventory.reserve(order.quantity);
        await this.inventoryRepo.save(inventory);
      } catch (e) {
        // 補償処理
        await this.compensate(order);
      }
    }
  }
}
```

## まとめ

### DDDの原則は「ガイドライン」であって「絶対法則」ではない

1. **理想**：1トランザクション = 1集約
2. **現実**：ビジネス要件次第で複数集約の更新もあり
3. **判断**：トレードオフを明確にして選択

### 重要なのは

- **なぜ**複数集約を同時更新するのか明確にする
- **どこまで**結果整合性で対応できるか検討する
- **段階的に**理想形に近づける

完璧な設計より、動くシステムを作りながら改善していくことが大切です。