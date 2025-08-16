import { v4 as uuidv4 } from 'uuid';

/**
 * CustomerId Value Object
 * 顧客IDを表現する値オブジェクト
 */
export class CustomerId {
  private readonly value: string;

  constructor(value: string) {
    if (!value || value.trim().length === 0) {
      throw new Error('CustomerIdは空にできません');
    }
    this.value = value;
  }

  static generate(): CustomerId {
    return new CustomerId(uuidv4());
  }

  equals(other: CustomerId): boolean {
    return this.value === other.value;
  }

  toString(): string {
    return this.value;
  }
}