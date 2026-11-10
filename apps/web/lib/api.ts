/**
 * OpenTrace API Client
 * Type-safe interface to the FastAPI backend.
 */

const API_BASE_URL = typeof window !== "undefined"
  ? (process.env.NEXT_PUBLIC_API_URL || "")
  : (process.env.INTERNAL_API_URL || "http://localhost:8000");

export interface InvestigationSummary {
  id: string;
  search_type: string;
  target_value: string;
  status: "queued" | "searching" | "completed" | "failed" | "cancelled";
  total_sites_checked: number;
  verified_count: number;
  inconclusive_count: number;
  created_at: string;
  completed_at?: string;
}

export interface EvidenceRecord {
  id: string;
  source_url: string;
  evidence_type: string;
  detection_method: string;
  verification_status: string;
  confidence_score: number;
  observed_at: string;
  match_evidence?: string;
}

export interface ProfileRecord {
  id: string;
  platform: string;
  category: string;
  username: string;
  profile_url: string;
  display_name?: string;
  biography?: string;
  public_website?: string;
  profile_image_url?: string;
  location?: string;
  confidence_existence: number;
  confidence_data: number;
  identity_confidence: number;
  first_seen_at: string;
  last_checked_at: string;
  evidence_records: EvidenceRecord[];
}

export interface InvestigationResults {
  investigation: InvestigationSummary;
  profiles: ProfileRecord[];
  verified_count: number;
  inconclusive_count: number;
  summary: {
    target: string;
    search_type: string;
    status: string;
    total_sites_checked: number;
    verified_profiles_count: number;
    inconclusive_count: number;
    category_breakdown: Record<string, number>;
    audit_report?: any;
  };
}

export interface GraphNode {
  id: string;
  type: string;
  label: string;
  platform?: string;
  category?: string;
  profile_url?: string;
  avatar_url?: string;
  confidence_existence: number;
  confidence_data: number;
  status: string;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  relationship_type: string;
  confidence_tier: "verified" | "strongly_supported" | "possible" | "unverified";
  confidence_score: number;
  evidence_reason: string;
}

export interface InvestigationGraph {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface SupportedSite {
  name: string;
  category: string;
  url_pattern: string;
  check_type: string;
  is_active: boolean;
}

export interface UserProfile {
  id: string;
  email: string;
  is_verified: boolean;
  created_at: string;
}

function getAuthHeaders(): HeadersInit {
  const headers: HeadersInit = {
    "Content-Type": "application/json",
  };
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("opentrace_auth_token");
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
  }
  return headers;
}

export const api = {
  // Investigations
  async createInvestigation(
    value: string,
    type: "username" | "email" | "phone" = "username",
    options?: { deep_search?: boolean; max_depth?: number; categories?: string[] }
  ): Promise<InvestigationSummary> {
    const res = await fetch(`${API_BASE_URL}/api/v1/investigations`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({ type, value, options }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Failed to initiate investigation.");
    }
    return res.json();
  },

  async getInvestigation(id: string): Promise<InvestigationSummary> {
    const res = await fetch(`${API_BASE_URL}/api/v1/investigations/${id}`, {
      headers: getAuthHeaders(),
      cache: "no-store",
    });
    if (!res.ok) throw new Error("Investigation not found.");
    return res.json();
  },

  async getInvestigationResults(id: string): Promise<InvestigationResults> {
    const res = await fetch(`${API_BASE_URL}/api/v1/investigations/${id}/results`, {
      headers: getAuthHeaders(),
      cache: "no-store",
    });
    if (!res.ok) throw new Error("Failed to load results.");
    return res.json();
  },

  async getInvestigationGraph(id: string): Promise<InvestigationGraph> {
    const res = await fetch(`${API_BASE_URL}/api/v1/investigations/${id}/graph`, {
      headers: getAuthHeaders(),
      cache: "no-store",
    });
    if (!res.ok) throw new Error("Failed to load investigation graph.");
    return res.json();
  },

  async deleteInvestigation(id: string): Promise<void> {
    const res = await fetch(`${API_BASE_URL}/api/v1/investigations/${id}`, {
      method: "DELETE",
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error("Failed to delete investigation.");
  },

  async listInvestigations(): Promise<InvestigationSummary[]> {
    const res = await fetch(`${API_BASE_URL}/api/v1/investigations`, {
      headers: getAuthHeaders(),
      cache: "no-store",
    });
    if (!res.ok) throw new Error("Failed to fetch investigation history.");
    return res.json();
  },

  // Sites Directory
  async listSites(category?: string): Promise<SupportedSite[]> {
    const url = category
      ? `${API_BASE_URL}/api/v1/sites?category=${category}`
      : `${API_BASE_URL}/api/v1/sites`;
    const res = await fetch(url, { cache: "no-store" });
    if (!res.ok) throw new Error("Failed to fetch supported sites.");
    return res.json();
  },

  // Health
  async getHealth(): Promise<{ status: string; supported_sites_count: number; service: string }> {
    const res = await fetch(`${API_BASE_URL}/api/health`, { cache: "no-store" });
    if (!res.ok) throw new Error("Backend offline.");
    return res.json();
  },

  // Auth
  async register(email: string, password: string): Promise<UserProfile> {
    const res = await fetch(`${API_BASE_URL}/api/v1/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Registration failed.");
    }
    return res.json();
  },

  async login(email: string, password: string): Promise<{ access_token: string }> {
    const res = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Invalid login credentials.");
    }
    const data = await res.json();
    if (typeof window !== "undefined") {
      localStorage.setItem("opentrace_auth_token", data.access_token);
    }
    return data;
  },

  async getMe(): Promise<UserProfile | null> {
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/auth/me`, {
        headers: getAuthHeaders(),
      });
      if (!res.ok) return null;
      return res.json();
    } catch {
      return null;
    }
  },

  logout(): void {
    if (typeof window !== "undefined") {
      localStorage.removeItem("opentrace_auth_token");
    }
  },

  // Self-Audits (Email & Phone)
  async requestEmailChallenge(email: string): Promise<{ challenge_id: string; dev_otp?: string; message: string }> {
    const res = await fetch(`${API_BASE_URL}/api/v1/audits/email/challenge`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Failed to request email verification.");
    }
    return res.json();
  },

  async verifyEmailAudit(challenge_id: string, code: string): Promise<any> {
    const res = await fetch(`${API_BASE_URL}/api/v1/audits/email/verify`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({ challenge_id, code }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Invalid or expired verification code.");
    }
    return res.json();
  },

  async requestPhoneChallenge(phone: string): Promise<{ challenge_id: string; dev_otp?: string; message: string }> {
    const res = await fetch(`${API_BASE_URL}/api/v1/audits/phone/challenge`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ phone }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Failed to request phone verification.");
    }
    return res.json();
  },

  async verifyPhoneAudit(challenge_id: string, code: string): Promise<any> {
    const res = await fetch(`${API_BASE_URL}/api/v1/audits/phone/verify`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({ challenge_id, code }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Invalid or expired verification code.");
    }
    return res.json();
  },
};

