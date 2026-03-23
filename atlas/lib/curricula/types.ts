export type DepartmentSummary = {
  department: string;
  courseCount: number;
};

export type CourseSummary = {
  name: string;
  code: string;
  learningOutcomes: string[];
  skillMappings: string[];
};
