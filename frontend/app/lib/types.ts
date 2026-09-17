export type VoteChoice = "going" | "maybe" | "no";

export interface VoteTotals { going: number; maybe: number; no: number }

export interface EventRecord {
  id: string;
  title: string;
  starts_at: string;
  ends_at: string | null;
  timezone: string;
  location: string | null;
  description: string | null;
  owner_id: string;
  created_at: string;
  updated_at: string;
  vote_totals: VoteTotals;
  my_vote: VoteChoice | null;
  group_ids: string[];
}

export interface GroupRecord {
  id: string;
  name: string;
  invite_code: string;
  created_at: string;
  role: "owner" | "member";
}

export interface ExtractionResult {
  title: string | null;
  starts_at: string | null;
  ends_at: string | null;
  timezone: string;
  location: string | null;
  description: string | null;
  confidence: number;
  warnings: string[];
}
