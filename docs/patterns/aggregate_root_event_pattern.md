# AggregateRootのイベント発行パターン

## 標準的な実装パターン

### 1. 内部蓄積パターン（現在の実装）
```python
class AggregateRoot:
    def __init__(self):
        self._domain_events = []
    
    def add_domain_event(self, event):
        self._domain_events.append(event)
    
    def pull_domain_events(self):
        events = self._domain_events.copy()
        self._domain_events.clear()
        return events
```

**メリット:**
- シンプルで理解しやすい
- トランザクション内で確実にイベントを発行
- ユニットテストが書きやすい

**採用例:**
- .NET Core のDDDテンプレート
- Axon Framework (Java)
- EventStore系の実装

### 2. 即座発行パターン（別の選択肢）
```python
class AggregateRoot:
    def __init__(self, event_publisher):
        self._event_publisher = event_publisher
    
    def raise_event(self, event):
        self._event_publisher.publish(event)  # 即座に発行
```

**メリット:**
- リアルタイム性が高い
- メモリ効率が良い

**デメリット:**
- トランザクション失敗時の扱いが複雑
- テストでモックが必要

### 3. アウトボックスパターン（高度な実装）
```python
class AggregateRoot:
    def add_domain_event(self, event):
        # イベントをDBのoutboxテーブルに保存
        self._outbox_events.append(event)
```

**メリット:**
- 確実なイベント配信（At-Least-Once保証）
- 分散システムに適している

**採用例:**
- Debezium
- Kafka Connect

## なぜ内部蓄積パターンが主流なのか

### 1. トランザクション整合性
```python
# リポジトリでの典型的な実装
class OrderRepository:
    async def save(self, order: Order):
        # 1. 集約の永続化
        await self._persist(order)
        
        # 2. 同一トランザクション内でイベント発行
        events = order.pull_domain_events()
        for event in events:
            await self._event_bus.publish(event)
        
        # 3. トランザクションコミット
        await self._commit()
```

### 2. テスタビリティ
```python
def test_order_placed_event_is_raised():
    # Arrange
    order = Order.create(customer_id)
    order.add_item(product_id, 2, Money(1000))
    
    # Act
    order.place()
    
    # Assert
    events = order.get_domain_events()
    assert len(events) == 2  # OrderCreated, OrderPlaced
    assert isinstance(events[1], OrderPlacedEvent)
```

### 3. 実装の分離
- ドメイン層：イベントの生成と蓄積
- アプリケーション層：イベントの配信
- インフラ層：実際の通知メカニズム

## 実装上の注意点

### メモリリーク対策
```python
class AggregateRoot:
    MAX_EVENTS = 100  # イベント数の上限
    
    def add_domain_event(self, event):
        if len(self._domain_events) >= self.MAX_EVENTS:
            raise OverflowError("Too many domain events")
        self._domain_events.append(event)
```

### イベントの重複防止
```python
class AggregateRoot:
    def add_domain_event(self, event):
        # 同じイベントIDの重複を防ぐ
        if not any(e.event_id == event.event_id for e in self._domain_events):
            self._domain_events.append(event)
```

## 実際のプロジェクトでの採用例

### 1. eShopOnContainers (Microsoft)
```csharp
public abstract class Entity
{
    private List<INotification> _domainEvents;
    
    public void AddDomainEvent(INotification eventItem)
    {
        _domainEvents = _domainEvents ?? new List<INotification>();
        _domainEvents.Add(eventItem);
    }
}
```

### 2. Java DDD Sample (Domain Language)
```java
public abstract class AggregateRoot {
    private final List<DomainEvent> events = new ArrayList<>();
    
    protected void registerEvent(DomainEvent event) {
        events.add(event);
    }
}
```

### 3. Symfony (PHP)
```php
trait DomainEventTrait {
    private array $domainEvents = [];
    
    public function recordDomainEvent(DomainEvent $event): void {
        $this->domainEvents[] = $event;
    }
}
```

## まとめ

現在の実装は：
- ✅ 業界標準のパターンに準拠
- ✅ 多くの有名プロジェクトで採用
- ✅ テスタビリティが高い
- ✅ トランザクション整合性を保証
- ✅ 将来的な拡張が容易

このパターンは、DDDコミュニティで広く受け入れられており、
プロダクション環境での実績も豊富です。