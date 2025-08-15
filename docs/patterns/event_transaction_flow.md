# イベント発行のトランザクションフロー詳細

## なぜ内部蓄積パターンが必要なのか

### 問題：即座発行パターンの危険性

```python
# ❌ 危険な実装例
class Order:
    def __init__(self, event_bus):
        self._event_bus = event_bus
    
    def place(self):
        self._status = OrderStatus.PLACED
        
        # 即座にイベントを発行
        self._event_bus.publish(OrderPlacedEvent(...))  # ← ここで発行
        
        # この後でエラーが起きたら？
        if self._total > CREDIT_LIMIT:
            raise ValueError("与信限度額を超えています")  # ← エラー！
```

**問題点:**
- イベントは既に発行済み（他システムに通知済み）
- でもトランザクションはロールバック
- **データとイベントの不整合が発生！**

### 解決：内部蓄積パターンの動作

```python
# ✅ 安全な実装
class Order(AggregateRoot):
    def place(self):
        # 1. ビジネスロジック実行
        self._status = OrderStatus.PLACED
        
        # 2. イベントを内部に蓄積（まだ発行しない）
        self.add_domain_event(OrderPlacedEvent(...))
        
        # 3. バリデーション
        if self._total > CREDIT_LIMIT:
            raise ValueError("与信限度額を超えています")
```

## 詳細なトランザクションフロー

### Step 1: ビジネスロジック実行 → イベント蓄積

```python
# Application Service
async def place_order(self, order_id: str):
    # トランザクション開始
    async with self._unit_of_work:
        # 1-1. 集約を取得
        order = await self._repository.find_by_id(order_id)
        
        # 1-2. ビジネスロジック実行
        order.place()  # 内部でOrderPlacedEventが蓄積される
        
        # この時点のorder._domain_eventsの中身:
        # [
        #     OrderPlacedEvent(id=xxx, customer_id=yyy, ...)
        # ]
```

### Step 2: 集約の永続化

```python
        # 2-1. 集約の状態をDBに保存
        await self._repository.save(order)
        
        # Repository内部の実装
        async def save(self, order: Order):
            # SQLの実行（まだコミットしない）
            await self._db.execute("""
                UPDATE orders 
                SET status = %s, placed_at = %s, total_amount = %s
                WHERE id = %s
            """, [order.status, order.placed_at, order.total_amount, order.id])
            
            # この時点：
            # - DBには変更が記録済み（ただしトランザクション内）
            # - イベントはまだ集約内部に保持
```

### Step 3: イベント取り出し → 配信

```python
        # 3-1. 蓄積されたイベントを取り出す
        events = order.pull_domain_events()  # 取得と同時にクリア
        
        # 3-2. イベントを配信
        for event in events:
            # Option A: 同期的に他の集約を更新
            await self._inventory_service.reserve_stock(event)
            
            # Option B: メッセージキューに送信
            await self._message_queue.publish(event)
            
            # Option C: イベントストアに保存
            await self._event_store.append(event)
```

### Step 4: トランザクションコミット

```python
        # 4. すべて成功したらコミット
        await self._unit_of_work.commit()
    
    # トランザクション終了
```

## エラー発生時の挙動

### ケース1: Step 2でエラー

```python
async def place_order(self, order_id: str):
    async with self._unit_of_work:
        order = await self._repository.find_by_id(order_id)
        order.place()  # イベント蓄積
        
        try:
            await self._repository.save(order)  # ← ここでDB接続エラー！
        except DatabaseError:
            # 自動的にロールバック
            # イベントは発行されていないので問題なし
            pass
```

**結果:** 
- ✅ DBは変更なし
- ✅ イベントも発行されていない
- ✅ 完全に一貫性が保たれる

### ケース2: Step 3でエラー

```python
async def place_order(self, order_id: str):
    async with self._unit_of_work:
        order = await self._repository.find_by_id(order_id)
        order.place()
        await self._repository.save(order)
        
        events = order.pull_domain_events()
        for event in events:
            await self._inventory_service.reserve_stock(event)  # ← 在庫不足エラー！
            
    # トランザクション全体がロールバック
```

**結果:**
- ✅ DBの変更はロールバック
- ✅ 在庫予約も部分的に成功していてもロールバック
- ✅ 一貫性が保たれる

## 実装バリエーション

### 1. 基本実装（現在の実装）
```python
class OrderRepository:
    async def save(self, order: Order):
        # 永続化
        await self._persist_order(order)
        
        # イベント発行
        events = order.pull_domain_events()
        for event in events:
            await self._event_publisher.publish(event)
```

### 2. Unit of Workパターンとの組み合わせ
```python
class UnitOfWork:
    def __init__(self):
        self._aggregates = []
        self._events = []
    
    def register_aggregate(self, aggregate):
        self._aggregates.append(aggregate)
        # イベントを収集
        self._events.extend(aggregate.pull_domain_events())
    
    async def commit(self):
        # 1. すべての集約を永続化
        for aggregate in self._aggregates:
            await self._persist(aggregate)
        
        # 2. すべてのイベントを発行
        for event in self._events:
            await self._publish(event)
        
        # 3. DBコミット
        await self._db.commit()
```

### 3. Outboxパターン（高信頼性）
```python
class OrderRepository:
    async def save(self, order: Order):
        # 同一トランザクション内で実行
        async with self._db.transaction():
            # 1. 集約を保存
            await self._save_order(order)
            
            # 2. イベントをoutboxテーブルに保存
            events = order.pull_domain_events()
            for event in events:
                await self._save_to_outbox(event)
            
            # 3. コミット
            
        # 4. 別プロセスがoutboxを監視して配信
```

## パフォーマンス考慮事項

### メモリ使用量
```python
class AggregateRoot:
    MAX_EVENTS = 100  # 制限を設ける
    
    def add_domain_event(self, event):
        if len(self._domain_events) >= self.MAX_EVENTS:
            # 古いイベントを削除 or エラー
            self._domain_events.pop(0)
        self._domain_events.append(event)
```

### バッチ処理
```python
class EventPublisher:
    async def publish_batch(self, events: List[DomainEvent]):
        # 複数イベントを一度に送信
        if len(events) > 0:
            await self._message_queue.send_batch(events)
```

## まとめ：なぜこのパターンが最適なのか

1. **原子性（Atomicity）**: データ変更とイベント発行が同じトランザクション
2. **一貫性（Consistency）**: エラー時は両方ロールバック
3. **分離性（Isolation）**: 他のトランザクションから隔離
4. **永続性（Durability）**: コミット後は確実に永続化

これがACID特性を満たす、最も信頼性の高いパターンです。