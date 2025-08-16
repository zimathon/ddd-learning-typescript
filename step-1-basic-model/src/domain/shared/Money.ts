/**
 * Money Value Object
 * お金を表現する値オブジェクト
 */
export class Money {
  private readonly amount: number;
  private readonly currency: string;

  constructor(amount: number, currency: string = 'JPY') {
    if (amount < 0) {
      throw new Error('金額は0以上である必要があります');
    }
    
    if (!currency || currency.length !== 3) {
      throw new Error('通貨コードは3文字である必要があります');
    }
    
    this.amount = amount;
    this.currency = currency.toUpperCase();
  }

  static zero(currency: string = 'JPY'): Money {
    return new Money(0, currency);
  }

  static fromYen(amount: number): Money {
    return new Money(amount, 'JPY');
  }

  add(other: Money): Money {
    this.assertSameCurrency(other);
    return new Money(this.amount + other.amount, this.currency);
  }

  subtract(other: Money): Money {
    this.assertSameCurrency(other);
    const result = this.amount - other.amount;
    if (result < 0) {
      throw new Error('計算結果が負の値になります');
    }
    return new Money(result, this.currency);
  }

  multiply(multiplier: number): Money {
    if (multiplier < 0) {
      throw new Error('乗数は0以上である必要があります');
    }
    return new Money(Math.floor(this.amount * multiplier), this.currency);
  }

  equals(other: Money): boolean {
    return this.amount === other.amount && this.currency === other.currency;
  }

  greaterThan(other: Money): boolean {
    this.assertSameCurrency(other);
    return this.amount > other.amount;
  }

  isZero(): boolean {
    return this.amount === 0;
  }

  format(): string {
    if (this.currency === 'JPY') {
      return `¥${this.amount.toLocaleString()}`;
    }
    return `${this.currency} ${this.amount.toLocaleString()}`;
  }

  private assertSameCurrency(other: Money): void {
    if (this.currency !== other.currency) {
      throw new Error(`異なる通貨の計算はできません: ${this.currency} != ${other.currency}`);
    }
  }

  getValue(): number {
    return this.amount;
  }

  getCurrency(): string {
    return this.currency;
  }
}