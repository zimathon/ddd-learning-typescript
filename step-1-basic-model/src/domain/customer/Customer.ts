import { CustomerId } from './CustomerId';
import { Email } from './Email';

export enum CustomerStatus {
  ACTIVE = 'ACTIVE',
  INACTIVE = 'INACTIVE',
  SUSPENDED = 'SUSPENDED',
}

/**
 * Customer Entity
 * 顧客を表現するエンティティ
 */
export class Customer {
  private readonly id: CustomerId;
  private name: string;
  private email: Email;
  private status: CustomerStatus;
  private loyaltyPoints: number;

  constructor(id: CustomerId, name: string, email: Email) {
    this.id = id;
    this.name = name;
    this.email = email;
    this.status = CustomerStatus.ACTIVE;
    this.loyaltyPoints = 0;
  }

  static create(name: string, email: Email): Customer {
    return new Customer(CustomerId.generate(), name, email);
  }

  changeEmail(newEmail: Email): void {
    if (this.email.equals(newEmail)) {
      return;
    }
    
    if (this.status === CustomerStatus.SUSPENDED) {
      throw new Error('停止中の顧客はメールアドレスを変更できません');
    }
    
    this.email = newEmail;
  }

  changeName(newName: string): void {
    if (!newName || newName.trim().length === 0) {
      throw new Error('名前は空にできません');
    }
    this.name = newName;
  }

  addLoyaltyPoints(points: number): void {
    if (points <= 0) {
      throw new Error('ポイントは正の値である必要があります');
    }
    
    if (this.status !== CustomerStatus.ACTIVE) {
      throw new Error('アクティブな顧客のみポイントを追加できます');
    }
    
    this.loyaltyPoints += points;
  }

  useLoyaltyPoints(points: number): void {
    if (points <= 0) {
      throw new Error('使用ポイントは正の値である必要があります');
    }
    
    if (points > this.loyaltyPoints) {
      throw new Error('ポイントが不足しています');
    }
    
    this.loyaltyPoints -= points;
  }

  suspend(): void {
    if (this.status === CustomerStatus.SUSPENDED) {
      return;
    }
    this.status = CustomerStatus.SUSPENDED;
  }

  activate(): void {
    if (this.status === CustomerStatus.ACTIVE) {
      return;
    }
    this.status = CustomerStatus.ACTIVE;
  }

  equals(other: Customer): boolean {
    return this.id.equals(other.id);
  }

  getId(): CustomerId {
    return this.id;
  }

  getName(): string {
    return this.name;
  }

  getEmail(): Email {
    return this.email;
  }

  getStatus(): CustomerStatus {
    return this.status;
  }

  getLoyaltyPoints(): number {
    return this.loyaltyPoints;
  }

  isActive(): boolean {
    return this.status === CustomerStatus.ACTIVE;
  }
}