"use client";

// In-memory, per-college session state for preview-mode drafts. Users can
// generate partnership artifacts during their visit without persisting
// anything server-side or to localStorage. Drafts live here until the
// user reloads, navigates to another college, or closes the tab.

import { createContext, useCallback, useContext, useMemo, useState } from "react";
import type { ReactNode } from "react";
import type { SavedProposal } from "@/college-atlas/partnerships/savedProposals";

type SessionDrafts = {
  partnerships: SavedProposal[];
  addPartnershipDraft: (proposal: SavedProposal) => void;
  removePartnershipDraft: (id: string) => void;
};

const SessionDraftsCtx = createContext<SessionDrafts | null>(null);

type ProviderProps = {
  collegeId: string;
  children: ReactNode;
};

export function SessionDraftsProvider({ collegeId, children }: ProviderProps) {
  // Keyed by collegeId via React's `key` prop pattern: the consumer wraps
  // <SessionDraftsProvider key={collegeId} collegeId={collegeId}> so the
  // provider remounts (and state resets) when the user navigates between
  // colleges. State scoped intentionally per-college.
  void collegeId;

  const [partnerships, setPartnerships] = useState<SavedProposal[]>([]);

  const addPartnershipDraft = useCallback((proposal: SavedProposal) => {
    setPartnerships((prev) => [proposal, ...prev.filter((p) => p.id !== proposal.id)]);
  }, []);

  const removePartnershipDraft = useCallback((id: string) => {
    setPartnerships((prev) => prev.filter((p) => p.id !== id));
  }, []);

  const value = useMemo<SessionDrafts>(
    () => ({
      partnerships,
      addPartnershipDraft,
      removePartnershipDraft,
    }),
    [partnerships, addPartnershipDraft, removePartnershipDraft],
  );

  return <SessionDraftsCtx.Provider value={value}>{children}</SessionDraftsCtx.Provider>;
}

export function useSessionDrafts(): SessionDrafts {
  const ctx = useContext(SessionDraftsCtx);
  if (!ctx) {
    // Outside a provider, drafts behave as empty and mutations no-op.
    // This lets components read drafts unconditionally without auth-mode
    // branching at every call site.
    return {
      partnerships: [],
      addPartnershipDraft: () => {},
      removePartnershipDraft: () => {},
    };
  }
  return ctx;
}
