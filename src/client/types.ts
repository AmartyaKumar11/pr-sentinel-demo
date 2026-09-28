export interface CreateOrderRequest {
  userId: string;
  token: string;
  items: string[];
  quantity: number;
}

export interface Order {
  id: string;
  status: string;
  userId: string;
  items: string[];
  quantity: number;
}

export interface ChargeRequest {
  userId: string;
  token: string;
  amount: number;
  currency?: string;
}

export interface ChargeResult {
  id: string;
  status: string;
  amount: number;
  currency: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface Session {
  token: string;
  userId: string;
}
