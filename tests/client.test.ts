import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";

import { charge, createOrder, login } from "../src/client/index.ts";

const calls: { url: string; body: string }[] = [];

afterEach(() => {
  calls.length = 0;
  delete (globalThis as { fetch?: typeof fetch }).fetch;
});

function mockFetch(payload: unknown) {
  globalThis.fetch = (async (url: string | URL, init?: RequestInit) => {
    calls.push({ url: String(url), body: String(init?.body ?? "") });
    return new Response(JSON.stringify(payload), { status: 200 });
  }) as typeof fetch;
}

describe("api client", () => {
  it("createOrder posts to the orders route", async () => {
    mockFetch({ id: "o1", status: "created", userId: "u", items: ["a"], quantity: 1 });
    const order = await createOrder({ userId: "u", token: "t", items: ["a"], quantity: 1 });
    assert.equal(order.status, "created");
    assert.equal(calls[0].url, "http://127.0.0.1:8000/orders");
    assert.match(calls[0].body, /"quantity":1/);
  });

  it("charge defaults currency to USD", async () => {
    mockFetch({ id: "c1", status: "charged", amount: 12, currency: "USD" });
    const result = await charge({ userId: "u", token: "t", amount: 12 });
    assert.equal(result.currency, "USD");
    assert.match(calls[0].body, /"currency":"USD"/);
    assert.equal(calls[0].url, "http://127.0.0.1:8000/billing/charge");
  });

  it("login posts credentials", async () => {
    mockFetch({ token: "tok", userId: "u" });
    const session = await login({ email: "a@b.c", password: "secret" });
    assert.equal(session.token, "tok");
    assert.equal(calls[0].url, "http://127.0.0.1:8000/auth/login");
  });
});
