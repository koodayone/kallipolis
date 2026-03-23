export type StudentSummary = {
  uuid: string;
  displayNumber: number;
  primaryFocus: string;
  coursesCompleted: number;
  avgPerformance: "Strong" | "Developing" | "Incomplete";
};

export type StudentEnrollment = {
  courseName: string;
  department: string;
  grade: string;
  term: string;
  status: string;
};

export type StudentDetail = {
  uuid: string;
  displayNumber: number;
  primaryFocus: string;
  coursesCompleted: number;
  avgPerformance: string;
  enrollments: StudentEnrollment[];
  skills: string[];
};
