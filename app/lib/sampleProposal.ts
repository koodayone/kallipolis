/**
 * Sample partnership proposal fixture for the Explore Partnerships page.
 *
 * Realistic structure matching the NarrativeProposal shape, with
 * representative (not real) data for exposition purposes.
 */

export const SAMPLE_PROPOSAL = {
  employer: "Pacific Regional Medical Center",
  sector: "Healthcare",
  partnership_type: "Internship Pipeline",
  selected_occupation: {
    title: "Registered Nurses",
    soc_code: "29-1141",
  },
  core_skills: [
    "Patient Care",
    "Clinical Assessment",
    "Electronic Health Records",
    "Pharmacology",
    "Medical Terminology",
    "Infection Control",
  ],
  gap_skill: null,
  regions: ["Bay Area / Peninsula"],

  opportunity: "Pacific Regional Medical Center operates a 312-bed acute care facility with documented nursing shortages across emergency, surgical, and ambulatory care units. Regional demand for registered nurses projects 2,400 annual openings at a median wage of $128,400, with a five-year growth rate of 8.2%. The facility's proximity to campus and existing clinical site agreements position it as a high-alignment internship partner.",

  opportunity_evidence: [
    {
      title: "Registered Nurses",
      soc_code: "29-1141",
      annual_wage: 128400,
      employment: 42300,
      growth_rate: 8.2,
      annual_openings: 2400,
    },
    {
      title: "Licensed Vocational Nurses",
      soc_code: "29-2061",
      annual_wage: 67200,
      employment: 8100,
      growth_rate: 5.1,
      annual_openings: 680,
    },
  ],

  justification: {
    curriculum_composition: "The Nursing Sciences department offers a 14-course registered nursing pathway that develops 5 of 6 core skills identified for this partnership. Clinical Assessment and Patient Care are developed across multiple courses with dedicated lab components. Electronic Health Records proficiency is embedded in the Health Information Technology sequence.",

    curriculum_evidence: [
      {
        department: "Nursing Sciences",
        courses: [
          { code: "NURS 110", name: "Fundamentals of Nursing", description: "Introduction to nursing concepts, patient assessment, and clinical reasoning.", learning_outcomes: ["Perform basic patient assessments", "Apply infection control protocols"], skills: ["Patient Care", "Clinical Assessment", "Infection Control"] },
          { code: "NURS 210", name: "Medical-Surgical Nursing", description: "Care of adult patients with acute and chronic conditions.", learning_outcomes: ["Manage complex patient care scenarios", "Administer medications safely"], skills: ["Patient Care", "Pharmacology", "Clinical Assessment"] },
          { code: "NURS 215", name: "Pharmacology for Nurses", description: "Drug classifications, mechanisms, and safe administration.", learning_outcomes: ["Calculate medication dosages", "Identify drug interactions"], skills: ["Pharmacology", "Medical Terminology"] },
        ],
      },
      {
        department: "Health Information Technology",
        courses: [
          { code: "HIT 101", name: "Health Records Systems", description: "EHR platforms, data entry standards, and clinical documentation.", learning_outcomes: ["Navigate EHR systems", "Maintain patient data integrity"], skills: ["Electronic Health Records", "Medical Terminology"] },
        ],
      },
    ],

    student_composition: "The aligned nursing and health information technology programs enroll 284 students, of whom 47 demonstrate proficiency in all 6 core skills. The top candidates combine clinical coursework with health records training, producing a competency profile that matches the facility's integrated care model.",

    student_evidence: {
      total_in_program: 284,
      with_all_core_skills: 47,
      top_students: [
        { uuid: "s-00247", display_number: 247, primary_focus: "Nursing Sciences", courses_completed: 12, gpa: 3.92, matching_skills: 6, enrollments: [], relevant_skills: ["Patient Care", "Clinical Assessment", "EHR", "Pharmacology", "Medical Terminology", "Infection Control"] },
        { uuid: "s-00831", display_number: 831, primary_focus: "Nursing Sciences", courses_completed: 14, gpa: 3.88, matching_skills: 6, enrollments: [], relevant_skills: ["Patient Care", "Clinical Assessment", "EHR", "Pharmacology", "Medical Terminology", "Infection Control"] },
        { uuid: "s-01204", display_number: 1204, primary_focus: "Health Information Technology", courses_completed: 10, gpa: 3.85, matching_skills: 5, enrollments: [], relevant_skills: ["EHR", "Medical Terminology", "Patient Care", "Clinical Assessment", "Infection Control"] },
      ],
    },
  },

  roadmap: "Begin with a 6-week summer clinical rotation for 8-12 students in emergency and ambulatory care. Map clinical hours to NURS 290 (Clinical Practicum) for academic credit. Establish a preceptor matching process with unit charge nurses. Target first cohort for Summer 2026 with an evaluation checkpoint at week 4 to assess patient interaction competency and EHR documentation readiness.",
};
