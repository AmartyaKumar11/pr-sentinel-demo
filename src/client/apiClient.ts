import type { ChargeRequest, ChargeResult, CreateOrderRequest, LoginRequest, Order, Session } from "./types.ts";

const baseUrl = process.env.PR_SENTINEL_API ?? "http://127.0.0.1:8000";

async function request<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${baseUrl}${path}`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new Error(`API ${path} failed: ${response.status}`);
  }
  return (await response.json()) as T;
}

// The cast keeps these from being parsed as function definitions, so a call to
// create_order / charge / validate_token name-matches the Python functions.
const create_order = ((input: CreateOrderRequest) =>
  request<Order>("/orders", input)) as (input: CreateOrderRequest) => Promise<Order>;

const chargeAccount = ((input: ChargeRequest) =>
  request<ChargeResult>("/billing/charge", input)) as (
  input: ChargeRequest,
) => Promise<ChargeResult>;

const validate_token = ((input: LoginRequest) =>
  request<Session>("/auth/login", input)) as (input: LoginRequest) => Promise<Session>;

/** Mirrors src/orders.py create_order. */
export function createOrder(input: CreateOrderRequest): Promise<Order> {
  return create_order(input);
}

/** Mirrors src/billing.py charge. */
export function charge(input: ChargeRequest): Promise<ChargeResult> {
  return chargeAccount({ ...input, currency: input.currency ?? "USD" });
}

/** Mirrors src/auth.py validate_token. The demo has no login(). */
export function login(input: LoginRequest): Promise<Session> {
  return validate_token(input);
}
