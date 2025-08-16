# EntityとAggregateの関係を正しく理解する

## 正確な定義

### Entity
**個体として識別される、ライフサイクルを持つオブジェクト**

### Aggregate
**関連するEntity・Value Objectをまとめた「境界」**

## Entity ≠ Aggregate

```typescript
// Entityは3つある
class Order {               // Entity（かつAggregate Root）
  private items: OrderItem[];  // OrderItemもEntity
  private shippingInfo: ShippingInfo;  // これもEntity
}

class OrderItem {           // Entity（でもAggregate Rootではない）
  private id: OrderItemId;
  private productId: ProductId;
  private quantity: number;
}

class ShippingInfo {        // Entity（でもAggregate Rootではない）
  private id: ShippingInfoId;
  private address: Address;
  private scheduledDate: Date;
}

// でもAggregateは1つ = Order Aggregate
```

## Aggregateの構成要素

```typescript
// Order Aggregate の構成
namespace OrderAggregate {
  // Aggregate Root（外部からアクセス可能）
  export class Order {
    private id: OrderId;
    private items: OrderItem[];        // 子Entity
    private shippingInfo: ShippingInfo; // 子Entity
    private totalAmount: Money;         // Value Object
    
    // Aggregate Rootがすべての操作の入り口
    addItem(productId: ProductId, quantity: number): void {
      const item = new OrderItem(productId, quantity);
      this.items.push(item);
      this.recalculateTotal();
    }
    
    updateShippingAddress(address: Address): void {
      this.shippingInfo.updateAddress(address);
    }
  }
  
  // 子Entity（外部から直接アクセス不可）
  class OrderItem {
    private id: OrderItemId;
    private productId: ProductId;
    private quantity: number;
    
    // ロジックを持つ
    increaseQuantity(amount: number): void {
      this.quantity += amount;
    }
  }
  
  // 子Entity（外部から直接アクセス不可）
  class ShippingInfo {
    private id: ShippingInfoId;
    private address: Address;
    
    // ロジックを持つ
    updateAddress(newAddress: Address): void {
      if (!newAddress.isDeliverable()) {
        throw new Error("配送不可地域です");
      }
      this.address = newAddress;
    }
  }
}
```

## 重要な概念：Aggregate Root

### Aggregate Rootとは
**集約の代表となるEntity**

```typescript
// ✅ 正しいアクセス方法
const order = await orderRepository.findById(orderId);
order.addItem(productId, 5);  // Aggregate Root経由

// ❌ 間違ったアクセス方法
const orderItem = await orderItemRepository.findById(itemId);
orderItem.increaseQuantity(5);  // 子Entityに直接アクセス（ダメ）
```

## 具体例：いろいろなAggregateパターン

### パターン1：単一EntityのAggregate
```typescript
// ProductはEntityでありAggregate
class Product {  // Entity = Aggregate Root = Aggregate全体
  private id: ProductId;
  private name: string;
  private price: Money;  // Value Object
  
  changePrice(newPrice: Money): void {
    if (newPrice.isNegative()) {
      throw new Error("価格は正の値である必要があります");
    }
    this.price = newPrice;
  }
}
// この場合：1 Entity = 1 Aggregate
```

### パターン2：複数EntityのAggregate
```typescript
// Blog Aggregate
class BlogPost {  // Aggregate Root (Entity)
  private id: PostId;
  private title: string;
  private content: string;
  private comments: Comment[];  // 子Entity
  
  addComment(author: string, text: string): void {
    if (this.comments.length >= 1000) {
      throw new Error("コメント数の上限");
    }
    const comment = new Comment(author, text);
    this.comments.push(comment);
  }
}

class Comment {  // 子Entity（Aggregate Rootではない）
  private id: CommentId;
  private author: string;
  private text: string;
  private likes: number = 0;
  
  like(): void {
    this.likes++;
  }
}
// この場合：2 Entity, 1 Aggregate
```

### パターン3：Value Objectのみの集約（稀）
```typescript
// Address Aggregate（Entityなし）
class AddressBook {  // これ自体はValue Object的
  private addresses: Address[];  // Value Objectのコレクション
  
  constructor(addresses: Address[]) {
    this.addresses = [...addresses];  // 不変性を保つ
  }
  
  add(address: Address): AddressBook {
    // 新しいインスタンスを返す（不変）
    return new AddressBook([...this.addresses, address]);
  }
}
```

## よくある誤解と正しい理解

### 誤解1：「Entity = Aggregate」
**違います**
- Entity：識別子を持つオブジェクト
- Aggregate：複数のオブジェクトをまとめた境界

### 誤解2：「ロジックを持つEntity = Aggregate」
**違います**
- 子Entityもロジックを持てる
- でも子EntityはAggregateではない

### 誤解3：「Aggregate = 大きなEntity」
**違います**
- Aggregateは「境界」の概念
- 1つのEntityだけでもAggregate

## 正しい理解のための図解

```
Order Aggregate
┌─────────────────────────────────────┐
│  Order (Aggregate Root / Entity)     │
│  ├── OrderItem (Entity)              │
│  │   ├── productId (Value Object)    │
│  │   └── quantity (Value Object)     │
│  ├── ShippingInfo (Entity)           │
│  │   └── address (Value Object)      │
│  └── totalAmount (Value Object)      │
└─────────────────────────────────────┘
         ↑
    Aggregate境界
    （この箱全体がAggregate）
```

## まとめ：正しい認識

### Entity
- **識別子**を持つオブジェクト
- **ライフサイクル**がある
- **ロジック**を持つ

### Aggregate
- Entity・Value Objectの**まとまり**
- **トランザクション境界**
- **整合性の単位**

### Aggregate Root
- Aggregateの**代表Entity**
- 外部からの**唯一の入り口**
- **他のEntityを管理**

### 関係性
```
Aggregate ⊇ Aggregate Root (Entity) ⊇ 子Entity ⊇ Value Object
```

つまり：
- **すべてのAggregateにはAggregate Root（Entity）がある**
- **すべてのEntityがAggregateではない**
- **Entityにロジックを書くのは正しいが、それだけでAggregateにはならない**