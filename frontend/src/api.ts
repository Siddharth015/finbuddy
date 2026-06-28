// Typed fetch client. Every request carries the Telegram initData so the
// backend can authenticate the user.
import { getInitData } from "./telegram";
import type {
  Account,
  Investment,
  InsightResponse,
  MeResponse,
  MonthlyReport,
  SettlementResponse,
  Space,
  SpaceSummary,
  Transaction,
} from "./types";

const BASE_URL = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    "X-Telegram-Init-Data": getInitData(),
    ...(options.headers as Record<string, string>),
  };
  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      /* ignore */
    }
    throw new ApiError(res.status, detail);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const api = {
  me: () => request<MeResponse>("/api/me"),

  createSpace: (name: string, type: "solo" | "shared", currency: string) =>
    request<Space>("/api/spaces", {
      method: "POST",
      body: JSON.stringify({ name, type, currency }),
    }),

  joinSpace: (invite_code: string) =>
    request<Space>("/api/spaces/join", {
      method: "POST",
      body: JSON.stringify({ invite_code }),
    }),

  summary: (spaceId: number, month?: string) =>
    request<SpaceSummary>(
      `/api/spaces/${spaceId}/summary${month ? `?month=${month}` : ""}`,
    ),

  transactions: (spaceId: number, limit = 50) =>
    request<Transaction[]>(`/api/spaces/${spaceId}/transactions?limit=${limit}`),

  addTransaction: (
    spaceId: number,
    payload: Record<string, unknown>,
  ) =>
    request<Transaction>(`/api/spaces/${spaceId}/transactions`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  deleteTransaction: (spaceId: number, txnId: number) =>
    request<void>(`/api/spaces/${spaceId}/transactions/${txnId}`, {
      method: "DELETE",
    }),

  accounts: (spaceId: number) =>
    request<Account[]>(`/api/spaces/${spaceId}/accounts`),

  addAccount: (spaceId: number, payload: Record<string, unknown>) =>
    request<Account>(`/api/spaces/${spaceId}/accounts`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  deleteAccount: (spaceId: number, accountId: number) =>
    request<void>(`/api/spaces/${spaceId}/accounts/${accountId}`, {
      method: "DELETE",
    }),

  investments: (spaceId: number) =>
    request<Investment[]>(`/api/spaces/${spaceId}/investments`),

  addInvestment: (spaceId: number, payload: Record<string, unknown>) =>
    request<Investment>(`/api/spaces/${spaceId}/investments`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  deleteInvestment: (spaceId: number, investmentId: number) =>
    request<void>(`/api/spaces/${spaceId}/investments/${investmentId}`, {
      method: "DELETE",
    }),

  insights: (spaceId: number, month?: string) =>
    request<InsightResponse>(
      `/api/spaces/${spaceId}/insights${month ? `?month=${month}` : ""}`,
    ),

  report: (spaceId: number, month?: string) =>
    request<MonthlyReport>(
      `/api/spaces/${spaceId}/report${month ? `?month=${month}` : ""}`,
    ),

  settlement: (spaceId: number) =>
    request<SettlementResponse>(`/api/spaces/${spaceId}/settlement`),
};
