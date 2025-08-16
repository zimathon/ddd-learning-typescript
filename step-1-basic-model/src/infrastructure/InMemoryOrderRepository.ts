import { Order } from '../domain/order/Order';
import { OrderId } from '../domain/order/OrderId';
import { CustomerId } from '../domain/customer/CustomerId';
import { OrderRepository } from '../domain/order/OrderRepository';

/**
 * InMemoryOrderRepository
 * メモリ上で動作するリポジトリ実装（テスト・学習用）
 */
export class InMemoryOrderRepository implements OrderRepository {
  private orders: Map<string, Order> = new Map();

  async save(order: Order): Promise<void> {
    this.orders.set(order.getId().toString(), order);
  }

  async findById(id: OrderId): Promise<Order | null> {
    const order = this.orders.get(id.toString());
    return order || null;
  }

  async findByCustomerId(customerId: CustomerId): Promise<Order[]> {
    const result: Order[] = [];
    
    for (const order of this.orders.values()) {
      if (order.getCustomerId().equals(customerId)) {
        result.push(order);
      }
    }
    
    return result;
  }

  async delete(id: OrderId): Promise<void> {
    this.orders.delete(id.toString());
  }

  // テスト用メソッド
  clear(): void {
    this.orders.clear();
  }

  size(): number {
    return this.orders.size;
  }
}