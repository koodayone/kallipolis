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

export type CourseRef = {
  code: string;
  name: string;
};

export type TopGroup = {
  topCode: string;
  topTitle: string;
  courses: CourseRef[];
};

export type OccupationAlignment = {
  socCode: string;
  title: string;
  matchedCourseCount: number;
  matchedTopGroups: TopGroup[];
};

export type StudentDetail = {
  uuid: string;
  displayNumber: number;
  primaryFocus: string;
  coursesCompleted: number;
  gpa: number;
  enrollments: StudentEnrollment[];
  occupationAlignment: OccupationAlignment[];
};
