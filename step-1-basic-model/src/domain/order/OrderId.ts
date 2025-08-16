import { v4 as uuidv4 } from 'uuid';

/**
 * OrderId Value Object
 */
export class OrderId {
  private readonly value: string;

  constructor(value: string) {
    if (!value || value.trim().length === 0) {
      throw new Error('OrderIdは空にできません');
    }
    this.value = value;
  }

  static generate(): OrderId {
    return new OrderId(uuidv4());
  }

  equals(other: OrderId): boolean {
    return this.value === other.value;
  }

  toString(): string {
    return this.value;
  }
}