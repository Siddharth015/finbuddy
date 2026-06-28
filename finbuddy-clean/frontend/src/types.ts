// Shared API types mirroring the backend Pydantic schemas.

export type SpaceType = "solo" | "shared";
export type MemberRole = "owner" | "member";
export type TxnType = "expense" | "income" | "transfer";
export type TxnScope = "personal" | "shared";
export type AccountType = "bank" | "cash" | "credit_card" | "wallet";
export type InvestmentType =
  | "equity"
  | "mutual_fund"
  | "fixed_deposit"
  | "bond"
  | "crypto"
  | "gold"
  | "other";

export interface User {
  id: number;
  telegram_id: number;
  first_name: string;
  username?: string | null;
}

export interface SpaceMember {
  id: number;
  role: MemberRole;
  user: User;
}

export interface Space {
  id: number;
  name: string;
  type: SpaceType;
  currency: string;
  invite_code: string;
  members: SpaceMember[];
}

export interface MeResponse {
  user: User;
  spaces: Space[];
}

export interface SpaceSummary {
  space: Space;
  month: string;
  total_spent: string;
  total_income: string;
  net: string;
  accounts_balance: string;
  investments_value: string;
  investments_invested: string;
  top_category: string | null;
}

export interface TransactionSplit {
  user_id: number;
  share: string;
}

export interface Transaction {
  id: number;
  space_id: number;
  user_id: number;
  account_id: number | null;
  type: TxnType;
  scope: TxnScope;
  amount: string;
  category: string;
  note: string | null;
  raw_text: string | null;
  occurred_at: string;
  splits: TransactionSplit[];
}

export interface Account {
  id: number;
  name: string;
  type: AccountType;
  balance: string;
  currency: string;
  user_id: number;
}

export interface Investment {
  id: number;
  name: string;
  type: InvestmentType;
  units: string;
  avg_buy_price: string;
  current_price: string;
  currency: string;
  user_id: number;
  invested: string;
  current_value: string;
}

export interface CategorySlice {
  category: string;
  amount: string;
  percentage: number;
}

export interface TrendPoint {
  period: string;
  amount: string;
}

export interface InsightResponse {
  month: string;
  currency: string;
  total_spent: string;
  categories: CategorySlice[];
  daily_trend: TrendPoint[];
  anomalies: string[];
}

export interface MonthlyReport {
  month: string;
  currency: string;
  total_spent: string;
  total_income: string;
  net: string;
  summary: string;
  advice: string[];
}

export interface SettlementEntry {
  from_user: User;
  to_user: User;
  amount: string;
}

export interface SettlementResponse {
  currency: string;
  balances: Record<number, string>;
  transfers: SettlementEntry[];
}
