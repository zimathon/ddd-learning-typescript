# Value ObjectとEntity - DDDの基本構成要素

## 概要

ドメイン駆動設計において、**Value Object（値オブジェクト）**と**Entity（エンティティ）**は、ドメインモデルを構成する最も基本的な要素です。これらの違いを理解することが、適切なドメインモデリングの第一歩となります。

## Value Object（値オブジェクト）

### 定義
Value Objectは、**概念的な完全性を持つ不変の値**を表現するオブジェクトです。識別子を持たず、その属性の組み合わせによってのみ等価性が判断されます。

### 特徴

#### 1. 不変性（Immutability）
```typescript
class Money {
  constructor(
    private readonly amount: number,
    private readonly currency: string
  ) {}
  
  // 新しいインスタンスを返す（元のオブジェクトは変更しない）
  add(other: Money): Money {
    if (this.currency !== other.currency) {
      throw new Error('異なる通貨の計算はできません');
    }
    return new Money(this.amount + other.amount, this.currency);
  }
}
```

#### 2. 等価性（Equality）
```typescript
class Email {
  constructor(private readonly value: string) {
    this.validate(value);
  }
  
  equals(other: Email): boolean {
    return this.value === other.value;
  }
}

const email1 = new Email("user@example.com");
const email2 = new Email("user@example.com");
console.log(email1.equals(email2)); // true（値が同じなら等しい）
```

#### 3. 自己完結性
Value Objectは、それ自体で意味を持つ完全な概念を表現します。

### いつValue Objectを使うか

- **識別子が不要**な概念
- **交換可能**な値（1万円札は別の1万円札と交換しても問題ない）
- **計測や説明**を表現する場合
- **複数の属性をまとめて**扱いたい場合

### 典型的な例

- 金額（Money）
- 住所（Address）
- メールアドレス（Email）
- 日付範囲（DateRange）
- 座標（Coordinate）

## Entity（エンティティ）

### 定義
Entityは、**一意の識別子を持ち、ライフサイクルを通じて同一性が保たれる**オブジェクトです。属性が変化しても、識別子が同じであれば同一のEntityとみなされます。

### 特徴

#### 1. 識別子による同一性（Identity）
```typescript
class Customer {
  constructor(
    private readonly id: CustomerId,  // 一意の識別子
    private name: string,
    private email: Email
  ) {}
  
  equals(other: Customer): boolean {
    // 属性ではなく、IDで等価性を判断
    return this.id.equals(other.id);
  }
  
  // 属性は変更可能
  changeEmail(newEmail: Email): void {
    this.email = newEmail;
    // IDは同じなので、同じ顧客
  }
}
```

#### 2. ライフサイクル
```typescript
class Product {
  private status: ProductStatus;
  
  constructor(
    private readonly id: ProductId,
    private name: string,
    private price: Money
  ) {
    this.status = ProductStatus.DRAFT;
  }
  
  // ライフサイクルメソッド
  publish(): void {
    if (this.status !== ProductStatus.DRAFT) {
      throw new Error('下書き状態の商品のみ公開できます');
    }
    this.status = ProductStatus.PUBLISHED;
  }
  
  discontinue(): void {
    this.status = ProductStatus.DISCONTINUED;
  }
}
```

#### 3. ビジネスロジックの保持
Entityは、自身に関連するビジネスルールを内包します。

### いつEntityを使うか

- **個体を区別する必要**がある概念
- **時間経過とともに状態が変化**する
- **ライフサイクル**を持つ
- **追跡が必要**なもの

### 典型的な例

- 顧客（Customer）
- 注文（Order）
- 商品（Product）
- 従業員（Employee）
- プロジェクト（Project）

## Value ObjectとEntityの使い分け

### 判断基準のフローチャート

```
その概念は...
├─ 識別子が必要か？
│  ├─ Yes → Entity
│  └─ No
│     ├─ 時間とともに変化するか？
│     │  ├─ Yes → Entity
│     │  └─ No
│     │     ├─ 個体を区別する必要があるか？
│     │     │  ├─ Yes → Entity
│     │     │  └─ No → Value Object
```

### 実例での比較

#### 住所の場合
```typescript
// Value Objectとして実装（推奨）
class Address {
  constructor(
    private readonly street: string,
    private readonly city: string,
    private readonly postalCode: string
  ) {}
  
  equals(other: Address): boolean {
    return this.street === other.street &&
           this.city === other.city &&
           this.postalCode === other.postalCode;
  }
}

// 顧客は住所を「持つ」
class Customer {
  constructor(
    private readonly id: CustomerId,
    private address: Address  // Value Objectを保持
  ) {}
  
  changeAddress(newAddress: Address): void {
    this.address = newAddress;  // 丸ごと置き換える
  }
}
```

#### 銀行口座の場合
```typescript
// Entityとして実装（口座は追跡が必要）
class BankAccount {
  constructor(
    private readonly accountNumber: AccountNumber,  // ID
    private balance: Money,
    private owner: CustomerId
  ) {}
  
  deposit(amount: Money): void {
    this.balance = this.balance.add(amount);
    // 口座番号は同じだが、残高は変化する
  }
}
```

## 実装のベストプラクティス

### Value Object

1. **コンストラクタで検証**
```typescript
class Email {
  constructor(private readonly value: string) {
    if (!this.isValid(value)) {
      throw new Error('無効なメールアドレス形式');
    }
  }
  
  private isValid(email: string): boolean {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  }
}
```

2. **ファクトリメソッドの活用**
```typescript
class Money {
  private constructor(
    private readonly amount: number,
    private readonly currency: string
  ) {}
  
  static zero(currency: string): Money {
    return new Money(0, currency);
  }
  
  static fromYen(amount: number): Money {
    return new Money(amount, 'JPY');
  }
}
```

### Entity

1. **IDの早期生成**
```typescript
class Order {
  static create(customerId: CustomerId, items: OrderItem[]): Order {
    const orderId = OrderId.generate();  // 作成時にID生成
    return new Order(orderId, customerId, items);
  }
}
```

2. **不変条件の保護**
```typescript
class ShoppingCart {
  private items: CartItem[] = [];
  
  addItem(product: Product, quantity: number): void {
    // ビジネスルールの適用
    if (quantity <= 0) {
      throw new Error('数量は1以上である必要があります');
    }
    
    if (this.items.length >= 100) {
      throw new Error('カートには最大100個まで追加可能です');
    }
    
    this.items.push(new CartItem(product, quantity));
  }
}
```

## まとめ

- **Value Object**は「何であるか」を表現し、**Entity**は「誰/どれであるか」を表現する
- Value Objectは不変で交換可能、Entityは可変で追跡可能
- 適切な使い分けにより、ドメインモデルがより表現力豊かになる
- 迷ったら「識別子が必要か」「個体を追跡する必要があるか」を考える

この基本的な区別を理解することで、より適切なドメインモデリングが可能になります。