import { Order } from './Order';
import { OrderId } from './OrderId';
import { CustomerId } from '../customer/CustomerId';

/**
 * OrderRepository Interface
 * Aggregate Root単位でRepositoryを定義
 */
export interface OrderRepository {
  save(order: Order): Promise<void>;
  findById(id: OrderId): Promise<Order | null>;
  findByCustomerId(customerId: CustomerId): Promise<Order[]>;
  delete(id: OrderId): Promise<void>;
}