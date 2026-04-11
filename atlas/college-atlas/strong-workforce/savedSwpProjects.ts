import type { ApiSwpProject } from "@/college-atlas/strong-workforce/api";

export type SavedSwpProject = {
  id: string;
  project: ApiSwpProject;
  partnershipId: string;
  collegeId: string;
  savedAt: string;
};

const SWP_KEY = (collegeId: string) =>
  `kallipolis-saved-swp-${collegeId}`;

export function getSavedSwpProjects(collegeId: string): SavedSwpProject[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(SWP_KEY(collegeId));
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

export function saveSwpProject(
  collegeId: string,
  project: ApiSwpProject,
  partnershipId: string,
): SavedSwpProject {
  const saved: SavedSwpProject = {
    id: crypto.randomUUID(),
    project,
    partnershipId,
    collegeId,
    savedAt: new Date().toISOString(),
  };
  const all = getSavedSwpProjects(collegeId);
  all.unshift(saved);
  localStorage.setItem(SWP_KEY(collegeId), JSON.stringify(all));
  return saved;
}

export function removeSwpProject(collegeId: string, id: string): void {
  const all = getSavedSwpProjects(collegeId).filter((p) => p.id !== id);
  localStorage.setItem(SWP_KEY(collegeId), JSON.stringify(all));
}
