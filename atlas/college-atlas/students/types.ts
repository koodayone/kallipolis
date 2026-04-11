export type StudentSummary = {
  uuid: string;
  displayNumber: number;
  primaryFocus: string;
  coursesCompleted: number;
  gpa: number;
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
  gpa: number;
  enrollments: StudentEnrollment[];
  skills: string[];
};
