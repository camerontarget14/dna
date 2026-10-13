import '@testing-library/jest-dom';
import { cleanup } from '@testing-library/react';
import { afterEach } from 'vitest';

class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}
(globalThis as Record<string, unknown>).ResizeObserver = ResizeObserverMock;

// Node 22+ defines its own global `localStorage` / `sessionStorage` that are
// `undefined` unless Node runs with --localstorage-file. They shadow jsdom's
// working storage (vitest only adds globals that aren't already present), so
// components that read storage during render throw. Replace them with an
// in-memory Storage when that happens.
class MemoryStorage implements Storage {
  private items = new Map<string, string>();
  get length() {
    return this.items.size;
  }
  key(index: number) {
    return [...this.items.keys()][index] ?? null;
  }
  getItem(key: string) {
    return this.items.get(key) ?? null;
  }
  setItem(key: string, value: string) {
    this.items.set(key, String(value));
  }
  removeItem(key: string) {
    this.items.delete(key);
  }
  clear() {
    this.items.clear();
  }
}
for (const name of ['localStorage', 'sessionStorage'] as const) {
  const current = (globalThis as Record<string, unknown>)[name] as
    | Storage
    | undefined;
  if (typeof current?.getItem !== 'function') {
    Object.defineProperty(globalThis, name, {
      value: new MemoryStorage(),
      configurable: true,
      writable: true,
    });
  }
}

// Cleanup after each test
afterEach(() => {
  cleanup();
});
