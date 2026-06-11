"use client";

import { useCallback } from "react";
import { SchoolConfig } from "@/config/schoolConfig";
import QueryShell from "@/ui/QueryShell";

// Non-PII posture: the ontology no longer carries individual Student
// nodes or enrollment edges (removed in the non-PII migration). The
// Students form is retained as a navigational surface; the QueryShell
// search bar is kept for visual consistency with the other forms, but
// there is no per-student data behind it — a query returns a short
// explanation, and the initial view is just the header + bar (no example
// panel, no body text). Program-level enrollment lives as aggregates per
// TOP6 in the Partnerships and Courses surfaces.
const NO_DATA_MESSAGE = "No individual student records are loaded.";

type Props = { school: SchoolConfig; onBack: () => void };

export default function StudentsView({ school, onBack }: Props) {
  const loadInitialData = useCallback(async () => {}, []);
  const queryFn = useCallback(
    async () => ({ items: [] as never[], message: NO_DATA_MESSAGE }),
    [],
  );

  return (
    <QueryShell<never>
      school={school}
      formName="Students"
      onBack={onBack}
      placeholder={`Ask me a question about ${school.name} students.`}
      examples={[]}
      queryFn={queryFn}
      loadInitialData={loadInitialData}
      renderInitialContent={() => null}
      renderResultsContent={() => null}
    />
  );
}
