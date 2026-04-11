export type DepartmentSummary = {
  department: string;
  courseCount: number;
};

export type CourseSummary = {
  name: string;
  code: string;
  description: string;
  learningOutcomes: string[];
  courseObjectives: string[];
  skillMappings: string[];
};
