import type { ApiTargetedProposal } from "@/college-atlas/partnerships/api";

const PROPOSAL_SCHEMA_VERSION = 8;

export type SavedProposal = {
  id: string;
  proposal: ApiTargetedProposal;
  engagementType: string;
  collegeId: string;
  savedAt: string;
  status: "saved" | "flagged";
  schemaVersion?: number;
};

const PROPOSALS_KEY = (collegeId: string) =>
  `kallipolis-saved-proposals-${collegeId}`;

export function getSavedProposals(collegeId: string): SavedProposal[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(PROPOSALS_KEY(collegeId));
    if (!raw) return [];
    const all: SavedProposal[] = JSON.parse(raw);
    return all.filter((p) => p.schemaVersion === PROPOSAL_SCHEMA_VERSION);
  } catch {
    return [];
  }
}

export function saveProposal(
  collegeId: string,
  proposal: ApiTargetedProposal,
  engagementType: string,
  status: "saved" | "flagged" = "saved",
): SavedProposal {
  const saved: SavedProposal = {
    id: crypto.randomUUID(),
    proposal,
    engagementType,
    collegeId,
    savedAt: new Date().toISOString(),
    status,
    schemaVersion: PROPOSAL_SCHEMA_VERSION,
  };
  const all = getSavedProposals(collegeId);
  all.unshift(saved);
  localStorage.setItem(PROPOSALS_KEY(collegeId), JSON.stringify(all));
  return saved;
}

export function removeProposal(collegeId: string, id: string): void {
  const all = getSavedProposals(collegeId).filter((p) => p.id !== id);
  localStorage.setItem(PROPOSALS_KEY(collegeId), JSON.stringify(all));
}

export function updateProposalStatus(
  collegeId: string,
  id: string,
  status: "saved" | "flagged",
): void {
  const all = getSavedProposals(collegeId);
  const item = all.find((p) => p.id === id);
  if (item) {
    item.status = status;
    localStorage.setItem(PROPOSALS_KEY(collegeId), JSON.stringify(all));
  }
}
