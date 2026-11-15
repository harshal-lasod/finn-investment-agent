const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}/api${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
    cache: "no-store"
  });
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.detail ?? `Request failed (${response.status})`);
  }
  return response.json() as Promise<T>;
}

export type Stock = {
  ticker: string;
  company_name: string;
  sector: string;
  market_cap_category: string;
  market_data_source?: string;
  quote_date?: string | null;
  market_data: {
    current_price: number;
    change_percent: number;
    volume_multiple: number;
    pe_ratio: number | null;
    market_cap_cr: number;
  };
};

export type Person = {
  id: string;
  name: string;
  current_role: string;
  current_company: string;
  closeness_score: number;
  role_type: string;
  expertise_tags: string[];
  past_companies: string[];
  alma_maters: string[];
};

export const demoNotice =
  "Illustrative demo data only. Prices, filings, financials, people, and guidance are synthetic and not verified.";
