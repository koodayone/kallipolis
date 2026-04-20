// Curated partnership proposals shipped with the atlas bundle for preview
// mode. The SWP flow requires saved partnerships as input; in preview there
// are no real saves, so these seeds stand in as the demonstration substrate.
//
// Keyed by college *display name* to match the lookup convention used by
// PartnershipsView / StrongWorkforceView (both pass `school.name` through
// to localStorage and API calls — the same key drives seeded reads).
//
// Regeneration procedure: see ./README.md. The schema must match
// PROPOSAL_SCHEMA_VERSION from savedProposals.ts — the Vitest suite fails
// the build if a seeded entry drifts.

import type { SavedProposal } from "@/college-atlas/partnerships/savedProposals";
import { CALIFORNIA_COLLEGES } from "@/state-atlas/californiaColleges";
import { FEATURED_COLLEGES } from "@/state-atlas/featuredColleges";

const FEATURED_NAMES = CALIFORNIA_COLLEGES.filter((c) =>
  FEATURED_COLLEGES.has(c.id),
).map((c) => c.name);

const SEEDED_BY_NAME: Record<string, SavedProposal[]> = {
  "Shasta College": [
    {
      "id": "seed-shasta-advisory-01",
      "proposal": {
        "employer": "Pacific Gas & Electric",
        "sector": "Utilities",
        "partnership_type": "Advisory Board",
        "selected_occupation": "Electrical and Electronics Repairers, Powerhouse, Substation, and Relay",
        "selected_soc_code": "49-2095",
        "core_skills": [
          "Electrical Systems",
          "Troubleshooting",
          "Workplace Safety"
        ],
        "gap_skill": "",
        "regions": [
          "Far North",
          "South Central Coast"
        ],
        "opportunity": "PG&E's role maintaining high-voltage substations, relay systems, and gas infrastructure across Northern California makes it a compelling advisory board partner for Shasta College's technical workforce programs. The company's operational emphasis on electrical systems maintenance and safety in demanding field environments connects directly to what the college's CTE programs prepare students to do. An advisory board formalizes that connection as an ongoing channel for industry guidance at no grant funding cost.",
        "opportunity_evidence": [
          {
            "title": "Facilities Managers",
            "soc_code": "11-3013",
            "annual_wage": 89040,
            "employment": 390,
            "annual_openings": 40,
            "growth_rate": 0.047168343
          },
          {
            "title": "Electrical and Electronics Repairers, Powerhouse, Substation, and Relay",
            "soc_code": "49-2095",
            "annual_wage": 113460,
            "employment": 40,
            "annual_openings": 0,
            "growth_rate": 0.103778807
          },
          {
            "title": "Electrical Engineers",
            "soc_code": "17-2071",
            "annual_wage": 135620,
            "employment": 210,
            "annual_openings": 20,
            "growth_rate": 0.165120743
          }
        ],
        "justification": {
          "curriculum_composition": "The Industrial Technology department provides the closest curricular match to PG&E's workforce operations, with coursework spanning electrical systems, troubleshooting, and workplace safety across eight courses. That breadth covers the core technical competencies PG&E's powerhouse repairers and facilities managers require in live electrical environments. The Computer Information Systems department contributes troubleshooting preparation, extending the pipeline into roles where diagnostic reasoning is central.",
          "curriculum_evidence": [
            {
              "department": "Industrial Technology (INDE)",
              "courses": [
                {
                  "code": "INDE 101",
                  "name": "INDUSTRIAL TRADE BASICS",
                  "description": "This course provides an overview of basic skills required for individuals seeking entry-level employment in industrial occupations. The subjects covered include workplace safety and regulations, hand and power tools, basic rigging, introduction to blueprints, and an overview of soft skills related to effective communications and employability requirements necessary for sustainable employment. This course may be offered in a distance education format.",
                  "learning_outcomes": [],
                  "skills": [
                    "Workplace Safety"
                  ]
                },
                {
                  "code": "INDE 301",
                  "name": "INDUSTRIAL TRADE BASICS",
                  "description": "The course provides an overview of basic skills required for individuals seeking entry-level employment in industrial occupations. The subjects covered include workplace safety and regulations, hand and power tools, basic rigging, introduction to blueprints, and an overview of soft skills related to effective communications and employability requirements necessary for sustainable employment. This course may be offered in a distance education format.",
                  "learning_outcomes": [],
                  "skills": [
                    "Workplace Safety"
                  ]
                },
                {
                  "code": "INDE 310",
                  "name": "OSHA 10",
                  "description": "This ten-hour general industry class is intended to provide training for workers and employers on the recognition, avoidance, abatement, and prevention of safety and health hazards in workplaces in general industry. The program also provides information regarding workers' rights and employer responsibilities. This course may be offered in a distance education format.",
                  "learning_outcomes": [],
                  "skills": [
                    "Workplace Safety"
                  ]
                },
                {
                  "code": "INDE 342",
                  "name": "INDUSTRIAL CONTROL DEVICES",
                  "description": "This course introduces industrial control devices used in advanced manufacturing. Devices include motors, sensors, valves, and more. This course also covers the control of these devices by Programmable Logic Controls (PLC) including PLC code using ladder logic with RS 5000, PLC Circuit design, schematics, wiring, troubleshooting and maintenance. This course may be offered in a distance education format.",
                  "learning_outcomes": [],
                  "skills": [
                    "Troubleshooting"
                  ]
                },
                {
                  "code": "INDE 344",
                  "name": "INDUSTRIAL PROCESS CONTROL",
                  "description": "This course introduces industrial process control using Programmable Logic Controls (PLCs) with loop control. Multiple process systems, Human-Machine Interface (HMI) devices, whole system design, wiring, coding using RS 5000, building, maintenance and troubleshooting are also covered. This course may be offered in a distance education format.",
                  "learning_outcomes": [],
                  "skills": [
                    "Troubleshooting"
                  ]
                },
                {
                  "code": "INDE 37",
                  "name": "Electricity and Electronics",
                  "description": "This course will provide the theory and hands-on electronic skills necessary for students in vocational or Career Technical Education courses such as those in the Automotive and Diesel Industrial Technology, Computers, Mechatronics, Energy, Heavy Equipment/Transportation programs, and more. Course content includes electrical theory, components testing, and troubleshooting of many types of electrical systems including AC and DC systems. This course may be offered in a distance education format. (CSU transferable)",
                  "learning_outcomes": [],
                  "skills": [
                    "Electrical Systems",
                    "Troubleshooting"
                  ]
                },
                {
                  "code": "INDE 42",
                  "name": "INDUSTRIAL CONTROL DEVICES",
                  "description": "This course introduces industrial control devices used in automation and advanced manufacturing. Devices include motors, sensors, valves, and more. This course also covers the control of these devices by Programmable Logic Controls (PLC) including PLC code using ladder logic with RS 5000, PLC Circuit design, schematics, wiring, troubleshooting and maintenance. This course may be offered in a distance education format. (CSU transferable)",
                  "learning_outcomes": [],
                  "skills": [
                    "Troubleshooting"
                  ]
                },
                {
                  "code": "INDE 44",
                  "name": "INDUSTRIAL PROCESS CONTROL",
                  "description": "This course introduces industrial process control using Programmable Logic Controls (PLCs) with loop control. Multiple process systems, Human-Machine Interface (HMI) devices, whole system design, wiring, coding using RS 5000, building, maintenance and troubleshooting are also covered. This course may be offered in a distance education format. (CSU transferable)",
                  "learning_outcomes": [],
                  "skills": [
                    "Troubleshooting"
                  ]
                }
              ],
              "aligned_skills": [
                "Electrical Systems",
                "Troubleshooting",
                "Workplace Safety"
              ]
            },
            {
              "department": "Computer Information Systems",
              "courses": [
                {
                  "code": "CIS 31",
                  "name": "CCNA 1 ROUTING AND SWITCHING - INTRODUCTION TO NETWORKS",
                  "description": "This course is the first in a two-course series designed to prepare students for the Cisco Certified Entry Network Technician (CCENT) exam, and the course is the first of a four-course series designed to prepare students for the Cisco Certified Networking Associate (CCNA) exam. CCNA Routing and Switching: Introduction to Networks (ITN) covers networking architecture, structure, and functions. The course introduces the principles and structure of IP addressing and the fundamentals of Ethernet concepts, media, and operations to provide a foundation for the curriculum. This course is offered by Shasta College as the Cisco Regional Networking Academy in the area. Instructional materials developed by Cisco Systems are utilized for the course. The course teaches students the skills needed to obtain entry-level network installer jobs. It also helps students develop some of the skills needed to become network technicians, computer technicians, cable installers, and help desk technicians. It provides a hands-on introduction to networking and the Internet using tools and hardware commonly found in small to medium size business environments. Labs include network device configuration, Internet connectivity, wireless connectivity, file and print sharing, and IP addressing. This course may be offered in a distance education format. (CSU transferable)",
                  "learning_outcomes": [],
                  "skills": [
                    "Troubleshooting"
                  ]
                },
                {
                  "code": "CIS 32",
                  "name": "CCNA 2 ROUTING AND SWITCHING - ROUTING AND SWITCHING ESSENTIALS",
                  "description": "This course is the second in a two-course series designed to prepare students for the Cisco Certified Entry Network Technician (CCENT) exam, and the course is the second of a four-course series designed to prepare students for the Cisco Certified Networking Associate (CCNA) exam. CCNA Routing and Switching: Routing and Switching Essentials (RSE) covers the architecture, components, and operations of routers and switches in a small network. Students learn how to configure a router and a switch for basic functionality. This course is offered by Shasta College as the Cisco Regional Networking Academy in the area. Instructional materials developed by Cisco Systems are utilized for the course. The course prepares students for jobs as network technicians. It also helps students develop additional skills required for computer technicians and help desk technicians. It provides a basic overview of routing and remote access, addressing, and security. It familiarizes students with servers that provide email services, Web space, and authenticated access. Students learn soft skills required for help desk and customer service positions. Network monitoring and basic troubleshooting skills are taught in context. This course may be offered in a distance education format. (CSU transferable)",
                  "learning_outcomes": [],
                  "skills": [
                    "Troubleshooting"
                  ]
                },
                {
                  "code": "CIS 90",
                  "name": "A+ CERTIFICATION PREPARATION/CISCO IT ESSENTIALS I",
                  "description": "This course provides students with the foundational knowledge and hands-on skills necessary for a career in IT support and computer maintenance. Designed to align with the CompTIA A+ certification objectives, it covers essential topics such as hardware components, system assembly, operating system installation and configuration, networking fundamentals, virtualization and cloud computing concepts, and troubleshooting methodologies. Students will gain practical experience diagnosing and repairing hardware and software issues, securing devices, and applying industry best practices. The course also emphasizes professionalism, operational procedures, ethical considerations, and effective communication in IT support roles. Through hands-on labs and real-world troubleshooting scenarios, students will develop critical problem-solving skills essential for success in the field. Offered in in-person, hybrid, or online learning formats. Upon completion, students will be prepared to take the CompTIA A+ certification exams and pursue entry-level roles in IT support and technical services. This course may be offered in a distance education format. (CSU transferable)",
                  "learning_outcomes": [],
                  "skills": [
                    "Troubleshooting"
                  ]
                }
              ],
              "aligned_skills": [
                "Troubleshooting"
              ]
            }
          ],
          "student_composition": "Students in the Industrial Technology department are building hands-on technical competencies in the same skill areas PG&E prioritizes for its utility and facilities roles. The Computer Information Systems program adds students developing troubleshooting skills applicable to technical support functions within utility operations. Together these programs represent a pipeline oriented toward the applied, safety-conscious technical work PG&E's entry-level hiring reflects.",
          "student_evidence": {
            "total_in_program": 176,
            "with_all_core_skills": 13,
            "top_students": [
              {
                "uuid": "db364ea3-0556-584b-9be7-e6a9c6edb932",
                "display_number": 1,
                "primary_focus": "Industrial Technology (INDE)",
                "courses_completed": 3,
                "gpa": 3.57,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "INDE 37",
                    "name": "Electricity and Electronics",
                    "grade": "A",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "INDE 44",
                    "name": "INDUSTRIAL PROCESS CONTROL",
                    "grade": "B",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "INDE 101",
                    "name": "INDUSTRIAL TRADE BASICS",
                    "grade": "A",
                    "term": "2025-Spring"
                  }
                ],
                "relevant_skills": [
                  "Electrical Systems",
                  "Troubleshooting",
                  "Workplace Safety"
                ]
              },
              {
                "uuid": "266e89a3-db90-57fe-8302-4f3f82d264f1",
                "display_number": 2,
                "primary_focus": "Industrial Technology (INDE)",
                "courses_completed": 3,
                "gpa": 3.56,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "INDE 37",
                    "name": "Electricity and Electronics",
                    "grade": "A",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "INDE 42",
                    "name": "INDUSTRIAL CONTROL DEVICES",
                    "grade": "B",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "INDE 101",
                    "name": "INDUSTRIAL TRADE BASICS",
                    "grade": "A",
                    "term": "2022-Fall"
                  }
                ],
                "relevant_skills": [
                  "Electrical Systems",
                  "Troubleshooting",
                  "Workplace Safety"
                ]
              },
              {
                "uuid": "32d96d0f-c7ef-5f38-8d36-e8ffad15b681",
                "display_number": 3,
                "primary_focus": "Industrial Technology (INDE)",
                "courses_completed": 2,
                "gpa": 3.33,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "INDE 37",
                    "name": "Electricity and Electronics",
                    "grade": "A",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "INDE 101",
                    "name": "INDUSTRIAL TRADE BASICS",
                    "grade": "A",
                    "term": "2025-Spring"
                  }
                ],
                "relevant_skills": [
                  "Electrical Systems",
                  "Troubleshooting",
                  "Workplace Safety"
                ]
              },
              {
                "uuid": "05acf789-6095-50ba-b531-cfbc9250b691",
                "display_number": 4,
                "primary_focus": "Industrial Technology (INDE)",
                "courses_completed": 3,
                "gpa": 3.24,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "INDE 37",
                    "name": "Electricity and Electronics",
                    "grade": "B",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "INDE 42",
                    "name": "INDUSTRIAL CONTROL DEVICES",
                    "grade": "A",
                    "term": "2022-Fall"
                  },
                  {
                    "code": "INDE 101",
                    "name": "INDUSTRIAL TRADE BASICS",
                    "grade": "A",
                    "term": "2022-Winter"
                  }
                ],
                "relevant_skills": [
                  "Electrical Systems",
                  "Troubleshooting",
                  "Workplace Safety"
                ]
              },
              {
                "uuid": "5b29973f-6157-5312-9394-84abb409e634",
                "display_number": 5,
                "primary_focus": "Industrial Technology (INDE)",
                "courses_completed": 3,
                "gpa": 3.11,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "INDE 37",
                    "name": "Electricity and Electronics",
                    "grade": "A",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "AGMA 42",
                    "name": "FARM POWER AND MACHINERY",
                    "grade": "A",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "INDE 101",
                    "name": "INDUSTRIAL TRADE BASICS",
                    "grade": "B",
                    "term": "2022-Fall"
                  }
                ],
                "relevant_skills": [
                  "Electrical Systems",
                  "Troubleshooting",
                  "Workplace Safety"
                ]
              },
              {
                "uuid": "77e04967-b9e8-5019-8086-97252ee206ae",
                "display_number": 6,
                "primary_focus": "Industrial Technology (INDE)",
                "courses_completed": 4,
                "gpa": 3.09,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "INDE 37",
                    "name": "Electricity and Electronics",
                    "grade": "A",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "AGMA 42",
                    "name": "FARM POWER AND MACHINERY",
                    "grade": "B",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "INDE 42",
                    "name": "INDUSTRIAL CONTROL DEVICES",
                    "grade": "B",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "INDE 101",
                    "name": "INDUSTRIAL TRADE BASICS",
                    "grade": "A",
                    "term": "2023-Winter"
                  }
                ],
                "relevant_skills": [
                  "Electrical Systems",
                  "Troubleshooting",
                  "Workplace Safety"
                ]
              },
              {
                "uuid": "7536589b-f996-5707-af15-b3a1fb18f41d",
                "display_number": 7,
                "primary_focus": "Industrial Technology (INDE)",
                "courses_completed": 2,
                "gpa": 3.04,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "INDE 37",
                    "name": "Electricity and Electronics",
                    "grade": "A",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "INDE 101",
                    "name": "INDUSTRIAL TRADE BASICS",
                    "grade": "A",
                    "term": "2024-Fall"
                  }
                ],
                "relevant_skills": [
                  "Electrical Systems",
                  "Troubleshooting",
                  "Workplace Safety"
                ]
              },
              {
                "uuid": "4fbc1e00-19b7-5e26-8f0e-529d0cf722b1",
                "display_number": 8,
                "primary_focus": "Industrial Technology (INDE)",
                "courses_completed": 3,
                "gpa": 2.89,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "INDE 37",
                    "name": "Electricity and Electronics",
                    "grade": "B",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "INDE 44",
                    "name": "INDUSTRIAL PROCESS CONTROL",
                    "grade": "B",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "INDE 101",
                    "name": "INDUSTRIAL TRADE BASICS",
                    "grade": "A",
                    "term": "2024-Fall"
                  }
                ],
                "relevant_skills": [
                  "Electrical Systems",
                  "Troubleshooting",
                  "Workplace Safety"
                ]
              },
              {
                "uuid": "24ba4eb8-35de-5214-9946-5a4c94f670f0",
                "display_number": 9,
                "primary_focus": "Industrial Technology (INDE)",
                "courses_completed": 3,
                "gpa": 2.87,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "INDE 37",
                    "name": "Electricity and Electronics",
                    "grade": "A",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "AGMA 42",
                    "name": "FARM POWER AND MACHINERY",
                    "grade": "F",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "HEOC 102",
                    "name": "INTRO TO CAREERS IN HEALTHCARE",
                    "grade": "A",
                    "term": "2023-Fall"
                  }
                ],
                "relevant_skills": [
                  "Electrical Systems",
                  "Troubleshooting",
                  "Workplace Safety"
                ]
              },
              {
                "uuid": "6969bbce-4665-51b2-97e8-23b72db0e984",
                "display_number": 10,
                "primary_focus": "Industrial Technology (INDE)",
                "courses_completed": 4,
                "gpa": 2.71,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "INDE 37",
                    "name": "Electricity and Electronics",
                    "grade": "C",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "INDE 44",
                    "name": "INDUSTRIAL PROCESS CONTROL",
                    "grade": "W",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "DIES 48",
                    "name": "HYDRAULICS",
                    "grade": "B",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "ADJU 102",
                    "name": "P.C. 832 FIREARMS",
                    "grade": "C",
                    "term": "2024-Winter"
                  }
                ],
                "relevant_skills": [
                  "Electrical Systems",
                  "Troubleshooting",
                  "Workplace Safety"
                ]
              }
            ]
          }
        },
        "roadmap": "A quarterly advisory board with PG&E regional operations or workforce development leadership could give the Industrial Technology department sustained access to industry perspective on utility workforce readiness. Potential starting points for the inaugural meeting include what substation and relay scenarios PG&E considers essential for entry-level technician preparation, which workplace safety certifications hiring managers prioritize when evaluating candidates, and how field deployment practices for remote infrastructure sites could inform curriculum development.",
        "selected_occupations": [
          "Electrical and Electronics Repairers, Powerhouse, Substation, and Relay",
          "Electrical Engineers",
          "Facilities Managers"
        ],
        "advisory_thesis": "PG&E operates one of the largest combined gas and electric utility networks in the United States, requiring a workforce trained in high-stakes electrical systems maintenance, substation and relay repair, and infrastructure safety across vast and varied terrain. Their emphasis on hands-on technical roles \u2014 from powerhouse repairers to facilities managers navigating live electrical environments \u2014 makes their hiring needs directly relevant to the college's CTE programs in electrical technology, utility operations, and workplace safety.",
        "agenda_topics": [
          {
            "topic": "What specific substation and relay scenarios should Industrial Technology students practice to meet PG&E's entry-level readiness expectations?",
            "rationale": "PG&E's operational experience with high-voltage substation environments can inform how Industrial Technology structures its hands-on lab sequences and scenario-based troubleshooting exercises."
          },
          {
            "topic": "Which workplace safety certifications do PG&E hiring managers most consistently look for when evaluating utility technician candidates?",
            "rationale": "PG&E's credentialing expectations for live electrical environments can help Industrial Technology determine which safety training to embed or prioritize within its existing course offerings."
          },
          {
            "topic": "How does PG&E onboard technicians to work across varied terrain and remote infrastructure sites safely?",
            "rationale": "PG&E's field deployment practices could inform Industrial Technology's curriculum around site-readiness preparation and strengthen the applied utility operations pathway."
          }
        ]
      },
      "engagementType": "advisory_board",
      "collegeId": "Shasta College",
      "savedAt": "2026-04-20T00:00:00.000Z",
      "status": "saved",
      "schemaVersion": 8
    },
    {
      "id": "seed-shasta-internship-01",
      "proposal": {
        "employer": "Mayers Memorial Hospital",
        "sector": "Professional Services",
        "partnership_type": "Internship Pipeline",
        "selected_occupation": "Registered Nurses",
        "selected_soc_code": "29-1141",
        "core_skills": [
          "Patient Assessment",
          "Nursing Process",
          "Medication Administration"
        ],
        "gap_skill": "",
        "regions": [
          "Far North"
        ],
        "opportunity": "Mayers Memorial Hospital is a compelling internship partner for Shasta College's Registered Nursing program given its location in the Far North region, where registered nurses earn $133,680 annually and 460 openings arise each year. A structured 8-16 week placement could give students direct experience with the patient care workflows central to this role. Regional access to a hospital employer of this kind is a concrete asset for students who intend to work locally.",
        "opportunity_evidence": [
          {
            "title": "Registered Nurses",
            "soc_code": "29-1141",
            "annual_wage": 133680,
            "employment": 6980,
            "annual_openings": 460,
            "growth_rate": 0.066071046
          }
        ],
        "justification": {
          "curriculum_composition": "The Registered Nursing program's 13-course curriculum builds the medication administration and nursing process competencies that would be exercised daily in a hospital internship at Mayers Memorial. The Allied Health department contributes patient assessment preparation, rounding out the skill set across the two programs. Together, these programs provide substantive preparation for the clinical responsibilities this role demands.",
          "curriculum_evidence": [
            {
              "department": "Registered Nursing",
              "courses": [
                {
                  "code": "REGN 15",
                  "name": "HEALTH AND ILLNESS I",
                  "description": "This is an introductory course which serves as the foundation for subsequent program courses for the Associate Degree Nursing Program and is one of two corequisite courses that comprise the first semester. The focus is on foundational concepts necessary for safe, client-centered nursing care to a diverse client population from adolescence through older adult while integrating professional, legal, and ethical responsibilities of the nurse. The course addresses health promotion and introduces critical thinking applied to nursing, the nursing process, communication techniques, evidence-based nursing practice, and nursing informatics. The course may be offered in a distance education format. (CSU transferable)",
                  "learning_outcomes": [],
                  "skills": [
                    "Nursing Process"
                  ]
                },
                {
                  "code": "REGN 25",
                  "name": "HEALTH AND ILLNESS II",
                  "description": "This course is one of the required courses for the Associate Degree Nursing program at Shasta College and one of two corequisite courses that comprise the second semester. The student will begin to build the foundation of Medical-Surgical Nursing. Concepts of family, community, health promotion, illness prevention, teaching, cultural sensitivity, nursing process, and critical thinking are promoted. The emphasis of the course is on adult and geriatric medical-surgical clients with acute and/or chronic illness in the inpatient and outpatient setting. This course may be offered in a distance education format. (CSU transferable)",
                  "learning_outcomes": [],
                  "skills": [
                    "Nursing Process"
                  ]
                },
                {
                  "code": "REGN 25P",
                  "name": "PROFESSIONAL NURSING PRACTICUM II",
                  "description": "This is one of the required courses for the Associate Degree Nursing program at Shasta College and one of two corequisite courses that comprise the second semester. Concepts of family, community, health promotion, illness prevention, teaching, cultural sensitivity, nursing process, and critical thinking are integrated into clinical practice. The emphasis of the course is on adult and geriatric medical-surgical clients with acute and/or chronic illness in the inpatient and outpatient setting. Knowledge and skills acquired in lecture-discussion and in simulation and skills laboratories are applied in medical-surgical settings. A portion of this course may be offered in a distance education format. (CSU transferable)",
                  "learning_outcomes": [],
                  "skills": [
                    "Nursing Process"
                  ]
                },
                {
                  "code": "REGN 35",
                  "name": "HEALTH AND ILLNESS III",
                  "description": "This course is a required course for the Associate Degree Nursing program at Shasta College. This course is one of four corequisite courses that make up the medical-surgical portion of the third semester of the Associate Degree Nursing program. Building upon the content of REGN 25 and REGN 25P, the students will expand their knowledge of medical-surgical nursing. Concepts emphasized include family, communication, health promotion, illness prevention, teaching, cultural sensitivity, nursing process, critical thinking, legal-ethical issues and advocacy. This course may be offered in a distance education format. (CSU transferable)",
                  "learning_outcomes": [],
                  "skills": [
                    "Nursing Process"
                  ]
                },
                {
                  "code": "REGN 35P",
                  "name": "PROFESSIONAL NURSING PRACTICUM III",
                  "description": "This is a required course for the Associate Degree Nursing program at Shasta College. This course is one of four corequisite courses that make up the medical-surgical portion of the third semester of the Associate Degree Nursing program. Building upon the content of REGN 25 and REGN 25P, students will expand the fundamental clinical nursing skills they mastered. Advanced psychomotor skills will be introduced. Students will have a variety of client assignments in medical-surgical care, with special assignments in diagnostic imaging areas. Students will progress from providing nursing care for a single client to providing care for several increasingly complex clients. Emphasis is placed on the integration of theory and the nursing process into the clinical setting by use of organizational tools, clinical papers, nursing care planning, chart review, and clinical conferences. A portion of this course may be offered in a distance education format. (CSU transferable)",
                  "learning_outcomes": [],
                  "skills": [
                    "Nursing Process"
                  ]
                },
                {
                  "code": "REGN 35PX",
                  "name": "PROFESSIONAL NURSING PRACTICUM III",
                  "description": "This is a required course for the Associate Degree Nursing Program at Shasta College. This course is one of two corequisite courses that make up the medical-surgical portion of the third semester of the Associate Degree Nursing program. Students will expand the fundamental clinical nursing skills they mastered. Advanced psychomotor skills will be introduced. Students will have a variety of client assignments in medical-surgical care, with special assignments in diagnostic imaging areas. Students will progress from providing nursing care for a single client to providing care for several increasingly complex clients. Emphasis is placed on the integration of theory and the nursing process into clinical application while providing students various opportunities to demonstrate critical thinking and advanced nursing skills. A portion of this course may be offered in a distance education format. (CSU transferable)",
                  "learning_outcomes": [],
                  "skills": [
                    "Nursing Process"
                  ]
                },
                {
                  "code": "REGN 35X",
                  "name": "HEALTH AND ILLNESS III",
                  "description": "This course is a required course for the Associate Degree Nursing Program at Shasta College. This course is one of four corequisite courses that make up the medical-surgical portion of the third semester of the Associate Degree Nursing program. The students will expand their knowledge of medical-surgical nursing. Concepts emphasized include family, communication, health promotion, illness prevention, teaching, cultural sensitivity, nursing process, critical thinking, legal-ethical issues and advocacy. This course may be offered in a distance education format. (CSU transferable)",
                  "learning_outcomes": [],
                  "skills": [
                    "Nursing Process"
                  ]
                },
                {
                  "code": "REGN 36",
                  "name": "MATERNAL-CHILD AND PEDIATRIC NURSING",
                  "description": "This course is one of the required courses for the Associate Degree Nursing program at Shasta College and one of four corequisite courses that comprise the third semester of the Associate Degree Nursing Program. The course provides the conceptual basis of nursing care for obstetrical, neonatal, pediatric, and adolescent clients and their families in acute and community-based settings. Concepts emphasized include family, communication, health promotion, illness prevention, teaching, cultural sensitivity, growth and development, nursing process, critical thinking, legal-ethical issues, and advocacy. This course may be offered in a distance education format. (CSU transferable)",
                  "learning_outcomes": [],
                  "skills": [
                    "Nursing Process"
                  ]
                },
                {
                  "code": "REGN 36X",
                  "name": "MATERNAL-CHILD AND PEDIATRIC NURSING",
                  "description": "This course is one of two corequisite courses that make up the Maternal- Child and Pediatric nursing portion of the third semester of the Associate Degree Nursing program. The students will expand their knowledge of medical-surgical nursing. Concepts emphasized include family, communication, health promotion, illness prevention, teaching, cultural sensitivity, nursing process, critical thinking, legal-ethical issues, and advocacy. This course is a required course for the Associate Degree Nursing Program at Shasta College. This course may be offered in a distance education format. (CSU transferable)",
                  "learning_outcomes": [],
                  "skills": [
                    "Nursing Process"
                  ]
                },
                {
                  "code": "REGN 40",
                  "name": "LVN-RN TRANSITION",
                  "description": "This is the theoretical transition course for LVNs to gain accelerated entry into the third semester of the Associate Degree Nursing program or participate in the 30-unit option program at Shasta College. In this course students will learn about and apply concepts of health assessment, medication administration, and the nursing process in the care of the medical-surgical client. This course may be offered in a distance education format. (CSU transferable)",
                  "learning_outcomes": [],
                  "skills": [
                    "Medication Administration",
                    "Nursing Process"
                  ]
                },
                {
                  "code": "REGN 40P",
                  "name": "LVN-RN TRANSITION LAB",
                  "description": "This is a prerequisite transition course for LVNs to gain accelerated entry into the Medical-Surgical and Pediatric/Maternity portions of the third semester of the Associate Degree Nursing program or participate in the 30-unit option program at Shasta College. Building upon their experience as an LVN, students will expand upon their fundamental clinical nursing skills to include aspects of pharmacology, physical assessment, and the nursing process. Students will have a variety of client assignments in medical-surgical care. Students will progress from providing nursing care for a single client to several increasingly complex clients. Emphasis is placed on the integration of theory and the nursing process into the clinical setting by care planning and clinical pre and post conferences. (CSU transferable)",
                  "learning_outcomes": [],
                  "skills": [
                    "Nursing Process"
                  ]
                },
                {
                  "code": "REGN 48",
                  "name": "HEALTH AND ILLNESS IV: COMMUNITY, MENTAL HEALTH, AND MEDICAL-SURGICAL NURSING",
                  "description": "This is a required course for the Associate Degree Nursing program at Shasta College and one of two corequisite courses that comprise the fourth semester. The course provides the conceptual basis for advanced medical-surgical, mental health, and community health nursing, and fundamental concepts of nursing leadership. The emphasis of the course is on nursing process and critical thinking related to care of the client in a variety of settings, and the current leadership issues involved in nursing practice. This course may be offered in a distance education format. (CSU transferable)",
                  "learning_outcomes": [],
                  "skills": [
                    "Nursing Process"
                  ]
                },
                {
                  "code": "REGN 48X",
                  "name": "HEALTH AND ILLNESS IV: COMMUNITY, MENTAL HEALTH, AND MEDICAL-SURGICAL NURSING",
                  "description": "This is a required course for the Associate Degree Nursing program at Shasta College and one of two corequisite courses that comprise the fourth semester. The course provides the conceptual basis for advanced medical-surgical, mental health, and community health nursing, and fundamental concepts of nursing leadership. The emphasis of the course is on nursing process and critical thinking related to care of the client in a variety of settings, and the current leadership issues involved in nursing practice. This course may be offered in a distance education format. (CSU transferable)",
                  "learning_outcomes": [],
                  "skills": [
                    "Nursing Process"
                  ]
                }
              ],
              "aligned_skills": [
                "Medication Administration",
                "Nursing Process"
              ]
            },
            {
              "department": "Vocational Nursing",
              "courses": [
                {
                  "code": "VOCN 161",
                  "name": "NURSING OF ADULTS",
                  "description": "This course is the second required course in the Vocational Nursing Program. The emphasis of this course is on the application of the nursing process in acute care settings. Theory content includes care of patients with common medical-surgical problems with adaptation to address all age groups. The student develops competence in the administration of medications and varied therapeutic skills to assigned patients with safety and increasing confidence. Assignments include practice in the Clinical Skills Laboratory and medical, surgical, and orthopedic areas in acute care settings. Students may be assigned to optional areas such as operating rooms and recovery rooms for follow-through experience with their assigned surgical patients and in an ambulatory center. A portion of this course may be offered in a distance education format.",
                  "learning_outcomes": [],
                  "skills": [
                    "Medication Administration",
                    "Nursing Process"
                  ]
                }
              ],
              "aligned_skills": [
                "Medication Administration",
                "Nursing Process"
              ]
            },
            {
              "department": "ALLIED HEALTH",
              "courses": [
                {
                  "code": "ALH 103",
                  "name": "CLINICAL MEDICAL ASSISTING I",
                  "description": "In this course students will learn the principles of infection control, medical asepsis, and regulatory guidelines in the medical lab. Also discussed are exams and procedures from the pediatric to geriatric patient, including gender specific exams. Students will learn their role in minor office surgery, diagnostic imaging, rehabilitation, and therapeutic modalities. This course may be offered in a distance education format.",
                  "learning_outcomes": [],
                  "skills": [
                    "Patient Assessment"
                  ]
                },
                {
                  "code": "ALH 103L",
                  "name": "CLINICAL MEDICAL ASSISTING I LAB",
                  "description": "This course serves as the corresponding lab for Clinical Medical Assisting I. In a lab environment, students will develop proficiency in skills related to infection control, medical asepsis, exams and procedures, and minor office surgery. This course may be offered in a distance education format.",
                  "learning_outcomes": [],
                  "skills": [
                    "Patient Assessment"
                  ]
                }
              ],
              "aligned_skills": [
                "Patient Assessment"
              ]
            }
          ],
          "student_composition": "Students in the Registered Nursing program are completing coursework directly aligned with the core competencies Mayers Memorial requires of its nursing staff. Students in the Allied Health program add patient assessment preparation to the pipeline. The combined pool spans the skills central to this internship.",
          "student_evidence": {
            "total_in_program": 205,
            "with_all_core_skills": 5,
            "top_students": [
              {
                "uuid": "9c96740a-1ba5-5713-87e4-267904965189",
                "display_number": 1,
                "primary_focus": "Registered Nursing",
                "courses_completed": 5,
                "gpa": 3.9,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "PTA 9L",
                    "name": "NEUROLOGIC MANAGEMENT LAB",
                    "grade": "B",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "REGN 40P",
                    "name": "LVN-RN TRANSITION LAB",
                    "grade": "A",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "REGN 40",
                    "name": "LVN-RN TRANSITION",
                    "grade": "A",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "REGN 35X",
                    "name": "HEALTH AND ILLNESS III",
                    "grade": "P",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "REGN 35PX",
                    "name": "PROFESSIONAL NURSING PRACTICUM III",
                    "grade": "A",
                    "term": "2023-Winter"
                  }
                ],
                "relevant_skills": [
                  "Medication Administration",
                  "Nursing Process",
                  "Patient Assessment"
                ]
              },
              {
                "uuid": "d7c77926-698c-58d0-bcf3-67e2f7df87f1",
                "display_number": 2,
                "primary_focus": "Registered Nursing",
                "courses_completed": 8,
                "gpa": 3.87,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "PTA 9L",
                    "name": "NEUROLOGIC MANAGEMENT LAB",
                    "grade": "B",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "REGN 40P",
                    "name": "LVN-RN TRANSITION LAB",
                    "grade": "A",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "REGN 40",
                    "name": "LVN-RN TRANSITION",
                    "grade": "A",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "REGN 36X",
                    "name": "MATERNAL-CHILD AND PEDIATRIC NURSING",
                    "grade": "A",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "VOCN 161",
                    "name": "NURSING OF ADULTS",
                    "grade": "A",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "REGN 25P",
                    "name": "PROFESSIONAL NURSING PRACTICUM II",
                    "grade": "A",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "REGN 15",
                    "name": "HEALTH AND ILLNESS I",
                    "grade": "P",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "HEOC 10",
                    "name": "APPLIED PHARMACOLOGY",
                    "grade": "A",
                    "term": "2024-Fall"
                  }
                ],
                "relevant_skills": [
                  "Medication Administration",
                  "Nursing Process",
                  "Patient Assessment"
                ]
              },
              {
                "uuid": "ef28eea4-1b58-5277-8071-c0517cb5c935",
                "display_number": 3,
                "primary_focus": "Registered Nursing",
                "courses_completed": 4,
                "gpa": 3.58,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "PTA 9L",
                    "name": "NEUROLOGIC MANAGEMENT LAB",
                    "grade": "A",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "REGN 35X",
                    "name": "HEALTH AND ILLNESS III",
                    "grade": "A",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "VOCN 161",
                    "name": "NURSING OF ADULTS",
                    "grade": "A",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "REGN 35",
                    "name": "HEALTH AND ILLNESS III",
                    "grade": "A",
                    "term": "2022-Winter"
                  }
                ],
                "relevant_skills": [
                  "Medication Administration",
                  "Nursing Process",
                  "Patient Assessment"
                ]
              },
              {
                "uuid": "2e197a80-75ad-5a3b-8e88-2e36ab9074bb",
                "display_number": 4,
                "primary_focus": "Registered Nursing",
                "courses_completed": 7,
                "gpa": 3.52,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "FAID 75",
                    "name": "EMERGENCY MEDICAL TECHNICIAN 1 BASIC",
                    "grade": "P",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "REGN 40P",
                    "name": "LVN-RN TRANSITION LAB",
                    "grade": "A",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "REGN 36X",
                    "name": "MATERNAL-CHILD AND PEDIATRIC NURSING",
                    "grade": "A",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "VOCN 161",
                    "name": "NURSING OF ADULTS",
                    "grade": "A",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "REGN 35P",
                    "name": "PROFESSIONAL NURSING PRACTICUM III",
                    "grade": "A",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "REGN 25",
                    "name": "HEALTH AND ILLNESS II",
                    "grade": "A",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "REGN 15",
                    "name": "HEALTH AND ILLNESS I",
                    "grade": "A",
                    "term": "2023-Spring"
                  }
                ],
                "relevant_skills": [
                  "Medication Administration",
                  "Nursing Process",
                  "Patient Assessment"
                ]
              },
              {
                "uuid": "58636a13-5df5-5e43-a429-cd4f4f2ba249",
                "display_number": 5,
                "primary_focus": "ALLIED HEALTH",
                "courses_completed": 3,
                "gpa": 3.28,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "ALH 103L",
                    "name": "CLINICAL MEDICAL ASSISTING I LAB",
                    "grade": "C",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "ALH 103",
                    "name": "CLINICAL MEDICAL ASSISTING I",
                    "grade": "A",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "REGN 40",
                    "name": "LVN-RN TRANSITION",
                    "grade": "A",
                    "term": "2024-Spring"
                  }
                ],
                "relevant_skills": [
                  "Medication Administration",
                  "Nursing Process",
                  "Patient Assessment"
                ]
              },
              {
                "uuid": "a3ba7541-2eae-5c18-ab0c-0b3ace04fd4a",
                "display_number": 6,
                "primary_focus": "Registered Nursing",
                "courses_completed": 4,
                "gpa": 4.0,
                "matching_skills": 2,
                "enrollments": [
                  {
                    "code": "REGN 40",
                    "name": "LVN-RN TRANSITION",
                    "grade": "A",
                    "term": "2022-Fall"
                  },
                  {
                    "code": "REGN 35X",
                    "name": "HEALTH AND ILLNESS III",
                    "grade": "A",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "REGN 36",
                    "name": "MATERNAL-CHILD AND PEDIATRIC NURSING",
                    "grade": "A",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "REGN 15",
                    "name": "HEALTH AND ILLNESS I",
                    "grade": "A",
                    "term": "2023-Spring"
                  }
                ],
                "relevant_skills": [
                  "Medication Administration",
                  "Nursing Process"
                ]
              },
              {
                "uuid": "10935fdc-c209-5f0f-aa75-72043035c81f",
                "display_number": 7,
                "primary_focus": "Registered Nursing",
                "courses_completed": 1,
                "gpa": 4.0,
                "matching_skills": 2,
                "enrollments": [
                  {
                    "code": "VOCN 161",
                    "name": "NURSING OF ADULTS",
                    "grade": "A",
                    "term": "2023-Fall"
                  }
                ],
                "relevant_skills": [
                  "Medication Administration",
                  "Nursing Process"
                ]
              },
              {
                "uuid": "79f935b0-b580-5ff0-9670-abc24714b9f2",
                "display_number": 8,
                "primary_focus": "Registered Nursing",
                "courses_completed": 2,
                "gpa": 4.0,
                "matching_skills": 2,
                "enrollments": [
                  {
                    "code": "REGN 40",
                    "name": "LVN-RN TRANSITION",
                    "grade": "A",
                    "term": "2022-Fall"
                  },
                  {
                    "code": "REGN 35P",
                    "name": "PROFESSIONAL NURSING PRACTICUM III",
                    "grade": "A",
                    "term": "2022-Fall"
                  }
                ],
                "relevant_skills": [
                  "Medication Administration",
                  "Nursing Process"
                ]
              },
              {
                "uuid": "0a713c8d-2e13-5398-b056-2cfe163eea3e",
                "display_number": 9,
                "primary_focus": "Registered Nursing",
                "courses_completed": 2,
                "gpa": 4.0,
                "matching_skills": 2,
                "enrollments": [
                  {
                    "code": "REGN 15",
                    "name": "HEALTH AND ILLNESS I",
                    "grade": "A",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "HEOC 10",
                    "name": "APPLIED PHARMACOLOGY",
                    "grade": "A",
                    "term": "2023-Winter"
                  }
                ],
                "relevant_skills": [
                  "Medication Administration",
                  "Nursing Process"
                ]
              },
              {
                "uuid": "01562a20-6c93-53c6-9e04-7cc5389f0d2a",
                "display_number": 10,
                "primary_focus": "Registered Nursing",
                "courses_completed": 5,
                "gpa": 3.94,
                "matching_skills": 2,
                "enrollments": [
                  {
                    "code": "REGN 40P",
                    "name": "LVN-RN TRANSITION LAB",
                    "grade": "A",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "REGN 35",
                    "name": "HEALTH AND ILLNESS III",
                    "grade": "A",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "REGN 25P",
                    "name": "PROFESSIONAL NURSING PRACTICUM II",
                    "grade": "A",
                    "term": "2022-Fall"
                  },
                  {
                    "code": "REGN 25",
                    "name": "HEALTH AND ILLNESS II",
                    "grade": "A",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "HEOC 10",
                    "name": "APPLIED PHARMACOLOGY",
                    "grade": "A",
                    "term": "2024-Winter"
                  }
                ],
                "relevant_skills": [
                  "Medication Administration",
                  "Nursing Process"
                ]
              }
            ]
          }
        },
        "roadmap": "A potential starting point would be a conversation between the Registered Nursing department chair and Mayers Memorial's nursing leadership to establish site capacity and supervision structures. An internship of 10-16 weeks could map to existing practicum or work experience course sequences within the Registered Nursing program. A first cohort placed within the next two semesters is a reasonable target given the curriculum alignment already in place.",
        "selected_occupations": [],
        "advisory_thesis": "",
        "agenda_topics": []
      },
      "engagementType": "internship",
      "collegeId": "Shasta College",
      "savedAt": "2026-04-20T00:00:00.000Z",
      "status": "saved",
      "schemaVersion": 8
    },
    {
      "id": "seed-shasta-curriculum-01",
      "proposal": {
        "employer": "Mercy Medical Center Redding",
        "sector": "Healthcare",
        "partnership_type": "Curriculum Co-Design",
        "selected_occupation": "Registered Nurses",
        "selected_soc_code": "29-1141",
        "core_skills": [
          "Nursing Process",
          "Patient Assessment",
          "Medication Administration"
        ],
        "gap_skill": "Electronic Health Records (EHR) Navigation",
        "regions": [
          "Far North"
        ],
        "opportunity": "Shasta College's Registered Nursing program is well-positioned to deepen its alignment with Mercy Medical Center Redding through a co-design partnership focused on EHR navigation. The program builds the clinical competencies central to registered nursing practice. Collaboration with Mercy's clinical education team could strengthen preparation in the EHR workflows that CommonSpirit Health's enterprise platforms require from day one.",
        "opportunity_evidence": [
          {
            "title": "Registered Nurses",
            "soc_code": "29-1141",
            "annual_wage": 133680,
            "employment": 6980,
            "annual_openings": 460,
            "growth_rate": 0.066071046
          }
        ],
        "justification": {
          "curriculum_composition": "The Registered Nursing department is the right home for this partnership, with nursing process and medication administration developed across 13 courses. That clinical depth gives the department a strong foundation from which to build. EHR navigation, a practical requirement within Dignity Health's CommonSpirit infrastructure, can be more rigorously developed through direct collaboration with Mercy's clinical staff.",
          "curriculum_evidence": [
            {
              "department": "Registered Nursing",
              "courses": [
                {
                  "code": "REGN 15",
                  "name": "HEALTH AND ILLNESS I",
                  "description": "This is an introductory course which serves as the foundation for subsequent program courses for the Associate Degree Nursing Program and is one of two corequisite courses that comprise the first semester. The focus is on foundational concepts necessary for safe, client-centered nursing care to a diverse client population from adolescence through older adult while integrating professional, legal, and ethical responsibilities of the nurse. The course addresses health promotion and introduces critical thinking applied to nursing, the nursing process, communication techniques, evidence-based nursing practice, and nursing informatics. The course may be offered in a distance education format. (CSU transferable)",
                  "learning_outcomes": [],
                  "skills": [
                    "Nursing Process"
                  ]
                },
                {
                  "code": "REGN 25",
                  "name": "HEALTH AND ILLNESS II",
                  "description": "This course is one of the required courses for the Associate Degree Nursing program at Shasta College and one of two corequisite courses that comprise the second semester. The student will begin to build the foundation of Medical-Surgical Nursing. Concepts of family, community, health promotion, illness prevention, teaching, cultural sensitivity, nursing process, and critical thinking are promoted. The emphasis of the course is on adult and geriatric medical-surgical clients with acute and/or chronic illness in the inpatient and outpatient setting. This course may be offered in a distance education format. (CSU transferable)",
                  "learning_outcomes": [],
                  "skills": [
                    "Nursing Process"
                  ]
                },
                {
                  "code": "REGN 25P",
                  "name": "PROFESSIONAL NURSING PRACTICUM II",
                  "description": "This is one of the required courses for the Associate Degree Nursing program at Shasta College and one of two corequisite courses that comprise the second semester. Concepts of family, community, health promotion, illness prevention, teaching, cultural sensitivity, nursing process, and critical thinking are integrated into clinical practice. The emphasis of the course is on adult and geriatric medical-surgical clients with acute and/or chronic illness in the inpatient and outpatient setting. Knowledge and skills acquired in lecture-discussion and in simulation and skills laboratories are applied in medical-surgical settings. A portion of this course may be offered in a distance education format. (CSU transferable)",
                  "learning_outcomes": [],
                  "skills": [
                    "Nursing Process"
                  ]
                },
                {
                  "code": "REGN 35",
                  "name": "HEALTH AND ILLNESS III",
                  "description": "This course is a required course for the Associate Degree Nursing program at Shasta College. This course is one of four corequisite courses that make up the medical-surgical portion of the third semester of the Associate Degree Nursing program. Building upon the content of REGN 25 and REGN 25P, the students will expand their knowledge of medical-surgical nursing. Concepts emphasized include family, communication, health promotion, illness prevention, teaching, cultural sensitivity, nursing process, critical thinking, legal-ethical issues and advocacy. This course may be offered in a distance education format. (CSU transferable)",
                  "learning_outcomes": [],
                  "skills": [
                    "Nursing Process"
                  ]
                },
                {
                  "code": "REGN 35P",
                  "name": "PROFESSIONAL NURSING PRACTICUM III",
                  "description": "This is a required course for the Associate Degree Nursing program at Shasta College. This course is one of four corequisite courses that make up the medical-surgical portion of the third semester of the Associate Degree Nursing program. Building upon the content of REGN 25 and REGN 25P, students will expand the fundamental clinical nursing skills they mastered. Advanced psychomotor skills will be introduced. Students will have a variety of client assignments in medical-surgical care, with special assignments in diagnostic imaging areas. Students will progress from providing nursing care for a single client to providing care for several increasingly complex clients. Emphasis is placed on the integration of theory and the nursing process into the clinical setting by use of organizational tools, clinical papers, nursing care planning, chart review, and clinical conferences. A portion of this course may be offered in a distance education format. (CSU transferable)",
                  "learning_outcomes": [],
                  "skills": [
                    "Nursing Process"
                  ]
                },
                {
                  "code": "REGN 35PX",
                  "name": "PROFESSIONAL NURSING PRACTICUM III",
                  "description": "This is a required course for the Associate Degree Nursing Program at Shasta College. This course is one of two corequisite courses that make up the medical-surgical portion of the third semester of the Associate Degree Nursing program. Students will expand the fundamental clinical nursing skills they mastered. Advanced psychomotor skills will be introduced. Students will have a variety of client assignments in medical-surgical care, with special assignments in diagnostic imaging areas. Students will progress from providing nursing care for a single client to providing care for several increasingly complex clients. Emphasis is placed on the integration of theory and the nursing process into clinical application while providing students various opportunities to demonstrate critical thinking and advanced nursing skills. A portion of this course may be offered in a distance education format. (CSU transferable)",
                  "learning_outcomes": [],
                  "skills": [
                    "Nursing Process"
                  ]
                },
                {
                  "code": "REGN 35X",
                  "name": "HEALTH AND ILLNESS III",
                  "description": "This course is a required course for the Associate Degree Nursing Program at Shasta College. This course is one of four corequisite courses that make up the medical-surgical portion of the third semester of the Associate Degree Nursing program. The students will expand their knowledge of medical-surgical nursing. Concepts emphasized include family, communication, health promotion, illness prevention, teaching, cultural sensitivity, nursing process, critical thinking, legal-ethical issues and advocacy. This course may be offered in a distance education format. (CSU transferable)",
                  "learning_outcomes": [],
                  "skills": [
                    "Nursing Process"
                  ]
                },
                {
                  "code": "REGN 36",
                  "name": "MATERNAL-CHILD AND PEDIATRIC NURSING",
                  "description": "This course is one of the required courses for the Associate Degree Nursing program at Shasta College and one of four corequisite courses that comprise the third semester of the Associate Degree Nursing Program. The course provides the conceptual basis of nursing care for obstetrical, neonatal, pediatric, and adolescent clients and their families in acute and community-based settings. Concepts emphasized include family, communication, health promotion, illness prevention, teaching, cultural sensitivity, growth and development, nursing process, critical thinking, legal-ethical issues, and advocacy. This course may be offered in a distance education format. (CSU transferable)",
                  "learning_outcomes": [],
                  "skills": [
                    "Nursing Process"
                  ]
                },
                {
                  "code": "REGN 36X",
                  "name": "MATERNAL-CHILD AND PEDIATRIC NURSING",
                  "description": "This course is one of two corequisite courses that make up the Maternal- Child and Pediatric nursing portion of the third semester of the Associate Degree Nursing program. The students will expand their knowledge of medical-surgical nursing. Concepts emphasized include family, communication, health promotion, illness prevention, teaching, cultural sensitivity, nursing process, critical thinking, legal-ethical issues, and advocacy. This course is a required course for the Associate Degree Nursing Program at Shasta College. This course may be offered in a distance education format. (CSU transferable)",
                  "learning_outcomes": [],
                  "skills": [
                    "Nursing Process"
                  ]
                },
                {
                  "code": "REGN 40",
                  "name": "LVN-RN TRANSITION",
                  "description": "This is the theoretical transition course for LVNs to gain accelerated entry into the third semester of the Associate Degree Nursing program or participate in the 30-unit option program at Shasta College. In this course students will learn about and apply concepts of health assessment, medication administration, and the nursing process in the care of the medical-surgical client. This course may be offered in a distance education format. (CSU transferable)",
                  "learning_outcomes": [],
                  "skills": [
                    "Medication Administration",
                    "Nursing Process"
                  ]
                },
                {
                  "code": "REGN 40P",
                  "name": "LVN-RN TRANSITION LAB",
                  "description": "This is a prerequisite transition course for LVNs to gain accelerated entry into the Medical-Surgical and Pediatric/Maternity portions of the third semester of the Associate Degree Nursing program or participate in the 30-unit option program at Shasta College. Building upon their experience as an LVN, students will expand upon their fundamental clinical nursing skills to include aspects of pharmacology, physical assessment, and the nursing process. Students will have a variety of client assignments in medical-surgical care. Students will progress from providing nursing care for a single client to several increasingly complex clients. Emphasis is placed on the integration of theory and the nursing process into the clinical setting by care planning and clinical pre and post conferences. (CSU transferable)",
                  "learning_outcomes": [],
                  "skills": [
                    "Nursing Process"
                  ]
                },
                {
                  "code": "REGN 48",
                  "name": "HEALTH AND ILLNESS IV: COMMUNITY, MENTAL HEALTH, AND MEDICAL-SURGICAL NURSING",
                  "description": "This is a required course for the Associate Degree Nursing program at Shasta College and one of two corequisite courses that comprise the fourth semester. The course provides the conceptual basis for advanced medical-surgical, mental health, and community health nursing, and fundamental concepts of nursing leadership. The emphasis of the course is on nursing process and critical thinking related to care of the client in a variety of settings, and the current leadership issues involved in nursing practice. This course may be offered in a distance education format. (CSU transferable)",
                  "learning_outcomes": [],
                  "skills": [
                    "Nursing Process"
                  ]
                },
                {
                  "code": "REGN 48X",
                  "name": "HEALTH AND ILLNESS IV: COMMUNITY, MENTAL HEALTH, AND MEDICAL-SURGICAL NURSING",
                  "description": "This is a required course for the Associate Degree Nursing program at Shasta College and one of two corequisite courses that comprise the fourth semester. The course provides the conceptual basis for advanced medical-surgical, mental health, and community health nursing, and fundamental concepts of nursing leadership. The emphasis of the course is on nursing process and critical thinking related to care of the client in a variety of settings, and the current leadership issues involved in nursing practice. This course may be offered in a distance education format. (CSU transferable)",
                  "learning_outcomes": [],
                  "skills": [
                    "Nursing Process"
                  ]
                }
              ],
              "aligned_skills": [
                "Medication Administration",
                "Nursing Process"
              ]
            }
          ],
          "student_composition": "Students in the Registered Nursing program are completing coursework in the clinical skills this role requires. They are the natural cohort for a co-design effort that deepens their readiness for Mercy's documentation and care coordination environment.",
          "student_evidence": {
            "total_in_program": 159,
            "with_all_core_skills": 4,
            "top_students": [
              {
                "uuid": "9c96740a-1ba5-5713-87e4-267904965189",
                "display_number": 1,
                "primary_focus": "Registered Nursing",
                "courses_completed": 5,
                "gpa": 3.9,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "REGN 40P",
                    "name": "LVN-RN TRANSITION LAB",
                    "grade": "A",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "REGN 40",
                    "name": "LVN-RN TRANSITION",
                    "grade": "A",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "REGN 35X",
                    "name": "HEALTH AND ILLNESS III",
                    "grade": "P",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "REGN 35PX",
                    "name": "PROFESSIONAL NURSING PRACTICUM III",
                    "grade": "A",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "PTA 9L",
                    "name": "NEUROLOGIC MANAGEMENT LAB",
                    "grade": "B",
                    "term": "2024-Winter"
                  }
                ],
                "relevant_skills": [
                  "Medication Administration",
                  "Nursing Process",
                  "Patient Assessment"
                ]
              },
              {
                "uuid": "d7c77926-698c-58d0-bcf3-67e2f7df87f1",
                "display_number": 2,
                "primary_focus": "Registered Nursing",
                "courses_completed": 8,
                "gpa": 3.87,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "REGN 40P",
                    "name": "LVN-RN TRANSITION LAB",
                    "grade": "A",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "REGN 40",
                    "name": "LVN-RN TRANSITION",
                    "grade": "A",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "REGN 36X",
                    "name": "MATERNAL-CHILD AND PEDIATRIC NURSING",
                    "grade": "A",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "VOCN 161",
                    "name": "NURSING OF ADULTS",
                    "grade": "A",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "REGN 25P",
                    "name": "PROFESSIONAL NURSING PRACTICUM II",
                    "grade": "A",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "REGN 15",
                    "name": "HEALTH AND ILLNESS I",
                    "grade": "P",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "PTA 9L",
                    "name": "NEUROLOGIC MANAGEMENT LAB",
                    "grade": "B",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "HEOC 10",
                    "name": "APPLIED PHARMACOLOGY",
                    "grade": "A",
                    "term": "2024-Fall"
                  }
                ],
                "relevant_skills": [
                  "Medication Administration",
                  "Nursing Process",
                  "Patient Assessment"
                ]
              },
              {
                "uuid": "ef28eea4-1b58-5277-8071-c0517cb5c935",
                "display_number": 3,
                "primary_focus": "Registered Nursing",
                "courses_completed": 4,
                "gpa": 3.58,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "REGN 35X",
                    "name": "HEALTH AND ILLNESS III",
                    "grade": "A",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "VOCN 161",
                    "name": "NURSING OF ADULTS",
                    "grade": "A",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "REGN 35",
                    "name": "HEALTH AND ILLNESS III",
                    "grade": "A",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "PTA 9L",
                    "name": "NEUROLOGIC MANAGEMENT LAB",
                    "grade": "A",
                    "term": "2022-Winter"
                  }
                ],
                "relevant_skills": [
                  "Medication Administration",
                  "Nursing Process",
                  "Patient Assessment"
                ]
              },
              {
                "uuid": "2e197a80-75ad-5a3b-8e88-2e36ab9074bb",
                "display_number": 4,
                "primary_focus": "Registered Nursing",
                "courses_completed": 7,
                "gpa": 3.52,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "REGN 40P",
                    "name": "LVN-RN TRANSITION LAB",
                    "grade": "A",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "REGN 36X",
                    "name": "MATERNAL-CHILD AND PEDIATRIC NURSING",
                    "grade": "A",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "VOCN 161",
                    "name": "NURSING OF ADULTS",
                    "grade": "A",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "REGN 35P",
                    "name": "PROFESSIONAL NURSING PRACTICUM III",
                    "grade": "A",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "REGN 25",
                    "name": "HEALTH AND ILLNESS II",
                    "grade": "A",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "REGN 15",
                    "name": "HEALTH AND ILLNESS I",
                    "grade": "A",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "FAID 75",
                    "name": "EMERGENCY MEDICAL TECHNICIAN 1 BASIC",
                    "grade": "P",
                    "term": "2024-Spring"
                  }
                ],
                "relevant_skills": [
                  "Medication Administration",
                  "Nursing Process",
                  "Patient Assessment"
                ]
              },
              {
                "uuid": "10935fdc-c209-5f0f-aa75-72043035c81f",
                "display_number": 5,
                "primary_focus": "Registered Nursing",
                "courses_completed": 1,
                "gpa": 4.0,
                "matching_skills": 2,
                "enrollments": [
                  {
                    "code": "VOCN 161",
                    "name": "NURSING OF ADULTS",
                    "grade": "A",
                    "term": "2023-Fall"
                  }
                ],
                "relevant_skills": [
                  "Medication Administration",
                  "Nursing Process"
                ]
              },
              {
                "uuid": "a3ba7541-2eae-5c18-ab0c-0b3ace04fd4a",
                "display_number": 6,
                "primary_focus": "Registered Nursing",
                "courses_completed": 4,
                "gpa": 4.0,
                "matching_skills": 2,
                "enrollments": [
                  {
                    "code": "REGN 40",
                    "name": "LVN-RN TRANSITION",
                    "grade": "A",
                    "term": "2022-Fall"
                  },
                  {
                    "code": "REGN 35X",
                    "name": "HEALTH AND ILLNESS III",
                    "grade": "A",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "REGN 36",
                    "name": "MATERNAL-CHILD AND PEDIATRIC NURSING",
                    "grade": "A",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "REGN 15",
                    "name": "HEALTH AND ILLNESS I",
                    "grade": "A",
                    "term": "2023-Spring"
                  }
                ],
                "relevant_skills": [
                  "Medication Administration",
                  "Nursing Process"
                ]
              },
              {
                "uuid": "79f935b0-b580-5ff0-9670-abc24714b9f2",
                "display_number": 7,
                "primary_focus": "Registered Nursing",
                "courses_completed": 2,
                "gpa": 4.0,
                "matching_skills": 2,
                "enrollments": [
                  {
                    "code": "REGN 40",
                    "name": "LVN-RN TRANSITION",
                    "grade": "A",
                    "term": "2022-Fall"
                  },
                  {
                    "code": "REGN 35P",
                    "name": "PROFESSIONAL NURSING PRACTICUM III",
                    "grade": "A",
                    "term": "2022-Fall"
                  }
                ],
                "relevant_skills": [
                  "Medication Administration",
                  "Nursing Process"
                ]
              },
              {
                "uuid": "0a713c8d-2e13-5398-b056-2cfe163eea3e",
                "display_number": 8,
                "primary_focus": "Registered Nursing",
                "courses_completed": 2,
                "gpa": 4.0,
                "matching_skills": 2,
                "enrollments": [
                  {
                    "code": "REGN 15",
                    "name": "HEALTH AND ILLNESS I",
                    "grade": "A",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "HEOC 10",
                    "name": "APPLIED PHARMACOLOGY",
                    "grade": "A",
                    "term": "2023-Winter"
                  }
                ],
                "relevant_skills": [
                  "Medication Administration",
                  "Nursing Process"
                ]
              },
              {
                "uuid": "01562a20-6c93-53c6-9e04-7cc5389f0d2a",
                "display_number": 9,
                "primary_focus": "Registered Nursing",
                "courses_completed": 5,
                "gpa": 3.94,
                "matching_skills": 2,
                "enrollments": [
                  {
                    "code": "REGN 40P",
                    "name": "LVN-RN TRANSITION LAB",
                    "grade": "A",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "REGN 35",
                    "name": "HEALTH AND ILLNESS III",
                    "grade": "A",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "REGN 25P",
                    "name": "PROFESSIONAL NURSING PRACTICUM II",
                    "grade": "A",
                    "term": "2022-Fall"
                  },
                  {
                    "code": "REGN 25",
                    "name": "HEALTH AND ILLNESS II",
                    "grade": "A",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "HEOC 10",
                    "name": "APPLIED PHARMACOLOGY",
                    "grade": "A",
                    "term": "2024-Winter"
                  }
                ],
                "relevant_skills": [
                  "Medication Administration",
                  "Nursing Process"
                ]
              },
              {
                "uuid": "bbd3aab8-0374-52f2-a90e-7f33598fc520",
                "display_number": 10,
                "primary_focus": "Registered Nursing",
                "courses_completed": 6,
                "gpa": 3.9,
                "matching_skills": 2,
                "enrollments": [
                  {
                    "code": "REGN 40P",
                    "name": "LVN-RN TRANSITION LAB",
                    "grade": "A",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "REGN 40",
                    "name": "LVN-RN TRANSITION",
                    "grade": "A",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "REGN 35X",
                    "name": "HEALTH AND ILLNESS III",
                    "grade": "A",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "REGN 35PX",
                    "name": "PROFESSIONAL NURSING PRACTICUM III",
                    "grade": "A",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "REGN 15",
                    "name": "HEALTH AND ILLNESS I",
                    "grade": "A",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "HEOC 10",
                    "name": "APPLIED PHARMACOLOGY",
                    "grade": "A",
                    "term": "2025-Spring"
                  }
                ],
                "relevant_skills": [
                  "Medication Administration",
                  "Nursing Process"
                ]
              }
            ]
          }
        },
        "roadmap": "A working group between the Registered Nursing department chair and Mercy Medical Center Redding's clinical education leadership could evaluate how EHR navigation is currently addressed in clinical coursework and where it can be strengthened. Revised content targeting CommonSpirit's platform workflows could be piloted within the next catalog cycle.",
        "selected_occupations": [],
        "advisory_thesis": "",
        "agenda_topics": []
      },
      "engagementType": "curriculum_codesign",
      "collegeId": "Shasta College",
      "savedAt": "2026-04-20T00:00:00.000Z",
      "status": "saved",
      "schemaVersion": 8
    }
  ],
  "College of the Sequoias": [
    {
      "id": "seed-sequoias-advisory-01",
      "proposal": {
        "employer": "National Guard",
        "sector": "Government",
        "partnership_type": "Advisory Board",
        "selected_occupation": "Military-only occupations",
        "selected_soc_code": "55-0000",
        "core_skills": [
          "Leadership",
          "Physical Fitness",
          "Clinical Documentation",
          "Patient Assessment",
          "Emergency Response",
          "Public Safety & Security"
        ],
        "gap_skill": "",
        "regions": [
          "Central Valley / Mother Lode"
        ],
        "opportunity": "The National Guard's dual-mission structure across emergency response and military health makes it a compelling advisory board partner for College of the Sequoias' public safety and health sciences programs. Guard personnel deploy clinical, firefighting, and command skills under austere, resource-constrained conditions that civilian training rarely replicates at scale. An advisory relationship formalizes that operational perspective as ongoing guidance with no grant funding required.",
        "opportunity_evidence": [
          {
            "title": "Firefighters",
            "soc_code": "33-2011",
            "annual_wage": 72400,
            "employment": 3540,
            "annual_openings": 340,
            "growth_rate": 0.091324694
          },
          {
            "title": "Military-only occupations",
            "soc_code": "55-9999",
            "annual_wage": 40510,
            "employment": 8580,
            "annual_openings": 1020,
            "growth_rate": 0.044553529
          },
          {
            "title": "Registered Nurses",
            "soc_code": "29-1141",
            "annual_wage": 129360,
            "employment": 32090,
            "annual_openings": 2160,
            "growth_rate": 0.071729571
          }
        ],
        "justification": {
          "curriculum_composition": "The Fire Technology, Emergency Medical Technician, and Nursing departments provide the closest curricular match to the National Guard's workforce operations. Fire Technology builds emergency response and public safety competencies across 13 courses, Nursing develops clinical documentation and patient assessment across 25, and the EMT program trains students in the documentation and emergency response skills Guard medics apply in the field. Together these programs span the applied professional competencies that define the Guard's non-combat roles.",
          "curriculum_evidence": [
            {
              "department": "Fire Technology",
              "courses": [
                {
                  "code": "FIRE 125",
                  "name": "Fundamentals of Fire Apparatus and Equipment",
                  "description": "This class is designed to provide students with information regarding design features, construction materials, performance factors, and maintenance requirements for motorized fire apparatus. Topics include laws, standards and regulations, design, construction, and maintenance requirements for fire apparatus. Operational considerations including tactics and strategy, safety and driving characteristics of pumping apparatus, aerial ladders, aerial platforms and specialized equipment are also presented.",
                  "learning_outcomes": [],
                  "skills": [
                    "Public Safety & Security"
                  ]
                },
                {
                  "code": "FIRE 155",
                  "name": "Fire Behavior and Combustion",
                  "description": "Theory and fundamentals of how and why fires start, spread, and are controlled; an in-depth study of fire chemistry and physics, fire characteristics of materials, extinguishing agents, and fire control techniques. This is one of the first courses a student should take in the sequence of fire technology classes. It covers the basic physical laws of fire combustion and extinguishing processes. It is part of the series of courses recommended by the Chancellor's Office for students in California Community Colleges.",
                  "learning_outcomes": [],
                  "skills": [
                    "Emergency Response"
                  ]
                },
                {
                  "code": "FIRE 157",
                  "name": "Fire Prevention Technology",
                  "description": "Provides information regarding the philosophy of fire prevention, organization and operation of a fire prevention bureau, application of fire codes, identification and correction of fire hazards, and the relationship of fire prevention with fire safety education and detection and suppression systems.",
                  "learning_outcomes": [],
                  "skills": [
                    "Emergency Response",
                    "Public Safety & Security"
                  ]
                },
                {
                  "code": "FIRE 159",
                  "name": "Introduction to Fire Protection Organizations",
                  "description": "This course provides an overview to fire protection, career opportunities in fire protection and related fields, philosophy and history of fire protection/ service, fire loss analysis, organization and function of public and private fire protection services, fire departments as part of local government, laws and regulations affecting the fire service, fire service nomenclature, specific fire protection functions, basic fire chemistry and physics, introduction to fire protection systems, introduction to fire strategy and tactics.",
                  "learning_outcomes": [],
                  "skills": [
                    "Emergency Response",
                    "Public Safety & Security"
                  ]
                },
                {
                  "code": "FIRE 160",
                  "name": "Fire and Emergency Safety",
                  "description": "This course introduces the basic principles and history related to the national firefighter life safety initiatives, focusing on the need for cultural and behavior change throughout the emergency services.",
                  "learning_outcomes": [],
                  "skills": [
                    "Emergency Response",
                    "Leadership",
                    "Public Safety & Security"
                  ]
                },
                {
                  "code": "FIRE 230",
                  "name": "SFM Company Officer 2A",
                  "description": "This course provides information on the use of human resources to accomplish assignments, evaluating member performance, supervising personnel, and integrating health and safety plans, policies, and procedures into daily activities as well as the emergency scene. The course is one of the required courses for California State Fire Marshal Company Officer certification. This course will be delivered in a one-week, 40 hour format, which includes lecture, activities, and a final exam.",
                  "learning_outcomes": [],
                  "skills": [
                    "Emergency Response",
                    "Leadership"
                  ]
                },
                {
                  "code": "FIRE 231",
                  "name": "SFM Company Officer 2B",
                  "description": "This course provides information on general administrative functions and the implementation of department policies and procedures and addresses conveying the fire department's role, image, and mission to the public.",
                  "learning_outcomes": [],
                  "skills": [
                    "Leadership"
                  ]
                },
                {
                  "code": "FIRE 232",
                  "name": "SFM Company Officer 2C",
                  "description": "Fire Inspections and Investigation for Company Officers. This is the third course in the new California State Fire Training Company Officer Certification.",
                  "learning_outcomes": [],
                  "skills": [
                    "Leadership",
                    "Public Safety & Security"
                  ]
                },
                {
                  "code": "FIRE 233",
                  "name": "SFM Company Officer 2D",
                  "description": "All-Risk Command Operations for Company Officers. This course is one of the six required by the Office of the State Fire Marshal for certification as a fire department Company Officer. This course will be taught in a forty-hour, five-day format, which includes lecture and computerized fire simulation activities.",
                  "learning_outcomes": [],
                  "skills": [
                    "Emergency Response",
                    "Leadership",
                    "Public Safety & Security"
                  ]
                },
                {
                  "code": "FIRE 234",
                  "name": "SFM Company Officer 2E",
                  "description": "Wildland Incident Operations for Company Officers. This is one of the courses required by the Office of the State Fire Marshal for certification as a fire department Company Officer. This course will be delivered in a one-week, 40 hour format, which includes lecture, activities, and a final exam.",
                  "learning_outcomes": [],
                  "skills": [
                    "Emergency Response",
                    "Leadership",
                    "Public Safety & Security"
                  ]
                },
                {
                  "code": "FIRE 235",
                  "name": "Fire Instructor I: Instructional Methodology",
                  "description": "This course covers fundamental principles and techniques of instruction with an emphasis on applied instruction in the fire service. Topics include course outline and lesson plan development, instructional aids, classroom environment management, legal and ethical issues, and instructor accountability and liability. This California State Fire Training course is intended for active duty firefighters seeking advancement to the company officer level.",
                  "learning_outcomes": [],
                  "skills": [
                    "Leadership"
                  ]
                },
                {
                  "code": "FIRE 280",
                  "name": "Fire Fighter 2 Academy",
                  "description": "Fire Fighter 2 Academy is the second of two courses in the State Fire Marshal's Fire Fighter series. This course expands on areas which were introduced in the Fire Fighter 1 curriculum. The course concentrates on the subjects of Fire Department Communications, Fireground Operations, Rescue Operations, and Fire Prevention, Preparation, and Maintenance. Students must have access to NFPA approved protective clothing for structural fire fighters.",
                  "learning_outcomes": [],
                  "skills": [
                    "Emergency Response",
                    "Public Safety & Security"
                  ]
                },
                {
                  "code": "FIRE 285",
                  "name": "Combined Firefighter 1 and 2 Academy",
                  "description": "This class includes manipulative and technical training in basic concepts in fire service organization and theories of fire control including: fire department organization, identification, use and maintenance of fire equipment, hazardous materials, structural, flammable liquid and LPG, and wildland fire control, auto extrication, fire prevention, and firefighter safety. This course meets current National Fire Protection Association and California State Fire Training for educational and testing requirements for Firefighter 1 and Firefighter 2 certification.",
                  "learning_outcomes": [],
                  "skills": [
                    "Emergency Response",
                    "Public Safety & Security"
                  ]
                }
              ],
              "aligned_skills": [
                "Emergency Response",
                "Leadership",
                "Public Safety & Security"
              ]
            },
            {
              "department": "Emergency Medical Technician",
              "courses": [
                {
                  "code": "EMT 251",
                  "name": "Emergency Medical Technician B",
                  "description": "The student who completes this course will develop skills in recognition of symptoms of illness and/or injury and proper procedures for emergency care. Those who complete the EMT B courses are eligible to sit for the National Registry of Emergency Medical Technicians and employment by government and private emergency health care services in the area (state certification and national testing fees apply). Successful completion of the course also allows eligibility for Emergency Medical Technician Paramedic training, which provides opportunity for career advancement, higher pay, and greater responsibility in providing emergency health care. Some EMTs enter nursing and other advanced health care fields. (California Code of Regulations Title 22).",
                  "learning_outcomes": [],
                  "skills": [
                    "Clinical Documentation",
                    "Emergency Response"
                  ]
                },
                {
                  "code": "EMT 401",
                  "name": "EMT Open Skills Lab",
                  "description": "This course provides the student an opportunity for additional directed learning and supervised laboratory time to practice, develop and refine skills necessary to the safe practice of the Emergency Medical Technician.",
                  "learning_outcomes": [],
                  "skills": [
                    "Emergency Response"
                  ]
                }
              ],
              "aligned_skills": [
                "Clinical Documentation",
                "Emergency Response"
              ]
            },
            {
              "department": "Nursing",
              "courses": [
                {
                  "code": "NURS 121",
                  "name": "Fundamentals for Nursing",
                  "description": "This course focuses on fundamental concepts necessary for safe, compassionate, patient-centered nursing care for a diverse patient population with well-defined healthcare concerns with a focus on elderly patients. The course offers an introduction to foundational concepts related to professional practices such as legal and ethical responsibilities of the Registered Nurse. The student also uses clinical judgment applied to nursing practice. Select nursing skills are taught in the skills laboratory; theory and skills re applied in various clinical settings.",
                  "learning_outcomes": [],
                  "skills": [
                    "Clinical Documentation"
                  ]
                },
                {
                  "code": "NURS 121A",
                  "name": "Fundamentals for Nursing - Apprenticeship",
                  "description": "This course focuses on fundamental concepts necessary for safe, compassionate, patient-centered nursing care for a diverse patient population with well-defined healthcare concerns with a focus on elderly patients. The course offers an introduction to foundational concepts related to professional practices such as legal and ethical responsibilities of the Registered Nurse. The student also uses clinical judgment applied to nursing practice. Select nursing skills are taught in the skills laboratory; theory and skills are applied in various clinical settings. This course is designated for students enrolled in the apprenticeship program.",
                  "learning_outcomes": [],
                  "skills": [
                    "Clinical Documentation"
                  ]
                },
                {
                  "code": "NURS 123",
                  "name": "Critical Thinking/Clinical Judgement in Nursing",
                  "description": "This course introduces clinical judgment through a focused study of critical thinking skills and strategies used by the Registered Nurse. The student applies critical thinking skills and strategies at the RN level that underscore the clinical judgment represented in the nursing process as well as dealing with aspects of the healthcare system for safe practice in the current healthcare environment. The major purpose of the course is to teach students the clinical judgment needed to predict and manage potential complications and to decrease the failure to rescue rate which results in improved patient outcomes. This course provides the foundation for the thinking processes applied throughout all nursing courses.",
                  "learning_outcomes": [],
                  "skills": [
                    "Clinical Documentation"
                  ]
                },
                {
                  "code": "NURS 123A",
                  "name": "Critical Thinking/Clinical Judgement in Nursing - Apprenticeship",
                  "description": "This course introduces clinical judgment through a focused study of critical thinking skills and strategies used by the Registered Nurse. The student applies critical thinking skills and strategies at the RN level that underscore the clinical judgment represented in the nursing process as well as dealing with aspects of the healthcare system for safe practice in the current healthcare environment. The major purpose of the course is to teach students the clinical judgment needed to predict and manage potential complications and to decrease the failure to rescue rate which results in improved patient outcomes. This course provides the foundation for the thinking processes applied throughout all nursing courses and is designed for students enrolled in the apprenticeship program.",
                  "learning_outcomes": [],
                  "skills": [
                    "Clinical Documentation"
                  ]
                },
                {
                  "code": "NURS 124",
                  "name": "Concepts of Adult Health Nursing 1",
                  "description": "This course presents fundamental concepts and leveled competencies necessary for safe, compassionate, patient-centered nursing care for a diverse adult patient population with well-defined healthcare concerns with a focus on elderly patients. The course continues as an introduction to foundational concepts related to professional practice such as the legal and ethical responsibilities of the Registered Nurse. The student also uses clinical judgment applied to nursing practice. Select nursing skills are taught in the skills laboratory; theory and skills are applied in various clinical settings.",
                  "learning_outcomes": [],
                  "skills": [
                    "Clinical Documentation"
                  ]
                },
                {
                  "code": "NURS 124A",
                  "name": "Concepts of Adult Health Nursing 1 - Apprenticeship",
                  "description": "This course presents fundamental concepts and levelled competencies necessary for safe, compassionate, patient-centered nursing care for a diverse adult patient population with well-defined healthcare concerns with a focus on elderly patients. The course continues as an introduction to foundational concepts related to professional practice such as the legal and ethical responsibilities of the Registered Nurse. The student also uses clinical judgment applied to nursing practice. Select nursing skills are taught in the skills laboratory; theory and skills are applied in various clinical settings. This course is specifically for those students enrolled in the nursing apprenticeship program.",
                  "learning_outcomes": [],
                  "skills": [
                    "Clinical Documentation"
                  ]
                },
                {
                  "code": "NURS 133",
                  "name": "Concepts of Mental Health and Psychiatric Nursing",
                  "description": "This course builds on and applies concepts and levelled competencies of nursing practice to the care of patients with various mental health needs, their families, and other support persons. Application of new and previously learned nursing concepts, patient care skills, and clinical judgment occurs in a variety of clinical settings.",
                  "learning_outcomes": [],
                  "skills": [
                    "Clinical Documentation"
                  ]
                },
                {
                  "code": "NURS 133A",
                  "name": "Concepts of Mental Health and Psychiatric Nursing - Apprenticeship",
                  "description": "This course builds on and applies concepts and leveled competencies of nursing practice to the care of patients with various mental health needs, their families, and other support persons. Application of new and previously learned nursing concepts, patient care skills, and clinical judgment occurs in a variety of clinical settings. This course is designated for students enrolled in the apprenticeship program.",
                  "learning_outcomes": [],
                  "skills": [
                    "Clinical Documentation"
                  ]
                },
                {
                  "code": "NURS 134",
                  "name": "Concepts of Adult Health Nursing 2",
                  "description": "Building on foundational nursing knowledge and leveled competencies, this second-semester course integrates advanced theoretical concepts with hands-on clinical practice. Students will deepen their understanding of complex patient care through a focus on pathophysiology, pharmacology, and evidence-based practice. Clinical placements emphasize the application of nursing interventions in diverse settings, promoting critical thinking and effective communication skills. Emphasis is placed on holistic patient assessment, care planning, and the delivery of high-quality, patient-centered care. By the end of the course, students will be equipped to manage more complex patient scenarios and collaborate effectively within interdisciplinary teams.",
                  "learning_outcomes": [],
                  "skills": [
                    "Patient Assessment"
                  ]
                },
                {
                  "code": "NURS 134A",
                  "name": "Concepts of Adult Health Nursing 2 - Apprenticeship",
                  "description": "Building on foundational nursing knowledge and leveled competencies, this second-semester course integrates advanced theoretical concepts with hands-on clinical practice. Students will deepen their understanding of complex patient care through a focus on pathophysiology, pharmacology, and evidence-based practice. Clinical placements emphasize the application of nursing interventions in diverse settings, promoting critical thinking and effective communication skills. Emphasis is placed on holistic patient assessment, care planning, and the delivery of high-quality, patient-centered care. By the end of the course, students will be equipped to manage more complex patient scenarios and collaborate effectively within interdisciplinary teams. This course is designated for students enrolled in the apprenticeship program.",
                  "learning_outcomes": [],
                  "skills": [
                    "Patient Assessment"
                  ]
                },
                {
                  "code": "NURS 135",
                  "name": "Concepts of Nursing Care of the Pregnant Family and the Neonate",
                  "description": "This course builds on and applies concepts and levelled competencies of nursing practice to the care of the pregnant family and the neonate. Application of new and previously learned nursing concepts, patient care skills, and clinical judgment occurs in a variety of clinical settings.",
                  "learning_outcomes": [],
                  "skills": [
                    "Clinical Documentation"
                  ]
                },
                {
                  "code": "NURS 135A",
                  "name": "Concepts of Nursing Care of the Pregnant Family and the Neonate - Apprenticeship",
                  "description": "This course builds on and applies concepts and leveled competencies of nursing practice to the care of the pregnant family and the neonate. Application of new and previously learned nursing concepts, patient care skills, and clinical judgment occurs in a variety of clinical settings. This course is designated for students enrolled in the apprenticeship program.",
                  "learning_outcomes": [],
                  "skills": [
                    "Clinical Documentation"
                  ]
                },
                {
                  "code": "NURS 142",
                  "name": "Pharmacology in Healthcare",
                  "description": "This nursing course is a study of the pharmacotherapy related to the nursing care of clients across the lifespan. The progressive themes of the nursing program are applied through the nursing process to attain the client's optimal well-being.",
                  "learning_outcomes": [],
                  "skills": [
                    "Clinical Documentation"
                  ]
                },
                {
                  "code": "NURS 143",
                  "name": "Concepts of Pediatric Nursing",
                  "description": "This course continues to build on and expand all previously learned concepts of nursing practice with application to the care of children, their families, and other support persons. Application of new and previously learned nursing concepts, patient care skills, and clinical judgment occurs in a variety of clinical settings.",
                  "learning_outcomes": [],
                  "skills": [
                    "Clinical Documentation"
                  ]
                },
                {
                  "code": "NURS 143A",
                  "name": "Concepts of Pediatric Nursing - Apprenticeship",
                  "description": "This course continues to build on and expand all previously learned concepts of nursing practice with application to the care of children, their families, and other support persons. Application of new and previously learned nursing concepts, patient care skills, and clinical judgment occurs in a variety of clinical settings. This course is designated for students enrolled in the apprenticeship program.",
                  "learning_outcomes": [],
                  "skills": [
                    "Clinical Documentation"
                  ]
                },
                {
                  "code": "NURS 144",
                  "name": "Concepts of Adult Health Nursing 3",
                  "description": "This course continues to build on and expand all previously learned concepts of nursing practice with application to the care of adult patients with complicated conditions, their families, and other support persons. Applications of new and previously learned nursing concepts, patient care skills, and clinical judgment occurs in a variety of clinical settings.",
                  "learning_outcomes": [],
                  "skills": [
                    "Clinical Documentation",
                    "Patient Assessment"
                  ]
                },
                {
                  "code": "NURS 144A",
                  "name": "Concepts of Adult Health Nursing 3 - Apprenticeship",
                  "description": "This course continues to build on and expand all previously learned concepts of nursing practice with application to the care of adult patients with complicated conditions, their families, and other support persons. Applications of new and previously learned nursing concepts, patient care skills, and clinical judgment occurs in a variety of clinical settings. This course is designated for students enrolled in the apprenticeship program.",
                  "learning_outcomes": [],
                  "skills": [
                    "Clinical Documentation",
                    "Patient Assessment"
                  ]
                },
                {
                  "code": "NURS 174",
                  "name": "Concepts of Adult Health 4",
                  "description": "This culminating course expands the concepts of nursing practice for the acquisition and application of care of adult patients with complex healthcare needs, their families, and other support persons. Application of knowledge, patient care skills, and clinical judgement occurs in a variety of clinical settings and in the simulation library.",
                  "learning_outcomes": [],
                  "skills": [
                    "Clinical Documentation"
                  ]
                },
                {
                  "code": "NURS 174A",
                  "name": "Concepts of Adult Health 4 - Apprenticeship",
                  "description": "This culminating course expands the concepts of nursing practice for the acquisition and application of care of adult patients with complex healthcare needs, their families, and other support persons. Application of knowledge, patient care skills, and clinical judgement occurs in a variety of clinical settings and in the simulation library. This course is designated for students enrolled in the apprenticeship program.",
                  "learning_outcomes": [],
                  "skills": [
                    "Clinical Documentation"
                  ]
                },
                {
                  "code": "NURS 175",
                  "name": "Transition to Registered Nursing Practice",
                  "description": "This advanced, comprehensive course provides a synthesis of all concepts and nursing content taught throughout the program with application in the simulation lab. This course enables the individual student to recognize areas that need enhancement prior to entering Registered Nursing practice and includes a review for the NCLEX-RN\u00ae and strategies for success.",
                  "learning_outcomes": [],
                  "skills": [
                    "Clinical Documentation"
                  ]
                },
                {
                  "code": "NURS 175A",
                  "name": "Transition to Registered Nursing Practice - Apprenticeship",
                  "description": "This advanced, comprehensive course provides a synthesis of all concepts and nursing content taught throughout the program with application in the simulation lab. This course enables the individual student to recognize areas that need enhancement prior to entering Registered Nursing practice and includes a review for the NCLEX-RN\u00ae and strategies for success. This course is designated for students enrolled in the apprenticeship program.",
                  "learning_outcomes": [],
                  "skills": [
                    "Clinical Documentation"
                  ]
                },
                {
                  "code": "NURS 220",
                  "name": "Perioperative Nursing",
                  "description": "This is an elective course in perioperative nursing. This course is designed to prepare a competent and knowledgeable practitioner to administer optimum care to select surgical patients during pre-operative, intra-operative, and post-operative phases of surgical intervention.",
                  "learning_outcomes": [],
                  "skills": [
                    "Clinical Documentation"
                  ]
                },
                {
                  "code": "NURS 220A",
                  "name": "Perioperative Nursing (Apprenticeship)",
                  "description": "This is an elective course in perioperative nursing for the nursing student in the apprenticeship program. This course is designed to prepare a competent and knowledgeable practitioner to administer optimum care to select surgical patients during pre-operative, intra-operative, and post-operative phases of surgical intervention for nursing apprenticeship students.",
                  "learning_outcomes": [],
                  "skills": [
                    "Clinical Documentation"
                  ]
                },
                {
                  "code": "NURS 260",
                  "name": "Nursing Assistant",
                  "description": "This course is designed to prepare the student as an entry-level worker, providing basic nursing care to patients in acute care and long-term care settings. The curriculum is structured to provide theory and application in skills needed to function as a Nursing Assistant. Upon completion, students will be eligible to take the state certification examination. *All students are required to submit to, and pass, a background and drug screen. Our partnered health care agencies will not accept any student with a flagged background for placement. Students with a flagged background must expunge their record prior to registering in the course. Other clinical requirements include immunizations, physical, fingerprints, and American Heart Association Health Care Provider CPR Certification, prior to the initiation of the clinical rotation.",
                  "learning_outcomes": [],
                  "skills": [
                    "Clinical Documentation"
                  ]
                },
                {
                  "code": "NURS 400",
                  "name": "Nursing Skills Lab",
                  "description": "This course provides the student an opportunity for additional directed learning and supervised laboratory time to develop and refine nursing clinical skills necessary to the safe clinical practice of professional nursing. The student will gain knowledge from instructor demonstration, a variety of electronic media, computers and simulation.",
                  "learning_outcomes": [],
                  "skills": [
                    "Clinical Documentation"
                  ]
                }
              ],
              "aligned_skills": [
                "Clinical Documentation",
                "Patient Assessment"
              ]
            }
          ],
          "student_composition": "Students across these three departments are building skills that translate directly into the roles the Guard fills in the Central Valley and Mother Lode region. The aggregate pipeline spans health sciences, public safety, and emergency response pathways, representing a broad range of students preparing for high-acuity, operationally demanding work.",
          "student_evidence": {
            "total_in_program": 556,
            "with_all_core_skills": 7,
            "top_students": [
              {
                "uuid": "d1aaf3f2-2136-521f-bccf-3e78e674b5ee",
                "display_number": 1,
                "primary_focus": "Nursing",
                "courses_completed": 10,
                "gpa": 3.35,
                "matching_skills": 6,
                "enrollments": [
                  {
                    "code": "DRAM 030",
                    "name": "Stage Movement/Stage Combat",
                    "grade": "A",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "NURS 144",
                    "name": "Concepts of Adult Health Nursing 3",
                    "grade": "B",
                    "term": "2022-Fall"
                  },
                  {
                    "code": "CHLD 143",
                    "name": "Administration I: Programs in Early Childhood Education",
                    "grade": "B",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "NURS 175",
                    "name": "Transition to Registered Nursing Practice",
                    "grade": "A",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "NURS 135",
                    "name": "Concepts of Nursing Care of the Pregnant Family and the Neonate",
                    "grade": "A",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "NURS 124A",
                    "name": "Concepts of Adult Health Nursing 1 - Apprenticeship",
                    "grade": "B",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "NURS 123A",
                    "name": "Critical Thinking/Clinical Judgement in Nursing - Apprenticeship",
                    "grade": "B",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "NURS 123",
                    "name": "Critical Thinking/Clinical Judgement in Nursing",
                    "grade": "A",
                    "term": "2022-Fall"
                  },
                  {
                    "code": "AJ 219",
                    "name": "Police Patrol Procedures",
                    "grade": "B",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "SMED 181",
                    "name": "Athletic Training Clinical 1",
                    "grade": "A",
                    "term": "2024-Fall"
                  }
                ],
                "relevant_skills": [
                  "Clinical Documentation",
                  "Emergency Response",
                  "Leadership",
                  "Patient Assessment",
                  "Physical Fitness",
                  "Public Safety & Security"
                ]
              },
              {
                "uuid": "b4c8917f-4fde-5e84-a7da-32a40e457d18",
                "display_number": 2,
                "primary_focus": "Nursing",
                "courses_completed": 8,
                "gpa": 3.11,
                "matching_skills": 6,
                "enrollments": [
                  {
                    "code": "PEAC 262",
                    "name": "Cheer Fitness 1",
                    "grade": "A",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "NURS 134A",
                    "name": "Concepts of Adult Health Nursing 2 - Apprenticeship",
                    "grade": "A",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "FIRE 160",
                    "name": "Fire and Emergency Safety",
                    "grade": "C",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "NURS 260",
                    "name": "Nursing Assistant",
                    "grade": "A",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "NURS 174A",
                    "name": "Concepts of Adult Health 4 - Apprenticeship",
                    "grade": "C",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "NURS 135A",
                    "name": "Concepts of Nursing Care of the Pregnant Family and the Neonate - Apprenticeship",
                    "grade": "A",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "NURS 135",
                    "name": "Concepts of Nursing Care of the Pregnant Family and the Neonate",
                    "grade": "B",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "NURS 133A",
                    "name": "Concepts of Mental Health and Psychiatric Nursing - Apprenticeship",
                    "grade": "B",
                    "term": "2024-Winter"
                  }
                ],
                "relevant_skills": [
                  "Clinical Documentation",
                  "Emergency Response",
                  "Leadership",
                  "Patient Assessment",
                  "Physical Fitness",
                  "Public Safety & Security"
                ]
              },
              {
                "uuid": "acb9f0f4-7632-5d84-a94c-babfa943113c",
                "display_number": 3,
                "primary_focus": "Nursing",
                "courses_completed": 11,
                "gpa": 3.1,
                "matching_skills": 6,
                "enrollments": [
                  {
                    "code": "PEAC 052",
                    "name": "Beginning Tennis",
                    "grade": "A",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "SMED 184",
                    "name": "Athletic Training Clinical 4",
                    "grade": "C",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "NURS 144A",
                    "name": "Concepts of Adult Health Nursing 3 - Apprenticeship",
                    "grade": "B",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "NURS 134A",
                    "name": "Concepts of Adult Health Nursing 2 - Apprenticeship",
                    "grade": "A",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "FIRE 233",
                    "name": "SFM Company Officer 2D",
                    "grade": "C",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "NURS 260",
                    "name": "Nursing Assistant",
                    "grade": "A",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "NURS 175A",
                    "name": "Transition to Registered Nursing Practice - Apprenticeship",
                    "grade": "B",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "NURS 143A",
                    "name": "Concepts of Pediatric Nursing - Apprenticeship",
                    "grade": "B",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "NURS 121A",
                    "name": "Fundamentals for Nursing - Apprenticeship",
                    "grade": "B",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "BIOL 030",
                    "name": "Human Anatomy",
                    "grade": "A",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "ASCI 207",
                    "name": "Veterinary Terminology",
                    "grade": "C",
                    "term": "2024-Spring"
                  }
                ],
                "relevant_skills": [
                  "Clinical Documentation",
                  "Emergency Response",
                  "Leadership",
                  "Patient Assessment",
                  "Physical Fitness",
                  "Public Safety & Security"
                ]
              },
              {
                "uuid": "010de819-b35d-5119-8f3e-3976a3b78243",
                "display_number": 4,
                "primary_focus": "Nursing",
                "courses_completed": 9,
                "gpa": 3.09,
                "matching_skills": 6,
                "enrollments": [
                  {
                    "code": "PEAC 042",
                    "name": "Soccer",
                    "grade": "A",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "NURS 144",
                    "name": "Concepts of Adult Health Nursing 3",
                    "grade": "A",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "FIRE 232",
                    "name": "SFM Company Officer 2C",
                    "grade": "C",
                    "term": "2022-Fall"
                  },
                  {
                    "code": "AGMT 102",
                    "name": "Ag Sales and Marketing",
                    "grade": "A",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "NURS 260",
                    "name": "Nursing Assistant",
                    "grade": "B",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "NURS 135",
                    "name": "Concepts of Nursing Care of the Pregnant Family and the Neonate",
                    "grade": "A",
                    "term": "2022-Fall"
                  },
                  {
                    "code": "NURS 124A",
                    "name": "Concepts of Adult Health Nursing 1 - Apprenticeship",
                    "grade": "C",
                    "term": "2022-Fall"
                  },
                  {
                    "code": "NURS 124",
                    "name": "Concepts of Adult Health Nursing 1",
                    "grade": "A",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "AJ 219",
                    "name": "Police Patrol Procedures",
                    "grade": "A",
                    "term": "2025-Spring"
                  }
                ],
                "relevant_skills": [
                  "Clinical Documentation",
                  "Emergency Response",
                  "Leadership",
                  "Patient Assessment",
                  "Physical Fitness",
                  "Public Safety & Security"
                ]
              },
              {
                "uuid": "053acea7-d8de-5286-b9ea-42f76a46e121",
                "display_number": 5,
                "primary_focus": "Fire Technology",
                "courses_completed": 8,
                "gpa": 3.06,
                "matching_skills": 6,
                "enrollments": [
                  {
                    "code": "PEAC 053",
                    "name": "Intermediate Tennis",
                    "grade": "A",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "IA 006AD",
                    "name": "Intercollegiate Football",
                    "grade": "A",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "NURS 144A",
                    "name": "Concepts of Adult Health Nursing 3 - Apprenticeship",
                    "grade": "A",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "FIRE 235",
                    "name": "Fire Instructor I: Instructional Methodology",
                    "grade": "F",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "FIRE 233",
                    "name": "SFM Company Officer 2D",
                    "grade": "A",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "DRAM 016",
                    "name": "Intermediate Stage Lighting",
                    "grade": "A",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "FIRE 157",
                    "name": "Fire Prevention Technology",
                    "grade": "B",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "FIRE 125",
                    "name": "Fundamentals of Fire Apparatus and Equipment",
                    "grade": "A",
                    "term": "2022-Fall"
                  }
                ],
                "relevant_skills": [
                  "Clinical Documentation",
                  "Emergency Response",
                  "Leadership",
                  "Patient Assessment",
                  "Physical Fitness",
                  "Public Safety & Security"
                ]
              },
              {
                "uuid": "849e18bf-f2c8-59a1-b8a8-9219407d620c",
                "display_number": 6,
                "primary_focus": "Fire Technology",
                "courses_completed": 12,
                "gpa": 2.96,
                "matching_skills": 6,
                "enrollments": [
                  {
                    "code": "PEAC 263",
                    "name": "Cheer Fitness 2",
                    "grade": "A",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "PEAC 025",
                    "name": "Fundamentals of Football",
                    "grade": "A",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "PEAC 002",
                    "name": "Non-Impact Aerobics",
                    "grade": "A",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "IA 001AD",
                    "name": "Intercollegiate Varsity Baseball",
                    "grade": "A",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "NURS 144A",
                    "name": "Concepts of Adult Health Nursing 3 - Apprenticeship",
                    "grade": "A",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "FIRE 235",
                    "name": "Fire Instructor I: Instructional Methodology",
                    "grade": "A",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "FIRE 234",
                    "name": "SFM Company Officer 2E",
                    "grade": "C",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "FIRE 232",
                    "name": "SFM Company Officer 2C",
                    "grade": "A",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "PT 228",
                    "name": "Pharmacy Technician Externship 1",
                    "grade": "B",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "HW 003",
                    "name": "First Aid/CPR/AED",
                    "grade": "A",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "FIRE 280",
                    "name": "Fire Fighter 2 Academy",
                    "grade": "C",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "FIRE 157",
                    "name": "Fire Prevention Technology",
                    "grade": "F",
                    "term": "2023-Spring"
                  }
                ],
                "relevant_skills": [
                  "Clinical Documentation",
                  "Emergency Response",
                  "Leadership",
                  "Patient Assessment",
                  "Physical Fitness",
                  "Public Safety & Security"
                ]
              },
              {
                "uuid": "6a4b79bd-6e76-5d9f-9c2a-9df547f4f330",
                "display_number": 7,
                "primary_focus": "Fire Technology",
                "courses_completed": 12,
                "gpa": 2.94,
                "matching_skills": 6,
                "enrollments": [
                  {
                    "code": "PEAC 071",
                    "name": "Cross Interval Training",
                    "grade": "A",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "PEAC 061",
                    "name": "Varsity Performance 2",
                    "grade": "A",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "PTA 125",
                    "name": "Basic Principles of Patient Management",
                    "grade": "B",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "FIRE 235",
                    "name": "Fire Instructor I: Instructional Methodology",
                    "grade": "B",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "FIRE 234",
                    "name": "SFM Company Officer 2E",
                    "grade": "B",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "FIRE 232",
                    "name": "SFM Company Officer 2C",
                    "grade": "A",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "AG 110",
                    "name": "Ag Leadership",
                    "grade": "C",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "NURS 133",
                    "name": "Concepts of Mental Health and Psychiatric Nursing",
                    "grade": "B",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "FIRE 280",
                    "name": "Fire Fighter 2 Academy",
                    "grade": "A",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "FIRE 157",
                    "name": "Fire Prevention Technology",
                    "grade": "C",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "AJ 219",
                    "name": "Police Patrol Procedures",
                    "grade": "C",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "FIRE 155",
                    "name": "Fire Behavior and Combustion",
                    "grade": "B",
                    "term": "2023-Winter"
                  }
                ],
                "relevant_skills": [
                  "Clinical Documentation",
                  "Emergency Response",
                  "Leadership",
                  "Patient Assessment",
                  "Physical Fitness",
                  "Public Safety & Security"
                ]
              },
              {
                "uuid": "26fc2216-c569-5824-8ffa-53832b3deb71",
                "display_number": 8,
                "primary_focus": "Nursing",
                "courses_completed": 9,
                "gpa": 3.64,
                "matching_skills": 5,
                "enrollments": [
                  {
                    "code": "NURS 144",
                    "name": "Concepts of Adult Health Nursing 3",
                    "grade": "A",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "FIRE 234",
                    "name": "SFM Company Officer 2E",
                    "grade": "A",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "CULN 226",
                    "name": "Industry Management",
                    "grade": "A",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "WEXP 195N",
                    "name": "Work Experience Nursing - Third Semester",
                    "grade": "C",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "NURS 220A",
                    "name": "Perioperative Nursing (Apprenticeship)",
                    "grade": "A",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "NURS 174A",
                    "name": "Concepts of Adult Health 4 - Apprenticeship",
                    "grade": "A",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "NURS 143A",
                    "name": "Concepts of Pediatric Nursing - Apprenticeship",
                    "grade": "A",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "NURS 124",
                    "name": "Concepts of Adult Health Nursing 1",
                    "grade": "B",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "NURS 123",
                    "name": "Critical Thinking/Clinical Judgement in Nursing",
                    "grade": "B",
                    "term": "2024-Fall"
                  }
                ],
                "relevant_skills": [
                  "Clinical Documentation",
                  "Emergency Response",
                  "Leadership",
                  "Patient Assessment",
                  "Public Safety & Security"
                ]
              },
              {
                "uuid": "70df00d3-9890-5781-b4a9-a49fa9095445",
                "display_number": 9,
                "primary_focus": "Fire Technology",
                "courses_completed": 9,
                "gpa": 3.46,
                "matching_skills": 5,
                "enrollments": [
                  {
                    "code": "DANC 054",
                    "name": "Modern Dance 1",
                    "grade": "A",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "FIRE 234",
                    "name": "SFM Company Officer 2E",
                    "grade": "B",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "FIRE 231",
                    "name": "SFM Company Officer 2B",
                    "grade": "A",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "BUS 082",
                    "name": "Introduction to Business",
                    "grade": "B",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "PTA 161",
                    "name": "Clinical Education 3",
                    "grade": "B",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "FIRE 159",
                    "name": "Introduction to Fire Protection Organizations",
                    "grade": "A",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "FIRE 157",
                    "name": "Fire Prevention Technology",
                    "grade": "A",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "FIRE 125",
                    "name": "Fundamentals of Fire Apparatus and Equipment",
                    "grade": "B",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "FIRE 155",
                    "name": "Fire Behavior and Combustion",
                    "grade": "A",
                    "term": "2024-Fall"
                  }
                ],
                "relevant_skills": [
                  "Clinical Documentation",
                  "Emergency Response",
                  "Leadership",
                  "Physical Fitness",
                  "Public Safety & Security"
                ]
              },
              {
                "uuid": "f91e558f-4ba8-5b93-b678-9e0e57361300",
                "display_number": 10,
                "primary_focus": "Fire Technology",
                "courses_completed": 7,
                "gpa": 3.44,
                "matching_skills": 5,
                "enrollments": [
                  {
                    "code": "PEAC 037",
                    "name": "Pilates Mat Class",
                    "grade": "A",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "FIRE 234",
                    "name": "SFM Company Officer 2E",
                    "grade": "C",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "FIRE 233",
                    "name": "SFM Company Officer 2D",
                    "grade": "A",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "NURS 133",
                    "name": "Concepts of Mental Health and Psychiatric Nursing",
                    "grade": "B",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "FIRE 285",
                    "name": "Combined Firefighter 1 and 2 Academy",
                    "grade": "A",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "FIRE 125",
                    "name": "Fundamentals of Fire Apparatus and Equipment",
                    "grade": "A",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "FIRE 155",
                    "name": "Fire Behavior and Combustion",
                    "grade": "A",
                    "term": "2024-Fall"
                  }
                ],
                "relevant_skills": [
                  "Clinical Documentation",
                  "Emergency Response",
                  "Leadership",
                  "Physical Fitness",
                  "Public Safety & Security"
                ]
              }
            ]
          }
        },
        "roadmap": "A quarterly advisory board with National Guard representatives could give the Fire Technology, Emergency Medical Technician, and Nursing departments sustained access to operational perspective from a dual-mission employer. Potential starting points for the inaugural meeting include how the Guard integrates clinical documentation standards into field nursing under austere conditions, what readiness benchmarks Guard firefighters meet before independent deployment, and how command responsibility is structured for EMT-level personnel during multi-agency disaster responses.",
        "selected_occupations": [
          "Military-only occupations",
          "Registered Nurses",
          "Firefighters"
        ],
        "advisory_thesis": "The National Guard operates at the intersection of military discipline and civilian emergency response, deploying personnel across roles ranging from combat leadership to nursing and firefighting in both peacetime crises and federal defense missions. This dual-mission structure means students in health sciences, public safety, and leadership programs can see how their skills translate into high-stakes, resource-constrained environments where military standards and civilian professional competencies converge.",
        "agenda_topics": [
          {
            "topic": "How does the National Guard integrate clinical documentation standards into field nursing roles under austere conditions?",
            "rationale": "National Guard nursing operations can inform how the Nursing department frames documentation training within resource-constrained, high-acuity environments."
          },
          {
            "topic": "What physical and decision-making benchmarks do Guard firefighters meet before independent emergency deployment?",
            "rationale": "Operational readiness criteria from the National Guard can help the Fire Technology department calibrate performance milestones in emergency response coursework."
          },
          {
            "topic": "How does the Guard structure command responsibility for EMT-level personnel during multi-agency disaster responses?",
            "rationale": "The Guard's dual-mission incident structure can inform how the Emergency Medical Technician department contextualizes public safety and field leadership within its curriculum."
          }
        ]
      },
      "engagementType": "advisory_board",
      "collegeId": "College of the Sequoias",
      "savedAt": "2026-04-20T00:00:00.000Z",
      "status": "saved",
      "schemaVersion": 8
    },
    {
      "id": "seed-sequoias-internship-01",
      "proposal": {
        "employer": "Saputo Cheese USA",
        "sector": "Manufacturing",
        "partnership_type": "Internship Pipeline",
        "selected_occupation": "Food Science Technicians",
        "selected_soc_code": "19-4013",
        "core_skills": [
          "Food Safety",
          "Food Production",
          "Laboratory Techniques"
        ],
        "gap_skill": "",
        "regions": [
          "Los Angeles",
          "Central Valley / Mother Lode"
        ],
        "opportunity": "Saputo Cheese USA is a compelling internship partner for College of the Sequoias students pursuing Food Science Technician roles in the Central Valley. The region supports 1,260 employed technicians with 190 annual openings and a median wage of $47,950, signaling sustained employer demand. A structured 8-16 week placement at Saputo could give students direct exposure to food production and quality control workflows in an active manufacturing environment.",
        "opportunity_evidence": [
          {
            "title": "Food Science Technicians",
            "soc_code": "19-4013",
            "annual_wage": 47950,
            "employment": 1260,
            "annual_openings": 190,
            "growth_rate": 0.024915091
          }
        ],
        "justification": {
          "curriculum_composition": "The Agriculture department provides the most direct preparation for an internship at Saputo, building laboratory techniques and food production skills that map closely to what a food science technician performs on the floor. The Chemistry and Biology departments reinforce laboratory techniques across a combined ten courses, giving students substantial bench experience before they arrive on site. That preparation supports a credible internship placement without additional prerequisite scaffolding.",
          "curriculum_evidence": [
            {
              "department": "Agriculture",
              "courses": [
                {
                  "code": "AG 002",
                  "name": "Environmental Conservation",
                  "description": "A study of the world's environment, including the study of food and fiber systems, ecology, populations, environmental pollution, bioterrorism, and conservation of natural resources. Students will participate in field tours to examine natural and altered habitats and threats to society and the environment.",
                  "learning_outcomes": [],
                  "skills": [
                    "Food Production"
                  ]
                },
                {
                  "code": "AG 003",
                  "name": "Economic Entomology",
                  "description": "The study of the insects and mites of economic importance to agriculture, including morphology, taxonomy, identification, life cycles, hosts, habitat relationships, and control methods. Collection and labeling of specimens will be required. Laboratory required. Recommended for Pest Control Advisors' licensing. (C-ID AG-PS 144L)",
                  "learning_outcomes": [],
                  "skills": [
                    "Laboratory Techniques"
                  ]
                }
              ],
              "aligned_skills": [
                "Food Production",
                "Laboratory Techniques"
              ]
            },
            {
              "department": "Biology",
              "courses": [
                {
                  "code": "BIOL 022",
                  "name": "Animal Biology",
                  "description": "This is a general principles course in animal biology designed to help meet a laboratory requirement for transfer students who are not life science majors. The principles of the scientific method, evolution and adaptation, bioenergetics, homeostasis, genetics, and ecology are emphasized in class and field activities. It is not open to students who have received credit for BIOL 001.",
                  "learning_outcomes": [],
                  "skills": [
                    "Laboratory Techniques"
                  ]
                },
                {
                  "code": "BIOL 031",
                  "name": "Human Physiology",
                  "description": "Study of the physiological principles, functions, integration and homeostasis of the human body at the cellular, tissue, organ, organ system and organism level: integumentary system, bone, skeletal, smooth and cardiac muscles, nervous system, sensory organs, cardiovascular system, lymphatic and immune systems, respiratory system, urinary system, digestive system, endocrine system, and reproductive system. Laboratory experiments and exercises will reinforce theories and processes described in lecture and introduce students to basic physiological scientific investigation. This course is primarily intended for Nursing, Allied Health, and other health related majors. (C-ID BIOL120B)",
                  "learning_outcomes": [],
                  "skills": [
                    "Laboratory Techniques"
                  ]
                },
                {
                  "code": "BIOL 040",
                  "name": "General Microbiology",
                  "description": "This course is designed for students entering the health sciences, home economics, as well as the life sciences. This course covers microbial diversity, classification, identification, growth, control measures, disease interactions, genetics, and applied microbiology.",
                  "learning_outcomes": [],
                  "skills": [
                    "Laboratory Techniques"
                  ]
                }
              ],
              "aligned_skills": [
                "Laboratory Techniques"
              ]
            },
            {
              "department": "Chemistry",
              "courses": [
                {
                  "code": "CHEM 001",
                  "name": "General Chemistry 1",
                  "description": "A course for majors and pre-professionals involving the fundamental theories and laws of chemistry. Topics include stoichiometry, atomic structure, bonding theories, ionic reactions and properties of gases. Chemistry prerequisite may be waived with one year of high school chemistry with a minimum grade of C. (C-ID CHEM110; C-ID CHEM120S includes CHEM 001 and 002)",
                  "learning_outcomes": [],
                  "skills": [
                    "Laboratory Techniques"
                  ]
                },
                {
                  "code": "CHEM 002",
                  "name": "General Chemistry 2",
                  "description": "A course for majors and pre-professionals involving the fundamental theories and laws of chemistry. Topics include liquids, solids, solutions, kinetics, acid/base theories, acid/base equilibrium, solubility and complex equilibrium, thermodynamics, electrochemistry, coordination compounds and nuclear chemistry. (C-ID CHEM120S - includes CHEM 001 and 002)",
                  "learning_outcomes": [],
                  "skills": [
                    "Laboratory Techniques"
                  ]
                },
                {
                  "code": "CHEM 010",
                  "name": "Introduction to Chemistry",
                  "description": "This is a one-semester elementary class for students who have never taken high school chemistry or for students who feel they need a refresher course. This course is also for students who need a physical lab science to satisfy their general education requirement or for students who want to become better prepared for more advanced chemistry. The course will give students a basic background in matter, energy, chemical reactions, measurements, formula writing, nomenclature and chemical calculations.",
                  "learning_outcomes": [],
                  "skills": [
                    "Laboratory Techniques"
                  ]
                },
                {
                  "code": "CHEM 012",
                  "name": "Organic Chemistry 1",
                  "description": "This is the first semester of a comprehensive study of organic chemistry. This course is primarily for chemistry or biochemistry and biology majors, premedical, pre-dental students, pre-pharmacy and medical technicians. Emphasis is on structural and functional group chemistry studied from a synthetic and mechanistic point of view. Topics include: nomenclature, stereochemistry, free radical processes, structure, bonding, hybridization of carbon compounds, basic elimination and substitution reactions, introductory infrared and nuclear magnetic resonance spectroscopy. The course includes a laboratory use of micro/macro methods and techniques, synthesis and instrumentation. Formerly CHEM 12 and 12L. (C-ID CHEM150; C-ID CHEM160S includes CHEM 012 AND 013)",
                  "learning_outcomes": [],
                  "skills": [
                    "Laboratory Techniques"
                  ]
                },
                {
                  "code": "CHEM 013",
                  "name": "Organic Chemistry 2",
                  "description": "This is a continuation of CHEM 12, a comprehensive study of organic chemistry. The course is primarily for chemistry, biochemistry and biology majors, premedical, predental, prepharmacy students and medical technicians. Emphasis is on structural and functional group chemistry studied from a synthetic and mechanistic point of view. Topics include: reactions of aromatic compounds, condensations, natural products chemistry, introductory bio-chemistry, mass spectrometry and ultraviolet/visible spectroscopy. The course includes a laboratory use of micro/macro methods and techniques, synthesis and instrumentation. (C-ID CHEM160S - includes CHEM 012 AND 013)",
                  "learning_outcomes": [],
                  "skills": [
                    "Laboratory Techniques"
                  ]
                },
                {
                  "code": "CHEM 020",
                  "name": "Introduction to General Chemistry",
                  "description": "CHEM 020 is a one semester transferable college chemistry course designed to meet the needs of allied-health and non-science majors. The course is a study of the fundamental theories and laws of chemistry. The laboratory portion of the course involves experimentation and drawing conclusions from data. (C-ID CHEM101)",
                  "learning_outcomes": [],
                  "skills": [
                    "Laboratory Techniques"
                  ]
                },
                {
                  "code": "CHEM 021",
                  "name": "Organic/Biological Chemistry",
                  "description": "CHEM 021 is the second semester of a full year college chemistry course which meets the needs of the science-related major. Content focuses on structural configurations, properties and reactions of organic and biochemical compounds. Both qualitative and quantitative aspects of these are part of lecture and laboratory. (C-ID CHEM102)",
                  "learning_outcomes": [],
                  "skills": [
                    "Laboratory Techniques"
                  ]
                }
              ],
              "aligned_skills": [
                "Laboratory Techniques"
              ]
            }
          ],
          "student_composition": "Students in the Agriculture program are completing coursework in food production and laboratory techniques that align with the technician role Saputo needs to fill. Chemistry and Biology students contribute additional laboratory depth to the same pipeline. The pool spans multiple departments, which broadens the number of eligible candidates for a first cohort.",
          "student_evidence": {
            "total_in_program": 524,
            "with_all_core_skills": 18,
            "top_students": [
              {
                "uuid": "14b12bfe-77d9-5a30-aa4d-b5338dd24741",
                "display_number": 1,
                "primary_focus": "Biology",
                "courses_completed": 2,
                "gpa": 3.43,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "CULN 225",
                    "name": "Garde Manger",
                    "grade": "B",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "PHYS 021",
                    "name": "General Physics 2",
                    "grade": "A",
                    "term": "2024-Winter"
                  }
                ],
                "relevant_skills": [
                  "Food Production",
                  "Food Safety",
                  "Laboratory Techniques"
                ]
              },
              {
                "uuid": "8b30dea7-528b-5a06-b530-760f010a4031",
                "display_number": 2,
                "primary_focus": "Chemistry",
                "courses_completed": 8,
                "gpa": 3.28,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "CULN 221",
                    "name": "Culinary Development 1",
                    "grade": "A",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "PLSI 106",
                    "name": "Fertilizers and Soil Amendments",
                    "grade": "A",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "CHEM 021",
                    "name": "Organic/Biological Chemistry",
                    "grade": "A",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "CHEM 020",
                    "name": "Introduction to General Chemistry",
                    "grade": "W",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "CHEM 013",
                    "name": "Organic Chemistry 2",
                    "grade": "C",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "CHEM 012",
                    "name": "Organic Chemistry 1",
                    "grade": "W",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "CHEM 002",
                    "name": "General Chemistry 2",
                    "grade": "W",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "CHEM 001",
                    "name": "General Chemistry 1",
                    "grade": "B",
                    "term": "2023-Winter"
                  }
                ],
                "relevant_skills": [
                  "Food Production",
                  "Food Safety",
                  "Laboratory Techniques"
                ]
              },
              {
                "uuid": "205b770a-96d6-5f11-83bd-8f97087690ed",
                "display_number": 3,
                "primary_focus": "Chemistry",
                "courses_completed": 7,
                "gpa": 3.0,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "CULN 221",
                    "name": "Culinary Development 1",
                    "grade": "B",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "CHEM 021",
                    "name": "Organic/Biological Chemistry",
                    "grade": "F",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "CHEM 020",
                    "name": "Introduction to General Chemistry",
                    "grade": "A",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "CHEM 013",
                    "name": "Organic Chemistry 2",
                    "grade": "C",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "CHEM 012",
                    "name": "Organic Chemistry 1",
                    "grade": "B",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "CHEM 010",
                    "name": "Introduction to Chemistry",
                    "grade": "B",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "CHEM 002",
                    "name": "General Chemistry 2",
                    "grade": "A",
                    "term": "2023-Spring"
                  }
                ],
                "relevant_skills": [
                  "Food Production",
                  "Food Safety",
                  "Laboratory Techniques"
                ]
              },
              {
                "uuid": "77c192f0-a468-5e61-b879-df5c096c1dc3",
                "display_number": 4,
                "primary_focus": "Chemistry",
                "courses_completed": 9,
                "gpa": 2.97,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "NUTR 107",
                    "name": "Sanitation and Safety",
                    "grade": "A",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "NUTR 020",
                    "name": "Cultural Foods",
                    "grade": "W",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "CULN 223",
                    "name": "Advanced Culinary",
                    "grade": "A",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "CHEM 021",
                    "name": "Organic/Biological Chemistry",
                    "grade": "W",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "CHEM 020",
                    "name": "Introduction to General Chemistry",
                    "grade": "D",
                    "term": "2022-Fall"
                  },
                  {
                    "code": "CHEM 012",
                    "name": "Organic Chemistry 1",
                    "grade": "B",
                    "term": "2022-Fall"
                  },
                  {
                    "code": "CHEM 010",
                    "name": "Introduction to Chemistry",
                    "grade": "B",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "CHEM 002",
                    "name": "General Chemistry 2",
                    "grade": "C",
                    "term": "2022-Fall"
                  },
                  {
                    "code": "CHEM 001",
                    "name": "General Chemistry 1",
                    "grade": "B",
                    "term": "2022-Fall"
                  }
                ],
                "relevant_skills": [
                  "Food Production",
                  "Food Safety",
                  "Laboratory Techniques"
                ]
              },
              {
                "uuid": "820373fc-6ac4-5b25-9cc2-095f23ce5f5c",
                "display_number": 5,
                "primary_focus": "Chemistry",
                "courses_completed": 8,
                "gpa": 2.96,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "ASCI 202",
                    "name": "Applied Food Safety Management",
                    "grade": "C",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "CULN 223",
                    "name": "Advanced Culinary",
                    "grade": "A",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "CHEM 020",
                    "name": "Introduction to General Chemistry",
                    "grade": "C",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "CHEM 013",
                    "name": "Organic Chemistry 2",
                    "grade": "A",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "CHEM 012",
                    "name": "Organic Chemistry 1",
                    "grade": "B",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "CHEM 010",
                    "name": "Introduction to Chemistry",
                    "grade": "W",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "CHEM 002",
                    "name": "General Chemistry 2",
                    "grade": "C",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "CHEM 001",
                    "name": "General Chemistry 1",
                    "grade": "F",
                    "term": "2022-Winter"
                  }
                ],
                "relevant_skills": [
                  "Food Production",
                  "Food Safety",
                  "Laboratory Techniques"
                ]
              },
              {
                "uuid": "c00f97c5-8889-5dee-b44b-6d73a7e5aa6d",
                "display_number": 6,
                "primary_focus": "Biology",
                "courses_completed": 2,
                "gpa": 2.94,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "ASCI 126",
                    "name": "Meat Science",
                    "grade": "A",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "BIOL 022",
                    "name": "Animal Biology",
                    "grade": "C",
                    "term": "2024-Spring"
                  }
                ],
                "relevant_skills": [
                  "Food Production",
                  "Food Safety",
                  "Laboratory Techniques"
                ]
              },
              {
                "uuid": "e34edb88-5d56-5353-adb9-5665fe3fe269",
                "display_number": 7,
                "primary_focus": "Chemistry",
                "courses_completed": 7,
                "gpa": 2.84,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "WEXP 193DD",
                    "name": "Culinary Internship - Work Experience - 1st Semester",
                    "grade": "A",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "CHEM 021",
                    "name": "Organic/Biological Chemistry",
                    "grade": "C",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "CHEM 020",
                    "name": "Introduction to General Chemistry",
                    "grade": "F",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "CHEM 013",
                    "name": "Organic Chemistry 2",
                    "grade": "C",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "CHEM 010",
                    "name": "Introduction to Chemistry",
                    "grade": "A",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "CHEM 002",
                    "name": "General Chemistry 2",
                    "grade": "F",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "CHEM 001",
                    "name": "General Chemistry 1",
                    "grade": "D",
                    "term": "2024-Fall"
                  }
                ],
                "relevant_skills": [
                  "Food Production",
                  "Food Safety",
                  "Laboratory Techniques"
                ]
              },
              {
                "uuid": "56b6446a-910a-5134-91fa-f23734f4124f",
                "display_number": 8,
                "primary_focus": "Chemistry",
                "courses_completed": 7,
                "gpa": 2.8,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "CULN 225",
                    "name": "Garde Manger",
                    "grade": "A",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "CHEM 020",
                    "name": "Introduction to General Chemistry",
                    "grade": "C",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "CHEM 013",
                    "name": "Organic Chemistry 2",
                    "grade": "F",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "CHEM 012",
                    "name": "Organic Chemistry 1",
                    "grade": "A",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "CHEM 010",
                    "name": "Introduction to Chemistry",
                    "grade": "A",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "CHEM 002",
                    "name": "General Chemistry 2",
                    "grade": "B",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "CHEM 001",
                    "name": "General Chemistry 1",
                    "grade": "B",
                    "term": "2023-Spring"
                  }
                ],
                "relevant_skills": [
                  "Food Production",
                  "Food Safety",
                  "Laboratory Techniques"
                ]
              },
              {
                "uuid": "6fc0fab0-3f72-594d-bf93-818b03e262a9",
                "display_number": 9,
                "primary_focus": "Chemistry",
                "courses_completed": 7,
                "gpa": 2.73,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "CULN 225",
                    "name": "Garde Manger",
                    "grade": "A",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "CHEM 021",
                    "name": "Organic/Biological Chemistry",
                    "grade": "C",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "CHEM 020",
                    "name": "Introduction to General Chemistry",
                    "grade": "W",
                    "term": "2022-Fall"
                  },
                  {
                    "code": "CHEM 012",
                    "name": "Organic Chemistry 1",
                    "grade": "B",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "CHEM 010",
                    "name": "Introduction to Chemistry",
                    "grade": "D",
                    "term": "2022-Fall"
                  },
                  {
                    "code": "CHEM 002",
                    "name": "General Chemistry 2",
                    "grade": "B",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "CHEM 001",
                    "name": "General Chemistry 1",
                    "grade": "W",
                    "term": "2022-Winter"
                  }
                ],
                "relevant_skills": [
                  "Food Production",
                  "Food Safety",
                  "Laboratory Techniques"
                ]
              },
              {
                "uuid": "488c99ca-9cf2-5a01-a917-ea40c3e24409",
                "display_number": 10,
                "primary_focus": "Chemistry",
                "courses_completed": 8,
                "gpa": 2.73,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "CULN 221",
                    "name": "Culinary Development 1",
                    "grade": "A",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "GEOG 001L",
                    "name": "Physical Geography Lab",
                    "grade": "W",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "CHEM 021",
                    "name": "Organic/Biological Chemistry",
                    "grade": "B",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "CHEM 020",
                    "name": "Introduction to General Chemistry",
                    "grade": "F",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "CHEM 013",
                    "name": "Organic Chemistry 2",
                    "grade": "W",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "CHEM 012",
                    "name": "Organic Chemistry 1",
                    "grade": "B",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "CHEM 002",
                    "name": "General Chemistry 2",
                    "grade": "F",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "CHEM 001",
                    "name": "General Chemistry 1",
                    "grade": "F",
                    "term": "2023-Spring"
                  }
                ],
                "relevant_skills": [
                  "Food Production",
                  "Food Safety",
                  "Laboratory Techniques"
                ]
              }
            ]
          }
        },
        "roadmap": "A potential starting point would be a conversation between the Agriculture department chair and Saputo's operations or HR team to define site capacity and supervision structure. An internship of 10-16 weeks could map to existing cooperative work experience courses for unit credit, with a first cohort of 5-10 students targeted within the next two semesters. Coordinating across the Agriculture, Chemistry, and Biology departments during recruiting would expand the candidate pool and reflect the range of preparation already in place.",
        "selected_occupations": [],
        "advisory_thesis": "",
        "agenda_topics": []
      },
      "engagementType": "internship",
      "collegeId": "College of the Sequoias",
      "savedAt": "2026-04-20T00:00:00.000Z",
      "status": "saved",
      "schemaVersion": 8
    },
    {
      "id": "seed-sequoias-curriculum-01",
      "proposal": {
        "employer": "Fresno County Department of Public Health",
        "sector": "Government",
        "partnership_type": "Curriculum Co-Design",
        "selected_occupation": "Registered Nurses",
        "selected_soc_code": "29-1141",
        "core_skills": [
          "Nursing Process",
          "Patient Assessment",
          "Infection Control"
        ],
        "gap_skill": "Community Health Outreach and Disease Surveillance",
        "regions": [
          "Central Valley / Mother Lode"
        ],
        "opportunity": "The College of the Sequoias Nursing program is well-positioned to deepen its alignment with the Fresno County Department of Public Health through a co-design partnership focused on community health outreach and disease surveillance. The program builds the clinical foundation that public health nursing requires. Collaboration with Fresno County Department of Public Health nursing staff could strengthen student preparation for population-level work that is central to public health practice in the Central Valley.",
        "opportunity_evidence": [
          {
            "title": "Registered Nurses",
            "soc_code": "29-1141",
            "annual_wage": 129360,
            "employment": 32090,
            "annual_openings": 2160,
            "growth_rate": 0.071729571
          }
        ],
        "justification": {
          "curriculum_composition": "The Nursing department is the right home for this partnership, with coursework across 25 courses developing the infection control, patient assessment, and nursing process skills that public health RN roles build on. Community health outreach and disease surveillance represent a dimension of practice that can be more rigorously developed through direct collaboration with the department's public health nursing staff. A co-design review could identify where communicable disease reporting and community prevention programming can be integrated into existing clinical coursework.",
          "curriculum_evidence": [
            {
              "department": "Nursing",
              "courses": [
                {
                  "code": "NURS 121",
                  "name": "Fundamentals for Nursing",
                  "description": "This course focuses on fundamental concepts necessary for safe, compassionate, patient-centered nursing care for a diverse patient population with well-defined healthcare concerns with a focus on elderly patients. The course offers an introduction to foundational concepts related to professional practices such as legal and ethical responsibilities of the Registered Nurse. The student also uses clinical judgment applied to nursing practice. Select nursing skills are taught in the skills laboratory; theory and skills re applied in various clinical settings.",
                  "learning_outcomes": [],
                  "skills": [
                    "Nursing Process"
                  ]
                },
                {
                  "code": "NURS 121A",
                  "name": "Fundamentals for Nursing - Apprenticeship",
                  "description": "This course focuses on fundamental concepts necessary for safe, compassionate, patient-centered nursing care for a diverse patient population with well-defined healthcare concerns with a focus on elderly patients. The course offers an introduction to foundational concepts related to professional practices such as legal and ethical responsibilities of the Registered Nurse. The student also uses clinical judgment applied to nursing practice. Select nursing skills are taught in the skills laboratory; theory and skills are applied in various clinical settings. This course is designated for students enrolled in the apprenticeship program.",
                  "learning_outcomes": [],
                  "skills": [
                    "Nursing Process"
                  ]
                },
                {
                  "code": "NURS 123",
                  "name": "Critical Thinking/Clinical Judgement in Nursing",
                  "description": "This course introduces clinical judgment through a focused study of critical thinking skills and strategies used by the Registered Nurse. The student applies critical thinking skills and strategies at the RN level that underscore the clinical judgment represented in the nursing process as well as dealing with aspects of the healthcare system for safe practice in the current healthcare environment. The major purpose of the course is to teach students the clinical judgment needed to predict and manage potential complications and to decrease the failure to rescue rate which results in improved patient outcomes. This course provides the foundation for the thinking processes applied throughout all nursing courses.",
                  "learning_outcomes": [],
                  "skills": [
                    "Nursing Process"
                  ]
                },
                {
                  "code": "NURS 123A",
                  "name": "Critical Thinking/Clinical Judgement in Nursing - Apprenticeship",
                  "description": "This course introduces clinical judgment through a focused study of critical thinking skills and strategies used by the Registered Nurse. The student applies critical thinking skills and strategies at the RN level that underscore the clinical judgment represented in the nursing process as well as dealing with aspects of the healthcare system for safe practice in the current healthcare environment. The major purpose of the course is to teach students the clinical judgment needed to predict and manage potential complications and to decrease the failure to rescue rate which results in improved patient outcomes. This course provides the foundation for the thinking processes applied throughout all nursing courses and is designed for students enrolled in the apprenticeship program.",
                  "learning_outcomes": [],
                  "skills": [
                    "Nursing Process"
                  ]
                },
                {
                  "code": "NURS 124",
                  "name": "Concepts of Adult Health Nursing 1",
                  "description": "This course presents fundamental concepts and leveled competencies necessary for safe, compassionate, patient-centered nursing care for a diverse adult patient population with well-defined healthcare concerns with a focus on elderly patients. The course continues as an introduction to foundational concepts related to professional practice such as the legal and ethical responsibilities of the Registered Nurse. The student also uses clinical judgment applied to nursing practice. Select nursing skills are taught in the skills laboratory; theory and skills are applied in various clinical settings.",
                  "learning_outcomes": [],
                  "skills": [
                    "Nursing Process"
                  ]
                },
                {
                  "code": "NURS 124A",
                  "name": "Concepts of Adult Health Nursing 1 - Apprenticeship",
                  "description": "This course presents fundamental concepts and levelled competencies necessary for safe, compassionate, patient-centered nursing care for a diverse adult patient population with well-defined healthcare concerns with a focus on elderly patients. The course continues as an introduction to foundational concepts related to professional practice such as the legal and ethical responsibilities of the Registered Nurse. The student also uses clinical judgment applied to nursing practice. Select nursing skills are taught in the skills laboratory; theory and skills are applied in various clinical settings. This course is specifically for those students enrolled in the nursing apprenticeship program.",
                  "learning_outcomes": [],
                  "skills": [
                    "Nursing Process"
                  ]
                },
                {
                  "code": "NURS 133",
                  "name": "Concepts of Mental Health and Psychiatric Nursing",
                  "description": "This course builds on and applies concepts and levelled competencies of nursing practice to the care of patients with various mental health needs, their families, and other support persons. Application of new and previously learned nursing concepts, patient care skills, and clinical judgment occurs in a variety of clinical settings.",
                  "learning_outcomes": [],
                  "skills": [
                    "Nursing Process"
                  ]
                },
                {
                  "code": "NURS 133A",
                  "name": "Concepts of Mental Health and Psychiatric Nursing - Apprenticeship",
                  "description": "This course builds on and applies concepts and leveled competencies of nursing practice to the care of patients with various mental health needs, their families, and other support persons. Application of new and previously learned nursing concepts, patient care skills, and clinical judgment occurs in a variety of clinical settings. This course is designated for students enrolled in the apprenticeship program.",
                  "learning_outcomes": [],
                  "skills": [
                    "Nursing Process"
                  ]
                },
                {
                  "code": "NURS 134",
                  "name": "Concepts of Adult Health Nursing 2",
                  "description": "Building on foundational nursing knowledge and leveled competencies, this second-semester course integrates advanced theoretical concepts with hands-on clinical practice. Students will deepen their understanding of complex patient care through a focus on pathophysiology, pharmacology, and evidence-based practice. Clinical placements emphasize the application of nursing interventions in diverse settings, promoting critical thinking and effective communication skills. Emphasis is placed on holistic patient assessment, care planning, and the delivery of high-quality, patient-centered care. By the end of the course, students will be equipped to manage more complex patient scenarios and collaborate effectively within interdisciplinary teams.",
                  "learning_outcomes": [],
                  "skills": [
                    "Nursing Process",
                    "Patient Assessment"
                  ]
                },
                {
                  "code": "NURS 134A",
                  "name": "Concepts of Adult Health Nursing 2 - Apprenticeship",
                  "description": "Building on foundational nursing knowledge and leveled competencies, this second-semester course integrates advanced theoretical concepts with hands-on clinical practice. Students will deepen their understanding of complex patient care through a focus on pathophysiology, pharmacology, and evidence-based practice. Clinical placements emphasize the application of nursing interventions in diverse settings, promoting critical thinking and effective communication skills. Emphasis is placed on holistic patient assessment, care planning, and the delivery of high-quality, patient-centered care. By the end of the course, students will be equipped to manage more complex patient scenarios and collaborate effectively within interdisciplinary teams. This course is designated for students enrolled in the apprenticeship program.",
                  "learning_outcomes": [],
                  "skills": [
                    "Nursing Process",
                    "Patient Assessment"
                  ]
                },
                {
                  "code": "NURS 135",
                  "name": "Concepts of Nursing Care of the Pregnant Family and the Neonate",
                  "description": "This course builds on and applies concepts and levelled competencies of nursing practice to the care of the pregnant family and the neonate. Application of new and previously learned nursing concepts, patient care skills, and clinical judgment occurs in a variety of clinical settings.",
                  "learning_outcomes": [],
                  "skills": [
                    "Nursing Process"
                  ]
                },
                {
                  "code": "NURS 135A",
                  "name": "Concepts of Nursing Care of the Pregnant Family and the Neonate - Apprenticeship",
                  "description": "This course builds on and applies concepts and leveled competencies of nursing practice to the care of the pregnant family and the neonate. Application of new and previously learned nursing concepts, patient care skills, and clinical judgment occurs in a variety of clinical settings. This course is designated for students enrolled in the apprenticeship program.",
                  "learning_outcomes": [],
                  "skills": [
                    "Nursing Process"
                  ]
                },
                {
                  "code": "NURS 142",
                  "name": "Pharmacology in Healthcare",
                  "description": "This nursing course is a study of the pharmacotherapy related to the nursing care of clients across the lifespan. The progressive themes of the nursing program are applied through the nursing process to attain the client's optimal well-being.",
                  "learning_outcomes": [],
                  "skills": [
                    "Nursing Process"
                  ]
                },
                {
                  "code": "NURS 143",
                  "name": "Concepts of Pediatric Nursing",
                  "description": "This course continues to build on and expand all previously learned concepts of nursing practice with application to the care of children, their families, and other support persons. Application of new and previously learned nursing concepts, patient care skills, and clinical judgment occurs in a variety of clinical settings.",
                  "learning_outcomes": [],
                  "skills": [
                    "Nursing Process"
                  ]
                },
                {
                  "code": "NURS 143A",
                  "name": "Concepts of Pediatric Nursing - Apprenticeship",
                  "description": "This course continues to build on and expand all previously learned concepts of nursing practice with application to the care of children, their families, and other support persons. Application of new and previously learned nursing concepts, patient care skills, and clinical judgment occurs in a variety of clinical settings. This course is designated for students enrolled in the apprenticeship program.",
                  "learning_outcomes": [],
                  "skills": [
                    "Nursing Process"
                  ]
                },
                {
                  "code": "NURS 144",
                  "name": "Concepts of Adult Health Nursing 3",
                  "description": "This course continues to build on and expand all previously learned concepts of nursing practice with application to the care of adult patients with complicated conditions, their families, and other support persons. Applications of new and previously learned nursing concepts, patient care skills, and clinical judgment occurs in a variety of clinical settings.",
                  "learning_outcomes": [],
                  "skills": [
                    "Nursing Process",
                    "Patient Assessment"
                  ]
                },
                {
                  "code": "NURS 144A",
                  "name": "Concepts of Adult Health Nursing 3 - Apprenticeship",
                  "description": "This course continues to build on and expand all previously learned concepts of nursing practice with application to the care of adult patients with complicated conditions, their families, and other support persons. Applications of new and previously learned nursing concepts, patient care skills, and clinical judgment occurs in a variety of clinical settings. This course is designated for students enrolled in the apprenticeship program.",
                  "learning_outcomes": [],
                  "skills": [
                    "Nursing Process",
                    "Patient Assessment"
                  ]
                },
                {
                  "code": "NURS 174",
                  "name": "Concepts of Adult Health 4",
                  "description": "This culminating course expands the concepts of nursing practice for the acquisition and application of care of adult patients with complex healthcare needs, their families, and other support persons. Application of knowledge, patient care skills, and clinical judgement occurs in a variety of clinical settings and in the simulation library.",
                  "learning_outcomes": [],
                  "skills": [
                    "Nursing Process"
                  ]
                },
                {
                  "code": "NURS 174A",
                  "name": "Concepts of Adult Health 4 - Apprenticeship",
                  "description": "This culminating course expands the concepts of nursing practice for the acquisition and application of care of adult patients with complex healthcare needs, their families, and other support persons. Application of knowledge, patient care skills, and clinical judgement occurs in a variety of clinical settings and in the simulation library. This course is designated for students enrolled in the apprenticeship program.",
                  "learning_outcomes": [],
                  "skills": [
                    "Nursing Process"
                  ]
                },
                {
                  "code": "NURS 175",
                  "name": "Transition to Registered Nursing Practice",
                  "description": "This advanced, comprehensive course provides a synthesis of all concepts and nursing content taught throughout the program with application in the simulation lab. This course enables the individual student to recognize areas that need enhancement prior to entering Registered Nursing practice and includes a review for the NCLEX-RN\u00ae and strategies for success.",
                  "learning_outcomes": [],
                  "skills": [
                    "Nursing Process"
                  ]
                },
                {
                  "code": "NURS 175A",
                  "name": "Transition to Registered Nursing Practice - Apprenticeship",
                  "description": "This advanced, comprehensive course provides a synthesis of all concepts and nursing content taught throughout the program with application in the simulation lab. This course enables the individual student to recognize areas that need enhancement prior to entering Registered Nursing practice and includes a review for the NCLEX-RN\u00ae and strategies for success. This course is designated for students enrolled in the apprenticeship program.",
                  "learning_outcomes": [],
                  "skills": [
                    "Nursing Process"
                  ]
                },
                {
                  "code": "NURS 220",
                  "name": "Perioperative Nursing",
                  "description": "This is an elective course in perioperative nursing. This course is designed to prepare a competent and knowledgeable practitioner to administer optimum care to select surgical patients during pre-operative, intra-operative, and post-operative phases of surgical intervention.",
                  "learning_outcomes": [],
                  "skills": [
                    "Nursing Process"
                  ]
                },
                {
                  "code": "NURS 220A",
                  "name": "Perioperative Nursing (Apprenticeship)",
                  "description": "This is an elective course in perioperative nursing for the nursing student in the apprenticeship program. This course is designed to prepare a competent and knowledgeable practitioner to administer optimum care to select surgical patients during pre-operative, intra-operative, and post-operative phases of surgical intervention for nursing apprenticeship students.",
                  "learning_outcomes": [],
                  "skills": [
                    "Nursing Process"
                  ]
                },
                {
                  "code": "NURS 260",
                  "name": "Nursing Assistant",
                  "description": "This course is designed to prepare the student as an entry-level worker, providing basic nursing care to patients in acute care and long-term care settings. The curriculum is structured to provide theory and application in skills needed to function as a Nursing Assistant. Upon completion, students will be eligible to take the state certification examination. *All students are required to submit to, and pass, a background and drug screen. Our partnered health care agencies will not accept any student with a flagged background for placement. Students with a flagged background must expunge their record prior to registering in the course. Other clinical requirements include immunizations, physical, fingerprints, and American Heart Association Health Care Provider CPR Certification, prior to the initiation of the clinical rotation.",
                  "learning_outcomes": [],
                  "skills": [
                    "Infection Control"
                  ]
                },
                {
                  "code": "NURS 400",
                  "name": "Nursing Skills Lab",
                  "description": "This course provides the student an opportunity for additional directed learning and supervised laboratory time to develop and refine nursing clinical skills necessary to the safe clinical practice of professional nursing. The student will gain knowledge from instructor demonstration, a variety of electronic media, computers and simulation.",
                  "learning_outcomes": [],
                  "skills": [
                    "Nursing Process"
                  ]
                }
              ],
              "aligned_skills": [
                "Infection Control",
                "Nursing Process",
                "Patient Assessment"
              ]
            }
          ],
          "student_composition": "Students in the Nursing program are completing coursework in the clinical competencies this occupation requires. They are preparing to enter a regional labor market where registered nursing roles carry a median wage of $129,360 annually and 2,160 openings occur each year. Students pursuing public health pathways stand to benefit most directly from curriculum shaped by Fresno County Department of Public Health's operational requirements.",
          "student_evidence": {
            "total_in_program": 396,
            "with_all_core_skills": 28,
            "top_students": [
              {
                "uuid": "beffeb84-ecb7-5e90-8baf-4ff412458a07",
                "display_number": 1,
                "primary_focus": "Nursing",
                "courses_completed": 2,
                "gpa": 3.5,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "NURS 144",
                    "name": "Concepts of Adult Health Nursing 3",
                    "grade": "B",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "NURS 260",
                    "name": "Nursing Assistant",
                    "grade": "B",
                    "term": "2025-Spring"
                  }
                ],
                "relevant_skills": [
                  "Infection Control",
                  "Nursing Process",
                  "Patient Assessment"
                ]
              },
              {
                "uuid": "b3e7ad69-99f5-5270-a078-415632cb0916",
                "display_number": 2,
                "primary_focus": "Nursing",
                "courses_completed": 6,
                "gpa": 3.5,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "NURS 220",
                    "name": "Perioperative Nursing",
                    "grade": "A",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "NURS 175",
                    "name": "Transition to Registered Nursing Practice",
                    "grade": "B",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "NURS 144",
                    "name": "Concepts of Adult Health Nursing 3",
                    "grade": "A",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "NURS 134A",
                    "name": "Concepts of Adult Health Nursing 2 - Apprenticeship",
                    "grade": "B",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "NURS 121A",
                    "name": "Fundamentals for Nursing - Apprenticeship",
                    "grade": "A",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "NURS 260",
                    "name": "Nursing Assistant",
                    "grade": "A",
                    "term": "2024-Winter"
                  }
                ],
                "relevant_skills": [
                  "Infection Control",
                  "Nursing Process",
                  "Patient Assessment"
                ]
              },
              {
                "uuid": "65028638-5338-56c9-b4c2-eec535ccff93",
                "display_number": 3,
                "primary_focus": "Nursing",
                "courses_completed": 6,
                "gpa": 3.47,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "NURS 175A",
                    "name": "Transition to Registered Nursing Practice - Apprenticeship",
                    "grade": "B",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "NURS 174A",
                    "name": "Concepts of Adult Health 4 - Apprenticeship",
                    "grade": "A",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "NURS 144A",
                    "name": "Concepts of Adult Health Nursing 3 - Apprenticeship",
                    "grade": "A",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "NURS 144",
                    "name": "Concepts of Adult Health Nursing 3",
                    "grade": "B",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "NURS 135",
                    "name": "Concepts of Nursing Care of the Pregnant Family and the Neonate",
                    "grade": "A",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "NURS 260",
                    "name": "Nursing Assistant",
                    "grade": "C",
                    "term": "2024-Fall"
                  }
                ],
                "relevant_skills": [
                  "Infection Control",
                  "Nursing Process",
                  "Patient Assessment"
                ]
              },
              {
                "uuid": "bc4adc33-787d-5b72-85aa-76e73e15d2fb",
                "display_number": 4,
                "primary_focus": "Nursing",
                "courses_completed": 5,
                "gpa": 3.33,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "NURS 220",
                    "name": "Perioperative Nursing",
                    "grade": "A",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "NURS 135A",
                    "name": "Concepts of Nursing Care of the Pregnant Family and the Neonate - Apprenticeship",
                    "grade": "A",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "NURS 134",
                    "name": "Concepts of Adult Health Nursing 2",
                    "grade": "A",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "NURS 121",
                    "name": "Fundamentals for Nursing",
                    "grade": "B",
                    "term": "2022-Fall"
                  },
                  {
                    "code": "NURS 260",
                    "name": "Nursing Assistant",
                    "grade": "B",
                    "term": "2023-Fall"
                  }
                ],
                "relevant_skills": [
                  "Infection Control",
                  "Nursing Process",
                  "Patient Assessment"
                ]
              },
              {
                "uuid": "177ddba1-8a88-5523-9e95-84cecbe4a331",
                "display_number": 5,
                "primary_focus": "Nursing",
                "courses_completed": 6,
                "gpa": 3.33,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "NURS 220",
                    "name": "Perioperative Nursing",
                    "grade": "A",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "NURS 175",
                    "name": "Transition to Registered Nursing Practice",
                    "grade": "A",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "NURS 134",
                    "name": "Concepts of Adult Health Nursing 2",
                    "grade": "B",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "NURS 133",
                    "name": "Concepts of Mental Health and Psychiatric Nursing",
                    "grade": "A",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "NURS 123A",
                    "name": "Critical Thinking/Clinical Judgement in Nursing - Apprenticeship",
                    "grade": "B",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "NURS 260",
                    "name": "Nursing Assistant",
                    "grade": "B",
                    "term": "2023-Winter"
                  }
                ],
                "relevant_skills": [
                  "Infection Control",
                  "Nursing Process",
                  "Patient Assessment"
                ]
              },
              {
                "uuid": "27b8dd74-dd8c-5bb0-902e-a787f3b589e5",
                "display_number": 6,
                "primary_focus": "Nursing",
                "courses_completed": 6,
                "gpa": 3.29,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "NURS 175",
                    "name": "Transition to Registered Nursing Practice",
                    "grade": "B",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "NURS 144",
                    "name": "Concepts of Adult Health Nursing 3",
                    "grade": "B",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "NURS 124A",
                    "name": "Concepts of Adult Health Nursing 1 - Apprenticeship",
                    "grade": "B",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "NURS 124",
                    "name": "Concepts of Adult Health Nursing 1",
                    "grade": "A",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "NURS 123A",
                    "name": "Critical Thinking/Clinical Judgement in Nursing - Apprenticeship",
                    "grade": "B",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "NURS 260",
                    "name": "Nursing Assistant",
                    "grade": "B",
                    "term": "2024-Spring"
                  }
                ],
                "relevant_skills": [
                  "Infection Control",
                  "Nursing Process",
                  "Patient Assessment"
                ]
              },
              {
                "uuid": "4f41a8bd-0c1e-51b8-a938-a8fd3d540ae5",
                "display_number": 7,
                "primary_focus": "Nursing",
                "courses_completed": 5,
                "gpa": 3.26,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "NURS 220A",
                    "name": "Perioperative Nursing (Apprenticeship)",
                    "grade": "A",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "NURS 175A",
                    "name": "Transition to Registered Nursing Practice - Apprenticeship",
                    "grade": "A",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "NURS 134",
                    "name": "Concepts of Adult Health Nursing 2",
                    "grade": "B",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "NURS 124A",
                    "name": "Concepts of Adult Health Nursing 1 - Apprenticeship",
                    "grade": "B",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "NURS 260",
                    "name": "Nursing Assistant",
                    "grade": "B",
                    "term": "2023-Fall"
                  }
                ],
                "relevant_skills": [
                  "Infection Control",
                  "Nursing Process",
                  "Patient Assessment"
                ]
              },
              {
                "uuid": "06f9a34d-0e9c-5096-93bf-8a8d4882213a",
                "display_number": 8,
                "primary_focus": "Nursing",
                "courses_completed": 7,
                "gpa": 3.25,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "NURS 144A",
                    "name": "Concepts of Adult Health Nursing 3 - Apprenticeship",
                    "grade": "B",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "NURS 143",
                    "name": "Concepts of Pediatric Nursing",
                    "grade": "A",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "NURS 123A",
                    "name": "Critical Thinking/Clinical Judgement in Nursing - Apprenticeship",
                    "grade": "A",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "NURS 123",
                    "name": "Critical Thinking/Clinical Judgement in Nursing",
                    "grade": "B",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "PM 203",
                    "name": "Paramedic Field Internship",
                    "grade": "A",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "NURS 260",
                    "name": "Nursing Assistant",
                    "grade": "A",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "BIOL 040",
                    "name": "General Microbiology",
                    "grade": "B",
                    "term": "2025-Spring"
                  }
                ],
                "relevant_skills": [
                  "Infection Control",
                  "Nursing Process",
                  "Patient Assessment"
                ]
              },
              {
                "uuid": "909da930-ff11-5640-b1d0-936859fef823",
                "display_number": 9,
                "primary_focus": "Nursing",
                "courses_completed": 6,
                "gpa": 3.2,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "NURS 220A",
                    "name": "Perioperative Nursing (Apprenticeship)",
                    "grade": "B",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "NURS 175A",
                    "name": "Transition to Registered Nursing Practice - Apprenticeship",
                    "grade": "B",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "NURS 144A",
                    "name": "Concepts of Adult Health Nursing 3 - Apprenticeship",
                    "grade": "A",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "NURS 135A",
                    "name": "Concepts of Nursing Care of the Pregnant Family and the Neonate - Apprenticeship",
                    "grade": "A",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "NURS 123",
                    "name": "Critical Thinking/Clinical Judgement in Nursing",
                    "grade": "A",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "NURS 260",
                    "name": "Nursing Assistant",
                    "grade": "B",
                    "term": "2024-Spring"
                  }
                ],
                "relevant_skills": [
                  "Infection Control",
                  "Nursing Process",
                  "Patient Assessment"
                ]
              },
              {
                "uuid": "be0fc6f3-7415-5589-b579-c3762579c73b",
                "display_number": 10,
                "primary_focus": "Nursing",
                "courses_completed": 6,
                "gpa": 3.19,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "NURS 220",
                    "name": "Perioperative Nursing",
                    "grade": "B",
                    "term": "2022-Fall"
                  },
                  {
                    "code": "NURS 144",
                    "name": "Concepts of Adult Health Nursing 3",
                    "grade": "A",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "NURS 143",
                    "name": "Concepts of Pediatric Nursing",
                    "grade": "A",
                    "term": "2022-Fall"
                  },
                  {
                    "code": "NURS 142",
                    "name": "Pharmacology in Healthcare",
                    "grade": "B",
                    "term": "2022-Fall"
                  },
                  {
                    "code": "NURS 121A",
                    "name": "Fundamentals for Nursing - Apprenticeship",
                    "grade": "A",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "NURS 260",
                    "name": "Nursing Assistant",
                    "grade": "A",
                    "term": "2022-Winter"
                  }
                ],
                "relevant_skills": [
                  "Infection Control",
                  "Nursing Process",
                  "Patient Assessment"
                ]
              }
            ]
          }
        },
        "roadmap": "A working group between the Nursing department chair and Fresno County Department of Public Health nursing leadership could evaluate how community health outreach and disease surveillance are currently addressed across clinical coursework. One potential starting point is identifying practicum or simulation opportunities where students engage with communicable disease reporting or community prevention outreach. Revised content could be piloted within the next catalog cycle.",
        "selected_occupations": [],
        "advisory_thesis": "",
        "agenda_topics": []
      },
      "engagementType": "curriculum_codesign",
      "collegeId": "College of the Sequoias",
      "savedAt": "2026-04-20T00:00:00.000Z",
      "status": "saved",
      "schemaVersion": 8
    }
  ],
  "College of the Desert": [
    {
      "id": "seed-desert-advisory-01",
      "proposal": {
        "employer": "Abbott Vascular",
        "sector": "Manufacturing",
        "partnership_type": "Advisory Board",
        "selected_occupation": "Bioengineers and Biomedical Engineers",
        "selected_soc_code": "17-2031",
        "core_skills": [
          "Design",
          "Biology",
          "Mechanical Systems",
          "Troubleshooting",
          "Electrical Systems"
        ],
        "gap_skill": "",
        "regions": [
          "Inland Empire / Desert"
        ],
        "opportunity": "Abbott Vascular's work designing and manufacturing life-critical interventional devices under FDA quality system requirements makes it a compelling advisory board partner for College of the Desert's engineering and science programs. The company's production environment integrates design precision, mechanical systems, and regulatory compliance into daily workflows across roles spanning biomedical engineering, mechanical engineering, and equipment repair. An advisory board formalization would give these programs a sustained channel for industry perspective at no grant funding cost.",
        "opportunity_evidence": [
          {
            "title": "Medical Equipment Repairers",
            "soc_code": "49-9062",
            "annual_wage": 67310,
            "employment": 490,
            "annual_openings": 50,
            "growth_rate": 0.092108863
          },
          {
            "title": "Mechanical Engineers",
            "soc_code": "17-2141",
            "annual_wage": 101720,
            "employment": 1520,
            "annual_openings": 110,
            "growth_rate": 0.07621993
          },
          {
            "title": "Bioengineers and Biomedical Engineers",
            "soc_code": "17-2031",
            "annual_wage": 122540,
            "employment": 110,
            "annual_openings": 10,
            "growth_rate": 0.013311777
          }
        ],
        "justification": {
          "curriculum_composition": "The Engineering Technology and Engineering, General departments provide the closest curricular match to Abbott Vascular's workforce operations. Engineering Technology builds design, electrical systems, and troubleshooting competencies that map directly to the equipment repair and production support roles Abbott fills. Engineering, General extends that foundation into mechanical systems and design, reflecting the integrated technical preparation that device manufacturing environments require.",
          "curriculum_evidence": [
            {
              "department": "Engineering Technology",
              "courses": [
                {
                  "code": "ENGT 020",
                  "name": "DC Circuit Analysis I",
                  "description": "This is the first course in a two-part series in Direct Current (DC) circuit analysis. Topics to be covered include Ohm's Law, series and parallel circuit analysis, voltage and current dividers.",
                  "learning_outcomes": [],
                  "skills": [
                    "Electrical Systems"
                  ]
                },
                {
                  "code": "ENGT 021",
                  "name": "DC Circuit Analysis II",
                  "description": "This is the second course in a two-part series of DC Circuit Analysis courses. Topics covered in this course include: Ohm's Law, series and parallel circuit analysis, voltage and current dividers, Kirchhoff's laws, magnetic circuits, and network theorems.",
                  "learning_outcomes": [],
                  "skills": [
                    "Electrical Systems"
                  ]
                },
                {
                  "code": "ENGT 022",
                  "name": "AC Circuit Analysis I",
                  "description": "This course is an in depth study in Alternating Current (AC) circuit analysis. Topics to be covered include AC generation and transformation, inductance and inductive circuits, capacitance and capacitive circuits, time constants, rectangular and polar notation, AC circuit analysis, resonance, and filters.",
                  "learning_outcomes": [],
                  "skills": [
                    "Electrical Systems"
                  ]
                },
                {
                  "code": "ENGT 024",
                  "name": "Manufacturing of Circuits",
                  "description": "This course covers electronic schematic capture, simulation, export to printed circuit board design, layout and auto-routing software. It includes basic Computer Aided Design (CAD) drafting, block diagrams, library component templates, and printed circuit baord (PCB) design, fabrication, and assembly, using through-hole and surface-mount technology and devices (SMT and SMD).",
                  "learning_outcomes": [],
                  "skills": [
                    "Design"
                  ]
                },
                {
                  "code": "ENGT 030",
                  "name": "PLCs and Industrial Controls I",
                  "description": "This course offers students the fundamentals of a Programmable Logic Controller (PLC). Students learn the basic parts of a PLC system, digital fundamentals, and PLC addressing.",
                  "learning_outcomes": [],
                  "skills": [
                    "Electrical Systems"
                  ]
                },
                {
                  "code": "ENGT 060",
                  "name": "Industrial Electronics",
                  "description": "This course includes basic topics related to industrial electronics. A brief review of analog circuits is expanded upon to develop more advanced circuit concepts. Topics include FETs, SCRs, basic components involved in motor control, DC and AC motors, and their controller circuits will be covered. Operational amplifiers will be covered, and their applications to sensor instrumentation. Transducers and applications to various sensors for heat, flow, force, etc. will be developed. Troubleshooting techniques for the above topics will be incorporated with each section.",
                  "learning_outcomes": [],
                  "skills": [
                    "Electrical Systems",
                    "Troubleshooting"
                  ]
                },
                {
                  "code": "ENGT 061",
                  "name": "Industrial Sensors and Advanced Applications",
                  "description": "Course includes topics related to basic process instrumentation and control. A brief review of industrial electronics is expanded upon to develop more advanced process instrumentation and control concepts. Topics include advanced applications of components used in both DC and AC motor control, recorders, control valves and actuators, temperature sensors, pressure sensors, level sensors, flow sensors and instrumentation maintenance techniques.",
                  "learning_outcomes": [],
                  "skills": [
                    "Electrical Systems"
                  ]
                }
              ],
              "aligned_skills": [
                "Design",
                "Electrical Systems",
                "Troubleshooting"
              ]
            },
            {
              "department": "Engineering, General",
              "courses": [
                {
                  "code": "ENGR 006A",
                  "name": "Electric Circuits for Engineering & Science",
                  "description": "This course is the first semester of a one year course designed to provide students with a broad knowledge of the theoretical background and experimental application of modern electronic devices and circuitry. It covers basic electronic concepts, solid state devices such as diodes and transistors, and an introduction to basic analog and digital circuit design and analysis emphasizing practical applications, including Ohm's Law and Kirchhoff's laws; nodal and loop analysis; analysis of linear circuits; network theorems; transients in RLC circuits; sinusoidal steady-state analysis and application of PSPICE to circuit analysis. (Equivalent to PH 006A.)",
                  "learning_outcomes": [],
                  "skills": [
                    "Electrical Systems"
                  ]
                },
                {
                  "code": "ENGR 009",
                  "name": "Introduction to Engineering",
                  "description": "This course is a basic introduction to Engineering and its different fields. Covers procedures and pathways to reach full academic potential in each student's field of choice. Discusses ethics and communication skills while applying design and analysis techniques to projects from various areas of engineering. This course is intended for students pursuing a degree in engineering. (C-ID ENGR 110)",
                  "learning_outcomes": [],
                  "skills": [
                    "Design"
                  ]
                },
                {
                  "code": "ENGR 011",
                  "name": "Statics",
                  "description": "This course is an introduction to the analysis of forces on engineering structures in equilibrium. Vector analysis is utilized to study two- and three-dimensional frames, machines, and trusses. Principles of friction, centroids, center of gravity, and moment of inertia for areas and masses are applied to analyze complex real-world problems. (Equivalent to PH 011.)",
                  "learning_outcomes": [],
                  "skills": [
                    "Mechanical Systems"
                  ]
                },
                {
                  "code": "ENGR 012",
                  "name": "Dynamics",
                  "description": "This course is intended for engineering majors planning to transfer to four-year institutions. It covers the fundamentals of kinematics and kinetics of particles and rigid bodies. Topics include kinematics of particle motion, Newton's Second Law, planar and three dimensional motion of rigid bodies, momentum and energy principles for rigid body motion, and an introduction to vibrations and oscillations. (Equivalent to PH 012.)",
                  "learning_outcomes": [],
                  "skills": [
                    "Mechanical Systems"
                  ]
                }
              ],
              "aligned_skills": [
                "Design",
                "Electrical Systems",
                "Mechanical Systems"
              ]
            },
            {
              "department": "Biology",
              "courses": [
                {
                  "code": "BI 004",
                  "name": "Elements of Biology",
                  "description": "An introduction to biology for non-science majors including the study of plants, animals, ecology, and evolution. The foundations of biology, including biochemistry, cell biology, genetics, anatomy and physiology, and the impact of humans on the environment will be covered in this course.",
                  "learning_outcomes": [],
                  "skills": [
                    "Biology"
                  ]
                },
                {
                  "code": "BI 005",
                  "name": "Molecular and Cell Biology",
                  "description": "This course presents a survey of basic biological principles with a strong emphasis on biochemistry, cell biology and genetics. Topics include: structure and function of prokaryotic and eukaryotic cells, origin and evolution of cellular life and molecular evolution, organelle structure and function, membrane structure and function, cellular transport, cellular chemistry and biomolecules, cellular metabolism (respiration and photosynthesis), cell reproduction and its controls, cell communication, classic and molecular genetics, DNA structure and function, gene structure, gene expression and control of gene expression, biotechnology, and scientific inquiry. This course is primarily designed for students pursuing careers in science, medicine, dentistry, veterinary medicine and other health fields requiring a strong foundation in biology. Together, BI 005 and BI 006, Biology of Organisms, provide students with the basic biology core curriculum for transfer. (C-ID BIOL 190; BIOL 135S)",
                  "learning_outcomes": [],
                  "skills": [
                    "Biology"
                  ]
                },
                {
                  "code": "BI 006",
                  "name": "Biology of Organisms",
                  "description": "This course covers classification, development, physiology and regulation at the organismal level. Additional topics include population dynamics, community ecology, evolution, and population genetics. This course is primarily designed for students pursuing careers in science, medicine, dentistry, veterinary medicine and other health fields requiring a strong foundation in biology. Together, BI-006 and BI-005, Molecular and Cell Biology, provide students with the basic biology core curriculum for transfer. (C-ID BIOL 140; BIOL 135S)",
                  "learning_outcomes": [],
                  "skills": [
                    "Biology"
                  ]
                },
                {
                  "code": "BI 007",
                  "name": "Biology of Mammals",
                  "description": "This course covers classification, development, physiology, and regulation of mammals. Additional topics covered include zoogeography, echolocation, domestication, conservation ethics, and diseases and zoonoses. This course is primarily designed for students pursuing careers in science, veterinary medicine, and other fields requiring a strong foundation in biology.",
                  "learning_outcomes": [],
                  "skills": [
                    "Biology"
                  ]
                },
                {
                  "code": "BI 007L",
                  "name": "Biology of Mammals Lab",
                  "description": "This course covers classification, development, physiology, and regulation of mammals. Additional topics covered include: zoogeography, evolution, identification of mammals based on skulls and teeth, and anatomy. This course is designed for students obtaining a general elective in natural science, as well as students pursuing careers in science, veterinary medicine, and other fields requiring a strong foundation in biology.",
                  "learning_outcomes": [],
                  "skills": [
                    "Biology"
                  ]
                },
                {
                  "code": "BI 011",
                  "name": "Biology of Viruses",
                  "description": "This course is designed for science and non-science major students. The course emphasizes molecular and cellular biology, epidemiology, and development of diseases caused by human viruses. This includes the study of viral structure, classification, natural viral habitats, viral replication methods, host immune responses to viral infections, human viral diseases, viral isolation techniques, immunization and treatments. The scientific method is introduced and specific examples of its application to the study of viruses are included.",
                  "learning_outcomes": [],
                  "skills": [
                    "Biology"
                  ]
                },
                {
                  "code": "BI 013",
                  "name": "Human Anatomy and Physiology I",
                  "description": "This course involves an integrated study of human body organization and function. Topics include anatomical terminology, cells and tissues, the integumentary system, the skeletal system, articulations, the muscular system, the nervous system, and special senses. This is the first part of a two-course sequence that studies the fundamental concepts of anatomy and physiology and provides a foundation for advanced study of the human body. Both BI 013 and BI 014 must be taken to study all of the major body systems. This two-course sequence is designed to meet the prerequisites for health professional programs, e.g. nursing, physical therapy. (C-ID BIOL 115BS)",
                  "learning_outcomes": [],
                  "skills": [
                    "Biology"
                  ]
                },
                {
                  "code": "BI 014",
                  "name": "Human Anatomy and Physiology II",
                  "description": "This course involves an integrated study of human body organization and function. Topics include the endocrine, immune, cardiovascular, respiratory, digestive, urinary and reproductive systems. This is the second part of a two-course sequence that studies the fundamental concepts of anatomy and physiology and provides a foundation for advanced study of the human body. Both BI 013 and BI 014 must be taken to study all of the major body systems. This two-course sequence is designed to meet the prerequisites for health professional programs; e.g. nursing, physical therapy. (C-ID BIOL 115BS)",
                  "learning_outcomes": [],
                  "skills": [
                    "Biology"
                  ]
                },
                {
                  "code": "BI 015",
                  "name": "General Microbiology",
                  "description": "This course is a comprehensive study of the microbial world. It is designed to develop an appreciation and understanding of microorganisms and their relationship to humans and their environment. A knowledge of the principles of microbiology and their practical applications is stressed. Subject matter includes medical microbiology, microbial physiology, microbial genetics, and industrial microbiology. The laboratory experience explores the development of current methods, techniques, and skills necessary to culture, propagate and identify micro-organisms.",
                  "learning_outcomes": [],
                  "skills": [
                    "Biology"
                  ]
                }
              ],
              "aligned_skills": [
                "Biology"
              ]
            }
          ],
          "student_composition": "Students across the Engineering Technology and Engineering, General programs are developing applied technical skills in design, electrical systems, mechanical systems, and troubleshooting. The Biology department adds a parallel pipeline of students grounding their preparation in the biological sciences that underpin device performance and biocompatibility. Together these programs represent a multi-pathway student population whose preparation spans the technical and scientific dimensions of Abbott Vascular's workforce.",
          "student_evidence": {
            "total_in_program": 292,
            "with_all_core_skills": 3,
            "top_students": [
              {
                "uuid": "daa83562-fe42-5412-9b71-da4d1127ea94",
                "display_number": 1,
                "primary_focus": "Engineering, General",
                "courses_completed": 6,
                "gpa": 3.19,
                "matching_skills": 5,
                "enrollments": [
                  {
                    "code": "ENGR 009",
                    "name": "Introduction to Engineering",
                    "grade": "A",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "ENGR 006A",
                    "name": "Electric Circuits for Engineering & Science",
                    "grade": "B",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "BI 006",
                    "name": "Biology of Organisms",
                    "grade": "A",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "ENGR 012",
                    "name": "Dynamics",
                    "grade": "A",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "ENGR 011",
                    "name": "Statics",
                    "grade": "A",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "AGEH 046L",
                    "name": "Landscape Irrigation Systems Lab",
                    "grade": "A",
                    "term": "2025-Spring"
                  }
                ],
                "relevant_skills": [
                  "Biology",
                  "Design",
                  "Electrical Systems",
                  "Mechanical Systems",
                  "Troubleshooting"
                ]
              },
              {
                "uuid": "3825fd13-9c25-525c-9eb5-269901582080",
                "display_number": 2,
                "primary_focus": "Biology",
                "courses_completed": 8,
                "gpa": 2.84,
                "matching_skills": 5,
                "enrollments": [
                  {
                    "code": "DRA 011",
                    "name": "Intro to Sketchup & Revit",
                    "grade": "B",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "ACR 064",
                    "name": "Air Conditioning & Refrigeration Electricity I",
                    "grade": "B",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "BI 015",
                    "name": "General Microbiology",
                    "grade": "A",
                    "term": "2022-Fall"
                  },
                  {
                    "code": "BI 011",
                    "name": "Biology of Viruses",
                    "grade": "W",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "BI 006",
                    "name": "Biology of Organisms",
                    "grade": "D",
                    "term": "2022-Fall"
                  },
                  {
                    "code": "BI 005",
                    "name": "Molecular and Cell Biology",
                    "grade": "C",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "BI 014",
                    "name": "Human Anatomy and Physiology II",
                    "grade": "A",
                    "term": "2022-Fall"
                  },
                  {
                    "code": "AUTO 013A",
                    "name": "Automotive Braking Systems",
                    "grade": "B",
                    "term": "2024-Spring"
                  }
                ],
                "relevant_skills": [
                  "Biology",
                  "Design",
                  "Electrical Systems",
                  "Mechanical Systems",
                  "Troubleshooting"
                ]
              },
              {
                "uuid": "6102e1b7-9ba8-5b4c-90e7-4719ac1eeb6a",
                "display_number": 3,
                "primary_focus": "Biology",
                "courses_completed": 9,
                "gpa": 2.1,
                "matching_skills": 5,
                "enrollments": [
                  {
                    "code": "DRA 011",
                    "name": "Intro to Sketchup & Revit",
                    "grade": "F",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "ART 021A",
                    "name": "Beginning Watercolor Painting",
                    "grade": "B",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "AUTO 016",
                    "name": "Automotive Manual Transmissions & Drive Train Systems",
                    "grade": "C",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "BI 015",
                    "name": "General Microbiology",
                    "grade": "A",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "BI 011",
                    "name": "Biology of Viruses",
                    "grade": "A",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "BI 007L",
                    "name": "Biology of Mammals Lab",
                    "grade": "C",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "BI 004",
                    "name": "Elements of Biology",
                    "grade": "B",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "BI 005",
                    "name": "Molecular and Cell Biology",
                    "grade": "W",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "BI 014",
                    "name": "Human Anatomy and Physiology II",
                    "grade": "F",
                    "term": "2023-Winter"
                  }
                ],
                "relevant_skills": [
                  "Biology",
                  "Design",
                  "Electrical Systems",
                  "Mechanical Systems",
                  "Troubleshooting"
                ]
              },
              {
                "uuid": "aa128ffa-418e-5036-bed6-b04f47caf763",
                "display_number": 4,
                "primary_focus": "Engineering, General",
                "courses_completed": 7,
                "gpa": 3.82,
                "matching_skills": 4,
                "enrollments": [
                  {
                    "code": "ARCH 150",
                    "name": "Foundation Digital Design",
                    "grade": "A",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "ART 004",
                    "name": "Three-Dimensional Design",
                    "grade": "A",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "ENGR 009",
                    "name": "Introduction to Engineering",
                    "grade": "A",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "ENGR 006A",
                    "name": "Electric Circuits for Engineering & Science",
                    "grade": "C",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "ENGR 012",
                    "name": "Dynamics",
                    "grade": "A",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "ENGR 011",
                    "name": "Statics",
                    "grade": "A",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "AUTO 040E",
                    "name": "CNG Diagnosis & Repair",
                    "grade": "A",
                    "term": "2024-Spring"
                  }
                ],
                "relevant_skills": [
                  "Design",
                  "Electrical Systems",
                  "Mechanical Systems",
                  "Troubleshooting"
                ]
              },
              {
                "uuid": "5fbe976b-2ed9-56f1-95ec-ac0564672d99",
                "display_number": 5,
                "primary_focus": "Biology",
                "courses_completed": 7,
                "gpa": 3.09,
                "matching_skills": 4,
                "enrollments": [
                  {
                    "code": "ART 014A",
                    "name": "Beginning Screen Printing",
                    "grade": "A",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "BI 015",
                    "name": "General Microbiology",
                    "grade": "A",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "BI 007",
                    "name": "Biology of Mammals",
                    "grade": "C",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "BI 004",
                    "name": "Elements of Biology",
                    "grade": "A",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "BI 006",
                    "name": "Biology of Organisms",
                    "grade": "D",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "BI 005",
                    "name": "Molecular and Cell Biology",
                    "grade": "W",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "AUTO 012A",
                    "name": "Automotive Suspension & Steering Systems",
                    "grade": "B",
                    "term": "2025-Spring"
                  }
                ],
                "relevant_skills": [
                  "Biology",
                  "Design",
                  "Mechanical Systems",
                  "Troubleshooting"
                ]
              },
              {
                "uuid": "4ea362e8-50f3-58f9-925e-673582d0c259",
                "display_number": 6,
                "primary_focus": "Engineering, General",
                "courses_completed": 6,
                "gpa": 3.09,
                "matching_skills": 4,
                "enrollments": [
                  {
                    "code": "DDP 106",
                    "name": "Generative AI for Creatives",
                    "grade": "F",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "ENGR 009",
                    "name": "Introduction to Engineering",
                    "grade": "A",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "ENGR 006A",
                    "name": "Electric Circuits for Engineering & Science",
                    "grade": "A",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "HSAD 004",
                    "name": "Biomedical Pharmacology",
                    "grade": "B",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "ENGR 012",
                    "name": "Dynamics",
                    "grade": "C",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "ENGR 011",
                    "name": "Statics",
                    "grade": "A",
                    "term": "2024-Spring"
                  }
                ],
                "relevant_skills": [
                  "Biology",
                  "Design",
                  "Electrical Systems",
                  "Mechanical Systems"
                ]
              },
              {
                "uuid": "0f157b8e-b7a4-59ef-954f-5106352b5db2",
                "display_number": 7,
                "primary_focus": "Biology",
                "courses_completed": 8,
                "gpa": 2.97,
                "matching_skills": 4,
                "enrollments": [
                  {
                    "code": "AUTO 018",
                    "name": "Automotive Heating, Ventilation & Air Conditioning",
                    "grade": "C",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "G 002",
                    "name": "Historical Geology with Laboratory",
                    "grade": "A",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "BI 011",
                    "name": "Biology of Viruses",
                    "grade": "C",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "BI 004",
                    "name": "Elements of Biology",
                    "grade": "A",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "BI 006",
                    "name": "Biology of Organisms",
                    "grade": "W",
                    "term": "2022-Fall"
                  },
                  {
                    "code": "BI 005",
                    "name": "Molecular and Cell Biology",
                    "grade": "A",
                    "term": "2022-Fall"
                  },
                  {
                    "code": "BI 013",
                    "name": "Human Anatomy and Physiology I",
                    "grade": "F",
                    "term": "2022-Fall"
                  },
                  {
                    "code": "CS 008",
                    "name": "Computer Architecture and Organization",
                    "grade": "B",
                    "term": "2024-Fall"
                  }
                ],
                "relevant_skills": [
                  "Biology",
                  "Electrical Systems",
                  "Mechanical Systems",
                  "Troubleshooting"
                ]
              },
              {
                "uuid": "a2a79021-0a81-50f6-987e-b7a5126162e4",
                "display_number": 8,
                "primary_focus": "Engineering, General",
                "courses_completed": 6,
                "gpa": 2.8,
                "matching_skills": 4,
                "enrollments": [
                  {
                    "code": "ACR 084",
                    "name": "Boiler & Hydronic Heating",
                    "grade": "B",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "ENGR 009",
                    "name": "Introduction to Engineering",
                    "grade": "C",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "ENGR 006A",
                    "name": "Electric Circuits for Engineering & Science",
                    "grade": "A",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "ENGR 012",
                    "name": "Dynamics",
                    "grade": "C",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "ENGR 011",
                    "name": "Statics",
                    "grade": "A",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "AUTO 014A",
                    "name": "Automotive Engine Management",
                    "grade": "B",
                    "term": "2025-Spring"
                  }
                ],
                "relevant_skills": [
                  "Design",
                  "Electrical Systems",
                  "Mechanical Systems",
                  "Troubleshooting"
                ]
              },
              {
                "uuid": "3b4574a2-0c65-5f20-90e9-267427bc6b88",
                "display_number": 9,
                "primary_focus": "Biology",
                "courses_completed": 11,
                "gpa": 2.72,
                "matching_skills": 4,
                "enrollments": [
                  {
                    "code": "ART 004",
                    "name": "Three-Dimensional Design",
                    "grade": "C",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "ACR 065",
                    "name": "Air Conditioning & Refrigeration Electricity II",
                    "grade": "C",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "AUTO 093D",
                    "name": "Diesel Diagnostics & Troubleshooting",
                    "grade": "A",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "AUTO 044C",
                    "name": "Advanced Driver Assist Systems (ADAS) Level 2",
                    "grade": "F",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "AUTO 043A",
                    "name": "Intro to Hybrid, Electric & Fuel-Cell Vehicle Technology",
                    "grade": "A",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "BI 015",
                    "name": "General Microbiology",
                    "grade": "A",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "BI 011",
                    "name": "Biology of Viruses",
                    "grade": "F",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "BI 007",
                    "name": "Biology of Mammals",
                    "grade": "C",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "BI 004",
                    "name": "Elements of Biology",
                    "grade": "A",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "BI 013",
                    "name": "Human Anatomy and Physiology I",
                    "grade": "A",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "AUTO 014A",
                    "name": "Automotive Engine Management",
                    "grade": "A",
                    "term": "2024-Fall"
                  }
                ],
                "relevant_skills": [
                  "Biology",
                  "Design",
                  "Electrical Systems",
                  "Troubleshooting"
                ]
              },
              {
                "uuid": "42b48e2e-5092-5de2-91ec-669b2c64f93f",
                "display_number": 10,
                "primary_focus": "Biology",
                "courses_completed": 7,
                "gpa": 2.17,
                "matching_skills": 4,
                "enrollments": [
                  {
                    "code": "DRA 001",
                    "name": "Technical Drafting I",
                    "grade": "C",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "AUTO 044C",
                    "name": "Advanced Driver Assist Systems (ADAS) Level 2",
                    "grade": "C",
                    "term": "2022-Fall"
                  },
                  {
                    "code": "BI 015",
                    "name": "General Microbiology",
                    "grade": "W",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "BI 007L",
                    "name": "Biology of Mammals Lab",
                    "grade": "W",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "BI 004",
                    "name": "Elements of Biology",
                    "grade": "W",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "BI 006",
                    "name": "Biology of Organisms",
                    "grade": "D",
                    "term": "2022-Fall"
                  },
                  {
                    "code": "BI 013",
                    "name": "Human Anatomy and Physiology I",
                    "grade": "A",
                    "term": "2023-Fall"
                  }
                ],
                "relevant_skills": [
                  "Biology",
                  "Design",
                  "Electrical Systems",
                  "Troubleshooting"
                ]
              }
            ]
          }
        },
        "roadmap": "A quarterly advisory board with Abbott Vascular engineering and quality leadership could give the Engineering Technology and Engineering, General departments ongoing access to regulated manufacturing perspective. Potential starting points for the inaugural meeting include how Abbott structures design documentation and revision control on the production floor, how troubleshooting protocols are shaped by FDA quality system requirements, and where mechanical systems considerations intersect with biological performance criteria in device development.",
        "selected_occupations": [
          "Bioengineers and Biomedical Engineers",
          "Mechanical Engineers",
          "Medical Equipment Repairers"
        ],
        "advisory_thesis": "Abbott Vascular designs and manufactures life-critical interventional devices such as coronary stents and catheters, where engineering precision and regulatory compliance are built directly into production and product development workflows. Exposure to this environment gives students in biomedical, mechanical, and electronics programs a concrete view of how design, troubleshooting, and systems thinking operate under the strict quality and safety standards of medical device manufacturing.",
        "agenda_topics": [
          {
            "topic": "What design documentation and revision control practices do Abbott Vascular engineers follow daily on the production floor?",
            "rationale": "Abbott Vascular's operational standards for design documentation could inform how Engineering Technology and Engineering, General programs sequence and contextualize design coursework within regulated manufacturing environments."
          },
          {
            "topic": "How does Abbott Vascular structure troubleshooting protocols for production equipment to meet FDA quality system requirements?",
            "rationale": "Insight into Abbott Vascular's equipment troubleshooting workflows under regulatory constraints could strengthen how Engineering Technology frames fault-isolation and corrective-action skills in its curriculum."
          },
          {
            "topic": "At what point in device development do mechanical systems considerations intersect with biocompatibility or biological performance requirements?",
            "rationale": "Abbott Vascular's experience integrating mechanical and biological design criteria could help Engineering, General and Biology departments identify meaningful points of coordination in their respective program outcomes."
          }
        ]
      },
      "engagementType": "advisory_board",
      "collegeId": "College of the Desert",
      "savedAt": "2026-04-20T00:00:00.000Z",
      "status": "saved",
      "schemaVersion": 8
    },
    {
      "id": "seed-desert-internship-01",
      "proposal": {
        "employer": "Collins Aerospace",
        "sector": "Manufacturing",
        "partnership_type": "Internship Pipeline",
        "selected_occupation": "Software Developers",
        "selected_soc_code": "15-1252",
        "core_skills": [
          "Software Development",
          "Programming",
          "Algorithms"
        ],
        "gap_skill": "",
        "regions": [
          "Orange County",
          "San Diego / Imperial",
          "Inland Empire / Desert"
        ],
        "opportunity": "Collins Aerospace is a compelling internship partner for College of the Desert's software development programs, with 390 annual openings and 12.7% projected growth among Software Developers across the Inland Empire and Desert region. At $135,210 annually, these roles represent high-wage outcomes directly accessible through an internship pipeline. A structured placement at Collins could give students hands-on experience applying software development and algorithms work within aerospace and defense systems.",
        "opportunity_evidence": [
          {
            "title": "Software Developers",
            "soc_code": "15-1252",
            "annual_wage": 135210,
            "employment": 4860,
            "annual_openings": 390,
            "growth_rate": 0.126706091
          }
        ],
        "justification": {
          "curriculum_composition": "The Computer Information Systems and Computer Science departments provide direct preparation for the technical demands of a Collins Aerospace internship, with coursework spanning software development, programming, and algorithms across a combined 15 courses. The Engineering Technology department extends this preparation into applied programming and software development contexts relevant to aerospace manufacturing environments. The breadth across three departments means Collins would have multiple academic entry points when building an internship cohort.",
          "curriculum_evidence": [
            {
              "department": "Computer Information Systems",
              "courses": [
                {
                  "code": "CIS 010",
                  "name": "Introduction to Information Systems",
                  "description": "Examination of information technologies and information systems used in business. Focus on information systems, database management systems, networking, ethics and security, computer hardware, and software applications and development. Lab sessions on popular software applications and enterprise resource planning systems are provided. (C-ID ITIS 120; BUS 140)",
                  "learning_outcomes": [],
                  "skills": [
                    "Software Development"
                  ]
                },
                {
                  "code": "CIS 023B",
                  "name": "Developing Using AWS Cloud Services",
                  "description": "This course will introduce the fundamentals of developing and deploying applications within the cloud using Amazon Web Services (AWS) technologies. The course delves into topics such as developing using cloud storage, NoSQL, REST APIs, event-driven solutions, containers, caching, messaging services, secure applications, and automated deployment.",
                  "learning_outcomes": [],
                  "skills": [
                    "Software Development"
                  ]
                },
                {
                  "code": "CIS 030",
                  "name": "Introduction to Linux Operating System",
                  "description": "Introduction to the Linux operating system primarily focused on command line usage. Covers the history, kernel, file systems, shells and user utilities. Also introduces students to the fundamentals of shell programming, processes, communications, and basic security.",
                  "learning_outcomes": [],
                  "skills": [
                    "Programming"
                  ]
                },
                {
                  "code": "CIS 055",
                  "name": "Systems and Network Administration",
                  "description": "This course will provide a student with the knowledge and skills at the administrator level to be able to do the job in any environment. The course covers essential hardware and software technologies of on-premise and hybrid server environments including high availability, cloud computing, and scripting. The course includes performance-based questions that require the candidate to demonstrate multi-step knowledge to securely deploy, administer and troubleshoot servers. This course requires the student to build, maintain, troubleshoot and support server hardware and software technologies. The student will be able to identify environmental issues; understand and comply with disaster recovery and physical/software security procedures; become familiar with industry terminology and concepts; understand server roles/specializations and interaction within the overall computing environment. This course will prepare students to take the current version of CompTIA's Server+ Certification exam. C-ID: ITIS 155",
                  "learning_outcomes": [],
                  "skills": [
                    "Programming"
                  ]
                },
                {
                  "code": "CIS 060",
                  "name": "Information Systems Security",
                  "description": "This course ensures that students gain hands-on practical skills, ensuring they are better prepared to problem solve a wider variety of today's complex issues. The baseline cybersecurity skills are applicable across more of today's job roles to secure systems, software, and hardware. This course covers the most core technical skills in risk assessment and management, incident response, forensics, enterprise networks, hybrid/cloud operations, and security controls, ensuring high-performance on the job.",
                  "learning_outcomes": [],
                  "skills": [
                    "Software Development"
                  ]
                },
                {
                  "code": "CIS 080",
                  "name": "Database Management Systems",
                  "description": "This course provides the students with an introduction to the core concepts in data and information management. It is centered around the core skills of identifying organizational information requirements, modeling them using conceptual data modeling techniques, converting the conceptual data models into relational data models and verifying its structural characteristics with normalization techniques, and implementing and utilizing a relational database using an industrial-strength database management system. The course will also include coverage of basic database administration tasks and key concepts of data quality and data security. Moreover, students will develop practical skills in the use of SQL for data design, manipulation, interrogation, and application development. In addition to developing database applications, the course helps the students understand how large-scale packaged systems are highly dependent on the use of Database Management Systems (DBMSs). Building on the transactional database understanding, the course provides an introduction to data and information management technologies that provide decision support capabilities under the broad business intelligence umbrella. C-ID: ITIS 180",
                  "learning_outcomes": [],
                  "skills": [
                    "Software Development"
                  ]
                },
                {
                  "code": "CIS 085C",
                  "name": "Dynamic Website Design",
                  "description": "This course teaches the fundamentals of client-side and server-side web programming, using JavaScript, PHP, Perl and MySQL. Students learn how to understand and use simple variables, proper programming syntax, arithmetic and string operations, conditional and logical operators, functions and subroutines, loops and arrays, data file operations and database concepts",
                  "learning_outcomes": [],
                  "skills": [
                    "Algorithms",
                    "Programming"
                  ]
                },
                {
                  "code": "CIS 087",
                  "name": "Introduction to Programming Using Python",
                  "description": "This course provides an introduction to programming and business applications using Python. The course focuses on developing the fundamental concepts and models of application development including the basic concepts of program design, debugging, data structures, structured and object-oriented programming, problem solving, programming logic, and fundamental design techniques. C-ID: ITIS 130",
                  "learning_outcomes": [],
                  "skills": [
                    "Algorithms",
                    "Programming",
                    "Software Development"
                  ]
                },
                {
                  "code": "CIS 088",
                  "name": "Introduction To Programming Using Java",
                  "description": "This course is an introduction to the fundamentals concepts of computer programming using Java. The course focuses on learning the basic concepts of program design, problem-solving, data structures, and programming logic. The course heavily relies on hands-on experience using Java and a modern integrated development environment (IDE) such as but not limited to Eclipse or IntelliJ. C-ID: ITIS 130",
                  "learning_outcomes": [],
                  "skills": [
                    "Programming",
                    "Software Development"
                  ]
                },
                {
                  "code": "CIS 095A",
                  "name": "Computer Information Systems Work Experience",
                  "description": "This course provides students with practical work experience in an approved occupational setting related to Computer Information Systems. Students apply classroom learning to real-world situations, develop professional skills, and gain insights into career opportunities under supervision.",
                  "learning_outcomes": [],
                  "skills": [
                    "Software Development"
                  ]
                }
              ],
              "aligned_skills": [
                "Algorithms",
                "Programming",
                "Software Development"
              ]
            },
            {
              "department": "Computer Science",
              "courses": [
                {
                  "code": "CS 007A",
                  "name": "Computer Science I",
                  "description": "This course is an introduction to computer programming and is designed primarily for computer science and related transfer majors. Its main objective is to teach principles and practices of computer science, but students will also engage in problem solving using the C++ programming language. Topics include structured procedural programming with program control structures (sequence, selection, iteration), modular program structures (functions and parameter passing), data types (primitive types, arrays, files and structures) and an intro to object-oriented programming. (C-ID COMP 122)",
                  "learning_outcomes": [],
                  "skills": [
                    "Algorithms",
                    "Programming",
                    "Software Development"
                  ]
                },
                {
                  "code": "CS 007B",
                  "name": "Computer Science II",
                  "description": "This second course in computer science introduces more advanced topics in programming. Students will use modularity to develop solutions for larger-scale programming problems. Recursion, file processing, and object-oriented programming are implemented. This course will be taught using the C++ programming language. (C-ID COMP 132)",
                  "learning_outcomes": [],
                  "skills": [
                    "Algorithms",
                    "Programming",
                    "Software Development"
                  ]
                },
                {
                  "code": "CS 008",
                  "name": "Computer Architecture and Organization",
                  "description": "The organization and behavior of computer systems at the assembly-language level. The translation of statements and constructs in a high-level language into sequences of machine instructions is studied, as well as the internal representation of simple data types and structures. Numerical computation is examined, noting the various data representation errors and potential procedural errors. Digital electronics with the Boolean algebra of logic gates is studied. (C-ID COMP 142)",
                  "learning_outcomes": [],
                  "skills": [
                    "Algorithms",
                    "Programming"
                  ]
                },
                {
                  "code": "CS 009",
                  "name": "Data Structures and Algorithms",
                  "description": "This is an advanced course in C++ programming. Students design, write, and debug C++ programs using structured programming concepts. Topics covered include pointers; linked lists, unions and data structures; bit operations, user-defined data types; recursion; incorporation of assembly language subroutines; and advanced graphical and animation techniques.",
                  "learning_outcomes": [],
                  "skills": [
                    "Algorithms",
                    "Programming",
                    "Software Development"
                  ]
                },
                {
                  "code": "CS 095A",
                  "name": "Computer Science Work Experience",
                  "description": "This work experience course of supervised employment provides students the opportunity to connect academics to applied experiential learning in the workplace. It assists students in developing transferable employability skills, career awareness, learning industry culture, competencies and norms, and developing professional networks that support career mobility. To enroll, students must have a job or internship placement in a part-time or full-time capacity. Credit may be accrued at the rate of one to five (1-5) units per semester based on the student's ability to meet the hours required per unit enrolled. Students must work 54 hours per unit earned. This Work Experience course is available to students whose job or internship placement is directly related to Computer Science.",
                  "learning_outcomes": [],
                  "skills": [
                    "Software Development"
                  ]
                }
              ],
              "aligned_skills": [
                "Algorithms",
                "Programming",
                "Software Development"
              ]
            },
            {
              "department": "Engineering Technology",
              "courses": [
                {
                  "code": "ENGT 009",
                  "name": "Introduction to Robotics",
                  "description": "This course is an introduction to robotics. The history of robots along with the components that constitute a robot will be covered. Students will learn to manipulate the basic building blocks of a robot by programming a microcontroller and interfacing with basic circuits, sensors and motors.",
                  "learning_outcomes": [],
                  "skills": [
                    "Programming"
                  ]
                },
                {
                  "code": "ENGT 015B",
                  "name": "Computer Numerical Controls IB",
                  "description": "This course is the second of an introduction to Computer Numerical Control (CNC) programming course series. The use of M&G code programming to produce CNC programs for machined parts will be taught. Specific areas of programming including linear and circular interpolation, canned cycles, drilling, reaming, tapping, boring, face milling, end milling and the use of sub programs will be covered. Machine operation will be covered and used to proof run programs.",
                  "learning_outcomes": [],
                  "skills": [
                    "Programming"
                  ]
                },
                {
                  "code": "ENGT 024",
                  "name": "Manufacturing of Circuits",
                  "description": "This course covers electronic schematic capture, simulation, export to printed circuit board design, layout and auto-routing software. It includes basic Computer Aided Design (CAD) drafting, block diagrams, library component templates, and printed circuit baord (PCB) design, fabrication, and assembly, using through-hole and surface-mount technology and devices (SMT and SMD).",
                  "learning_outcomes": [],
                  "skills": [
                    "Software Development"
                  ]
                },
                {
                  "code": "ENGT 030",
                  "name": "PLCs and Industrial Controls I",
                  "description": "This course offers students the fundamentals of a Programmable Logic Controller (PLC). Students learn the basic parts of a PLC system, digital fundamentals, and PLC addressing.",
                  "learning_outcomes": [],
                  "skills": [
                    "Programming"
                  ]
                },
                {
                  "code": "ENGT 031",
                  "name": "PLCs and Industrial Controls II",
                  "description": "In this course students learn to program a PLC for advanced sequencing operation. Students also learn to program timers and counters that are used in a PLC application, as well as to write a PLC program using advanced math and data functions. An introduction of SCADA systems and ControlLogix Controllers will also be given.",
                  "learning_outcomes": [],
                  "skills": [
                    "Programming"
                  ]
                }
              ],
              "aligned_skills": [
                "Programming",
                "Software Development"
              ]
            }
          ],
          "student_composition": "Students in these programs are actively building the core technical competencies Collins requires for Software Developer roles. The pipeline spans Computer Information Systems, Computer Science, and Engineering Technology, concentrating preparation in the skills most directly tied to this occupation. That distribution gives College of the Desert a credible cohort to put forward for a first placement.",
          "student_evidence": {
            "total_in_program": 205,
            "with_all_core_skills": 121,
            "top_students": [
              {
                "uuid": "e20499bc-5c70-54a6-b162-00d3adabf513",
                "display_number": 1,
                "primary_focus": "Computer Science",
                "courses_completed": 1,
                "gpa": 4.0,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "CS 007B",
                    "name": "Computer Science II",
                    "grade": "A",
                    "term": "2023-Fall"
                  }
                ],
                "relevant_skills": [
                  "Algorithms",
                  "Programming",
                  "Software Development"
                ]
              },
              {
                "uuid": "ac914c98-223e-52e4-8cf4-d09c042bbfdd",
                "display_number": 2,
                "primary_focus": "Computer Science",
                "courses_completed": 1,
                "gpa": 4.0,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "CS 009",
                    "name": "Data Structures and Algorithms",
                    "grade": "A",
                    "term": "2023-Fall"
                  }
                ],
                "relevant_skills": [
                  "Algorithms",
                  "Programming",
                  "Software Development"
                ]
              },
              {
                "uuid": "5e977662-66ed-56a5-94e5-8d6fc60fc31d",
                "display_number": 3,
                "primary_focus": "Computer Science",
                "courses_completed": 2,
                "gpa": 4.0,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "CS 007B",
                    "name": "Computer Science II",
                    "grade": "W",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "CS 007A",
                    "name": "Computer Science I",
                    "grade": "A",
                    "term": "2025-Spring"
                  }
                ],
                "relevant_skills": [
                  "Algorithms",
                  "Programming",
                  "Software Development"
                ]
              },
              {
                "uuid": "bc8a60cd-f073-5c74-a82f-07a013fcde5b",
                "display_number": 4,
                "primary_focus": "Computer Science",
                "courses_completed": 2,
                "gpa": 4.0,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "CS 007B",
                    "name": "Computer Science II",
                    "grade": "A",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "CS 008",
                    "name": "Computer Architecture and Organization",
                    "grade": "A",
                    "term": "2025-Spring"
                  }
                ],
                "relevant_skills": [
                  "Algorithms",
                  "Programming",
                  "Software Development"
                ]
              },
              {
                "uuid": "e47f05e5-3aa9-5300-b468-e9a4622e53b3",
                "display_number": 5,
                "primary_focus": "Computer Science",
                "courses_completed": 2,
                "gpa": 4.0,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "CS 009",
                    "name": "Data Structures and Algorithms",
                    "grade": "A",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "CS 007A",
                    "name": "Computer Science I",
                    "grade": "W",
                    "term": "2025-Spring"
                  }
                ],
                "relevant_skills": [
                  "Algorithms",
                  "Programming",
                  "Software Development"
                ]
              },
              {
                "uuid": "75294284-2c94-55e5-b198-8725a72e58bf",
                "display_number": 6,
                "primary_focus": "Computer Science",
                "courses_completed": 5,
                "gpa": 3.88,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "CS 095A",
                    "name": "Computer Science Work Experience",
                    "grade": "A",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "CS 009",
                    "name": "Data Structures and Algorithms",
                    "grade": "A",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "CS 007B",
                    "name": "Computer Science II",
                    "grade": "A",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "CS 007A",
                    "name": "Computer Science I",
                    "grade": "A",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "CS 008",
                    "name": "Computer Architecture and Organization",
                    "grade": "B",
                    "term": "2024-Winter"
                  }
                ],
                "relevant_skills": [
                  "Algorithms",
                  "Programming",
                  "Software Development"
                ]
              },
              {
                "uuid": "db995014-a252-5d6b-868f-08805135f951",
                "display_number": 7,
                "primary_focus": "Computer Science",
                "courses_completed": 3,
                "gpa": 3.8,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "CS 095A",
                    "name": "Computer Science Work Experience",
                    "grade": "A",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "CS 007B",
                    "name": "Computer Science II",
                    "grade": "A",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "CS 007A",
                    "name": "Computer Science I",
                    "grade": "A",
                    "term": "2025-Spring"
                  }
                ],
                "relevant_skills": [
                  "Algorithms",
                  "Programming",
                  "Software Development"
                ]
              },
              {
                "uuid": "dfcb3389-af3e-5b09-94f3-48cbbeaef5af",
                "display_number": 8,
                "primary_focus": "Computer Science",
                "courses_completed": 3,
                "gpa": 3.67,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "CS 009",
                    "name": "Data Structures and Algorithms",
                    "grade": "A",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "CS 007A",
                    "name": "Computer Science I",
                    "grade": "B",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "CS 008",
                    "name": "Computer Architecture and Organization",
                    "grade": "A",
                    "term": "2025-Spring"
                  }
                ],
                "relevant_skills": [
                  "Algorithms",
                  "Programming",
                  "Software Development"
                ]
              },
              {
                "uuid": "1866d935-a424-58ee-878e-198df7d7d582",
                "display_number": 9,
                "primary_focus": "Computer Science",
                "courses_completed": 3,
                "gpa": 3.5,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "DDP 110",
                    "name": "Graphic Design",
                    "grade": "W",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "ARCH 250",
                    "name": "Intermediate Digital Design",
                    "grade": "A",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "CS 008",
                    "name": "Computer Architecture and Organization",
                    "grade": "B",
                    "term": "2025-Spring"
                  }
                ],
                "relevant_skills": [
                  "Algorithms",
                  "Programming",
                  "Software Development"
                ]
              },
              {
                "uuid": "ce92d02a-d53d-5acc-826b-0474d779654d",
                "display_number": 10,
                "primary_focus": "Computer Science",
                "courses_completed": 1,
                "gpa": 3.5,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "CS 007A",
                    "name": "Computer Science I",
                    "grade": "B",
                    "term": "2025-Spring"
                  }
                ],
                "relevant_skills": [
                  "Algorithms",
                  "Programming",
                  "Software Development"
                ]
              }
            ]
          }
        },
        "roadmap": "A potential starting point would be a conversation between the Computer Information Systems or Computer Science department chair and Collins Aerospace's workforce development or university relations team to define site capacity and project scope. An internship structured at 12-16 weeks could map to existing cooperative education or work experience course sequences for credit. A first cohort of 4-8 students placed within the next two semesters is a realistic near-term target.",
        "selected_occupations": [],
        "advisory_thesis": "",
        "agenda_topics": []
      },
      "engagementType": "internship",
      "collegeId": "College of the Desert",
      "savedAt": "2026-04-20T00:00:00.000Z",
      "status": "saved",
      "schemaVersion": 8
    },
    {
      "id": "seed-desert-curriculum-01",
      "proposal": {
        "employer": "Oasis Date Gardens",
        "sector": "Agriculture",
        "partnership_type": "Curriculum Co-Design",
        "selected_occupation": "Agricultural Technicians",
        "selected_soc_code": "19-4012",
        "core_skills": [
          "Agriculture",
          "Plant Science",
          "Pest Management"
        ],
        "gap_skill": "Date Palm Cultivation and Pollination Techniques",
        "regions": [
          "Inland Empire / Desert"
        ],
        "opportunity": "College of the Desert's Agriculture/Plant Science program is well-positioned to strengthen its Agricultural Technician pipeline through a co-design partnership with Oasis Date Gardens focused on date palm cultivation and pollination techniques. The program already develops plant science and pest management competencies that are central to this role. With 20 annual openings and $50,980 median wages in the regional labor market, deepening preparation in date-specific practices would directly improve graduate readiness for technician work in the Coachella Valley.",
        "opportunity_evidence": [
          {
            "title": "Agricultural Technicians",
            "soc_code": "19-4012",
            "annual_wage": 50980,
            "employment": 120,
            "annual_openings": 20,
            "growth_rate": 0.020244916
          }
        ],
        "justification": {
          "curriculum_composition": "The Agriculture/Plant Science department is the right home for this partnership, with five courses developing plant science and pest management skills directly relevant to agricultural technician work. Date palm cultivation and pollination techniques represent a more specialized layer of that foundation \u2014 hand pollination timing, offshoot management, and fruit development specific to Phoenix dactylifera are areas that could be more rigorously developed through structured collaboration with Oasis Date Gardens. A co-design review with employer faculty would determine where these practices fit most naturally within existing coursework.",
          "curriculum_evidence": [
            {
              "department": "Agriculture/Plant Science",
              "courses": [
                {
                  "code": "AGPS 001",
                  "name": "Soils & Plant Nutrition",
                  "description": "This lecture and laboratory course covers soil derivation, classification, texture, structure, water movement and measurement, organic matter, microorganisms, sampling techniques, pH, salinity, reclamation and tillage. Also included are soil survey reports and maps, basic soil chemistry, essential plant nutrients, soil analysis, and fertilizers. (C-ID AG-PS 128L)",
                  "learning_outcomes": [],
                  "skills": [
                    "Plant Science"
                  ]
                },
                {
                  "code": "AGPS 002",
                  "name": "Entomology - General & Applied",
                  "description": "This course is a study of insects including external and internal structures, major life systems, growth and development, classification, ecology, behavior, economic importance, and an overview of pest management. Suggested for Biological Science General Education Requirements.",
                  "learning_outcomes": [],
                  "skills": [
                    "Pest Management"
                  ]
                },
                {
                  "code": "AGPS 005",
                  "name": "Plant Science",
                  "description": "This course offers an opportunity to learn the basic structure and function of plants, their place in the world of human activity and the methods used to manipulate the botanical world to human advantage. Students can expect to be exposed to plant anatomy, morphology and physiology as well as such practical matters as plant propagation, pruning and fertilization. (C-ID AG-PS 106L)",
                  "learning_outcomes": [],
                  "skills": [
                    "Plant Science"
                  ]
                },
                {
                  "code": "AGPS 005L",
                  "name": "Plant Science Lab",
                  "description": "This laboratory is the companion of AGPS 005. It is intended to provide an introduction to some biological science procedures as well as direct experience with horticultural operations. Included are: plant propagation, pruning, anatomy, morphology, taxonomic keys, transplanting and plant use and pesticides. (C-ID AG-PS 106 L)",
                  "learning_outcomes": [],
                  "skills": [
                    "Pest Management",
                    "Plant Science"
                  ]
                },
                {
                  "code": "AGPS 032",
                  "name": "Pesticide Laws & Regulations",
                  "description": "This course covers state and federal laws regulating the use of pesticides and prepares students to take California's Certified Applicator examinations. Proper and safe methods of applying agricultural chemicals are discussed, along with procedures for calculating the amount of material needed. In addition, students study alternative pest control methods.",
                  "learning_outcomes": [],
                  "skills": [
                    "Pest Management"
                  ]
                }
              ],
              "aligned_skills": [
                "Pest Management",
                "Plant Science"
              ]
            }
          ],
          "student_composition": "Students in the Agriculture/Plant Science program are building plant science and pest management skills that align with the core demands of agricultural technician roles. They represent the direct audience for any curriculum strengthened through this partnership. A co-design effort would deepen preparation for the date palm production practices they are most likely to encounter working in the Inland Empire and Desert region.",
          "student_evidence": {
            "total_in_program": 166,
            "with_all_core_skills": 2,
            "top_students": [
              {
                "uuid": "3a23208a-91c4-5844-a421-23f70861a33d",
                "display_number": 1,
                "primary_focus": "Agriculture/Plant Science",
                "courses_completed": 6,
                "gpa": 3.12,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "NR 021",
                    "name": "Introduction to GIS",
                    "grade": "B",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "AGPS 005L",
                    "name": "Plant Science Lab",
                    "grade": "A",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "AGPS 005",
                    "name": "Plant Science",
                    "grade": "A",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "AGPS 001",
                    "name": "Soils & Plant Nutrition",
                    "grade": "A",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "AGPS 032",
                    "name": "Pesticide Laws & Regulations",
                    "grade": "B",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "AGPS 002",
                    "name": "Entomology - General & Applied",
                    "grade": "A",
                    "term": "2024-Fall"
                  }
                ],
                "relevant_skills": [
                  "Agriculture",
                  "Pest Management",
                  "Plant Science"
                ]
              },
              {
                "uuid": "cecf962b-fad1-544a-bb1e-ef7e8c55cf35",
                "display_number": 2,
                "primary_focus": "Agriculture/Plant Science",
                "courses_completed": 6,
                "gpa": 2.64,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "NR 004",
                    "name": "Introduction to Ecosystem Management",
                    "grade": "C",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "AGPS 005L",
                    "name": "Plant Science Lab",
                    "grade": "D",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "AGPS 005",
                    "name": "Plant Science",
                    "grade": "B",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "AGPS 001",
                    "name": "Soils & Plant Nutrition",
                    "grade": "C",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "AGPS 032",
                    "name": "Pesticide Laws & Regulations",
                    "grade": "A",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "AGPS 002",
                    "name": "Entomology - General & Applied",
                    "grade": "A",
                    "term": "2024-Spring"
                  }
                ],
                "relevant_skills": [
                  "Agriculture",
                  "Pest Management",
                  "Plant Science"
                ]
              },
              {
                "uuid": "107c45ba-7cf6-5f17-ba95-2504ab9a3faa",
                "display_number": 3,
                "primary_focus": "Agriculture/Plant Science",
                "courses_completed": 2,
                "gpa": 4.0,
                "matching_skills": 2,
                "enrollments": [
                  {
                    "code": "AGPS 005",
                    "name": "Plant Science",
                    "grade": "A",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "AGPS 002",
                    "name": "Entomology - General & Applied",
                    "grade": "A",
                    "term": "2025-Spring"
                  }
                ],
                "relevant_skills": [
                  "Pest Management",
                  "Plant Science"
                ]
              },
              {
                "uuid": "f9058b0a-f623-57cc-af05-10a416561951",
                "display_number": 4,
                "primary_focus": "Agriculture/Plant Science",
                "courses_completed": 3,
                "gpa": 3.83,
                "matching_skills": 2,
                "enrollments": [
                  {
                    "code": "AGPS 005",
                    "name": "Plant Science",
                    "grade": "B",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "AGPS 001",
                    "name": "Soils & Plant Nutrition",
                    "grade": "A",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "AGPS 032",
                    "name": "Pesticide Laws & Regulations",
                    "grade": "A",
                    "term": "2022-Fall"
                  }
                ],
                "relevant_skills": [
                  "Pest Management",
                  "Plant Science"
                ]
              },
              {
                "uuid": "2065ed7b-e7f3-57ec-895e-bc37228ab724",
                "display_number": 5,
                "primary_focus": "Agriculture/Plant Science",
                "courses_completed": 5,
                "gpa": 3.78,
                "matching_skills": 2,
                "enrollments": [
                  {
                    "code": "AGPS 005L",
                    "name": "Plant Science Lab",
                    "grade": "A",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "AGPS 005",
                    "name": "Plant Science",
                    "grade": "A",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "AGPS 001",
                    "name": "Soils & Plant Nutrition",
                    "grade": "A",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "AGPS 032",
                    "name": "Pesticide Laws & Regulations",
                    "grade": "A",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "AGPS 002",
                    "name": "Entomology - General & Applied",
                    "grade": "A",
                    "term": "2023-Spring"
                  }
                ],
                "relevant_skills": [
                  "Pest Management",
                  "Plant Science"
                ]
              },
              {
                "uuid": "4adeb5cf-35bc-5d4a-b59b-2b426942973c",
                "display_number": 6,
                "primary_focus": "Agriculture/Plant Science",
                "courses_completed": 3,
                "gpa": 3.75,
                "matching_skills": 2,
                "enrollments": [
                  {
                    "code": "AGPS 005",
                    "name": "Plant Science",
                    "grade": "A",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "AGPS 001",
                    "name": "Soils & Plant Nutrition",
                    "grade": "A",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "AGPS 032",
                    "name": "Pesticide Laws & Regulations",
                    "grade": "B",
                    "term": "2024-Winter"
                  }
                ],
                "relevant_skills": [
                  "Pest Management",
                  "Plant Science"
                ]
              },
              {
                "uuid": "aba2b6de-a7f2-5d3b-9a03-e8c93f9e12f7",
                "display_number": 7,
                "primary_focus": "Agriculture/Plant Science",
                "courses_completed": 4,
                "gpa": 3.75,
                "matching_skills": 2,
                "enrollments": [
                  {
                    "code": "AGPS 005L",
                    "name": "Plant Science Lab",
                    "grade": "A",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "AGPS 005",
                    "name": "Plant Science",
                    "grade": "A",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "AGPS 001",
                    "name": "Soils & Plant Nutrition",
                    "grade": "A",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "AGPS 002",
                    "name": "Entomology - General & Applied",
                    "grade": "B",
                    "term": "2024-Winter"
                  }
                ],
                "relevant_skills": [
                  "Pest Management",
                  "Plant Science"
                ]
              },
              {
                "uuid": "be2107b3-0019-54b3-9296-8941b5db3b09",
                "display_number": 8,
                "primary_focus": "Agriculture/Plant Science",
                "courses_completed": 5,
                "gpa": 3.73,
                "matching_skills": 2,
                "enrollments": [
                  {
                    "code": "AGPS 005L",
                    "name": "Plant Science Lab",
                    "grade": "A",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "AGPS 005",
                    "name": "Plant Science",
                    "grade": "W",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "AGPS 001",
                    "name": "Soils & Plant Nutrition",
                    "grade": "A",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "AGPS 032",
                    "name": "Pesticide Laws & Regulations",
                    "grade": "A",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "AGPS 002",
                    "name": "Entomology - General & Applied",
                    "grade": "A",
                    "term": "2023-Winter"
                  }
                ],
                "relevant_skills": [
                  "Pest Management",
                  "Plant Science"
                ]
              },
              {
                "uuid": "31c14e81-efde-59a4-8e9d-f9a42ac722b2",
                "display_number": 9,
                "primary_focus": "Agriculture/Plant Science",
                "courses_completed": 5,
                "gpa": 3.67,
                "matching_skills": 2,
                "enrollments": [
                  {
                    "code": "AGPS 005L",
                    "name": "Plant Science Lab",
                    "grade": "A",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "AGPS 005",
                    "name": "Plant Science",
                    "grade": "A",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "AGPS 001",
                    "name": "Soils & Plant Nutrition",
                    "grade": "A",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "AGPS 032",
                    "name": "Pesticide Laws & Regulations",
                    "grade": "A",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "AGPS 002",
                    "name": "Entomology - General & Applied",
                    "grade": "B",
                    "term": "2023-Winter"
                  }
                ],
                "relevant_skills": [
                  "Pest Management",
                  "Plant Science"
                ]
              },
              {
                "uuid": "3fd37941-8cb3-53ea-b19f-87d4d81f7548",
                "display_number": 10,
                "primary_focus": "Agriculture/Plant Science",
                "courses_completed": 4,
                "gpa": 3.67,
                "matching_skills": 2,
                "enrollments": [
                  {
                    "code": "AGPS 001",
                    "name": "Soils & Plant Nutrition",
                    "grade": "A",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "AGEH 001L",
                    "name": "Horticulture Laboratory",
                    "grade": "A",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "AGPS 032",
                    "name": "Pesticide Laws & Regulations",
                    "grade": "A",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "AGPS 002",
                    "name": "Entomology - General & Applied",
                    "grade": "A",
                    "term": "2025-Spring"
                  }
                ],
                "relevant_skills": [
                  "Pest Management",
                  "Plant Science"
                ]
              }
            ]
          }
        },
        "roadmap": "A working group between the Agriculture/Plant Science department and Oasis Date Gardens could evaluate how date palm cultivation and pollination techniques can be integrated into existing coursework. One potential starting point is identifying which current courses in the five-course sequence offer the most natural entry points for Phoenix dactylifera-specific content. Revised or supplemental material could be piloted within the next catalog cycle.",
        "selected_occupations": [],
        "advisory_thesis": "",
        "agenda_topics": []
      },
      "engagementType": "curriculum_codesign",
      "collegeId": "College of the Desert",
      "savedAt": "2026-04-20T00:00:00.000Z",
      "status": "saved",
      "schemaVersion": 8
    }
  ],
  "Oxnard College": [
    {
      "id": "seed-oxnard-advisory-01",
      "proposal": {
        "employer": "University of California, Santa Barbara",
        "sector": "Education",
        "partnership_type": "Advisory Board",
        "selected_occupation": "Teaching Assistants, Postsecondary",
        "selected_soc_code": "25-9194",
        "core_skills": [
          "Mentoring",
          "Classroom Management",
          "Research Methods",
          "Environmental Science",
          "Programming",
          "Data Structures"
        ],
        "gap_skill": "",
        "regions": [
          "Orange County",
          "Los Angeles",
          "South Central Coast"
        ],
        "opportunity": "UC Santa Barbara's position as a research-intensive public university makes it a compelling advisory board partner for Oxnard College's workforce programs in computing, environmental science, and education support. UCSB operates at the intersection of software development, environmental research, and postsecondary teaching \u2014 three domains where applied institutional expectations are difficult to surface without direct employer input. An advisory board relationship creates a standing channel for that guidance with no grant funding required.",
        "opportunity_evidence": [
          {
            "title": "Software Developers",
            "soc_code": "15-1252",
            "annual_wage": 147900,
            "employment": 3760,
            "annual_openings": 230,
            "growth_rate": 0.039868254
          },
          {
            "title": "Teaching Assistants, Postsecondary",
            "soc_code": "25-9044",
            "annual_wage": 42340,
            "employment": 1090,
            "annual_openings": 140,
            "growth_rate": 0.025452139
          },
          {
            "title": "Environmental Scientists and Specialists, Including Health",
            "soc_code": "19-2041",
            "annual_wage": 95090,
            "employment": 430,
            "annual_openings": 40,
            "growth_rate": 0.036611892
          }
        ],
        "justification": {
          "curriculum_composition": "The Computer Science department provides the closest curricular match to UCSB's software development operations, building programming and data structures competencies directly relevant to the roles UCSB fills. The Biology department's coursework in environmental science and research methods aligns with the field-ready preparation UCSB expects from entry-level environmental specialists. These are workforce-oriented programs where employer perspective on applied expectations translates directly into instructional relevance.",
          "curriculum_evidence": [
            {
              "department": "Computer Science",
              "courses": [
                {
                  "code": "CS R131",
                  "name": "Programming Concepts and Methodology I",
                  "description": "This course provides an introduction to fundamental programming concepts using a high-level programming language. Students will learn essential skills including algorithm development, data structures, control structures, and functions. The course emphasizes practical problem-solving and programming techniques, enabling students to write, test, and debug simple programs. Through hands-on lab activities, students will gain proficiency in programming constructs and methodologies, preparing them for advanced studies in computer science.",
                  "learning_outcomes": [],
                  "skills": [
                    "Data Structures",
                    "Programming"
                  ]
                },
                {
                  "code": "CS R132",
                  "name": "Programming Concepts and Methodology II",
                  "description": "This course introduces fundamental data structures and their applications, focusing on their design, implementation, and analysis. Utilizing Java as the primary programming language, students will explore a variety of data structures, including Lists, Stacks, Queues, Trees, and Graphs. The course also delves into sorting and searching algorithms, providing a comprehensive understanding of algorithm efficiency and performance.",
                  "learning_outcomes": [],
                  "skills": [
                    "Data Structures",
                    "Programming"
                  ]
                },
                {
                  "code": "CS R142",
                  "name": "Computer Architecture and Organization",
                  "description": "This course explores the organization and behavior of real computer systems at the assembly-language level. Students will study the mapping of high-level language constructs onto sequences of machine instructions, as well as the internal representation of simple data types and structures. Numerical computation is examined, noting various data representation errors and potential procedural errors.",
                  "learning_outcomes": [],
                  "skills": [
                    "Data Structures",
                    "Programming"
                  ]
                },
                {
                  "code": "CS R152",
                  "name": "Discrete Structures",
                  "description": "This course introduces students to the fundamental discrete structures used in computer science, emphasizing their practical applications. Key topics include logic and proofs, set theory, functions, sequences, summations, algorithm analysis, properties of integers, mathematical induction, recursion, combinatorics, relations, graph theory, tree structures, and discrete probability. Through a combination of theoretical knowledge and practical problem-solving, students will develop a strong foundation in these essential concepts.",
                  "learning_outcomes": [],
                  "skills": [
                    "Data Structures",
                    "Programming",
                    "Research Methods"
                  ]
                }
              ],
              "aligned_skills": [
                "Data Structures",
                "Programming",
                "Research Methods"
              ]
            },
            {
              "department": "Biology",
              "courses": [
                {
                  "code": "BIOL R100",
                  "name": "Marine Biology",
                  "description": "This course provides an introduction to the diversity of marine organisms and the physical and biological processes that influence their life history, behavior, distribution, and anatomical structure. Topics also address the interactions of these organisms and processes in a variety of habitats, marine ecology, and marine conservation.",
                  "learning_outcomes": [],
                  "skills": [
                    "Environmental Science"
                  ]
                },
                {
                  "code": "BIOL R120",
                  "name": "Principles of Biology I",
                  "description": "The first semester of biology for majors introduces the student to principles of cellular and molecular biology. Knowledge from a breadth of disciplines related to health, medical and research science careers is examined including: biochemistry, metabolism, molecular biology, genetics, cellular biology, recombinant DNA, developmental biology, microbiology and molecular evolution. While the diversity of life is surveyed, an emphasis is placed on the biology worldview derived from experimental data of specific model genera, animal cell culture systems and prokaryotic/eukaryotic viruses. The method of generating hypothesis based research results and the role of paradigms in advancing biological science theory are examined.",
                  "learning_outcomes": [],
                  "skills": [
                    "Research Methods"
                  ]
                },
                {
                  "code": "BIOL R170",
                  "name": "Biological Marine Resource Management",
                  "description": "This field course is an introduction to topics in marine biology related to current resource management issues in this region. Trips to natural areas where biological, geological, and oceanographic resources can be observed will be combined with related information about resource management at the federal, state, and local levels.",
                  "learning_outcomes": [],
                  "skills": [
                    "Environmental Science"
                  ]
                },
                {
                  "code": "BIOL R199",
                  "name": "Directed Studies in Biology Related Topics",
                  "description": "Designed for students interested in furthering their knowledge of Biology on an independent study basis. These studies may require a combination of laboratory and library research. Project findings will be presented in a scientific poster format, video, protocol or research publication.",
                  "learning_outcomes": [],
                  "skills": [
                    "Research Methods"
                  ]
                }
              ],
              "aligned_skills": [
                "Environmental Science",
                "Research Methods"
              ]
            },
            {
              "department": "Environmental Science",
              "courses": [
                {
                  "code": "ESRM R100",
                  "name": "Introduction to Environmental Science",
                  "description": "This course is an interdisciplinary introduction to environmental issues from a scientific perspective focusing on physical, chemical, and biological processes within the Earth system, the interactions between humans and these processes, and the role of science in finding sustainable solutions. Topics include ecological principles, biodiversity, climate change, sustainability, renewable and non-renewable energy, water resources, air and water pollution, and solid waste management.",
                  "learning_outcomes": [],
                  "skills": [
                    "Environmental Science"
                  ]
                },
                {
                  "code": "ESRM R100L",
                  "name": "Introduction to Environmental Science Laboratory",
                  "description": "Explores environmental processes associated with society including energy production, waste management, and soil and water quality. The laboratory class is focused on using environmental sampling, monitoring and assessment devices, and equipment and analytical tools to detect and quantify environmental contaminants in air, water and soil, as well as to assess the overall quality of those basic environmental resources. This course emphasizes the scientific method, data collection, and the completion of a research-based oral presentation.",
                  "learning_outcomes": [],
                  "skills": [
                    "Environmental Science"
                  ]
                }
              ],
              "aligned_skills": [
                "Environmental Science"
              ]
            }
          ],
          "student_composition": "Students across the Computer Science, Biology, and Environmental Science departments are developing technical and applied research competencies in fields UCSB actively hires. The pipeline spans pathways in software development, environmental inquiry, and postsecondary teaching support \u2014 roles that require both disciplinary knowledge and the ability to function within a research-driven institutional environment.",
          "student_evidence": {
            "total_in_program": 340,
            "with_all_core_skills": 0,
            "top_students": [
              {
                "uuid": "46e222b8-863f-57f6-a75d-a99f11f4611a",
                "display_number": 1,
                "primary_focus": "Biology",
                "courses_completed": 3,
                "gpa": 3.6,
                "matching_skills": 4,
                "enrollments": [
                  {
                    "code": "BIOL R170",
                    "name": "Biological Marine Resource Management",
                    "grade": "B",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "BIOL R120",
                    "name": "Principles of Biology I",
                    "grade": "A",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "MATH R148",
                    "name": "Programming and Problem-Solving in MATLAB",
                    "grade": "A",
                    "term": "2024-Winter"
                  }
                ],
                "relevant_skills": [
                  "Data Structures",
                  "Environmental Science",
                  "Programming",
                  "Research Methods"
                ]
              },
              {
                "uuid": "27334976-eeb0-5879-acc5-a411702936f7",
                "display_number": 2,
                "primary_focus": "Biology",
                "courses_completed": 10,
                "gpa": 3.26,
                "matching_skills": 4,
                "enrollments": [
                  {
                    "code": "HED R446",
                    "name": "Optimizing Health Across the Lifespan: Key Considerations",
                    "grade": "A",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "GEOG R104",
                    "name": "Geography of California",
                    "grade": "D",
                    "term": "2022-Fall"
                  },
                  {
                    "code": "BIOL R170",
                    "name": "Biological Marine Resource Management",
                    "grade": "A",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "BIOL R100",
                    "name": "Marine Biology",
                    "grade": "A",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "HIST R150H",
                    "name": "Honors: World History I",
                    "grade": "D",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "HIST R140H",
                    "name": "Honors: History of the United States II",
                    "grade": "A",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "BIOL R120",
                    "name": "Principles of Biology I",
                    "grade": "A",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "ANTH R199",
                    "name": "Directed Studies in Anthropology",
                    "grade": "C",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "MATH R148",
                    "name": "Programming and Problem-Solving in MATLAB",
                    "grade": "A",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "STAT C1000H",
                    "name": "Introduction to Statistics - Honors",
                    "grade": "C",
                    "term": "2023-Winter"
                  }
                ],
                "relevant_skills": [
                  "Data Structures",
                  "Environmental Science",
                  "Programming",
                  "Research Methods"
                ]
              },
              {
                "uuid": "e66fd9c7-30a7-5c15-9f35-51bbc49f365c",
                "display_number": 3,
                "primary_focus": "Biology",
                "courses_completed": 4,
                "gpa": 3.17,
                "matching_skills": 4,
                "enrollments": [
                  {
                    "code": "BIOL R100",
                    "name": "Marine Biology",
                    "grade": "B",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "SOC R125",
                    "name": "Statistics for the Behavioral and Social Sciences",
                    "grade": "A",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "BIOL R120",
                    "name": "Principles of Biology I",
                    "grade": "A",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "MATH R148",
                    "name": "Programming and Problem-Solving in MATLAB",
                    "grade": "A",
                    "term": "2025-Spring"
                  }
                ],
                "relevant_skills": [
                  "Data Structures",
                  "Environmental Science",
                  "Programming",
                  "Research Methods"
                ]
              },
              {
                "uuid": "9197629d-b37a-5b02-be47-cc9ed10c5ec1",
                "display_number": 4,
                "primary_focus": "Biology",
                "courses_completed": 5,
                "gpa": 3.14,
                "matching_skills": 4,
                "enrollments": [
                  {
                    "code": "GEOG R101",
                    "name": "Elements of Physical Geography",
                    "grade": "C",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "HED R116",
                    "name": "Stress Management and Health",
                    "grade": "A",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "ECON R202H",
                    "name": "Honors: Introduction to the Principles of Macroeconomics",
                    "grade": "A",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "BIOL R199",
                    "name": "Directed Studies in Biology Related Topics",
                    "grade": "A",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "ENGR R148",
                    "name": "Programming and Problem-Solving in MATLAB",
                    "grade": "A",
                    "term": "2024-Winter"
                  }
                ],
                "relevant_skills": [
                  "Data Structures",
                  "Environmental Science",
                  "Programming",
                  "Research Methods"
                ]
              },
              {
                "uuid": "0dbbb3cf-821d-513e-b830-461eff5595a1",
                "display_number": 5,
                "primary_focus": "Biology",
                "courses_completed": 8,
                "gpa": 2.92,
                "matching_skills": 4,
                "enrollments": [
                  {
                    "code": "GEOG R198A",
                    "name": "Geographic Field Interpretation",
                    "grade": "A",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "BIOL R170",
                    "name": "Biological Marine Resource Management",
                    "grade": "C",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "BIOL R100",
                    "name": "Marine Biology",
                    "grade": "A",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "BIOL R199",
                    "name": "Directed Studies in Biology Related Topics",
                    "grade": "A",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "ART R102H",
                    "name": "Honors: Western Art I: Prehistory through the Middle Ages",
                    "grade": "A",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "ANTH R106",
                    "name": "Psychological Anthropology",
                    "grade": "B",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "ANTH R101L",
                    "name": "Introduction to Biological Anthropology Lab",
                    "grade": "C",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "ENGR R148",
                    "name": "Programming and Problem-Solving in MATLAB",
                    "grade": "A",
                    "term": "2025-Spring"
                  }
                ],
                "relevant_skills": [
                  "Data Structures",
                  "Environmental Science",
                  "Programming",
                  "Research Methods"
                ]
              },
              {
                "uuid": "e6683af9-5c2f-5963-850c-a64d5f5f248a",
                "display_number": 6,
                "primary_focus": "Biology",
                "courses_completed": 8,
                "gpa": 2.78,
                "matching_skills": 4,
                "enrollments": [
                  {
                    "code": "HED R113",
                    "name": "Introduction to Public Health",
                    "grade": "C",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "HED R104",
                    "name": "Personal Health and Wellness",
                    "grade": "A",
                    "term": "2022-Fall"
                  },
                  {
                    "code": "ANTH R119",
                    "name": "Introduction to Border Studies",
                    "grade": "B",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "ENGL C1001",
                    "name": "Critical Thinking and Writing",
                    "grade": "A",
                    "term": "2022-Fall"
                  },
                  {
                    "code": "BIOL R199",
                    "name": "Directed Studies in Biology Related Topics",
                    "grade": "B",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "ANAT R101",
                    "name": "General Human Anatomy",
                    "grade": "A",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "MATH R148",
                    "name": "Programming and Problem-Solving in MATLAB",
                    "grade": "A",
                    "term": "2022-Fall"
                  },
                  {
                    "code": "BIS R124",
                    "name": "Microsoft Access",
                    "grade": "A",
                    "term": "2022-Winter"
                  }
                ],
                "relevant_skills": [
                  "Data Structures",
                  "Environmental Science",
                  "Programming",
                  "Research Methods"
                ]
              },
              {
                "uuid": "116eaa8b-98d0-5ab3-bb1d-c3f13255dc27",
                "display_number": 7,
                "primary_focus": "Biology",
                "courses_completed": 2,
                "gpa": 3.8,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "BIOL R170",
                    "name": "Biological Marine Resource Management",
                    "grade": "A",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "MATH R148",
                    "name": "Programming and Problem-Solving in MATLAB",
                    "grade": "A",
                    "term": "2023-Fall"
                  }
                ],
                "relevant_skills": [
                  "Data Structures",
                  "Environmental Science",
                  "Programming"
                ]
              },
              {
                "uuid": "fa342522-4e17-5ae3-9198-b70df9076d84",
                "display_number": 8,
                "primary_focus": "Biology",
                "courses_completed": 5,
                "gpa": 3.38,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "HED R113",
                    "name": "Introduction to Public Health",
                    "grade": "W",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "BIOL R100",
                    "name": "Marine Biology",
                    "grade": "A",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "BIOL R199",
                    "name": "Directed Studies in Biology Related Topics",
                    "grade": "A",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "BIOL R120",
                    "name": "Principles of Biology I",
                    "grade": "A",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "STAT C1000",
                    "name": "Introduction to Statistics",
                    "grade": "B",
                    "term": "2024-Winter"
                  }
                ],
                "relevant_skills": [
                  "Environmental Science",
                  "Programming",
                  "Research Methods"
                ]
              },
              {
                "uuid": "b75cbc80-8e8c-5c20-928a-fcf811681728",
                "display_number": 9,
                "primary_focus": "Biology",
                "courses_completed": 7,
                "gpa": 3.18,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "BIOL R170",
                    "name": "Biological Marine Resource Management",
                    "grade": "A",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "ANTH R110",
                    "name": "People of the World: The Cultures of Globalization and Change",
                    "grade": "A",
                    "term": "2022-Fall"
                  },
                  {
                    "code": "SOC R125",
                    "name": "Statistics for the Behavioral and Social Sciences",
                    "grade": "A",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "BIOL R120",
                    "name": "Principles of Biology I",
                    "grade": "B",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "ANTH R106",
                    "name": "Psychological Anthropology",
                    "grade": "B",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "ANTH R101",
                    "name": "Introduction to Biological Anthropology",
                    "grade": "A",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "STAT C1000",
                    "name": "Introduction to Statistics",
                    "grade": "A",
                    "term": "2022-Winter"
                  }
                ],
                "relevant_skills": [
                  "Environmental Science",
                  "Programming",
                  "Research Methods"
                ]
              },
              {
                "uuid": "9c700bba-7e96-5985-a000-cb547ba5c508",
                "display_number": 10,
                "primary_focus": "Biology",
                "courses_completed": 5,
                "gpa": 3.13,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "ANTH R119",
                    "name": "Introduction to Border Studies",
                    "grade": "B",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "HED R116",
                    "name": "Stress Management and Health",
                    "grade": "A",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "BIOL R120",
                    "name": "Principles of Biology I",
                    "grade": "A",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "ADS R122",
                    "name": "Reducing Binge and Underage Drinking: A Collective Responsibility",
                    "grade": "A",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "BIS R124",
                    "name": "Microsoft Access",
                    "grade": "A",
                    "term": "2025-Spring"
                  }
                ],
                "relevant_skills": [
                  "Data Structures",
                  "Environmental Science",
                  "Research Methods"
                ]
              }
            ]
          }
        },
        "roadmap": "A quarterly advisory board with UCSB staff and faculty could give these programs ongoing access to the practical expectations of a research university employer. Potential starting points for the inaugural meeting include how UCSB structures teaching assistant onboarding around classroom management, what field protocols environmental researchers expect from entry-level specialists, and which data structures concepts prove most immediately applicable when new developers come on board.",
        "selected_occupations": [
          "Teaching Assistants, Postsecondary",
          "Environmental Scientists and Specialists, Including Health",
          "Software Developers"
        ],
        "advisory_thesis": "UC Santa Barbara operates as a major public research university where teaching support, environmental research, and software development intersect within a rigorous academic environment, reflecting the applied demands of higher education at scale. Exposure to this employer's perspective helps community college programs align instruction in education support, environmental science, and computing with the practical expectations of a research-intensive institution that actively bridges theory and hands-on inquiry.",
        "agenda_topics": [
          {
            "topic": "How does UCSB structure teaching assistant onboarding to build classroom management skills before first solo instruction?",
            "rationale": "UCSB's onboarding model could inform how the college's Education Support curriculum sequences mentoring and classroom management preparation for students entering postsecondary teaching roles."
          },
          {
            "topic": "What data collection and field protocols do UCSB environmental researchers expect from entry-level specialists on active projects?",
            "rationale": "UCSB's operational expectations for field-ready staff could strengthen how Environmental Science structures its applied research methods coursework."
          },
          {
            "topic": "Which data structures concepts does UCSB's software development team find most immediately applicable when onboarding new developers?",
            "rationale": "UCSB's hiring and onboarding experience could help Computer Science prioritize sequencing within its programming and data structures coursework for workforce-bound students."
          }
        ]
      },
      "engagementType": "advisory_board",
      "collegeId": "Oxnard College",
      "savedAt": "2026-04-20T00:00:00.000Z",
      "status": "saved",
      "schemaVersion": 8
    },
    {
      "id": "seed-oxnard-internship-01",
      "proposal": {
        "employer": "Technicolor",
        "sector": "Information & Media",
        "partnership_type": "Internship Pipeline",
        "selected_occupation": "Audio and Video Technicians",
        "selected_soc_code": "27-4011",
        "core_skills": [
          "Audio Production",
          "Video Production",
          "Equipment Operation"
        ],
        "gap_skill": "",
        "regions": [
          "Los Angeles",
          "South Central Coast"
        ],
        "opportunity": "Technicolor's post-production and content distribution operations in the Los Angeles region make it a strong internship partner for Oxnard College's film and media programs. The Audio and Video Technicians occupation shows 30 annual openings at a median wage of $54,260 with 4.9% projected growth. A structured 8-16 week placement could give students direct exposure to professional production workflows in a live industry environment.",
        "opportunity_evidence": [
          {
            "title": "Audio and Video Technicians",
            "soc_code": "27-4011",
            "annual_wage": 54260,
            "employment": 300,
            "annual_openings": 30,
            "growth_rate": 0.048543414
          }
        ],
        "justification": {
          "curriculum_composition": "The Film, Television, and Electronic Media department provides direct preparation for an internship at Technicolor across 18 courses covering audio production, video production, and equipment operation. The Music department deepens audio production and equipment operation through dedicated coursework. The Art + Design department extends video production and equipment operation preparation, broadening the technical range students bring to a placement.",
          "curriculum_evidence": [
            {
              "department": "Film, Television, and Electronic Media",
              "courses": [
                {
                  "code": "FTVE R101",
                  "name": "Film Analysis and Appreciation",
                  "description": "Film Analysis and Appreciation is an introduction to film as a contemporary art form. It emphasizes close observation and analysis of essential film language, specifically mise en sc\u00e8ne, camera and editing techniques, lighting, and the cinematic use of sound. Students will learn and utilize various methods of interpreting and evaluating motion pictures with an eye on its socio-political context. Students will correctly identify key inventions, events, and movements in an effort to explain how each affected the development of Film as both an industry and art form. Screenings for this course include a broad range of films and film excerpts representing different time periods, cultures, and cinematic traditions. Students who complete this course will have a deeper understanding and appreciation of movies.",
                  "learning_outcomes": [],
                  "skills": [
                    "Video Production"
                  ]
                },
                {
                  "code": "FTVE R102",
                  "name": "Media Production Planning",
                  "description": "This course provides a fundamental working knowledge of the varied aspects of media and film producing and production management and prepares students for future studies in more specialized topics within the subject area. This course will explore the role of the producer in developing projects and the systems and teams that support them. Issues specific to working independently, via web-based content creation and within the studio system will be addressed as well as specific challenges relating to adapting material, creating an artistically supportive atmosphere, location work, financial management, working with unions and problem solving. Students will increase their awareness of the overall environment and function of the film and media business as well as observe the trends of various media industries. Production Planning is a survey course designed to teach aesthetic and technical approaches to all phases of film and content creation from the producer's perspective with emphasis on production management and logistics.",
                  "learning_outcomes": [],
                  "skills": [
                    "Video Production"
                  ]
                },
                {
                  "code": "FTVE R103",
                  "name": "Fundamentals of Cinematography and Lighting",
                  "description": "This course provides an introduction to the fundamental technical and aesthetic principles of film and media digital photography. Students are instructed in practical training in the use of cameras, with an introduction to image control through exposure, lighting, and selection of camera, lenses, and filters. Students learn practical and theoretical elements of cinematography with an emphasis on lighting and camera technique. Technical topics include camera operation, composition, HD video basics, and camera settings including ISO, aperture, shutter speed, focus, and focal length. Lighting basics include working with both indoor and outdoor lighting, using professional light kits, and lighting accessories (flags, gels, cookies, filters), as well as important information of lighting safety. The course also offers an examination of the cinematographer as a visual storyteller to develop a broader understanding of the balance between artist and technician as well as an examination of the different crew positions and processes of the camera crew.",
                  "learning_outcomes": [],
                  "skills": [
                    "Equipment Operation",
                    "Video Production"
                  ]
                },
                {
                  "code": "FTVE R104",
                  "name": "Content Creation: The Art of Vlogging",
                  "description": "One of the goals of the FTVE advisory committee is to expand the curriculum to reflect courses that support content creation. This will be the first of several content creation specific courses that provide training for students interested in professional media work in the web-based media industry. This is an introductory course that provides students with hands-on training for how to create vlogs and properly share them with a specific audience. This course covers everything including the available vlogging platforms, necessary equipment and equipment set-ups, the secrets of making better vlogs, dealing with your fear of vlogging in public, the best video editing software you'll need and promotion of your channel or preferred platform. This course provides understanding of what being a vlogger entails, how to practically plan, film, and edit a vlog, as well as how to proceed in the vast world of vlogging.",
                  "learning_outcomes": [],
                  "skills": [
                    "Video Production"
                  ]
                },
                {
                  "code": "FTVE R106",
                  "name": "Beginning Digital Editing",
                  "description": "In this course, students develop and improve their digital editing skills using non-linear editing software. Students will explore film/video editing theory and apply various editing styles to video footage from multiple sources. Students will gain understanding of the impact that editing has on audience response. Critical analysis of the editing process, editing complex scenes and creating visual effects will be part of the curriculum.",
                  "learning_outcomes": [],
                  "skills": [
                    "Video Production"
                  ]
                },
                {
                  "code": "FTVE R113",
                  "name": "Digital Video Editing",
                  "description": "This course focuses on digital video editing techniques, skills, and theories of editing as well as the technical requirements for assembling a digital video project. Through a series of hands-on projects, students will put traditional theories of picture and sound editing into practice using techniques of organizing media, editing, basic color correction, audio mixing fundamentals and exporting projects for various platforms. *Catalog Course Comment: This course uses DaVinci Resolve software.",
                  "learning_outcomes": [],
                  "skills": [
                    "Audio Production",
                    "Video Production"
                  ]
                },
                {
                  "code": "FTVE R115",
                  "name": "Introduction to Podcasting and Digital Storytelling",
                  "description": "This course is an introduction to all aspects of digital storytelling and podcasting. Students will produce content in the form of podcasts in formats such as talk shows, newscasts, and documentaries. Basic writing, diction, and audio editing techniques for broadcast and digital media will be covered. Ethical and legal aspects of broadcast communication and journalism are also covered. An emphasis will be placed on producing content for the public, including markup languages for submitting and hosting podcasts.",
                  "learning_outcomes": [],
                  "skills": [
                    "Audio Production"
                  ]
                },
                {
                  "code": "FTVE R120",
                  "name": "Beginning Audio Production",
                  "description": "This course serves as an introduction to the theory and practice of audio production for broadcasting, internet, film, and music recording applications. Students will learn the fundamentals of sound design and aesthetics, microphone use, and digital recording equipment. Students gain hands on experience recording, editing, and mixing audio for various applications. Upon completion, students will have basic knowledge of applied audio concepts, production workflow, equipment functions, and audio editing software.",
                  "learning_outcomes": [],
                  "skills": [
                    "Audio Production",
                    "Equipment Operation"
                  ]
                },
                {
                  "code": "FTVE R130",
                  "name": "Beginning Single Camera Production",
                  "description": "The course provides an introduction to the theory, terminology, and operation of single camera video production, including composition and editing techniques, camera operation, portable lighting, video recorder operation, audio control and basic editing. This course focuses on the aesthetics and fundamentals of scripting, producing and directing on location, postproduction, and exhibition/distribution. This course gives students skills needed for directing and editing digital video projects utilizing single camera production.",
                  "learning_outcomes": [],
                  "skills": [
                    "Audio Production",
                    "Equipment Operation",
                    "Video Production"
                  ]
                },
                {
                  "code": "FTVE R135",
                  "name": "Beginning TV Studio Production",
                  "description": "This course introduces theory, terminology and operation of a multi-camera television studio and control room. Topics include studio signal flow, directing, theory and operation of camera and audio equipment, switcher operation, fundamentals of lighting, graphics, video control and video recording and real-time video production. Through a series of practica, it provides hands-on instruction in pre-production, production, and post-production. Content development for live television is emphasized using a three camera studio format.",
                  "learning_outcomes": [],
                  "skills": [
                    "Audio Production",
                    "Equipment Operation",
                    "Video Production"
                  ]
                },
                {
                  "code": "FTVE R150",
                  "name": "Beginning Motion Picture Production",
                  "description": "This course provides an introduction to the basic theory, terminology, and practice of motion picture production as applied in feature films, and films made for television and internet through developed skill sets, and teamwork in pre-production, production, and post-production processes. Topics include basic cinematography including the operation, function and creative uses of production and post-production equipment, scriptwriting, camera operation, shot composition, lighting, sound recording and mixing, and editing.",
                  "learning_outcomes": [],
                  "skills": [
                    "Audio Production",
                    "Equipment Operation",
                    "Video Production"
                  ]
                },
                {
                  "code": "FTVE R155",
                  "name": "Advanced Studio: Live Media Production Practicum",
                  "description": "This is an advanced course in live media production. Students will develop their production skills while creating videos in a variety of forms. Through a series of hands-on practical projects, students continue to refine their aesthetic vision and technical skills in pre-production, production and post-production for all forms of live media production.",
                  "learning_outcomes": [],
                  "skills": [
                    "Audio Production",
                    "Video Production"
                  ]
                },
                {
                  "code": "FTVE R160",
                  "name": "Introduction to Digital Photography",
                  "description": "The history, theory and aesthetics of digital photography will be explored in this course. Students will learn the fundamentals of digital photography with an emphasis on processes, principles and tools of photography. Topics include the development of technical and aesthetic skills, elements of design and composition, camera technology, materials and equipment, and contemporary trends in photography.",
                  "learning_outcomes": [],
                  "skills": [
                    "Equipment Operation"
                  ]
                },
                {
                  "code": "FTVE R190A",
                  "name": "Media Production Portfolio I",
                  "description": "This course is a hands-on portfolio development course that provides students with practical steps to create and build a polished demo reel and/or e-portfolio. Students will develop an online portfolio to showcase creative projects suitable for gaining entry-level work in the Entertainment and Media industries and for transfer institutions. This in-depth portfolio course, is a self-driven, project-based class designed to enhance student skill set as they work to develop original, high-quality projects. Projects include varying aspects of media pre-production such as producing, script development, budgeting and scheduling. Varying aspects of media production including cinematography, directing, and sound production. Varying aspects of media post-production including video editing and finishing. Much of the learning takes place through discovery, as determined by each student's individual goals and creative direction.",
                  "learning_outcomes": [],
                  "skills": [
                    "Audio Production",
                    "Video Production"
                  ]
                },
                {
                  "code": "FTVE R190B",
                  "name": "Media Production Portfolio II",
                  "description": "This course provides additional hands-on training for students to create and produce intermediate-level media projects focused on high production value and advanced techniques in pre-production, production, post-production and finishing media content. Emphasis is on continued focused practical application to create and build a polished demo reel and/or e-portfolio. Students will develop an online portfolio to showcase creative projects suitable for gaining entry-level work in the Entertainment and Media industries and for transfer institutions. This in-depth portfolio course, is a self-driven, project-based class designed to enhance student skill set as they work to develop original, high-quality projects. Projects include varying aspects of media pre-production such as producing, script development, budgeting and scheduling. Varying aspects of media production including cinematography, directing, and sound production. Varying aspects of media post-production including video editing and finishing. Much of the learning takes place through discovery, as determined by each student's individual goals and creative direction.",
                  "learning_outcomes": [],
                  "skills": [
                    "Audio Production",
                    "Video Production"
                  ]
                },
                {
                  "code": "FTVE R191A",
                  "name": "Work Experience Education in Film, Television, & Electronic Media I",
                  "description": "Work Experience Education provides supervised employment extending classroom occupational learning at an on-the-job learning station relating to the students' educational or occupational goals. Each unit of credit requires 54 hours of employment during the semester. Work Experience Education is available to all students.",
                  "learning_outcomes": [],
                  "skills": [
                    "Video Production"
                  ]
                },
                {
                  "code": "FTVE R191B",
                  "name": "Work Experience Education in Film, Television, & Electronic Media II",
                  "description": "Work Experience Education provides supervised employment extending classroom occupational learning at an on-the-job learning station relating to the students' educational or occupational goals. Each unit of credit requires 54 hours of employment during the semester. Work Experience Education is available to all students.",
                  "learning_outcomes": [],
                  "skills": [
                    "Video Production"
                  ]
                },
                {
                  "code": "FTVE R191C",
                  "name": "Work Experience Education in Film, Television, & Electronic Media III",
                  "description": "Work Experience Education provides supervised employment extending classroom occupational learning at an on-the-job learning station relating to the students' educational or occupational goals. Each unit of credit requires 54 hours of employment during the semester. Work Experience Education is available to all students.",
                  "learning_outcomes": [],
                  "skills": [
                    "Video Production"
                  ]
                }
              ],
              "aligned_skills": [
                "Audio Production",
                "Equipment Operation",
                "Video Production"
              ]
            },
            {
              "department": "Art + Design",
              "courses": [
                {
                  "code": "ART R160",
                  "name": "Introduction to Digital Photography",
                  "description": "The history, theory and aesthetics of digital photography will be explored in this course. Students will learn the fundamentals of digital photography with an emphasis on processes, principles and tools of photography. Topics include the development of technical and aesthetic skills, elements of design and composition, camera technology, materials and equipment, and contemporary trends in photography.",
                  "learning_outcomes": [],
                  "skills": [
                    "Equipment Operation"
                  ]
                },
                {
                  "code": "ART R186",
                  "name": "Motion Graphics",
                  "description": "This course introduces motion graphics fundamentals, including compositing, visual effects, type in motion, and animation techniques. Includes concept development, storytelling, and aesthetics in creating motion graphics, including composition, color, motion, and timing. Students will create animated sequences that include digital images, vector-based content, video, and audio.",
                  "learning_outcomes": [],
                  "skills": [
                    "Video Production"
                  ]
                }
              ],
              "aligned_skills": [
                "Equipment Operation",
                "Video Production"
              ]
            },
            {
              "department": "Music",
              "courses": [
                {
                  "code": "MUS R801",
                  "name": "Pro Tools Fundamentals",
                  "description": "Pro Tools is the industry standard software for audio recording, mixing, and editing. This course is the first of a 2-part non-credit series that will award an industry recognized credential for both academic users and industry professionals, the Avid Certified User: Pro Tools. This course introduces fundamental Pro Tools concepts and principles, covering everything an individual needs to know to complete a basic Pro Tools project, from initial setup to final mixdown.",
                  "learning_outcomes": [],
                  "skills": [
                    "Audio Production",
                    "Equipment Operation"
                  ]
                },
                {
                  "code": "MUS R810",
                  "name": "Pro Tools Fundamentals II",
                  "description": "Pro Tools is the industry standard software for audio recording, mixing, and editing. This course is the second of a 2-part non-credit sequence that will award an industry recognized credential for both academic users and industry professionals, the Avid Certified User: Pro Tools. This course expands upon the basic principles taught in the Pro Tools Fundamentals I (MUS R801) course and introduces the core concepts and techniques students need to competently operate a Pro Tools system running mid-sized sessions. Students will learn to build sessions designed for commercial purposes and improve the results of their recording, editing, and mixing efforts.",
                  "learning_outcomes": [],
                  "skills": [
                    "Audio Production",
                    "Equipment Operation"
                  ]
                }
              ],
              "aligned_skills": [
                "Audio Production",
                "Equipment Operation"
              ]
            }
          ],
          "student_composition": "Students in the Film, Television, and Electronic Media program are building skills in the exact technical areas Technicolor's internship would engage. The Music and Art + Design departments contribute additional students whose training overlaps meaningfully with the role's core competencies. The pipeline spans three departments, giving Technicolor access to students approaching audio and video production from different disciplinary angles.",
          "student_evidence": {
            "total_in_program": 101,
            "with_all_core_skills": 41,
            "top_students": [
              {
                "uuid": "17dff853-5224-5918-976c-b6277420fdd1",
                "display_number": 1,
                "primary_focus": "Film, Television, and Electronic Media",
                "courses_completed": 5,
                "gpa": 3.6,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "FTVE R150",
                    "name": "Beginning Motion Picture Production",
                    "grade": "A",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "FTVE R120",
                    "name": "Beginning Audio Production",
                    "grade": "A",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "FTVE R115",
                    "name": "Introduction to Podcasting and Digital Storytelling",
                    "grade": "A",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "FTVE R106",
                    "name": "Beginning Digital Editing",
                    "grade": "W",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "FTVE R104",
                    "name": "Content Creation: The Art of Vlogging",
                    "grade": "W",
                    "term": "2023-Winter"
                  }
                ],
                "relevant_skills": [
                  "Audio Production",
                  "Equipment Operation",
                  "Video Production"
                ]
              },
              {
                "uuid": "81470549-e57c-5cbd-8469-ad4fc27ab325",
                "display_number": 2,
                "primary_focus": "Film, Television, and Electronic Media",
                "courses_completed": 4,
                "gpa": 3.53,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "FTVE R130",
                    "name": "Beginning Single Camera Production",
                    "grade": "W",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "FTVE R120",
                    "name": "Beginning Audio Production",
                    "grade": "B",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "FTVE R191B",
                    "name": "Work Experience Education in Film, Television, & Electronic Media II",
                    "grade": "A",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "FTVE R106",
                    "name": "Beginning Digital Editing",
                    "grade": "B",
                    "term": "2024-Spring"
                  }
                ],
                "relevant_skills": [
                  "Audio Production",
                  "Equipment Operation",
                  "Video Production"
                ]
              },
              {
                "uuid": "b2b949b9-25cf-597c-b210-19a08148391e",
                "display_number": 3,
                "primary_focus": "Film, Television, and Electronic Media",
                "courses_completed": 2,
                "gpa": 3.5,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "FTVE R135",
                    "name": "Beginning TV Studio Production",
                    "grade": "B",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "FTVE R115",
                    "name": "Introduction to Podcasting and Digital Storytelling",
                    "grade": "A",
                    "term": "2024-Fall"
                  }
                ],
                "relevant_skills": [
                  "Audio Production",
                  "Equipment Operation",
                  "Video Production"
                ]
              },
              {
                "uuid": "fb9836f8-5659-5ba8-a1bb-53e8af9d2ee8",
                "display_number": 4,
                "primary_focus": "Film, Television, and Electronic Media",
                "courses_completed": 6,
                "gpa": 3.33,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "FTVE R155",
                    "name": "Advanced Studio: Live Media Production Practicum",
                    "grade": "A",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "FTVE R130",
                    "name": "Beginning Single Camera Production",
                    "grade": "A",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "FTVE R115",
                    "name": "Introduction to Podcasting and Digital Storytelling",
                    "grade": "A",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "FTVE R113",
                    "name": "Digital Video Editing",
                    "grade": "A",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "FTVE R101",
                    "name": "Film Analysis and Appreciation",
                    "grade": "A",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "FTVE R160",
                    "name": "Introduction to Digital Photography",
                    "grade": "A",
                    "term": "2023-Spring"
                  }
                ],
                "relevant_skills": [
                  "Audio Production",
                  "Equipment Operation",
                  "Video Production"
                ]
              },
              {
                "uuid": "45546671-d34a-5f52-814e-0f72ff158ad6",
                "display_number": 5,
                "primary_focus": "Film, Television, and Electronic Media",
                "courses_completed": 4,
                "gpa": 3.33,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "FTVE R135",
                    "name": "Beginning TV Studio Production",
                    "grade": "A",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "FTVE R106",
                    "name": "Beginning Digital Editing",
                    "grade": "B",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "FTVE R102",
                    "name": "Media Production Planning",
                    "grade": "B",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "FTVE R160",
                    "name": "Introduction to Digital Photography",
                    "grade": "B",
                    "term": "2024-Winter"
                  }
                ],
                "relevant_skills": [
                  "Audio Production",
                  "Equipment Operation",
                  "Video Production"
                ]
              },
              {
                "uuid": "cf7ebe37-5f4a-51a5-a4b1-ddeb02e258fd",
                "display_number": 6,
                "primary_focus": "Film, Television, and Electronic Media",
                "courses_completed": 4,
                "gpa": 3.33,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "FTVE R155",
                    "name": "Advanced Studio: Live Media Production Practicum",
                    "grade": "A",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "FTVE R130",
                    "name": "Beginning Single Camera Production",
                    "grade": "B",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "FTVE R115",
                    "name": "Introduction to Podcasting and Digital Storytelling",
                    "grade": "A",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "FTVE R160",
                    "name": "Introduction to Digital Photography",
                    "grade": "A",
                    "term": "2024-Winter"
                  }
                ],
                "relevant_skills": [
                  "Audio Production",
                  "Equipment Operation",
                  "Video Production"
                ]
              },
              {
                "uuid": "199cbb53-cc1d-5a9a-b5dc-b57649edeb1e",
                "display_number": 7,
                "primary_focus": "Film, Television, and Electronic Media",
                "courses_completed": 2,
                "gpa": 3.33,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "FTVE R130",
                    "name": "Beginning Single Camera Production",
                    "grade": "A",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "FTVE R115",
                    "name": "Introduction to Podcasting and Digital Storytelling",
                    "grade": "W",
                    "term": "2025-Spring"
                  }
                ],
                "relevant_skills": [
                  "Audio Production",
                  "Equipment Operation",
                  "Video Production"
                ]
              },
              {
                "uuid": "a025fa97-591a-54f3-ae2e-4272ff66d25a",
                "display_number": 8,
                "primary_focus": "Art + Design",
                "courses_completed": 1,
                "gpa": 3.25,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "FTVE R135",
                    "name": "Beginning TV Studio Production",
                    "grade": "C",
                    "term": "2024-Winter"
                  }
                ],
                "relevant_skills": [
                  "Audio Production",
                  "Equipment Operation",
                  "Video Production"
                ]
              },
              {
                "uuid": "5d3130d6-6c11-5035-81a1-2fc0106488d1",
                "display_number": 9,
                "primary_focus": "Film, Television, and Electronic Media",
                "courses_completed": 5,
                "gpa": 3.23,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "FTVE R150",
                    "name": "Beginning Motion Picture Production",
                    "grade": "A",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "FTVE R130",
                    "name": "Beginning Single Camera Production",
                    "grade": "W",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "FTVE R115",
                    "name": "Introduction to Podcasting and Digital Storytelling",
                    "grade": "B",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "FT R173",
                    "name": "Fire Service Physical Fitness",
                    "grade": "A",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "FTVE R160",
                    "name": "Introduction to Digital Photography",
                    "grade": "A",
                    "term": "2023-Winter"
                  }
                ],
                "relevant_skills": [
                  "Audio Production",
                  "Equipment Operation",
                  "Video Production"
                ]
              },
              {
                "uuid": "608bd983-2f9c-50a3-b2b1-f90b29207e0a",
                "display_number": 10,
                "primary_focus": "Film, Television, and Electronic Media",
                "courses_completed": 7,
                "gpa": 3.22,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "FTVE R135",
                    "name": "Beginning TV Studio Production",
                    "grade": "A",
                    "term": "2022-Fall"
                  },
                  {
                    "code": "FTVE R115",
                    "name": "Introduction to Podcasting and Digital Storytelling",
                    "grade": "B",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "FTVE R191A",
                    "name": "Work Experience Education in Film, Television, & Electronic Media I",
                    "grade": "D",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "FTVE R104",
                    "name": "Content Creation: The Art of Vlogging",
                    "grade": "A",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "FTVE R103",
                    "name": "Fundamentals of Cinematography and Lighting",
                    "grade": "A",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "FT R167",
                    "name": "Fire Equipment and Apparatus",
                    "grade": "A",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "FTVE R160",
                    "name": "Introduction to Digital Photography",
                    "grade": "B",
                    "term": "2022-Winter"
                  }
                ],
                "relevant_skills": [
                  "Audio Production",
                  "Equipment Operation",
                  "Video Production"
                ]
              }
            ]
          }
        },
        "roadmap": "A conversation between the Film, Television, and Electronic Media department chair and Technicolor's workforce or production operations team could establish site capacity and define the scope of a first cohort. An internship structure of 10-16 weeks mapped to existing work experience or cooperative education courses could formalize the placement for credit. Targeting a first cohort of 4-8 students within two semesters is a realistic starting point given the pipeline across the three contributing departments.",
        "selected_occupations": [],
        "advisory_thesis": "",
        "agenda_topics": []
      },
      "engagementType": "internship",
      "collegeId": "Oxnard College",
      "savedAt": "2026-04-20T00:00:00.000Z",
      "status": "saved",
      "schemaVersion": 8
    },
    {
      "id": "seed-oxnard-curriculum-01",
      "proposal": {
        "employer": "Dole Packaged Foods",
        "sector": "Wholesale",
        "partnership_type": "Curriculum Co-Design",
        "selected_occupation": "Heavy and Tractor-Trailer Truck Drivers",
        "selected_soc_code": "53-3032",
        "core_skills": [
          "Logistics",
          "Regulatory Compliance",
          "Workplace Safety"
        ],
        "gap_skill": "Temperature-Controlled Cargo Handling",
        "regions": [
          "South Central Coast"
        ],
        "opportunity": "Oxnard College's Logistics department is well-positioned to deepen its alignment with Dole Packaged Foods through a co-design partnership focused on temperature-controlled cargo handling. The department builds the logistics and regulatory compliance competencies that heavy truck drivers need in a food distribution environment. Collaboration with Dole could strengthen preparation in perishable-goods transport, where pre-cooling procedures, reefer unit monitoring, and temperature documentation are operational requirements.",
        "opportunity_evidence": [
          {
            "title": "Heavy and Tractor-Trailer Truck Drivers",
            "soc_code": "53-3032",
            "annual_wage": 58170,
            "employment": 4190,
            "annual_openings": 450,
            "growth_rate": 0.02351158
          }
        ],
        "justification": {
          "curriculum_composition": "The Logistics department is the right home for this partnership. Its coursework across five courses develops the logistics and regulatory compliance foundation that underlies professional driving in a food supply chain context. Temperature-controlled cargo handling is a perishable-goods-specific competency that can be more rigorously developed through direct collaboration with Dole Packaged Foods.",
          "curriculum_evidence": [
            {
              "department": "Logistics",
              "courses": [
                {
                  "code": "LOGI R100",
                  "name": "Introduction to Logistics",
                  "description": "This course introduces students to the various elements of logistics. In addition, the course will include information on logistics in relation to manufacturing, commercial transportation and Naval operations. Topics will include logistics systems, supply chain management, order, demand inventory and warehouse management, and the control systems and automated components of logistics systems. Logistics concepts will focus on the system integration and automation and lean manufacturing applications.",
                  "learning_outcomes": [],
                  "skills": [
                    "Logistics"
                  ]
                },
                {
                  "code": "LOGI R101",
                  "name": "Supply Chain Management",
                  "description": "This course provides a detailed study of the key elements of the global supply chain including industry standards, regulations, documentation, transportation, warehousing, technology, management, and pricing. The course examines emerging issues and trends and their impact on tracking and transporting goods.",
                  "learning_outcomes": [],
                  "skills": [
                    "Logistics",
                    "Regulatory Compliance"
                  ]
                },
                {
                  "code": "LOGI R102",
                  "name": "Transportation Systems",
                  "description": "This class examines the structure and importance of the commercial transportation industry in the logistics sector of business. Topics covered encompass the various modes of transportation including discussions of regulations, economics, characteristics, and development in major transportation modes. Also discussed are costing and pricing issues in transportation and relationship management between buyers and sellers of transportation.",
                  "learning_outcomes": [],
                  "skills": [
                    "Logistics",
                    "Regulatory Compliance"
                  ]
                },
                {
                  "code": "LOGI R103",
                  "name": "Imports and Exports",
                  "description": "This course provides an overview of the fundamentals of importing and exporting with an emphasis on export-related programs and the network of government support agencies that are involved in international trade. The course focuses on finding new market segments overseas, logistics, documentation, contract administration, terminology, quality control, and payment procedures.",
                  "learning_outcomes": [],
                  "skills": [
                    "Logistics"
                  ]
                },
                {
                  "code": "LOGI R104",
                  "name": "Introduction to Global Business",
                  "description": "This class teaches an introduction to global business, ethics, finance and logistics. The course will cover how political, economic, and cultural differences affect the global business environment. The class examines issues related to the importing and exporting of goods, supply chain management, and production.",
                  "learning_outcomes": [],
                  "skills": [
                    "Logistics"
                  ]
                }
              ],
              "aligned_skills": [
                "Logistics",
                "Regulatory Compliance"
              ]
            }
          ],
          "student_composition": "Students in the Logistics department are studying the logistics and regulatory compliance skills that apply directly to this role. They represent a natural cohort for a co-design effort that deepens their preparation for the operational demands of refrigerated freight in a food distribution context.",
          "student_evidence": {
            "total_in_program": 0,
            "with_all_core_skills": 0,
            "top_students": []
          }
        },
        "roadmap": "A working group between the Logistics department chair and Dole Packaged Foods' transportation or operations leadership could evaluate how temperature-controlled cargo handling is addressed in existing coursework. One potential starting point is a focused curriculum review of loading, transit monitoring, and documentation protocols specific to refrigerated and frozen freight. Revised content could be piloted within the next catalog cycle.",
        "selected_occupations": [],
        "advisory_thesis": "",
        "agenda_topics": []
      },
      "engagementType": "curriculum_codesign",
      "collegeId": "Oxnard College",
      "savedAt": "2026-04-20T00:00:00.000Z",
      "status": "saved",
      "schemaVersion": 8
    }
  ],
  "Foothill College": [
    {
      "id": "seed-foothill-advisory-01",
      "proposal": {
        "employer": "Johnson & Johnson Vision",
        "sector": "Wholesale",
        "partnership_type": "Advisory Board",
        "selected_occupation": "Bioengineers and Biomedical Engineers",
        "selected_soc_code": "17-2031",
        "core_skills": [
          "Biology",
          "Engineering & Technology",
          "Electrical Systems",
          "Troubleshooting",
          "Software Development",
          "Programming"
        ],
        "gap_skill": "",
        "regions": [
          "Orange County",
          "Bay Area"
        ],
        "opportunity": "Johnson & Johnson Vision's position at the intersection of medical device manufacturing and eye health innovation makes it a compelling advisory board partner for Foothill College's technical programs. The company applies biomedical engineering, embedded software development, and hands-on device repair within a regulated product environment \u2014 a combination that maps directly onto the applied technical preparation these programs provide. Formalizing that perspective as an advisory board creates a standing channel for industry guidance with no grant funding required.",
        "opportunity_evidence": [
          {
            "title": "Medical Equipment Repairers",
            "soc_code": "49-9062",
            "annual_wage": 82260,
            "employment": 1380,
            "annual_openings": 130,
            "growth_rate": 0.046982336
          },
          {
            "title": "Bioengineers and Biomedical Engineers",
            "soc_code": "17-2031",
            "annual_wage": 136050,
            "employment": 930,
            "annual_openings": 70,
            "growth_rate": 0.068233972
          },
          {
            "title": "Software Developers",
            "soc_code": "15-1252",
            "annual_wage": 194960,
            "employment": 169710,
            "annual_openings": 11440,
            "growth_rate": 0.072506539
          }
        ],
        "justification": {
          "curriculum_composition": "The Computer Science department provides the closest curricular match to J&J Vision's software and firmware operations, with 40 courses developing software development, programming, and troubleshooting competencies central to the company's technical workforce. The Biology department contributes the biological and engineering foundations that biomedical engineering roles at J&J Vision draw on. Physical Sciences & Engineering, while smaller in course volume, addresses engineering and technology principles relevant to the device manufacturing environment.",
          "curriculum_evidence": [
            {
              "department": "Computer Science",
              "courses": [
                {
                  "code": "C S 10",
                  "name": "COMPUTER ARCHITECTURE & ORGANIZATION",
                  "description": "Introduction to the organization, architecture and machine-level programming of computer systems. Topics include mapping of high-level language constructs into assembly code, internal data representations, numerical computation, virtual memory, pipelines, caching, multitasking, MIPS architecture, MIPA assembly language code, interrupts, input/output, peripheral storage processing, and comparison of CISC (Intel) and RISC (MIPS) instruction sets.",
                  "learning_outcomes": [],
                  "skills": [
                    "Engineering & Technology",
                    "Programming",
                    "Troubleshooting"
                  ]
                },
                {
                  "code": "C S 11A",
                  "name": "INTRODUCTION TO ARTIFICIAL INTELLIGENCE",
                  "description": "A survey of arti\ufb01cial intelligence (AI) and its application. Includes search algorithms, evolutionary algorithms, and machine learning. Explores issues of ethics and equity. Students will use Python and publicly available packages to develop and test AI models. Students will gain practical experience coding models, with less emphasis on math and theory.",
                  "learning_outcomes": [],
                  "skills": [
                    "Engineering & Technology",
                    "Programming",
                    "Software Development"
                  ]
                },
                {
                  "code": "C S 12A",
                  "name": "INTRODUCTION TO MACHINE LEARNING",
                  "description": "A survey of machine learning algorithms and modern packages. Includes models in supervised, unsupervised, and reinforcement learning. Explores the entire machine learning pipeline from dataset selection through model evaluation. Students will gain practical experience coding models, with less emphasis on math and theory.",
                  "learning_outcomes": [],
                  "skills": [
                    "Engineering & Technology",
                    "Programming",
                    "Software Development"
                  ]
                },
                {
                  "code": "C S 18",
                  "name": "DISCRETE MATHEMATICS",
                  "description": "This course is for any student majoring in math or computer science, as well as for students interested in the topics taught in this course. Discrete mathematics: set theory, logic, Boolean algebra, methods of proof, mathematical induction, number theory, discrete probability, combinatorics, functions, relations, recursion, algorithm ef\ufb01ciencies, graphs, trees.",
                  "learning_outcomes": [],
                  "skills": [
                    "Programming"
                  ]
                },
                {
                  "code": "C S 1A",
                  "name": "OBJECT-ORIENTED PROGRAMMING METHODOLOGIES IN JAVA",
                  "description": "Systematic introduction to fundamental concepts of computer science through the study of the Java programming language. Coding topics include Java control structures, classes, methods, arrays, graphical user interfaces and elementary data structures. Concept topics include algorithms, recursion, data abstraction, problem solving strategies, code style, documentation, debugging techniques and testing.",
                  "learning_outcomes": [],
                  "skills": [
                    "Programming",
                    "Software Development"
                  ]
                },
                {
                  "code": "C S 1B",
                  "name": "INTERMEDIATE SOFTWARE DESIGN IN JAVA",
                  "description": "Systematic treatment of intermediate concepts in computer science through the study of Java object-oriented programming (OOP). Coding topics include Java interfaces, class extension, generics, the Java collections framework, multi-dimensional arrays and \ufb01le I/O. Concept topics include OOP project design, inheritance, polymorphism, method chaining, functional programming, linked-lists, FIFOs, LIFOs, event-driven programming and guarded code.",
                  "learning_outcomes": [],
                  "skills": [
                    "Programming",
                    "Software Development"
                  ]
                },
                {
                  "code": "C S 1C",
                  "name": "ADVANCED DATA STRUCTURES & ALGORITHMS IN JAVA",
                  "description": "Systematic treatment of advanced data structures, algorithm analysis and abstract data types in the Java programming language. Coding topics include the development of ADTs from scratch, building ADTs on top of the java.util collections, array lists, linked lists, trees, maps, hashing functions and graphs. Concept topics include searching, big-O time complexity, analysis of all major sorting techniques, top down splaying, AVL tree balancing, shortest path algorithms, minimum spanning trees and maximum flow graphs.",
                  "learning_outcomes": [],
                  "skills": [
                    "Programming",
                    "Software Development"
                  ]
                },
                {
                  "code": "C S 203A",
                  "name": "JUST-IN-TIME SUPPORT FOR C S 3A",
                  "description": "A just-in-time approach to the core prerequisite skills, competencies, and concepts needed in C S 3A. Intended for students who are concurrently enrolled in C S 3A at Foothill College. Topics include: installation of an integrated development environment and other software, navigating a \ufb01le system hierarchy, developing a logic-based approach to programming, identifying errors in a program using a debugger and other means.",
                  "learning_outcomes": [],
                  "skills": [
                    "Programming",
                    "Troubleshooting"
                  ]
                },
                {
                  "code": "C S 20A",
                  "name": "PROGRAMMING IN C#",
                  "description": "Introduction to the C# programming language and the .NET platform. Topics include object oriented programming, graphical user interfaces, elementary data structures, algorithms, recursion, data abstraction, code style, documentation, debugging techniques, and testing.",
                  "learning_outcomes": [],
                  "skills": [
                    "Programming",
                    "Software Development"
                  ]
                },
                {
                  "code": "C S 22A",
                  "name": "JAVASCRIPT FOR PROGRAMMERS",
                  "description": "Introduction to object oriented programming in JavaScript. Topics include: client and server side programming, Model/View/Controller architecture, current tools and testing methods, interaction with HTML and CSS, Document Object Model, XML, and JSON. Students will have practice writing programs for mobile web browsers and creating dynamic webpages including animation.",
                  "learning_outcomes": [],
                  "skills": [
                    "Programming",
                    "Software Development"
                  ]
                },
                {
                  "code": "C S 2A",
                  "name": "OBJECT-ORIENTED PROGRAMMING METHODOLOGIES IN C++",
                  "description": "Systematic introduction to fundamental concepts of computer science through the study of the C++ programming language. Coding topics include C++ control structures, objects, global-scope functions, class methods, arrays and elementary data structures. Concept topics include algorithms, recursion, data abstraction, problem solving strategies, code style, documentation, debugging techniques and testing.",
                  "learning_outcomes": [],
                  "skills": [
                    "Programming",
                    "Software Development"
                  ]
                },
                {
                  "code": "C S 2B",
                  "name": "INTERMEDIATE SOFTWARE DESIGN IN C++",
                  "description": "Systematic treatment of intermediate concepts in computer science through the study of C++ object-oriented programming (OOP). Coding topics include C++ derived classes, class templates, function templates, virtual functions, operator overloading, an introduction to the Standard Template Library, multiple inheritance, pointers, dynamic memory allocation and \ufb01le I/O. Concept topics include OOP project design, inheritance, polymorphism, method chaining, functional programming, linked-lists, FIFOs, LIFOs, events in GUIs and guarded code.",
                  "learning_outcomes": [],
                  "skills": [
                    "Programming",
                    "Software Development"
                  ]
                },
                {
                  "code": "C S 2C",
                  "name": "ADVANCED DATA STRUCTURES & ALGORITHMS IN C++",
                  "description": "Systematic treatment of advanced data structures, algorithm analysis and abstract data types in the C++ programming language. Coding topics include the development of ADTs from scratch, building ADTs on top of the STL templates, vectors, lists, trees, maps, hashing functions and graphs. Concept topics include searching, big-O time complexity, analysis of all major sorting techniques, top down splaying, AVL tree balancing, shortest path algorithms, minimum spanning trees and maximum flow graphs.",
                  "learning_outcomes": [],
                  "skills": [
                    "Programming",
                    "Software Development"
                  ]
                },
                {
                  "code": "C S 30A",
                  "name": "INTRODUCTION TO LINUX",
                  "description": "Introduction to the Linux operating system primarily focused on command line usage. Covers the history, kernel, \ufb01le systems, shells, and user utilities. Also introduces students to the fundamentals of shell programming, processes, communications, and basic security.",
                  "learning_outcomes": [],
                  "skills": [
                    "Programming"
                  ]
                },
                {
                  "code": "C S 30B",
                  "name": "LINUX SHELL PROGRAMMING",
                  "description": "Linux shell script programming using the Bourne Again shell programming language (bash) and Linux utilities to create practical shell scripts. Topics covered include customizing the environment, running and writing scripts, variables, loops, functions, text processing and debugging.",
                  "learning_outcomes": [],
                  "skills": [
                    "Programming",
                    "Troubleshooting"
                  ]
                },
                {
                  "code": "C S 30C",
                  "name": "LINUX SYSTEM ADMINISTRATION",
                  "description": "Basic Linux systems administration. Command line fundamentals, \ufb01le management from command line, help commands, create/view/edit text \ufb01les, manage local Linux users and groups, control access to \ufb01les with Linux \ufb01le system permissions, monitor and manage Linux processes, control services and daemons, con\ufb01gure and secure OpenSSH service, analyze and store logs, manage Linux networking, archive and copy \ufb01les between systems, install and update software packages, access Linux \ufb01le systems, use virtualized systems.",
                  "learning_outcomes": [],
                  "skills": [
                    "Troubleshooting"
                  ]
                },
                {
                  "code": "C S 30D",
                  "name": "ADVANCED LINUX SYSTEM ADMINISTRATION",
                  "description": "Advanced systems administration of Red Hat Enterprise Linux (RHEL). Overview of automated installation, basic Linux command line usage, regular expression overview, pipelines, redirection, network con\ufb01guration and troubleshooting, simple partition and \ufb01lesystems creation, logical volumes, SMB and NFS network \ufb01le systems, user account management, access control lists (ACLs), SELinux security overview, software package management, installed services management, log \ufb01le analysis and maintenance, process management, Linux kernel tuning and maintenance, Linux troubleshooting techniques.",
                  "learning_outcomes": [],
                  "skills": [
                    "Troubleshooting"
                  ]
                },
                {
                  "code": "C S 30E",
                  "name": "LINUX SYSTEM ADMINISTRATION: NETWORK SERVICES",
                  "description": "The course is focused on deploying and managing network servers running caching Domain Name Service (DNS), MariaDB, Apache HTTPD, Post\ufb01x SMTP mail clients, network \ufb01le sharing with Network File System (NFS) and Server Message Block (SMB), iSCSI initiators and targets, advanced networking facilities and \ufb01rewall con\ufb01gurations, and the use of Bash shell scripting to help automate, con\ufb01gure, and troubleshoot the system. These topics are taught through lectures and hands-on labs.",
                  "learning_outcomes": [],
                  "skills": [
                    "Programming",
                    "Troubleshooting"
                  ]
                },
                {
                  "code": "C S 31A",
                  "name": "INTRODUCTION TO DATABASE MANAGEMENT SYSTEMS",
                  "description": "Introduction to database design and use of database management systems for applications. Topics include database architecture, comparison to \ufb01le-based systems, historical data models, conceptual model; integrity constraints and triggers; functional dependencies and normal forms; relational model, algebra, database processing and Structured Query Language (SQL), database access from Applications-Embedded SQL, JDBC, Cursors, Dynamic SQL, Stored Procedures. Emerging trends will be studied, such as NoSQL databases, internet and databases, and Online Analytical Processing (OLAP). A team project that builds a database application for a real-world scenario is an important element of the course.",
                  "learning_outcomes": [],
                  "skills": [
                    "Programming",
                    "Software Development"
                  ]
                },
                {
                  "code": "C S 3A",
                  "name": "OBJECT-ORIENTED PROGRAMMING METHODOLOGIES IN PYTHON",
                  "description": "Systematic introduction to fundamental concepts of computer science through the study of the Python programming language. Coding topics include control structures, functions, classes, string processing, lists, tuples, dictionaries, working with \ufb01les, and elementary graphics. Concept topics include algorithms, data abstraction, problem solving strategies, code style, documentation, debugging techniques and testing.",
                  "learning_outcomes": [],
                  "skills": [
                    "Programming",
                    "Software Development"
                  ]
                },
                {
                  "code": "C S 3B",
                  "name": "INTERMEDIATE SOFTWARE DESIGN IN PYTHON",
                  "description": "Systematic treatment of intermediate concepts in computer science through the study of Python object-oriented programming (OOP). Coding topics include Python sequences, user-de\ufb01ned classes and interfaces, modules, packages, collection classes, threads, lambda expressions, list comprehensions, regular expressions and multi-dimensional arrays. Concept topics include OOP project design, recursion, inheritance, polymorphism, functional programming, linked-lists, FIFOs, LIFOs, event-driven parsing, exceptions, and guarded code.",
                  "learning_outcomes": [],
                  "skills": [
                    "Programming",
                    "Software Development"
                  ]
                },
                {
                  "code": "C S 3C",
                  "name": "ADVANCED DATA STRUCTURES & ALGORITHMS IN PYTHON",
                  "description": "A systematic treatment of advanced data structures, algorithm analysis, and abstract data types in the Python programming language, intended for computer science majors as well as non-majors and professionals seeking advanced Python experience. Coding topics include large program software engineering design, multi-dimensional arrays, string processing, primitives, compound types, and allocation of instance and static data. Data structure concept topics include dynamic memory, inheritance, polymorphism, hierarchies, recursion, linked-lists, stacks, queues, trees, hash tables, and graphs. Algorithm concept topics include searching, big-O time complexity, analysis of all major sorting techniques, top down splaying, AVL tree balancing, shortest path algorithms, minimum spanning trees, and maximum flow graphs.",
                  "learning_outcomes": [],
                  "skills": [
                    "Programming",
                    "Software Development"
                  ]
                },
                {
                  "code": "C S 40A",
                  "name": "SOFTWARE ENGINEERING METHODOLOGIES",
                  "description": "A collaboration-oriented course that trains students in the techniques currently used by software engineers to develop reliable products in an ef\ufb01cient manner. The course emphasizes Agile methods and a variety of tools used during the software development lifecycle.",
                  "learning_outcomes": [],
                  "skills": [
                    "Engineering & Technology",
                    "Software Development"
                  ]
                },
                {
                  "code": "C S 48A",
                  "name": "DATA VISUALIZATION",
                  "description": "Introduction to the effective processing and communication of data. Topics include identifying the key techniques and theory used in data visualization, creating and designing static and interactive visualizations using data, and communicating insight through data visualization to an intended audience. Students will use a data visualization package, such as R, Tableau, or MatPlotLib in Python.",
                  "learning_outcomes": [],
                  "skills": [
                    "Programming"
                  ]
                },
                {
                  "code": "C S 49",
                  "name": "FOUNDATIONS OF COMPUTER PROGRAMMING",
                  "description": "Introduction to basic computer programming concepts using an object-oriented language. Topics include the software life-cycle, procedural vs. object-oriented programming, IDE and debugging, documentation, and coding conventions. Using an object-oriented computer language, students will explore data types, basic data structures and algorithms, control structure, console and \ufb01le I/O, functions, error handling and testing.",
                  "learning_outcomes": [],
                  "skills": [
                    "Programming",
                    "Software Development"
                  ]
                },
                {
                  "code": "C S 50A",
                  "name": "NETWORK BASICS (CCNA)",
                  "description": "Introduction to the architecture, structure, functions, components, and models of the internet and other computer networks. The principles and structure of IP addressing and the fundamentals of Ethernet concepts, media, and operations are introduced to provide a foundation for the curriculum. Students will be able to build simple LANs, perform basic con\ufb01gurations for routers and switches, and implement IP addressing schemes.",
                  "learning_outcomes": [],
                  "skills": [
                    "Engineering & Technology",
                    "Troubleshooting"
                  ]
                },
                {
                  "code": "C S 50B",
                  "name": "ROUTING & SWITCHING ESSENTIALS (CCNA)",
                  "description": "This course describes the architecture, components, and operations of routers and switches in a small network. Students learn how to con\ufb01gure a router and a switch for basic functionality. By the end of this course students will be able to con\ufb01gure and troubleshoot routers and switches and resolve common issues with RIPv1, RIPv2, single-area and multi-area OSPF, virtual LANs, and inter-VLAN routing in both IPv4 and IPv6 networks. This course is preparation for the CCENT and CCNA certi\ufb01cation exams. This course describes the architecture, components, and operations of routers, and explains the principles of routing and routing protocols. Students will be given the opportunity to con\ufb01gure a router for basic and advanced functionality. Students will be able to con\ufb01gure and troubleshoot routers and resolve common issues with RIPv1, RIPv2, EIGRP, and OSPF in both IPv4 and IPv6 networks.",
                  "learning_outcomes": [],
                  "skills": [
                    "Engineering & Technology",
                    "Troubleshooting"
                  ]
                },
                {
                  "code": "C S 50C",
                  "name": "SCALING LOCAL AREA NETWORKS (CCNA)",
                  "description": "This course describes the architecture, components, and operations of routers and switches in larger and more complex networks. Students learn how to con\ufb01gure routers and switches for advanced functionality. By the end of this course, students will be able to con\ufb01gure and troubleshoot routers and switches and resolve common issues with OSPF, EIGRP, and STP in both IPv4 and IPv6 networks. Students will also develop the knowledge and skills needed to implement a WLAN in a small-to-medium network.",
                  "learning_outcomes": [],
                  "skills": [
                    "Engineering & Technology",
                    "Troubleshooting"
                  ]
                },
                {
                  "code": "C S 53C",
                  "name": "ETHICAL HACKING",
                  "description": "Surveys current techniques used by malicious hackers to attack computers and networks, and develops the defenses that security professionals use to defend Windows and Linux systems from such attacks. Topics will be presented in the context of legal restrictions and ethical guidelines. Hands-on labs, playing the role of both attacker and defender, using port scans, footprinting, buffer overflow exploits, SQL injection, privilege escalation, Trojans, and backdoors.",
                  "learning_outcomes": [],
                  "skills": [
                    "Troubleshooting"
                  ]
                },
                {
                  "code": "C S 55A",
                  "name": "INTRODUCTION TO CLOUD COMPUTING IN AMAZON WEB SERVICES",
                  "description": "This course introduces cloud computing which shifts information systems from on-premises computing infrastructure to highly scalable internet architectures using the Amazon AWS platform. The course provides a basic understanding of cloud computing technologies and provides students with the abilities to con\ufb01gure, deploy, and manage cloud facilities including simple and complex compute instances, web servers, and web services. The course also demonstrates/makes available the AWS Educate platform for educational, industry career path guidance and career opportunities.",
                  "learning_outcomes": [],
                  "skills": [
                    "Engineering & Technology"
                  ]
                },
                {
                  "code": "C S 55B",
                  "name": "DATABASE ESSENTIALS IN AMAZON WEB SERVICES",
                  "description": "This course addresses database fundamentals and cloud database design patterns and management. A wide variety of database needs are presented, such as structured, semi-structured, and unstructured datasets, and how those are supported in the cloud. Students learn to deploy a SQL database on infrastructure components and perform basic data operations on that infrastructure. Students then take those basic concepts and learn managed platform as a service solutions, such as Amazon RDS, Amazon DynamoDB, Amazon Kinesis stream processing/ analytics, in memory database accelerators, and ML big data tools. Basic database administration skills, such as migration, backups, restoration, retention, service con\ufb01guration, high availability, and service scaling, are presented.",
                  "learning_outcomes": [],
                  "skills": [
                    "Programming"
                  ]
                },
                {
                  "code": "C S 55C",
                  "name": "COMPUTE ENGINES IN AMAZON WEB SERVICES",
                  "description": "In this course, students explore how compute workloads are supported using a set of core technologies in the Amazon Web Services (AWS) platform. Students use the AWS Management Console, Command Line Interface (CLI), and Cloud Formation infrastructure deployment tools to deploy services. The course takes a deep look into virtualization using AWS Elastic Compute Cloud (EC2) by detailing con\ufb01guration options for speci\ufb01c workloads in terms of performant compute/memory/storage capabilities. Modern application architectures, such as serverless, microservices, containerization, service orchestration, and edge computing, are detailed and their deployment using AWS services are demonstrated.",
                  "learning_outcomes": [],
                  "skills": [
                    "Engineering & Technology",
                    "Software Development"
                  ]
                },
                {
                  "code": "C S 56B",
                  "name": "IT ESSENTIALS",
                  "description": "The course presents a working knowledge of computer internals and provides practical skills in computer hardware assembly and software installation. Emphasis is placed on troubleshooting problems throughout the process. Activities include hands-on labs and virtual learning tools which encourage critical thinking and complex problem-solving skills.",
                  "learning_outcomes": [],
                  "skills": [
                    "Engineering & Technology",
                    "Software Development",
                    "Troubleshooting"
                  ]
                },
                {
                  "code": "C S 63A",
                  "name": "DEVELOPING APPLICATIONS FOR IOS",
                  "description": "An introduction to programming the iPhone and other iOS devices. Covers Swift, Cocoa Touch, and the Model/View/Controller architecture. Students learn the basics of Swift and acquire practical experience with the tools, techniques, and concepts needed to build a basic iOS app from scratch.",
                  "learning_outcomes": [],
                  "skills": [
                    "Programming",
                    "Software Development"
                  ]
                },
                {
                  "code": "C S 64A",
                  "name": "WRITING APPS FOR THE ANDROID",
                  "description": "Introduction to programming mobile apps for the Android. Coding topics include the Android SDK for Eclipse, the ADT plugin, XML fundamentals, and a survey of API methods and objects used to control the Android user interface. Concept topics include layouts, activity lifecycles, runtime binding, intents, location awareness, audio, video, OpenGL ES, and monetizing apps.",
                  "learning_outcomes": [],
                  "skills": [
                    "Programming",
                    "Software Development"
                  ]
                },
                {
                  "code": "C S 77A",
                  "name": "ADVANCED WEB APPLICATION DEVELOPMENT",
                  "description": "Design and develop applications that deliver similar features and functions normally associated with desktop applications using modern web client and server technologies.",
                  "learning_outcomes": [],
                  "skills": [
                    "Programming",
                    "Software Development"
                  ]
                },
                {
                  "code": "C S 77B",
                  "name": "PROJECTS IN WEB APPLICATION DEVELOPMENT",
                  "description": "Team-based applied web application projects as determined in consultation with the instructor. Students meet at least twice per week with the instructor; about half of the lecture periods are team project-based interactions. Volunteer or work-based learning portfolio, progress reports, oral presentations, \ufb01nal report, teamwork assessments, and evaluation by project supervisor or client will be used to demonstrate the mastery of competencies identi\ufb01ed as goals prior to, or near the start of, the project(s). Project work can be within the context of an internship or developing an internship or start-up opportunity.",
                  "learning_outcomes": [],
                  "skills": [
                    "Software Development"
                  ]
                },
                {
                  "code": "C S 80A",
                  "name": "OPEN SOURCE CONTRIBUTION",
                  "description": "Introduction to the tools for, and culture of, contributing to open source software projects. Tool-based topics include Git repositories, pull requests, forks, logs, merges, tagging, rebasing and server con\ufb01guration. Concept topics include commit guidelines, branching workflows, small- team vs. large-team workflows, project maintenance, iterative staging, selecting viable source communities, joining public projects, setting up accurate dev environments, testing and prepping patch merges, and becoming a committer.",
                  "learning_outcomes": [],
                  "skills": [
                    "Software Development"
                  ]
                },
                {
                  "code": "C S 84A",
                  "name": "DATABASE-DRIVEN WEB APPLICATION DEVELOPMENT",
                  "description": "Students evolve simple static websites into dynamic, database-driven web applications. Students will use the popular LAMP framework (Linux, Apache, MySQL, and PHP), in combination with JavaScript, CSS, and HTML5.",
                  "learning_outcomes": [],
                  "skills": [
                    "Programming",
                    "Software Development"
                  ]
                },
                {
                  "code": "C S 8A",
                  "name": "INTRODUCTION TO DATA SCIENCE",
                  "description": "Introduction to the fundamental concepts and computational skills needed to understand and analyze data arising from real-world phenomena. Topics include key data science concepts such as correlation vs. causation, randomness, sampling, uncertainty, predictive models, and classi\ufb01cation. Using a tool such as Jupyter notebooks, students write code for transformation and use of data tables, simulation models, and A/B testing.",
                  "learning_outcomes": [],
                  "skills": [
                    "Programming"
                  ]
                }
              ],
              "aligned_skills": [
                "Engineering & Technology",
                "Programming",
                "Software Development",
                "Troubleshooting"
              ]
            },
            {
              "department": "Biology",
              "courses": [
                {
                  "code": "BIOL 10",
                  "name": "GENERAL BIOLOGY: BASIC PRINCIPLES",
                  "description": "Methods of science and basic principles of biology. Special emphasis on genetics, ecology, evolution, overpopulation, nutrition, and disease prevention.",
                  "learning_outcomes": [],
                  "skills": [
                    "Biology"
                  ]
                },
                {
                  "code": "BIOL 12",
                  "name": "HUMAN GENETICS",
                  "description": "An introduction to the nature of human inheritance. The molecular basis of inheritance, Mendelian genetics, population genetics, common human genetic diseases, factors affecting human diversity, and the social and moral implications of recent advances in genetics. Intended for both majors and GE students.",
                  "learning_outcomes": [],
                  "skills": [
                    "Biology"
                  ]
                },
                {
                  "code": "BIOL 13",
                  "name": "MARINE BIOLOGY",
                  "description": "An introduction to biology using marine animals, plants, and ecosystems. Major emphasis given to the ecology and conservation issues with examples drawn from California marine life. Conceptual development of seashore, estuaries, coral reefs, kelp forests, and pelagic life as interrelated ecosystems.",
                  "learning_outcomes": [],
                  "skills": [
                    "Biology"
                  ]
                },
                {
                  "code": "BIOL 14",
                  "name": "HUMAN BIOLOGY",
                  "description": "An introduction to biology using human beings as the exemplary organism. The evolution and biological unity of the human species and of all life forms; American and global patterns of human biological diversity; reproduction and heredity; how human organ systems function; humans and their environment; the uses and misuses of the scienti\ufb01c method; the scienti\ufb01c and biological bases for human equality.",
                  "learning_outcomes": [],
                  "skills": [
                    "Biology"
                  ]
                },
                {
                  "code": "BIOL 15",
                  "name": "CALIFORNIA ECOLOGY/NATURAL HISTORY",
                  "description": "An introduction to ecology, natural history, and \ufb01eld biology through the study, largely in an outdoor setting, of the plants and animals of the San Francisco Bay Area.",
                  "learning_outcomes": [],
                  "skills": [
                    "Biology"
                  ]
                },
                {
                  "code": "BIOL 1A",
                  "name": "PRINCIPLES OF CELL BIOLOGY",
                  "description": "An introduction to biological molecules, cellular structure and function, bioenergetics, the genetics of both prokaryotic and eukaryotic organisms, cell communication and signaling, the cell cycle, and elements of molecular biology. Intended for biology majors.",
                  "learning_outcomes": [],
                  "skills": [
                    "Biology"
                  ]
                },
                {
                  "code": "BIOL 1B",
                  "name": "FORM & FUNCTION IN PLANTS & ANIMALS",
                  "description": "An introduction to the structure and physiological processes of plants and animals. Transport systems, reproduction, digestion, gas exchange, regulation of the internal environment, responses to external stimuli, nervous systems, hormones, and locomotion. Intended for biology majors.",
                  "learning_outcomes": [],
                  "skills": [
                    "Biology"
                  ]
                },
                {
                  "code": "BIOL 1C",
                  "name": "EVOLUTION, SYSTEMATICS & ECOLOGY",
                  "description": "Principles of evolutionary theory, classi\ufb01cation of organisms, and basic ecology. Phylogenetic survey of the major groups of organisms (bacteria, archaea, protistans, plants, animals, and fungi) and their evolutionary history. Intended for biology majors.",
                  "learning_outcomes": [],
                  "skills": [
                    "Biology"
                  ]
                },
                {
                  "code": "BIOL 1D",
                  "name": "INTRODUCTION TO MOLECULAR GENETICS",
                  "description": "Intended for students wishing to transfer to a four year school with a major in molecular biology, biochemistry, or molecular genetics. An introduction to molecular genetics with an emphasis in genome organization, DNA replication and repair, mutation, transcription, translation, and the regulation of gene expression.",
                  "learning_outcomes": [],
                  "skills": [
                    "Biology"
                  ]
                },
                {
                  "code": "BIOL 28",
                  "name": "INTRODUCTION TO BIOENGINEERING",
                  "description": "Introduction to the \ufb01eld of bioengineering. Topics covered will include an overview of basic biological systems and biochemistry for non-biology majors, how the basic principles of engineering and physics can be applied to problems in biological science, and an overview of current trends in bioengineering, including: medical devices, biomaterials, bioinstrumentation, computational biology, and agricultural biotechnology.",
                  "learning_outcomes": [],
                  "skills": [
                    "Biology",
                    "Engineering & Technology"
                  ]
                },
                {
                  "code": "BIOL 40A",
                  "name": "HUMAN ANATOMY & PHYSIOLOGY I",
                  "description": "Human anatomy and physiology with an emphasis on integration of systems and homeostatic mechanisms. Physical and chemical basis of life, histology and integumentary, skeletal and muscular systems. This course is primarily intended for nursing, allied health, kinesiology, and other health-related majors.",
                  "learning_outcomes": [],
                  "skills": [
                    "Biology"
                  ]
                },
                {
                  "code": "BIOL 40B",
                  "name": "HUMAN ANATOMY & PHYSIOLOGY II",
                  "description": "Human anatomy and physiology with an emphasis on integration of systems and homeostatic mechanisms for the nervous, cardiovascular, and respiratory systems. This course is primarily intended for nursing, allied health, kinesiology, and other health-related majors.",
                  "learning_outcomes": [],
                  "skills": [
                    "Biology"
                  ]
                },
                {
                  "code": "BIOL 40C",
                  "name": "HUMAN ANATOMY & PHYSIOLOGY III",
                  "description": "Human anatomy and physiology with an emphasis on integration of systems and homeostatic mechanisms for the digestive system, metabolism, urinary system, fluid, electrolyte and acid/base balance, lymphatic system, endocrine system, and reproductive system. This course is primarily intended for nursing, allied health, kinesiology, and other health-related majors.",
                  "learning_outcomes": [],
                  "skills": [
                    "Biology"
                  ]
                },
                {
                  "code": "BIOL 41",
                  "name": "MICROBIOLOGY",
                  "description": "Morphology and physiology of microorganisms with emphasis on the important roles that microbes play in human life. Mechanisms of pathogenicity, host-parasite relationships, the immune response and principles of disease transmission. Techniques of microbial control including sterilization, aseptic procedures, use of disinfectants, antiseptics and chemotherapy. Basic laboratory skills of microbiology.",
                  "learning_outcomes": [],
                  "skills": [
                    "Biology"
                  ]
                },
                {
                  "code": "BIOL 45",
                  "name": "INTRODUCTION TO HUMAN NUTRITION",
                  "description": "Introduction to the medical aspects of nutrition, intended for students wishing to pursue a career in health care. Biological function and chemical classi\ufb01cation of nutrients. Nutritional needs throughout the lifespan. Effects of nutritional de\ufb01ciencies and excesses. Recommended nutrient intakes and the role of diet in the development of chronic disease.",
                  "learning_outcomes": [],
                  "skills": [
                    "Biology"
                  ]
                },
                {
                  "code": "BIOL 54H",
                  "name": "HONORS INSTITUTE SEMINAR IN BIOLOGY",
                  "description": "A seminar in directed readings, discussions and projects in biology. Speci\ufb01c topic to be determined by the instructor. This advanced honors course is open to all majors.",
                  "learning_outcomes": [],
                  "skills": [
                    "Biology"
                  ]
                },
                {
                  "code": "BIOL 70R",
                  "name": "INDEPENDENT STUDY IN BIOLOGY",
                  "description": "Provides an opportunity for the student to expand their studies in Biology beyond the classroom by completing a project or an assignment arranged by agreement between the student and instructor. The student is required to contract with the instructor to determine the scope of assignment and the unit value assigned for successful completion. Students may take a maximum of 6 units of Independent Study per department.",
                  "learning_outcomes": [],
                  "skills": [
                    "Biology"
                  ]
                },
                {
                  "code": "BIOL 71R",
                  "name": "INDEPENDENT STUDY IN BIOLOGY",
                  "description": "Provides an opportunity for the student to expand their studies in Biology beyond the classroom by completing a project or an assignment arranged by agreement between the student and instructor. The student is required to contract with the instructor to determine the scope of assignment and the unit value assigned for successful completion. Students may take a maximum of 6 units of Independent Study per department.",
                  "learning_outcomes": [],
                  "skills": [
                    "Biology"
                  ]
                },
                {
                  "code": "BIOL 72R",
                  "name": "INDEPENDENT STUDY IN BIOLOGY",
                  "description": "Provides an opportunity for the student to expand their studies in Biology beyond the classroom by completing a project or an assignment arranged by agreement between the student and instructor. The student is required to contract with the instructor to determine the scope of assignment and the unit value assigned for successful completion. Students may take a maximum of 6 units of Independent Study per department.",
                  "learning_outcomes": [],
                  "skills": [
                    "Biology"
                  ]
                },
                {
                  "code": "BIOL 73R",
                  "name": "INDEPENDENT STUDY IN BIOLOGY",
                  "description": "Provides an opportunity for the student to expand their studies in Biology beyond the classroom by completing a project or an assignment arranged by agreement between the student and instructor. The student is required to contract with the instructor to determine the scope of assignment and the unit value assigned for successful completion. Students may take a maximum of 6 units of Independent Study per department.",
                  "learning_outcomes": [],
                  "skills": [
                    "Biology"
                  ]
                },
                {
                  "code": "BIOL 8",
                  "name": "BASIC NUTRITION",
                  "description": "Introductory nutrition course intended for non-science/health-career majors. Not intended for students wishing to pursue a career in health care. Basic biological function of nutrients. Nutritional needs throughout the life span. Relationship between nutrition and disease. Current scienti\ufb01c, social, and psychological issues and controversies in nutrition.",
                  "learning_outcomes": [],
                  "skills": [
                    "Biology"
                  ]
                },
                {
                  "code": "BIOL 9",
                  "name": "ENVIRONMENTAL BIOLOGY",
                  "description": "An introduction to environmental biology and a survey of the biological and ecological principles needed to understand environmental issues. Global, national, and local perspectives on current issues, such as resource use, pollution, biodiversity, and impacts of human population growth.",
                  "learning_outcomes": [],
                  "skills": [
                    "Biology"
                  ]
                },
                {
                  "code": "BIOL 9L",
                  "name": "ENVIRONMENTAL BIOLOGY LABORATORY",
                  "description": "An introduction to environmental biology through laboratory and \ufb01eld experiments, examination of local examples illustrating ecological concepts, use of sampling techniques to assess environmental quality, and student research of environmental topics.",
                  "learning_outcomes": [],
                  "skills": [
                    "Biology"
                  ]
                }
              ],
              "aligned_skills": [
                "Biology",
                "Engineering & Technology"
              ]
            },
            {
              "department": "Physical Sciences & Engineering",
              "courses": [
                {
                  "code": "PSE 20",
                  "name": "INTRODUCTION TO PHYSICAL SCIENCE",
                  "description": "This activity-based course provides an introduction to the basic concepts of physical science with emphasis on their practical importance and application in the real world. This course is intended for students who want to become primary school teachers.",
                  "learning_outcomes": [],
                  "skills": [
                    "Engineering & Technology"
                  ]
                }
              ],
              "aligned_skills": [
                "Engineering & Technology"
              ]
            }
          ],
          "student_composition": "Students across these three departments are building competencies in software development, programming, troubleshooting, biology, and engineering and technology \u2014 the same cross-cutting skills J&J Vision's biomedical engineers, software developers, and medical equipment repairers apply on the job. The pipeline spans students pursuing transfer pathways in computer science and biology alongside those developing applied technical skills in physical sciences and engineering.",
          "student_evidence": {
            "total_in_program": 1009,
            "with_all_core_skills": 29,
            "top_students": [
              {
                "uuid": "97f58447-95ba-50ba-98d9-7b362958cd89",
                "display_number": 1,
                "primary_focus": "Computer Science",
                "courses_completed": 8,
                "gpa": 3.74,
                "matching_skills": 6,
                "enrollments": [
                  {
                    "code": "BIOL 13",
                    "name": "MARINE BIOLOGY",
                    "grade": "A",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "C S 11A",
                    "name": "INTRODUCTION TO ARTIFICIAL INTELLIGENCE",
                    "grade": "A",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "AATA 101B",
                    "name": "MAGNETIC PARTICLE TESTING LEVEL 2",
                    "grade": "A",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "PHYS 6",
                    "name": "INTRODUCTORY PHYSICS",
                    "grade": "B",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "C S 22A",
                    "name": "JAVASCRIPT FOR PROGRAMMERS",
                    "grade": "A",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "C S 31A",
                    "name": "INTRODUCTION TO DATABASE MANAGEMENT SYSTEMS",
                    "grade": "A",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "C S 80A",
                    "name": "OPEN SOURCE CONTRIBUTION",
                    "grade": "W",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "C S 203A",
                    "name": "JUST-IN-TIME SUPPORT FOR C S 3A",
                    "grade": "P",
                    "term": "2023-Spring"
                  }
                ],
                "relevant_skills": [
                  "Biology",
                  "Electrical Systems",
                  "Engineering & Technology",
                  "Programming",
                  "Software Development",
                  "Troubleshooting"
                ]
              },
              {
                "uuid": "45fd583a-4d12-514e-8249-a3513ac449f9",
                "display_number": 2,
                "primary_focus": "Computer Science",
                "courses_completed": 7,
                "gpa": 3.69,
                "matching_skills": 6,
                "enrollments": [
                  {
                    "code": "ANTH 1",
                    "name": "INTRODUCTION TO BIOLOGICAL ANTHROPOLOGY",
                    "grade": "A",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "BIOL 41",
                    "name": "MICROBIOLOGY",
                    "grade": "A",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "APSM 154A",
                    "name": "REFRIGERATION IN AIR CONDITIONING",
                    "grade": "A",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "APEL 126",
                    "name": "MOTORS; MOTOR CONTROL; LIGHTING PROTECTION",
                    "grade": "A",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "MTEC 70D",
                    "name": "PRO TOOLS 210M-AVID CERTIFICATION",
                    "grade": "A",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "C S 20A",
                    "name": "PROGRAMMING IN C#",
                    "grade": "B",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "C S 30D",
                    "name": "ADVANCED LINUX SYSTEM ADMINISTRATION",
                    "grade": "A",
                    "term": "2023-Winter"
                  }
                ],
                "relevant_skills": [
                  "Biology",
                  "Electrical Systems",
                  "Engineering & Technology",
                  "Programming",
                  "Software Development",
                  "Troubleshooting"
                ]
              },
              {
                "uuid": "5bb00307-749f-5c50-8f6c-808e1a736fde",
                "display_number": 3,
                "primary_focus": "Computer Science",
                "courses_completed": 6,
                "gpa": 3.62,
                "matching_skills": 6,
                "enrollments": [
                  {
                    "code": "KINS 51",
                    "name": "PERFORMANCE ENHANCING SUBSTANCES IN SPORT & EXERCISE",
                    "grade": "A",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "BIOL 1A",
                    "name": "PRINCIPLES OF CELL BIOLOGY",
                    "grade": "A",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "APEL 128A",
                    "name": "NEC REVIEW, ELECTRIC VEHICLE POWER TRANSFER SYSTEMS, ADVANCED LIGHTING CONTROLS",
                    "grade": "A",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "C S 31A",
                    "name": "INTRODUCTION TO DATABASE MANAGEMENT SYSTEMS",
                    "grade": "P",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "HORT 90Q",
                    "name": "RESIDENTIAL IRRIGATION SYSTEMS",
                    "grade": "A",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "C S 30A",
                    "name": "INTRODUCTION TO LINUX",
                    "grade": "A",
                    "term": "2023-Fall"
                  }
                ],
                "relevant_skills": [
                  "Biology",
                  "Electrical Systems",
                  "Engineering & Technology",
                  "Programming",
                  "Software Development",
                  "Troubleshooting"
                ]
              },
              {
                "uuid": "c80213c9-2edb-5f4e-b7d9-fb868bf11efb",
                "display_number": 4,
                "primary_focus": "Computer Science",
                "courses_completed": 10,
                "gpa": 3.6,
                "matching_skills": 6,
                "enrollments": [
                  {
                    "code": "ANTH 1HL",
                    "name": "HONORS BIOLOGICAL ANTHROPOLOGY LABORATORY",
                    "grade": "A",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "APEL 127A",
                    "name": "ADVANCED MOTOR CONTROLS, VARIABLE FREQUENCY DRIVES, PROGRAMMABLE LOGIC CONTROLS",
                    "grade": "A",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "C S 10",
                    "name": "COMPUTER ARCHITECTURE & ORGANIZATION",
                    "grade": "A",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "ENGR 6",
                    "name": "ENGINEERING GRAPHICS",
                    "grade": "A",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "C S 49",
                    "name": "FOUNDATIONS OF COMPUTER PROGRAMMING",
                    "grade": "A",
                    "term": "2022-Fall"
                  },
                  {
                    "code": "MATH 1AHP",
                    "name": "HONORS CALCULUS I SEMINAR",
                    "grade": "B",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "C S 30B",
                    "name": "LINUX SHELL PROGRAMMING",
                    "grade": "A",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "C S 30C",
                    "name": "LINUX SYSTEM ADMINISTRATION",
                    "grade": "A",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "C S 30A",
                    "name": "INTRODUCTION TO LINUX",
                    "grade": "A",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "C S 8A",
                    "name": "INTRODUCTION TO DATA SCIENCE",
                    "grade": "A",
                    "term": "2024-Spring"
                  }
                ],
                "relevant_skills": [
                  "Biology",
                  "Electrical Systems",
                  "Engineering & Technology",
                  "Programming",
                  "Software Development",
                  "Troubleshooting"
                ]
              },
              {
                "uuid": "5ae8d3bd-3b46-5c7a-bcc3-e85b8264a5db",
                "display_number": 5,
                "primary_focus": "Computer Science",
                "courses_completed": 9,
                "gpa": 3.58,
                "matching_skills": 6,
                "enrollments": [
                  {
                    "code": "BIOL 54H",
                    "name": "HONORS INSTITUTE SEMINAR IN BIOLOGY",
                    "grade": "A",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "PSYC 40",
                    "name": "HUMAN DEVELOPMENT",
                    "grade": "B",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "APEL 128",
                    "name": "PROGRAMMABLE LOGIC CONTROLLERS; LOW-VOLTAGE SYSTEMS & HIGH-VOLTAGE SYSTEMS",
                    "grade": "B",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "C S 40A",
                    "name": "SOFTWARE ENGINEERING METHODOLOGIES",
                    "grade": "W",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "C S 55A",
                    "name": "INTRODUCTION TO CLOUD COMPUTING IN AMAZON WEB SERVICES",
                    "grade": "F",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "C S 1A",
                    "name": "OBJECT-ORIENTED PROGRAMMING METHODOLOGIES IN JAVA",
                    "grade": "A",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "C S 77A",
                    "name": "ADVANCED WEB APPLICATION DEVELOPMENT",
                    "grade": "A",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "APPT 195",
                    "name": "HYDRONICS/STEAM SYSTEMS/PUMPS",
                    "grade": "A",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "C S 48A",
                    "name": "DATA VISUALIZATION",
                    "grade": "A",
                    "term": "2023-Fall"
                  }
                ],
                "relevant_skills": [
                  "Biology",
                  "Electrical Systems",
                  "Engineering & Technology",
                  "Programming",
                  "Software Development",
                  "Troubleshooting"
                ]
              },
              {
                "uuid": "e2ad9f15-81e0-5037-9120-f87fb2022b0a",
                "display_number": 6,
                "primary_focus": "Biology",
                "courses_completed": 9,
                "gpa": 3.48,
                "matching_skills": 6,
                "enrollments": [
                  {
                    "code": "BIOL 72R",
                    "name": "INDEPENDENT STUDY IN BIOLOGY",
                    "grade": "A",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "HLTH 300",
                    "name": "HEALTH ACROSS THE LIFESPAN",
                    "grade": "B",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "BIOL 9L",
                    "name": "ENVIRONMENTAL BIOLOGY LABORATORY",
                    "grade": "F",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "BIOL 41",
                    "name": "MICROBIOLOGY",
                    "grade": "A",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "PSYC 40",
                    "name": "HUMAN DEVELOPMENT",
                    "grade": "A",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "MTEC 57B",
                    "name": "SURROUND SOUND PRODUCTION",
                    "grade": "A",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "APEL 128",
                    "name": "PROGRAMMABLE LOGIC CONTROLLERS; LOW-VOLTAGE SYSTEMS & HIGH-VOLTAGE SYSTEMS",
                    "grade": "B",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "APEL 126A",
                    "name": "OVERCURRENT DEVICES, NFPA 70E: ELECTRICAL SAFETY, INTRO TO RELAYS & CONTROLS, PHOTOVOLTAIC SYSTEMS",
                    "grade": "B",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "MTEC 54A",
                    "name": "MUSIC THEORY FOR AUDIO PRODUCERS",
                    "grade": "A",
                    "term": "2024-Winter"
                  }
                ],
                "relevant_skills": [
                  "Biology",
                  "Electrical Systems",
                  "Engineering & Technology",
                  "Programming",
                  "Software Development",
                  "Troubleshooting"
                ]
              },
              {
                "uuid": "4705438e-a287-5084-8e72-912a38cd2cdb",
                "display_number": 7,
                "primary_focus": "Computer Science",
                "courses_completed": 10,
                "gpa": 3.43,
                "matching_skills": 6,
                "enrollments": [
                  {
                    "code": "KINS 51",
                    "name": "PERFORMANCE ENHANCING SUBSTANCES IN SPORT & EXERCISE",
                    "grade": "A",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "PSYC 4",
                    "name": "INTRODUCTION TO BIOPSYCHOLOGY",
                    "grade": "A",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "ENGR 101A",
                    "name": "ADVANCED MANUFACTURING",
                    "grade": "A",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "BUSI 30",
                    "name": "EMERGING TECHNOLOGIES & BUSINESS",
                    "grade": "W",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "C S 84A",
                    "name": "DATABASE-DRIVEN WEB APPLICATION DEVELOPMENT",
                    "grade": "F",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "C S 2A",
                    "name": "OBJECT-ORIENTED PROGRAMMING METHODOLOGIES IN C++",
                    "grade": "A",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "C S 64A",
                    "name": "WRITING APPS FOR THE ANDROID",
                    "grade": "A",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "C S 77B",
                    "name": "PROJECTS IN WEB APPLICATION DEVELOPMENT",
                    "grade": "A",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "C S 53C",
                    "name": "ETHICAL HACKING",
                    "grade": "A",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "APPT 158",
                    "name": "RF 402 ADVANCED REFRIGERATION & CHILLERS",
                    "grade": "B",
                    "term": "2023-Winter"
                  }
                ],
                "relevant_skills": [
                  "Biology",
                  "Electrical Systems",
                  "Engineering & Technology",
                  "Programming",
                  "Software Development",
                  "Troubleshooting"
                ]
              },
              {
                "uuid": "12e76484-b1d7-5c4b-b012-d9448d48dc35",
                "display_number": 8,
                "primary_focus": "Computer Science",
                "courses_completed": 9,
                "gpa": 3.43,
                "matching_skills": 6,
                "enrollments": [
                  {
                    "code": "D A 62B",
                    "name": "DENTAL SCIENCES II",
                    "grade": "A",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "BIOL 41",
                    "name": "MICROBIOLOGY",
                    "grade": "A",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "APEL 127",
                    "name": "DIGITAL ELECTRONICS; MOTOR SPEED CONTROL; ADVANCED NATIONAL ELECTRICAL CODE",
                    "grade": "B",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "C S 56B",
                    "name": "IT ESSENTIALS",
                    "grade": "A",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "ACTG 54",
                    "name": "ACCOUNTING INFORMATION SYSTEMS",
                    "grade": "A",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "APPT 129",
                    "name": "SPECIAL TOPICS",
                    "grade": "A",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "C S 3B",
                    "name": "INTERMEDIATE SOFTWARE DESIGN IN PYTHON",
                    "grade": "A",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "C S 3C",
                    "name": "ADVANCED DATA STRUCTURES & ALGORITHMS IN PYTHON",
                    "grade": "B",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "C S 64A",
                    "name": "WRITING APPS FOR THE ANDROID",
                    "grade": "A",
                    "term": "2023-Spring"
                  }
                ],
                "relevant_skills": [
                  "Biology",
                  "Electrical Systems",
                  "Engineering & Technology",
                  "Programming",
                  "Software Development",
                  "Troubleshooting"
                ]
              },
              {
                "uuid": "4a666f33-6719-5d8b-9fb4-bf6008194126",
                "display_number": 9,
                "primary_focus": "Computer Science",
                "courses_completed": 9,
                "gpa": 3.38,
                "matching_skills": 6,
                "enrollments": [
                  {
                    "code": "CHEM 12A",
                    "name": "ORGANIC CHEMISTRY",
                    "grade": "B",
                    "term": "2022-Fall"
                  },
                  {
                    "code": "MTEC 51C",
                    "name": "STUDIO RECORDING III",
                    "grade": "B",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "C S 50C",
                    "name": "SCALING LOCAL AREA NETWORKS (CCNA)",
                    "grade": "A",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "C S 10",
                    "name": "COMPUTER ARCHITECTURE & ORGANIZATION",
                    "grade": "D",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "APEL 137",
                    "name": "RESIDENTIAL ELECTRICAL A/C THEORY & CIRCUITRY",
                    "grade": "C",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "C S 1A",
                    "name": "OBJECT-ORIENTED PROGRAMMING METHODOLOGIES IN JAVA",
                    "grade": "W",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "C S 1C",
                    "name": "ADVANCED DATA STRUCTURES & ALGORITHMS IN JAVA",
                    "grade": "W",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "C S 2C",
                    "name": "ADVANCED DATA STRUCTURES & ALGORITHMS IN C++",
                    "grade": "A",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "C S 22A",
                    "name": "JAVASCRIPT FOR PROGRAMMERS",
                    "grade": "A",
                    "term": "2022-Winter"
                  }
                ],
                "relevant_skills": [
                  "Biology",
                  "Electrical Systems",
                  "Engineering & Technology",
                  "Programming",
                  "Software Development",
                  "Troubleshooting"
                ]
              },
              {
                "uuid": "5ec69b47-1f2b-54d0-ae73-19eae5e6403b",
                "display_number": 10,
                "primary_focus": "Biology",
                "courses_completed": 14,
                "gpa": 3.36,
                "matching_skills": 6,
                "enrollments": [
                  {
                    "code": "BIOL 73R",
                    "name": "INDEPENDENT STUDY IN BIOLOGY",
                    "grade": "A",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "HLTH 300",
                    "name": "HEALTH ACROSS THE LIFESPAN",
                    "grade": "D",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "BIOL 9",
                    "name": "ENVIRONMENTAL BIOLOGY",
                    "grade": "A",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "BIOL 14",
                    "name": "HUMAN BIOLOGY",
                    "grade": "A",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "BIOL 8",
                    "name": "BASIC NUTRITION",
                    "grade": "A",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "BIOL 45",
                    "name": "INTRODUCTION TO HUMAN NUTRITION",
                    "grade": "A",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "PSYC C1000",
                    "name": "INTRODUCTION TO PSYCHOLOGY",
                    "grade": "C",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "APSM 152C",
                    "name": "INTRODUCTION TO ELECTRICITY",
                    "grade": "A",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "MTEC 49",
                    "name": "HISTORY OF MUSIC TECHNOLOGY",
                    "grade": "A",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "GIST 58",
                    "name": "REMOTE SENSING & DIGITAL IMAGE PROCESSING",
                    "grade": "W",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "C S 50A",
                    "name": "NETWORK BASICS (CCNA)",
                    "grade": "A",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "MATH 1BH",
                    "name": "HONORS CALCULUS II",
                    "grade": "A",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "APSM 132",
                    "name": "SMQ-32 INTERMEDIATE CAD DETAILING THIRD PARTY",
                    "grade": "A",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "C S 8A",
                    "name": "INTRODUCTION TO DATA SCIENCE",
                    "grade": "A",
                    "term": "2022-Winter"
                  }
                ],
                "relevant_skills": [
                  "Biology",
                  "Electrical Systems",
                  "Engineering & Technology",
                  "Programming",
                  "Software Development",
                  "Troubleshooting"
                ]
              }
            ]
          }
        },
        "roadmap": "A quarterly advisory board structure with J&J Vision's regional technical leadership could give Foothill College's programs sustained access to perspective from a regulated medical device environment. Potential starting points for the inaugural meeting include what embedded software validation workflows reveal about real-world firmware quality and compliance, which entry-level troubleshooting tasks new equipment repairers perform in their first six months, and how J&J Vision onboards biomedical engineering hires who come from two-year or pre-transfer programs.",
        "selected_occupations": [
          "Bioengineers and Biomedical Engineers",
          "Medical Equipment Repairers",
          "Software Developers"
        ],
        "advisory_thesis": "Johnson & Johnson Vision operates at the intersection of medical device manufacturing and eye health innovation, applying biomedical engineering, software development, and equipment maintenance to bring vision care products from design to distribution. Exposure to this employer gives students a concrete view of how technical disciplines\u2014from embedded software to hands-on device repair\u2014function together within a regulated, science-driven product environment.",
        "agenda_topics": [
          {
            "topic": "What embedded software workflows do J&J Vision technicians use when validating medical device firmware before distribution?",
            "rationale": "J&J Vision's operational experience with regulated firmware validation could inform how Computer Science structures its software development coursework around real-world quality and compliance contexts."
          },
          {
            "topic": "Which hands-on troubleshooting tasks do new medical equipment repairers perform in their first six months on the floor?",
            "rationale": "Insight into entry-level repair workflows could help Physical Sciences & Engineering refine the sequencing and applied emphasis of its electrical systems coursework."
          },
          {
            "topic": "How does J&J Vision onboard biomedical engineering hires who come from two-year or pre-transfer programs?",
            "rationale": "Understanding J&J Vision's onboarding experience with early-career hires could help Biology and Physical Sciences & Engineering better align their program pathways with industry entry points."
          }
        ]
      },
      "engagementType": "advisory_board",
      "collegeId": "Foothill College",
      "savedAt": "2026-04-20T00:00:00.000Z",
      "status": "saved",
      "schemaVersion": 8
    },
    {
      "id": "seed-foothill-internship-01",
      "proposal": {
        "employer": "Alpha Teknova",
        "sector": "Manufacturing",
        "partnership_type": "Internship Pipeline",
        "selected_occupation": "Chemical Technicians",
        "selected_soc_code": "19-4031",
        "core_skills": [
          "Laboratory Techniques",
          "Quality Control",
          "Safety Protocols"
        ],
        "gap_skill": "",
        "regions": [
          "Bay Area"
        ],
        "opportunity": "Alpha Teknova is a compelling internship partner for Foothill College's Chemical Technicians pipeline in the Bay Area. The region supports 1,930 employed chemical technicians with 240 annual openings and a median wage of $63,690, signaling steady employer demand. A structured 8-16 week placement at Alpha Teknova could give students direct exposure to life science R&D workflows in a biotechnology production environment.",
        "opportunity_evidence": [
          {
            "title": "Chemical Technicians",
            "soc_code": "19-4031",
            "annual_wage": 63690,
            "employment": 1930,
            "annual_openings": 240,
            "growth_rate": 0.019812217
          }
        ],
        "justification": {
          "curriculum_composition": "Foothill College's programs provide direct preparation for the laboratory and quality-focused work students would encounter at Alpha Teknova. The Engineering department builds laboratory techniques, quality control, and safety protocols across its coursework, covering the full set of competencies this role requires. The Chemistry department extends that preparation through 13 courses emphasizing laboratory techniques and quality control, giving students substantial depth before they step on site.",
          "curriculum_evidence": [
            {
              "department": "Engineering",
              "courses": [
                {
                  "code": "ENGR 37L",
                  "name": "CIRCUIT ANALYSIS LABORATORY",
                  "description": "Practical verification of theorems and concepts learned in ENGR 37 through experimentation. Included are experiments in DC and AC circuits involving the utilization of a variety of instruments, such as DC/AC meters, regulated power supplies, signal generators, oscilloscopes, and frequency counters. Students taking this lab along with the lecture course will see hands-on applications to better understand the theory.",
                  "learning_outcomes": [],
                  "skills": [
                    "Laboratory Techniques"
                  ]
                },
                {
                  "code": "ENGR 45",
                  "name": "PROPERTIES OF MATERIALS",
                  "description": "Properties of engineering materials related to basic structure; applications to the selection and use of engineering materials.",
                  "learning_outcomes": [],
                  "skills": [
                    "Quality Control"
                  ]
                },
                {
                  "code": "ENGR 61A",
                  "name": "INTRODUCTION TO SEMICONDUCTOR TECHNOLOGY",
                  "description": "This course provides an overview of the semiconductor industry. Focus on clean room safety, wafer processing, and troubleshooting. Students practice scientific thinking and have exposure to running experiments.",
                  "learning_outcomes": [],
                  "skills": [
                    "Safety Protocols"
                  ]
                }
              ],
              "aligned_skills": [
                "Laboratory Techniques",
                "Quality Control",
                "Safety Protocols"
              ]
            },
            {
              "department": "Chemistry",
              "courses": [
                {
                  "code": "CHEM 12AL",
                  "name": "ORGANIC CHEMISTRY LABORATORY",
                  "description": "Laboratory course to accompany CHEM\u00a012A. Intended to introduce students to laboratory techniques common in modern synthetic organic chemistry. Students will work on both standard preparative scale and microscale to synthesize, isolate, purify, and characterize organic compounds.",
                  "learning_outcomes": [],
                  "skills": [
                    "Laboratory Techniques",
                    "Quality Control"
                  ]
                },
                {
                  "code": "CHEM 12BL",
                  "name": "ORGANIC CHEMISTRY LABORATORY",
                  "description": "Laboratory course to accompany CHEM\u00a012B. Emphasis is on spectroscopic methods for the structure elucidation of organic compounds. Provides extensive practice in the synthesis, puri\ufb01cation, isolation, and characterization of organic target molecules. For chemistry and other STEM majors, and for pre-professional students in dentistry, medicine, pharmacy, and veterinary medicine, or any other interested students that have mastered the prerequisites.",
                  "learning_outcomes": [],
                  "skills": [
                    "Laboratory Techniques",
                    "Quality Control"
                  ]
                },
                {
                  "code": "CHEM 12CL",
                  "name": "ORGANIC CHEMISTRY LABORATORY",
                  "description": "Laboratory course to accompany CHEM\u00a012C. Intended to strengthen student's skill in application of laboratory techniques, and to encourage independent work. Emphasis is on chemical reactions relevant to CHEM\u00a012C, multi-step syntheses, and identi\ufb01cation of unknowns.",
                  "learning_outcomes": [],
                  "skills": [
                    "Laboratory Techniques",
                    "Quality Control"
                  ]
                },
                {
                  "code": "CHEM 1A",
                  "name": "GENERAL CHEMISTRY",
                  "description": "Fundamental chemical principles with an emphasis on physical and chemical properties, stoichiometry, chemical reaction types, thermochemistry, modern atomic theory and atomic structure, chemical bonding and bonding theory, and molecular shapes. Laboratory component parallels lecture topics and also includes chemical nomenclature, basic chemical equations, stoichiometry, unknown analysis, and fundamentals of oxidation and reduction.",
                  "learning_outcomes": [],
                  "skills": [
                    "Laboratory Techniques"
                  ]
                },
                {
                  "code": "CHEM 1B",
                  "name": "GENERAL CHEMISTRY",
                  "description": "Kinetic molecular theory and gas laws, intermolecular forces, chemical kinetics, equilibria, behavior of acids and bases, acid/base equilibrium, and classical thermodynamics. Laboratory parallels lecture topics and includes computer graphing techniques, chemical kinetics, equilibrium measurements, heat transfer experiments, thermodynamics of an equilibrium system, vapor pressure of liquids.",
                  "learning_outcomes": [],
                  "skills": [
                    "Laboratory Techniques"
                  ]
                },
                {
                  "code": "CHEM 1C",
                  "name": "GENERAL CHEMISTRY & QUALITATIVE ANALYSIS",
                  "description": "Aqueous ionic equilibria of buffers, solubility product constants and formation constants; properties of solutions, including factors affecting solubility, energy changes in the solution process and colligative properties; electrochemistry, including the thermodynamics of voltaic cells; introduction to coordination chemistry and bonding theory; nuclear chemistry with emphasis on applications; and, time permitting, an introduction to modern materials. Laboratory parallels lecture topics with an introduction to qualitative inorganic analysis.",
                  "learning_outcomes": [],
                  "skills": [
                    "Laboratory Techniques"
                  ]
                },
                {
                  "code": "CHEM 25",
                  "name": "FUNDAMENTALS OF CHEMISTRY",
                  "description": "This course includes basic chemical laboratory techniques and methods, a survey of important chemical principles with emphasis on problem solving, and a description of the elements and their compounds. The course includes active learning and student-to-student learning strategies to promote meaningful and productive work to ensure the success of all students. Intended for students who wish to meet general education requirements in physical science or need background preparation for CHEM 1A.",
                  "learning_outcomes": [],
                  "skills": [
                    "Laboratory Techniques"
                  ]
                },
                {
                  "code": "CHEM 30A",
                  "name": "SURVEY OF INORGANIC & ORGANIC CHEMISTRY",
                  "description": "An introductory course covering basic principles of chemistry more descriptive than quantitative in emphasis. Topics include atomic structure, the periodic table, the three states of matter, energy, chemical bonding in ionic and molecular compounds, nomenclature, measurement and the metric system, chemical reactions and equations, solutions, acids, bases, salts and electrolyte systems. The course includes active learning and student-to-student learning strategies to promote meaningful and productive work to ensure the success of all students. Primarily intended for students entering the allied health \ufb01eld, including: nursing, veterinary technology, dental assistant, dental hygiene, biotechnology, primary care associate, radiation therapy technology, radiologic technology, respiratory therapy, and pharmaceutical technology.",
                  "learning_outcomes": [],
                  "skills": [
                    "Laboratory Techniques"
                  ]
                },
                {
                  "code": "CHEM 30B",
                  "name": "SURVEY OF ORGANIC & BIOCHEMISTRY",
                  "description": "Basic principles of organic chemistry and biological chemistry. Topics include organic chemistry nomenclature, functional groups, and an introduction to structure and properties of carbohydrates, lipids, nucleic acids, proteins, and enzymes. An overview of metabolism is also given. The course includes active learning and student-to-student learning strategies to promote meaningful and productive work to ensure the success of all students. Primarily intended for students entering the allied health \ufb01eld, including: nursing, dental hygiene, and biotechnology.",
                  "learning_outcomes": [],
                  "skills": [
                    "Laboratory Techniques"
                  ]
                },
                {
                  "code": "CHEM 70R",
                  "name": "INDEPENDENT STUDY IN CHEMISTRY",
                  "description": "Provides an opportunity for the student to expand their studies in chemistry by completing a project or an assignment arranged by agreement between the student and instructor. The student is required to contract with the instructor to determine the scope of the assignment and the unit value assigned for successful completion. Students may take a maximum of 6 units of independent study coursework per department.",
                  "learning_outcomes": [],
                  "skills": [
                    "Laboratory Techniques"
                  ]
                },
                {
                  "code": "CHEM 71R",
                  "name": "INDEPENDENT STUDY IN CHEMISTRY",
                  "description": "Provides an opportunity for the student to expand their studies in chemistry by completing a project or an assignment arranged by agreement between the student and instructor. The student is required to contract with the instructor to determine the scope of the assignment and the unit value assigned for successful completion. Students may take a maximum of 6 units of independent study coursework per department.",
                  "learning_outcomes": [],
                  "skills": [
                    "Laboratory Techniques"
                  ]
                },
                {
                  "code": "CHEM 72R",
                  "name": "INDEPENDENT STUDY IN CHEMISTRY",
                  "description": "Provides an opportunity for the student to expand their studies in chemistry by completing a project or an assignment arranged by agreement between the student and instructor. The student is required to contract with the instructor to determine the scope of the assignment and the unit value assigned for successful completion. Students may take a maximum of 6 units of independent study coursework per department.",
                  "learning_outcomes": [],
                  "skills": [
                    "Laboratory Techniques"
                  ]
                },
                {
                  "code": "CHEM 73R",
                  "name": "INDEPENDENT STUDY IN CHEMISTRY",
                  "description": "Provides an opportunity for the student to expand their studies in chemistry by completing a project or an assignment arranged by agreement between the student and instructor. The student is required to contract with the instructor to determine the scope of the assignment and the unit value assigned for successful completion. Students may take a maximum of 6 units of independent study coursework per department.",
                  "learning_outcomes": [],
                  "skills": [
                    "Laboratory Techniques"
                  ]
                }
              ],
              "aligned_skills": [
                "Laboratory Techniques",
                "Quality Control"
              ]
            },
            {
              "department": "Biology",
              "courses": [
                {
                  "code": "BIOL 1A",
                  "name": "PRINCIPLES OF CELL BIOLOGY",
                  "description": "An introduction to biological molecules, cellular structure and function, bioenergetics, the genetics of both prokaryotic and eukaryotic organisms, cell communication and signaling, the cell cycle, and elements of molecular biology. Intended for biology majors.",
                  "learning_outcomes": [],
                  "skills": [
                    "Laboratory Techniques"
                  ]
                },
                {
                  "code": "BIOL 1B",
                  "name": "FORM & FUNCTION IN PLANTS & ANIMALS",
                  "description": "An introduction to the structure and physiological processes of plants and animals. Transport systems, reproduction, digestion, gas exchange, regulation of the internal environment, responses to external stimuli, nervous systems, hormones, and locomotion. Intended for biology majors.",
                  "learning_outcomes": [],
                  "skills": [
                    "Laboratory Techniques"
                  ]
                },
                {
                  "code": "BIOL 1D",
                  "name": "INTRODUCTION TO MOLECULAR GENETICS",
                  "description": "Intended for students wishing to transfer to a four year school with a major in molecular biology, biochemistry, or molecular genetics. An introduction to molecular genetics with an emphasis in genome organization, DNA replication and repair, mutation, transcription, translation, and the regulation of gene expression.",
                  "learning_outcomes": [],
                  "skills": [
                    "Laboratory Techniques"
                  ]
                },
                {
                  "code": "BIOL 36AH",
                  "name": "HONORS EXPERIMENTAL RESEARCH IN BIOLOGY I",
                  "description": "This course provides interested students with an opportunity to carry out an authentic research project in biology. Students will coordinate research and planning of an original research project, write a proposal and research design, carry out the research, and report on their results. Emphasis is placed on scienti\ufb01c thinking, experimental design, laboratory and/or \ufb01eld work skills, project design and implementation, bioethics, and scienti\ufb01c communication.",
                  "learning_outcomes": [],
                  "skills": [
                    "Laboratory Techniques"
                  ]
                },
                {
                  "code": "BIOL 36BH",
                  "name": "HONORS EXPERIMENTAL RESEARCH IN BIOLOGY II",
                  "description": "This course provides students with an opportunity to carry out an authentic research project in biology. Students will further explore their original research project while exploring how to narrow and/or expand the scope of their research project as it develops. Additionally, students will gain valuable collaboration and skills by training and coordinating with students in BIOL 36AH. Emphasis is placed on scienti\ufb01c thinking, laboratory and/or \ufb01eld work skills, project design, coordination and implementation, bioethics, and scienti\ufb01c communication.",
                  "learning_outcomes": [],
                  "skills": [
                    "Laboratory Techniques"
                  ]
                },
                {
                  "code": "BIOL 36CH",
                  "name": "HONORS EXPERIMENTAL RESEARCH IN BIOLOGY III",
                  "description": "This course provides students with an opportunity to carry out an authentic research project in biology. Students will further explore their original research project while exploring how to narrow and/or expand the scope of their research project as it develops. Additionally, students will gain valuable leadership skills by coordinating projects with students in BIOL 36AH and BIOL 36BH. Emphasis is placed on leadership, scienti\ufb01c thinking, laboratory and/or \ufb01eld work skills, project design, coordination and implementation, bioethics, and scienti\ufb01c communication.",
                  "learning_outcomes": [],
                  "skills": [
                    "Laboratory Techniques"
                  ]
                },
                {
                  "code": "BIOL 40A",
                  "name": "HUMAN ANATOMY & PHYSIOLOGY I",
                  "description": "Human anatomy and physiology with an emphasis on integration of systems and homeostatic mechanisms. Physical and chemical basis of life, histology and integumentary, skeletal and muscular systems. This course is primarily intended for nursing, allied health, kinesiology, and other health-related majors.",
                  "learning_outcomes": [],
                  "skills": [
                    "Laboratory Techniques"
                  ]
                },
                {
                  "code": "BIOL 40B",
                  "name": "HUMAN ANATOMY & PHYSIOLOGY II",
                  "description": "Human anatomy and physiology with an emphasis on integration of systems and homeostatic mechanisms for the nervous, cardiovascular, and respiratory systems. This course is primarily intended for nursing, allied health, kinesiology, and other health-related majors.",
                  "learning_outcomes": [],
                  "skills": [
                    "Laboratory Techniques"
                  ]
                },
                {
                  "code": "BIOL 40C",
                  "name": "HUMAN ANATOMY & PHYSIOLOGY III",
                  "description": "Human anatomy and physiology with an emphasis on integration of systems and homeostatic mechanisms for the digestive system, metabolism, urinary system, fluid, electrolyte and acid/base balance, lymphatic system, endocrine system, and reproductive system. This course is primarily intended for nursing, allied health, kinesiology, and other health-related majors.",
                  "learning_outcomes": [],
                  "skills": [
                    "Laboratory Techniques"
                  ]
                },
                {
                  "code": "BIOL 41",
                  "name": "MICROBIOLOGY",
                  "description": "Morphology and physiology of microorganisms with emphasis on the important roles that microbes play in human life. Mechanisms of pathogenicity, host-parasite relationships, the immune response and principles of disease transmission. Techniques of microbial control including sterilization, aseptic procedures, use of disinfectants, antiseptics and chemotherapy. Basic laboratory skills of microbiology.",
                  "learning_outcomes": [],
                  "skills": [
                    "Laboratory Techniques"
                  ]
                },
                {
                  "code": "BIOL 9L",
                  "name": "ENVIRONMENTAL BIOLOGY LABORATORY",
                  "description": "An introduction to environmental biology through laboratory and \ufb01eld experiments, examination of local examples illustrating ecological concepts, use of sampling techniques to assess environmental quality, and student research of environmental topics.",
                  "learning_outcomes": [],
                  "skills": [
                    "Laboratory Techniques"
                  ]
                }
              ],
              "aligned_skills": [
                "Laboratory Techniques"
              ]
            }
          ],
          "student_composition": "Students in the Engineering and Chemistry programs are actively developing the competencies Alpha Teknova would expect from an intern in a chemical technician role. The Biology department adds a third pipeline of students with hands-on laboratory training. Across these three programs, the eligible student pool is broad and concentrated in directly relevant coursework.",
          "student_evidence": {
            "total_in_program": 970,
            "with_all_core_skills": 138,
            "top_students": [
              {
                "uuid": "240435f1-e180-5924-86ae-88ce94ffe45c",
                "display_number": 1,
                "primary_focus": "Chemistry",
                "courses_completed": 5,
                "gpa": 4.0,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "CHEM 71R",
                    "name": "INDEPENDENT STUDY IN CHEMISTRY",
                    "grade": "W",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "CHEM 30B",
                    "name": "SURVEY OF ORGANIC & BIOCHEMISTRY",
                    "grade": "A",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "CHEM 30A",
                    "name": "SURVEY OF INORGANIC & ORGANIC CHEMISTRY",
                    "grade": "A",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "CHEM 12AL",
                    "name": "ORGANIC CHEMISTRY LABORATORY",
                    "grade": "A",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "APSM 101",
                    "name": "SMQ-1 TRADE INTRODUCTION",
                    "grade": "A",
                    "term": "2023-Winter"
                  }
                ],
                "relevant_skills": [
                  "Laboratory Techniques",
                  "Quality Control",
                  "Safety Protocols"
                ]
              },
              {
                "uuid": "aac78510-2eab-5ea5-9a58-e29e5cc1447c",
                "display_number": 2,
                "primary_focus": "Chemistry",
                "courses_completed": 2,
                "gpa": 4.0,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "R T 72",
                    "name": "VENIPUNCTURE",
                    "grade": "A",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "CHEM 12AL",
                    "name": "ORGANIC CHEMISTRY LABORATORY",
                    "grade": "A",
                    "term": "2025-Spring"
                  }
                ],
                "relevant_skills": [
                  "Laboratory Techniques",
                  "Quality Control",
                  "Safety Protocols"
                ]
              },
              {
                "uuid": "276cc957-17c9-591d-96de-49cc92101150",
                "display_number": 3,
                "primary_focus": "Chemistry",
                "courses_completed": 4,
                "gpa": 4.0,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "CHEM 72R",
                    "name": "INDEPENDENT STUDY IN CHEMISTRY",
                    "grade": "A",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "RSPT 61A",
                    "name": "ADULT MECHANICAL VENTILATION",
                    "grade": "A",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "APSM 133",
                    "name": "SMQ-33 ADVANCED ARCHITECTURAL",
                    "grade": "A",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "CHLD 80C",
                    "name": "SAFETY & NUTRITION OF YOUNG CHILDREN IN THE HOME",
                    "grade": "A",
                    "term": "2025-Spring"
                  }
                ],
                "relevant_skills": [
                  "Laboratory Techniques",
                  "Quality Control",
                  "Safety Protocols"
                ]
              },
              {
                "uuid": "7db18088-8ec6-56e8-a07e-6fa34e56e261",
                "display_number": 4,
                "primary_focus": "Biology",
                "courses_completed": 2,
                "gpa": 3.75,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "BIOL 36CH",
                    "name": "HONORS EXPERIMENTAL RESEARCH IN BIOLOGY III",
                    "grade": "A",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "R T 201",
                    "name": "DIGITAL RADIOGRAPHY FOR RADIOLOGIC TECHNOLOGISTS",
                    "grade": "A",
                    "term": "2025-Spring"
                  }
                ],
                "relevant_skills": [
                  "Laboratory Techniques",
                  "Quality Control",
                  "Safety Protocols"
                ]
              },
              {
                "uuid": "c94bc7b2-ae98-582b-85ec-95306a86c9e8",
                "display_number": 5,
                "primary_focus": "Chemistry",
                "courses_completed": 7,
                "gpa": 3.75,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "CHEM 73R",
                    "name": "INDEPENDENT STUDY IN CHEMISTRY",
                    "grade": "A",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "CHEM 71R",
                    "name": "INDEPENDENT STUDY IN CHEMISTRY",
                    "grade": "A",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "CHEM 70R",
                    "name": "INDEPENDENT STUDY IN CHEMISTRY",
                    "grade": "B",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "CHEM 25",
                    "name": "FUNDAMENTALS OF CHEMISTRY",
                    "grade": "W",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "CHEM 1A",
                    "name": "GENERAL CHEMISTRY",
                    "grade": "B",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "CHEM 12CL",
                    "name": "ORGANIC CHEMISTRY LABORATORY",
                    "grade": "B",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "CHLD 80C",
                    "name": "SAFETY & NUTRITION OF YOUNG CHILDREN IN THE HOME",
                    "grade": "A",
                    "term": "2023-Winter"
                  }
                ],
                "relevant_skills": [
                  "Laboratory Techniques",
                  "Quality Control",
                  "Safety Protocols"
                ]
              },
              {
                "uuid": "27d9c8b7-acb1-5754-a047-9cafecd7b44f",
                "display_number": 6,
                "primary_focus": "Biology",
                "courses_completed": 5,
                "gpa": 3.73,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "BIOL 36BH",
                    "name": "HONORS EXPERIMENTAL RESEARCH IN BIOLOGY II",
                    "grade": "A",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "BIOL 9L",
                    "name": "ENVIRONMENTAL BIOLOGY LABORATORY",
                    "grade": "A",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "BIOL 40C",
                    "name": "HUMAN ANATOMY & PHYSIOLOGY III",
                    "grade": "B",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "APSM 118",
                    "name": "SMQ-18 INDUSTRIAL & STAINLESS STEEL INTRODUCTION",
                    "grade": "A",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "HLTH 21",
                    "name": "CONTEMPORARY HEALTH CONCERNS",
                    "grade": "B",
                    "term": "2025-Spring"
                  }
                ],
                "relevant_skills": [
                  "Laboratory Techniques",
                  "Quality Control",
                  "Safety Protocols"
                ]
              },
              {
                "uuid": "4ab60ddb-2d3b-5c46-8672-119cf41567dd",
                "display_number": 7,
                "primary_focus": "Chemistry",
                "courses_completed": 5,
                "gpa": 3.67,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "CHEM 73R",
                    "name": "INDEPENDENT STUDY IN CHEMISTRY",
                    "grade": "B",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "CHEM 72R",
                    "name": "INDEPENDENT STUDY IN CHEMISTRY",
                    "grade": "W",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "CHEM 12AL",
                    "name": "ORGANIC CHEMISTRY LABORATORY",
                    "grade": "A",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "CHEM 12BL",
                    "name": "ORGANIC CHEMISTRY LABORATORY",
                    "grade": "A",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "PSYC 51",
                    "name": "APPLIED RESEARCH EXPERIENCE",
                    "grade": "A",
                    "term": "2024-Spring"
                  }
                ],
                "relevant_skills": [
                  "Laboratory Techniques",
                  "Quality Control",
                  "Safety Protocols"
                ]
              },
              {
                "uuid": "2086db42-6e45-50f4-8a76-eed3c9d86eca",
                "display_number": 8,
                "primary_focus": "Biology",
                "courses_completed": 6,
                "gpa": 3.67,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "BIOL 1D",
                    "name": "INTRODUCTION TO MOLECULAR GENETICS",
                    "grade": "A",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "BIOL 36BH",
                    "name": "HONORS EXPERIMENTAL RESEARCH IN BIOLOGY II",
                    "grade": "A",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "AATA 105C",
                    "name": "NON-FILM RADIOGRAPHIC TESTING",
                    "grade": "A",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "CHEM 1A",
                    "name": "GENERAL CHEMISTRY",
                    "grade": "B",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "BIOL 40A",
                    "name": "HUMAN ANATOMY & PHYSIOLOGY I",
                    "grade": "A",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "HLTH 21",
                    "name": "CONTEMPORARY HEALTH CONCERNS",
                    "grade": "A",
                    "term": "2024-Spring"
                  }
                ],
                "relevant_skills": [
                  "Laboratory Techniques",
                  "Quality Control",
                  "Safety Protocols"
                ]
              },
              {
                "uuid": "c4002e84-ab6c-51b7-ab36-dd8bffa5c329",
                "display_number": 9,
                "primary_focus": "Chemistry",
                "courses_completed": 7,
                "gpa": 3.65,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "CHEM 73R",
                    "name": "INDEPENDENT STUDY IN CHEMISTRY",
                    "grade": "A",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "CHEM 71R",
                    "name": "INDEPENDENT STUDY IN CHEMISTRY",
                    "grade": "A",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "CHEM 70R",
                    "name": "INDEPENDENT STUDY IN CHEMISTRY",
                    "grade": "A",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "CHEM 30A",
                    "name": "SURVEY OF INORGANIC & ORGANIC CHEMISTRY",
                    "grade": "A",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "CHEM 1B",
                    "name": "GENERAL CHEMISTRY",
                    "grade": "A",
                    "term": "2022-Fall"
                  },
                  {
                    "code": "CHEM 12CL",
                    "name": "ORGANIC CHEMISTRY LABORATORY",
                    "grade": "A",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "APSM 171C",
                    "name": "SAFETY TRAINING FOR TAB APPRENTICESHIP",
                    "grade": "C",
                    "term": "2023-Spring"
                  }
                ],
                "relevant_skills": [
                  "Laboratory Techniques",
                  "Quality Control",
                  "Safety Protocols"
                ]
              },
              {
                "uuid": "641572e6-a679-52f1-a1ab-118e99e70110",
                "display_number": 10,
                "primary_focus": "Chemistry",
                "courses_completed": 6,
                "gpa": 3.64,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "CHEM 73R",
                    "name": "INDEPENDENT STUDY IN CHEMISTRY",
                    "grade": "B",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "CHEM 72R",
                    "name": "INDEPENDENT STUDY IN CHEMISTRY",
                    "grade": "B",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "CHEM 25",
                    "name": "FUNDAMENTALS OF CHEMISTRY",
                    "grade": "A",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "CHEM 1C",
                    "name": "GENERAL CHEMISTRY & QUALITATIVE ANALYSIS",
                    "grade": "W",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "CHEM 12BL",
                    "name": "ORGANIC CHEMISTRY LABORATORY",
                    "grade": "A",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "V T 75A",
                    "name": "ANIMAL CARE SKILLS I",
                    "grade": "B",
                    "term": "2023-Winter"
                  }
                ],
                "relevant_skills": [
                  "Laboratory Techniques",
                  "Quality Control",
                  "Safety Protocols"
                ]
              }
            ]
          }
        },
        "roadmap": "A conversation between the Engineering or Chemistry department chair and Alpha Teknova's workforce or HR team could confirm site capacity and define the scope of a first cohort. An internship structured at 10-16 weeks could map to existing cooperative work experience course credits, with a target of placing an initial cohort within the next two semesters.",
        "selected_occupations": [],
        "advisory_thesis": "",
        "agenda_topics": []
      },
      "engagementType": "internship",
      "collegeId": "Foothill College",
      "savedAt": "2026-04-20T00:00:00.000Z",
      "status": "saved",
      "schemaVersion": 8
    },
    {
      "id": "seed-foothill-curriculum-01",
      "proposal": {
        "employer": "Agilent Technologies",
        "sector": "Manufacturing",
        "partnership_type": "Curriculum Co-Design",
        "selected_occupation": "Software Developers",
        "selected_soc_code": "15-1252",
        "core_skills": [
          "Programming",
          "Software Development",
          "Algorithms"
        ],
        "gap_skill": "Laboratory Instrument Software Integration and Automation (e.g., SCPI/GPIB protocols)",
        "regions": [
          "Bay Area",
          "South Central Coast"
        ],
        "opportunity": "Foothill College's Computer Science department is well-positioned to deepen its alignment with Agilent Technologies through a co-design partnership focused on laboratory instrument software integration and automation. The department builds strong preparation in programming, software development, and algorithms across a broad course offering. Collaboration with Agilent could strengthen that foundation in SCPI and GPIB protocols, which are central to software-driven instrument control in Agilent's product environment.",
        "opportunity_evidence": [
          {
            "title": "Software Developers",
            "soc_code": "15-1252",
            "annual_wage": 194960,
            "employment": 169710,
            "annual_openings": 11440,
            "growth_rate": 0.072506539
          }
        ],
        "justification": {
          "curriculum_composition": "The Computer Science department is the right home for this partnership. Its coursework develops the programming and software development skills that underpin this occupation, with 33 courses providing substantial curricular depth. Laboratory instrument software integration and automation, including SCPI and GPIB-based control, is a domain-specific layer that could be more rigorously developed through direct collaboration with Agilent's engineering teams.",
          "curriculum_evidence": [
            {
              "department": "Computer Science",
              "courses": [
                {
                  "code": "C S 10",
                  "name": "COMPUTER ARCHITECTURE & ORGANIZATION",
                  "description": "Introduction to the organization, architecture and machine-level programming of computer systems. Topics include mapping of high-level language constructs into assembly code, internal data representations, numerical computation, virtual memory, pipelines, caching, multitasking, MIPS architecture, MIPA assembly language code, interrupts, input/output, peripheral storage processing, and comparison of CISC (Intel) and RISC (MIPS) instruction sets.",
                  "learning_outcomes": [],
                  "skills": [
                    "Algorithms",
                    "Programming"
                  ]
                },
                {
                  "code": "C S 11A",
                  "name": "INTRODUCTION TO ARTIFICIAL INTELLIGENCE",
                  "description": "A survey of arti\ufb01cial intelligence (AI) and its application. Includes search algorithms, evolutionary algorithms, and machine learning. Explores issues of ethics and equity. Students will use Python and publicly available packages to develop and test AI models. Students will gain practical experience coding models, with less emphasis on math and theory.",
                  "learning_outcomes": [],
                  "skills": [
                    "Algorithms",
                    "Programming",
                    "Software Development"
                  ]
                },
                {
                  "code": "C S 12A",
                  "name": "INTRODUCTION TO MACHINE LEARNING",
                  "description": "A survey of machine learning algorithms and modern packages. Includes models in supervised, unsupervised, and reinforcement learning. Explores the entire machine learning pipeline from dataset selection through model evaluation. Students will gain practical experience coding models, with less emphasis on math and theory.",
                  "learning_outcomes": [],
                  "skills": [
                    "Algorithms",
                    "Programming",
                    "Software Development"
                  ]
                },
                {
                  "code": "C S 18",
                  "name": "DISCRETE MATHEMATICS",
                  "description": "This course is for any student majoring in math or computer science, as well as for students interested in the topics taught in this course. Discrete mathematics: set theory, logic, Boolean algebra, methods of proof, mathematical induction, number theory, discrete probability, combinatorics, functions, relations, recursion, algorithm ef\ufb01ciencies, graphs, trees.",
                  "learning_outcomes": [],
                  "skills": [
                    "Algorithms",
                    "Programming"
                  ]
                },
                {
                  "code": "C S 1A",
                  "name": "OBJECT-ORIENTED PROGRAMMING METHODOLOGIES IN JAVA",
                  "description": "Systematic introduction to fundamental concepts of computer science through the study of the Java programming language. Coding topics include Java control structures, classes, methods, arrays, graphical user interfaces and elementary data structures. Concept topics include algorithms, recursion, data abstraction, problem solving strategies, code style, documentation, debugging techniques and testing.",
                  "learning_outcomes": [],
                  "skills": [
                    "Algorithms",
                    "Programming",
                    "Software Development"
                  ]
                },
                {
                  "code": "C S 1B",
                  "name": "INTERMEDIATE SOFTWARE DESIGN IN JAVA",
                  "description": "Systematic treatment of intermediate concepts in computer science through the study of Java object-oriented programming (OOP). Coding topics include Java interfaces, class extension, generics, the Java collections framework, multi-dimensional arrays and \ufb01le I/O. Concept topics include OOP project design, inheritance, polymorphism, method chaining, functional programming, linked-lists, FIFOs, LIFOs, event-driven programming and guarded code.",
                  "learning_outcomes": [],
                  "skills": [
                    "Algorithms",
                    "Programming",
                    "Software Development"
                  ]
                },
                {
                  "code": "C S 1C",
                  "name": "ADVANCED DATA STRUCTURES & ALGORITHMS IN JAVA",
                  "description": "Systematic treatment of advanced data structures, algorithm analysis and abstract data types in the Java programming language. Coding topics include the development of ADTs from scratch, building ADTs on top of the java.util collections, array lists, linked lists, trees, maps, hashing functions and graphs. Concept topics include searching, big-O time complexity, analysis of all major sorting techniques, top down splaying, AVL tree balancing, shortest path algorithms, minimum spanning trees and maximum flow graphs.",
                  "learning_outcomes": [],
                  "skills": [
                    "Algorithms",
                    "Programming",
                    "Software Development"
                  ]
                },
                {
                  "code": "C S 203A",
                  "name": "JUST-IN-TIME SUPPORT FOR C S 3A",
                  "description": "A just-in-time approach to the core prerequisite skills, competencies, and concepts needed in C S 3A. Intended for students who are concurrently enrolled in C S 3A at Foothill College. Topics include: installation of an integrated development environment and other software, navigating a \ufb01le system hierarchy, developing a logic-based approach to programming, identifying errors in a program using a debugger and other means.",
                  "learning_outcomes": [],
                  "skills": [
                    "Programming"
                  ]
                },
                {
                  "code": "C S 20A",
                  "name": "PROGRAMMING IN C#",
                  "description": "Introduction to the C# programming language and the .NET platform. Topics include object oriented programming, graphical user interfaces, elementary data structures, algorithms, recursion, data abstraction, code style, documentation, debugging techniques, and testing.",
                  "learning_outcomes": [],
                  "skills": [
                    "Algorithms",
                    "Programming",
                    "Software Development"
                  ]
                },
                {
                  "code": "C S 22A",
                  "name": "JAVASCRIPT FOR PROGRAMMERS",
                  "description": "Introduction to object oriented programming in JavaScript. Topics include: client and server side programming, Model/View/Controller architecture, current tools and testing methods, interaction with HTML and CSS, Document Object Model, XML, and JSON. Students will have practice writing programs for mobile web browsers and creating dynamic webpages including animation.",
                  "learning_outcomes": [],
                  "skills": [
                    "Programming",
                    "Software Development"
                  ]
                },
                {
                  "code": "C S 2A",
                  "name": "OBJECT-ORIENTED PROGRAMMING METHODOLOGIES IN C++",
                  "description": "Systematic introduction to fundamental concepts of computer science through the study of the C++ programming language. Coding topics include C++ control structures, objects, global-scope functions, class methods, arrays and elementary data structures. Concept topics include algorithms, recursion, data abstraction, problem solving strategies, code style, documentation, debugging techniques and testing.",
                  "learning_outcomes": [],
                  "skills": [
                    "Algorithms",
                    "Programming",
                    "Software Development"
                  ]
                },
                {
                  "code": "C S 2B",
                  "name": "INTERMEDIATE SOFTWARE DESIGN IN C++",
                  "description": "Systematic treatment of intermediate concepts in computer science through the study of C++ object-oriented programming (OOP). Coding topics include C++ derived classes, class templates, function templates, virtual functions, operator overloading, an introduction to the Standard Template Library, multiple inheritance, pointers, dynamic memory allocation and \ufb01le I/O. Concept topics include OOP project design, inheritance, polymorphism, method chaining, functional programming, linked-lists, FIFOs, LIFOs, events in GUIs and guarded code.",
                  "learning_outcomes": [],
                  "skills": [
                    "Algorithms",
                    "Programming",
                    "Software Development"
                  ]
                },
                {
                  "code": "C S 2C",
                  "name": "ADVANCED DATA STRUCTURES & ALGORITHMS IN C++",
                  "description": "Systematic treatment of advanced data structures, algorithm analysis and abstract data types in the C++ programming language. Coding topics include the development of ADTs from scratch, building ADTs on top of the STL templates, vectors, lists, trees, maps, hashing functions and graphs. Concept topics include searching, big-O time complexity, analysis of all major sorting techniques, top down splaying, AVL tree balancing, shortest path algorithms, minimum spanning trees and maximum flow graphs.",
                  "learning_outcomes": [],
                  "skills": [
                    "Algorithms",
                    "Programming",
                    "Software Development"
                  ]
                },
                {
                  "code": "C S 30A",
                  "name": "INTRODUCTION TO LINUX",
                  "description": "Introduction to the Linux operating system primarily focused on command line usage. Covers the history, kernel, \ufb01le systems, shells, and user utilities. Also introduces students to the fundamentals of shell programming, processes, communications, and basic security.",
                  "learning_outcomes": [],
                  "skills": [
                    "Programming"
                  ]
                },
                {
                  "code": "C S 30B",
                  "name": "LINUX SHELL PROGRAMMING",
                  "description": "Linux shell script programming using the Bourne Again shell programming language (bash) and Linux utilities to create practical shell scripts. Topics covered include customizing the environment, running and writing scripts, variables, loops, functions, text processing and debugging.",
                  "learning_outcomes": [],
                  "skills": [
                    "Programming"
                  ]
                },
                {
                  "code": "C S 30E",
                  "name": "LINUX SYSTEM ADMINISTRATION: NETWORK SERVICES",
                  "description": "The course is focused on deploying and managing network servers running caching Domain Name Service (DNS), MariaDB, Apache HTTPD, Post\ufb01x SMTP mail clients, network \ufb01le sharing with Network File System (NFS) and Server Message Block (SMB), iSCSI initiators and targets, advanced networking facilities and \ufb01rewall con\ufb01gurations, and the use of Bash shell scripting to help automate, con\ufb01gure, and troubleshoot the system. These topics are taught through lectures and hands-on labs.",
                  "learning_outcomes": [],
                  "skills": [
                    "Programming"
                  ]
                },
                {
                  "code": "C S 31A",
                  "name": "INTRODUCTION TO DATABASE MANAGEMENT SYSTEMS",
                  "description": "Introduction to database design and use of database management systems for applications. Topics include database architecture, comparison to \ufb01le-based systems, historical data models, conceptual model; integrity constraints and triggers; functional dependencies and normal forms; relational model, algebra, database processing and Structured Query Language (SQL), database access from Applications-Embedded SQL, JDBC, Cursors, Dynamic SQL, Stored Procedures. Emerging trends will be studied, such as NoSQL databases, internet and databases, and Online Analytical Processing (OLAP). A team project that builds a database application for a real-world scenario is an important element of the course.",
                  "learning_outcomes": [],
                  "skills": [
                    "Programming",
                    "Software Development"
                  ]
                },
                {
                  "code": "C S 3A",
                  "name": "OBJECT-ORIENTED PROGRAMMING METHODOLOGIES IN PYTHON",
                  "description": "Systematic introduction to fundamental concepts of computer science through the study of the Python programming language. Coding topics include control structures, functions, classes, string processing, lists, tuples, dictionaries, working with \ufb01les, and elementary graphics. Concept topics include algorithms, data abstraction, problem solving strategies, code style, documentation, debugging techniques and testing.",
                  "learning_outcomes": [],
                  "skills": [
                    "Algorithms",
                    "Programming",
                    "Software Development"
                  ]
                },
                {
                  "code": "C S 3B",
                  "name": "INTERMEDIATE SOFTWARE DESIGN IN PYTHON",
                  "description": "Systematic treatment of intermediate concepts in computer science through the study of Python object-oriented programming (OOP). Coding topics include Python sequences, user-de\ufb01ned classes and interfaces, modules, packages, collection classes, threads, lambda expressions, list comprehensions, regular expressions and multi-dimensional arrays. Concept topics include OOP project design, recursion, inheritance, polymorphism, functional programming, linked-lists, FIFOs, LIFOs, event-driven parsing, exceptions, and guarded code.",
                  "learning_outcomes": [],
                  "skills": [
                    "Algorithms",
                    "Programming",
                    "Software Development"
                  ]
                },
                {
                  "code": "C S 3C",
                  "name": "ADVANCED DATA STRUCTURES & ALGORITHMS IN PYTHON",
                  "description": "A systematic treatment of advanced data structures, algorithm analysis, and abstract data types in the Python programming language, intended for computer science majors as well as non-majors and professionals seeking advanced Python experience. Coding topics include large program software engineering design, multi-dimensional arrays, string processing, primitives, compound types, and allocation of instance and static data. Data structure concept topics include dynamic memory, inheritance, polymorphism, hierarchies, recursion, linked-lists, stacks, queues, trees, hash tables, and graphs. Algorithm concept topics include searching, big-O time complexity, analysis of all major sorting techniques, top down splaying, AVL tree balancing, shortest path algorithms, minimum spanning trees, and maximum flow graphs.",
                  "learning_outcomes": [],
                  "skills": [
                    "Algorithms",
                    "Programming",
                    "Software Development"
                  ]
                },
                {
                  "code": "C S 40A",
                  "name": "SOFTWARE ENGINEERING METHODOLOGIES",
                  "description": "A collaboration-oriented course that trains students in the techniques currently used by software engineers to develop reliable products in an ef\ufb01cient manner. The course emphasizes Agile methods and a variety of tools used during the software development lifecycle.",
                  "learning_outcomes": [],
                  "skills": [
                    "Software Development"
                  ]
                },
                {
                  "code": "C S 48A",
                  "name": "DATA VISUALIZATION",
                  "description": "Introduction to the effective processing and communication of data. Topics include identifying the key techniques and theory used in data visualization, creating and designing static and interactive visualizations using data, and communicating insight through data visualization to an intended audience. Students will use a data visualization package, such as R, Tableau, or MatPlotLib in Python.",
                  "learning_outcomes": [],
                  "skills": [
                    "Programming"
                  ]
                },
                {
                  "code": "C S 49",
                  "name": "FOUNDATIONS OF COMPUTER PROGRAMMING",
                  "description": "Introduction to basic computer programming concepts using an object-oriented language. Topics include the software life-cycle, procedural vs. object-oriented programming, IDE and debugging, documentation, and coding conventions. Using an object-oriented computer language, students will explore data types, basic data structures and algorithms, control structure, console and \ufb01le I/O, functions, error handling and testing.",
                  "learning_outcomes": [],
                  "skills": [
                    "Algorithms",
                    "Programming",
                    "Software Development"
                  ]
                },
                {
                  "code": "C S 55B",
                  "name": "DATABASE ESSENTIALS IN AMAZON WEB SERVICES",
                  "description": "This course addresses database fundamentals and cloud database design patterns and management. A wide variety of database needs are presented, such as structured, semi-structured, and unstructured datasets, and how those are supported in the cloud. Students learn to deploy a SQL database on infrastructure components and perform basic data operations on that infrastructure. Students then take those basic concepts and learn managed platform as a service solutions, such as Amazon RDS, Amazon DynamoDB, Amazon Kinesis stream processing/ analytics, in memory database accelerators, and ML big data tools. Basic database administration skills, such as migration, backups, restoration, retention, service con\ufb01guration, high availability, and service scaling, are presented.",
                  "learning_outcomes": [],
                  "skills": [
                    "Programming"
                  ]
                },
                {
                  "code": "C S 55C",
                  "name": "COMPUTE ENGINES IN AMAZON WEB SERVICES",
                  "description": "In this course, students explore how compute workloads are supported using a set of core technologies in the Amazon Web Services (AWS) platform. Students use the AWS Management Console, Command Line Interface (CLI), and Cloud Formation infrastructure deployment tools to deploy services. The course takes a deep look into virtualization using AWS Elastic Compute Cloud (EC2) by detailing con\ufb01guration options for speci\ufb01c workloads in terms of performant compute/memory/storage capabilities. Modern application architectures, such as serverless, microservices, containerization, service orchestration, and edge computing, are detailed and their deployment using AWS services are demonstrated.",
                  "learning_outcomes": [],
                  "skills": [
                    "Software Development"
                  ]
                },
                {
                  "code": "C S 56B",
                  "name": "IT ESSENTIALS",
                  "description": "The course presents a working knowledge of computer internals and provides practical skills in computer hardware assembly and software installation. Emphasis is placed on troubleshooting problems throughout the process. Activities include hands-on labs and virtual learning tools which encourage critical thinking and complex problem-solving skills.",
                  "learning_outcomes": [],
                  "skills": [
                    "Software Development"
                  ]
                },
                {
                  "code": "C S 63A",
                  "name": "DEVELOPING APPLICATIONS FOR IOS",
                  "description": "An introduction to programming the iPhone and other iOS devices. Covers Swift, Cocoa Touch, and the Model/View/Controller architecture. Students learn the basics of Swift and acquire practical experience with the tools, techniques, and concepts needed to build a basic iOS app from scratch.",
                  "learning_outcomes": [],
                  "skills": [
                    "Programming",
                    "Software Development"
                  ]
                },
                {
                  "code": "C S 64A",
                  "name": "WRITING APPS FOR THE ANDROID",
                  "description": "Introduction to programming mobile apps for the Android. Coding topics include the Android SDK for Eclipse, the ADT plugin, XML fundamentals, and a survey of API methods and objects used to control the Android user interface. Concept topics include layouts, activity lifecycles, runtime binding, intents, location awareness, audio, video, OpenGL ES, and monetizing apps.",
                  "learning_outcomes": [],
                  "skills": [
                    "Programming",
                    "Software Development"
                  ]
                },
                {
                  "code": "C S 77A",
                  "name": "ADVANCED WEB APPLICATION DEVELOPMENT",
                  "description": "Design and develop applications that deliver similar features and functions normally associated with desktop applications using modern web client and server technologies.",
                  "learning_outcomes": [],
                  "skills": [
                    "Programming",
                    "Software Development"
                  ]
                },
                {
                  "code": "C S 77B",
                  "name": "PROJECTS IN WEB APPLICATION DEVELOPMENT",
                  "description": "Team-based applied web application projects as determined in consultation with the instructor. Students meet at least twice per week with the instructor; about half of the lecture periods are team project-based interactions. Volunteer or work-based learning portfolio, progress reports, oral presentations, \ufb01nal report, teamwork assessments, and evaluation by project supervisor or client will be used to demonstrate the mastery of competencies identi\ufb01ed as goals prior to, or near the start of, the project(s). Project work can be within the context of an internship or developing an internship or start-up opportunity.",
                  "learning_outcomes": [],
                  "skills": [
                    "Software Development"
                  ]
                },
                {
                  "code": "C S 80A",
                  "name": "OPEN SOURCE CONTRIBUTION",
                  "description": "Introduction to the tools for, and culture of, contributing to open source software projects. Tool-based topics include Git repositories, pull requests, forks, logs, merges, tagging, rebasing and server con\ufb01guration. Concept topics include commit guidelines, branching workflows, small- team vs. large-team workflows, project maintenance, iterative staging, selecting viable source communities, joining public projects, setting up accurate dev environments, testing and prepping patch merges, and becoming a committer.",
                  "learning_outcomes": [],
                  "skills": [
                    "Software Development"
                  ]
                },
                {
                  "code": "C S 84A",
                  "name": "DATABASE-DRIVEN WEB APPLICATION DEVELOPMENT",
                  "description": "Students evolve simple static websites into dynamic, database-driven web applications. Students will use the popular LAMP framework (Linux, Apache, MySQL, and PHP), in combination with JavaScript, CSS, and HTML5.",
                  "learning_outcomes": [],
                  "skills": [
                    "Programming",
                    "Software Development"
                  ]
                },
                {
                  "code": "C S 8A",
                  "name": "INTRODUCTION TO DATA SCIENCE",
                  "description": "Introduction to the fundamental concepts and computational skills needed to understand and analyze data arising from real-world phenomena. Topics include key data science concepts such as correlation vs. causation, randomness, sampling, uncertainty, predictive models, and classi\ufb01cation. Using a tool such as Jupyter notebooks, students write code for transformation and use of data tables, simulation models, and A/B testing.",
                  "learning_outcomes": [],
                  "skills": [
                    "Algorithms",
                    "Programming"
                  ]
                }
              ],
              "aligned_skills": [
                "Algorithms",
                "Programming",
                "Software Development"
              ]
            }
          ],
          "student_composition": "Students in the Computer Science department are studying programming, algorithms, and software development \u2014 the same competencies Agilent builds on for instrument software roles. They represent a strong candidate pool for a co-design effort that deepens their preparation in the applied, instrument-facing dimensions of software work.",
          "student_evidence": {
            "total_in_program": 563,
            "with_all_core_skills": 385,
            "top_students": [
              {
                "uuid": "b5959389-0f25-5c8a-911b-0369ea11e78a",
                "display_number": 1,
                "primary_focus": "Computer Science",
                "courses_completed": 3,
                "gpa": 4.0,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "C S 10",
                    "name": "COMPUTER ARCHITECTURE & ORGANIZATION",
                    "grade": "W",
                    "term": "2022-Fall"
                  },
                  {
                    "code": "C S 1C",
                    "name": "ADVANCED DATA STRUCTURES & ALGORITHMS IN JAVA",
                    "grade": "A",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "C S 12A",
                    "name": "INTRODUCTION TO MACHINE LEARNING",
                    "grade": "W",
                    "term": "2022-Winter"
                  }
                ],
                "relevant_skills": [
                  "Algorithms",
                  "Programming",
                  "Software Development"
                ]
              },
              {
                "uuid": "d5ab73d9-b2f4-5b14-97f5-050ef35e8a73",
                "display_number": 2,
                "primary_focus": "Computer Science",
                "courses_completed": 5,
                "gpa": 4.0,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "C S 3A",
                    "name": "OBJECT-ORIENTED PROGRAMMING METHODOLOGIES IN PYTHON",
                    "grade": "W",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "C S 30E",
                    "name": "LINUX SYSTEM ADMINISTRATION: NETWORK SERVICES",
                    "grade": "W",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "C S 2B",
                    "name": "INTERMEDIATE SOFTWARE DESIGN IN C++",
                    "grade": "A",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "C S 11A",
                    "name": "INTRODUCTION TO ARTIFICIAL INTELLIGENCE",
                    "grade": "W",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "C S 77A",
                    "name": "ADVANCED WEB APPLICATION DEVELOPMENT",
                    "grade": "A",
                    "term": "2025-Spring"
                  }
                ],
                "relevant_skills": [
                  "Algorithms",
                  "Programming",
                  "Software Development"
                ]
              },
              {
                "uuid": "00d566bc-0b16-5cc2-8e5a-e365ad8c5299",
                "display_number": 3,
                "primary_focus": "Computer Science",
                "courses_completed": 2,
                "gpa": 4.0,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "C S 10",
                    "name": "COMPUTER ARCHITECTURE & ORGANIZATION",
                    "grade": "A",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "C S 55C",
                    "name": "COMPUTE ENGINES IN AMAZON WEB SERVICES",
                    "grade": "A",
                    "term": "2023-Fall"
                  }
                ],
                "relevant_skills": [
                  "Algorithms",
                  "Programming",
                  "Software Development"
                ]
              },
              {
                "uuid": "741ada8c-b02e-554b-9605-75436c525626",
                "display_number": 4,
                "primary_focus": "Computer Science",
                "courses_completed": 1,
                "gpa": 4.0,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "C S 2A",
                    "name": "OBJECT-ORIENTED PROGRAMMING METHODOLOGIES IN C++",
                    "grade": "A",
                    "term": "2025-Spring"
                  }
                ],
                "relevant_skills": [
                  "Algorithms",
                  "Programming",
                  "Software Development"
                ]
              },
              {
                "uuid": "668813f7-8214-5e47-b99c-843584c3419b",
                "display_number": 5,
                "primary_focus": "Computer Science",
                "courses_completed": 3,
                "gpa": 4.0,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "C S 3A",
                    "name": "OBJECT-ORIENTED PROGRAMMING METHODOLOGIES IN PYTHON",
                    "grade": "A",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "C S 2C",
                    "name": "ADVANCED DATA STRUCTURES & ALGORITHMS IN C++",
                    "grade": "A",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "C S 77B",
                    "name": "PROJECTS IN WEB APPLICATION DEVELOPMENT",
                    "grade": "W",
                    "term": "2024-Fall"
                  }
                ],
                "relevant_skills": [
                  "Algorithms",
                  "Programming",
                  "Software Development"
                ]
              },
              {
                "uuid": "021c5a52-e474-5b04-b676-ecc7dfb4e6d9",
                "display_number": 6,
                "primary_focus": "Computer Science",
                "courses_completed": 3,
                "gpa": 4.0,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "C S 2A",
                    "name": "OBJECT-ORIENTED PROGRAMMING METHODOLOGIES IN C++",
                    "grade": "A",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "C S 10",
                    "name": "COMPUTER ARCHITECTURE & ORGANIZATION",
                    "grade": "A",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "C S 3B",
                    "name": "INTERMEDIATE SOFTWARE DESIGN IN PYTHON",
                    "grade": "A",
                    "term": "2025-Spring"
                  }
                ],
                "relevant_skills": [
                  "Algorithms",
                  "Programming",
                  "Software Development"
                ]
              },
              {
                "uuid": "00bd321a-9d3d-5368-ba52-4fb0e55c46a4",
                "display_number": 7,
                "primary_focus": "Computer Science",
                "courses_completed": 2,
                "gpa": 4.0,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "C S 3A",
                    "name": "OBJECT-ORIENTED PROGRAMMING METHODOLOGIES IN PYTHON",
                    "grade": "A",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "C S 84A",
                    "name": "DATABASE-DRIVEN WEB APPLICATION DEVELOPMENT",
                    "grade": "A",
                    "term": "2024-Spring"
                  }
                ],
                "relevant_skills": [
                  "Algorithms",
                  "Programming",
                  "Software Development"
                ]
              },
              {
                "uuid": "77bdd90c-ae06-5894-bafa-f7c33d264a49",
                "display_number": 8,
                "primary_focus": "Computer Science",
                "courses_completed": 2,
                "gpa": 4.0,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "C S 3A",
                    "name": "OBJECT-ORIENTED PROGRAMMING METHODOLOGIES IN PYTHON",
                    "grade": "A",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "C S 64A",
                    "name": "WRITING APPS FOR THE ANDROID",
                    "grade": "A",
                    "term": "2025-Spring"
                  }
                ],
                "relevant_skills": [
                  "Algorithms",
                  "Programming",
                  "Software Development"
                ]
              },
              {
                "uuid": "eec7b14d-e58c-5b72-854f-e0c72af62fb0",
                "display_number": 9,
                "primary_focus": "Computer Science",
                "courses_completed": 4,
                "gpa": 4.0,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "C S 1A",
                    "name": "OBJECT-ORIENTED PROGRAMMING METHODOLOGIES IN JAVA",
                    "grade": "W",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "C S 2A",
                    "name": "OBJECT-ORIENTED PROGRAMMING METHODOLOGIES IN C++",
                    "grade": "A",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "C S 48A",
                    "name": "DATA VISUALIZATION",
                    "grade": "A",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "C S 203A",
                    "name": "JUST-IN-TIME SUPPORT FOR C S 3A",
                    "grade": "P",
                    "term": "2024-Fall"
                  }
                ],
                "relevant_skills": [
                  "Algorithms",
                  "Programming",
                  "Software Development"
                ]
              },
              {
                "uuid": "6ed48fd9-99d0-5353-85bd-e461b205392e",
                "display_number": 10,
                "primary_focus": "Computer Science",
                "courses_completed": 5,
                "gpa": 4.0,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "C S 30A",
                    "name": "INTRODUCTION TO LINUX",
                    "grade": "A",
                    "term": "2022-Fall"
                  },
                  {
                    "code": "C S 12A",
                    "name": "INTRODUCTION TO MACHINE LEARNING",
                    "grade": "A",
                    "term": "2022-Fall"
                  },
                  {
                    "code": "C S 20A",
                    "name": "PROGRAMMING IN C#",
                    "grade": "W",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "C S 22A",
                    "name": "JAVASCRIPT FOR PROGRAMMERS",
                    "grade": "A",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "C S 49",
                    "name": "FOUNDATIONS OF COMPUTER PROGRAMMING",
                    "grade": "A",
                    "term": "2022-Winter"
                  }
                ],
                "relevant_skills": [
                  "Algorithms",
                  "Programming",
                  "Software Development"
                ]
              }
            ]
          }
        },
        "roadmap": "A working group between the Computer Science department and Agilent's software engineering or applications teams could evaluate how laboratory instrument software integration and automation, specifically SCPI and GPIB protocols, might be incorporated into existing coursework or a targeted module. Revised or new content could be piloted within the next catalog cycle, with scope and approach determined collaboratively.",
        "selected_occupations": [],
        "advisory_thesis": "",
        "agenda_topics": []
      },
      "engagementType": "curriculum_codesign",
      "collegeId": "Foothill College",
      "savedAt": "2026-04-20T00:00:00.000Z",
      "status": "saved",
      "schemaVersion": 8
    }
  ],
  "Compton College": [
    {
      "id": "seed-compton-advisory-01",
      "proposal": {
        "employer": "Southern California Edison",
        "sector": "Utilities",
        "partnership_type": "Advisory Board",
        "selected_occupation": "Electrical Engineers",
        "selected_soc_code": "17-2071",
        "core_skills": [
          "Electrical Systems",
          "Circuit Analysis",
          "Troubleshooting",
          "Workplace Safety"
        ],
        "gap_skill": "",
        "regions": [
          "Orange County",
          "Los Angeles",
          "South Central Coast"
        ],
        "opportunity": "Southern California Edison's role operating one of the largest electrical distribution networks in the country makes it a compelling advisory board partner for Compton College's technical programs. SCE employs electrical engineers, powerhouse and relay repairers, and facilities managers across Orange County, Los Angeles, and the South Central Coast to sustain grid reliability across a densely populated region. An advisory board formalizes that operational expertise as a standing channel for program guidance with no grant funding required.",
        "opportunity_evidence": [
          {
            "title": "Facilities Managers",
            "soc_code": "11-3013",
            "annual_wage": 113350,
            "employment": 4300,
            "annual_openings": 380,
            "growth_rate": 0.027319381
          },
          {
            "title": "Electrical and Electronics Repairers, Powerhouse, Substation, and Relay",
            "soc_code": "49-2095",
            "annual_wage": 110270,
            "employment": 470,
            "annual_openings": 40,
            "growth_rate": -0.035732244
          },
          {
            "title": "Electrical Engineers",
            "soc_code": "17-2071",
            "annual_wage": 133230,
            "employment": 4860,
            "annual_openings": 260,
            "growth_rate": -0.004901741
          }
        ],
        "justification": {
          "curriculum_composition": "The Engineering Technology and Manufacturing Technology departments provide the closest match to SCE's workforce operations. Engineering Technology builds circuit analysis, electrical systems, and troubleshooting competencies directly relevant to substation and relay protection work. Manufacturing Technology reinforces electrical systems and troubleshooting preparation across four courses, grounding students in the hands-on technical foundation that utility-scale maintenance roles require.",
          "curriculum_evidence": [
            {
              "department": "Engineering Technology",
              "courses": [
                {
                  "code": "ETEC 114",
                  "name": "Electronics for Engineering Technologists",
                  "description": "In this course, students are introduced to the application of electronics in engineering technology. The topics studied include safety, Ohm's Law, engineering notation, Direct Current (DC) circuits, capacitance, inductance, reactance, impedance, analog and digital waveforms, basic motors, number systems, logic gates, Boolean algebra, flipflops, shift registers and microprocessors. Techniques in computer simulation and electrical measurements will be stressed.",
                  "learning_outcomes": [],
                  "skills": [
                    "Circuit Analysis",
                    "Electrical Systems",
                    "Troubleshooting"
                  ]
                },
                {
                  "code": "ETEC 114A",
                  "name": "Electronics for Engineering Technologists I",
                  "description": "This is the first of two courses in which students are introduced to the application of electronics in engineering technology. The topics studied include safety, Ohm's Law, engineering notation, direct current circuits, capacitance, inductance, reactance, and impedance. Techniques in computer simulation and electrical measurements will be stressed.",
                  "learning_outcomes": [],
                  "skills": [
                    "Circuit Analysis",
                    "Electrical Systems",
                    "Troubleshooting"
                  ]
                },
                {
                  "code": "ETEC 114B",
                  "name": "Electronics for Engineering Technologists II",
                  "description": "This is the second of two courses in which students are introduced to the application of electronics in engineering technology. The topics studied include safety, analog and digital waveforms, basic motors, number systems, logic gates, Boolean algebra, flip-flops, shift registers and micro-processors. Techniques in computer simulation and electrical measurements will be stressed.",
                  "learning_outcomes": [],
                  "skills": [
                    "Circuit Analysis",
                    "Electrical Systems",
                    "Troubleshooting"
                  ]
                }
              ],
              "aligned_skills": [
                "Circuit Analysis",
                "Electrical Systems",
                "Troubleshooting"
              ]
            },
            {
              "department": "Manufacturing Technology",
              "courses": [
                {
                  "code": "MTEC 170",
                  "name": "Basic Robotics",
                  "description": "Students will explore the technologies used to fabricate model robotics systems. Additional topics covered include basic electronics theory, electro-mechanical assembly, motors and micro-controller operation, basic programming, and careers in technology. Students will construct and test prototype robots. Project building and problem solving will be emphasized.",
                  "learning_outcomes": [],
                  "skills": [
                    "Electrical Systems",
                    "Troubleshooting"
                  ]
                },
                {
                  "code": "MTEC 175",
                  "name": "Integrated Robotic and Automated Technologies",
                  "description": "This course covers robotic and automation applications with emphasis on imbedded electronics, micro- controller programming, motors, and drive trains. Additional topics covered include electronics theory, electro- mechanical fabrication, sensors, manufacturing materials and processes and career fields in which robotic applications are used. Students will construct, program, and test a vehicular or process robot.",
                  "learning_outcomes": [],
                  "skills": [
                    "Electrical Systems"
                  ]
                },
                {
                  "code": "MTEC 175A",
                  "name": "Integrated Robotic and Automated Technologies I",
                  "description": "This is the first course in a two-course sequence that covers robotic and automation applications with emphasis on electronics theory, electromechanical fabrication, motors, and drive trains. Students will construct, program, and test a vehicular or process robot.",
                  "learning_outcomes": [],
                  "skills": [
                    "Electrical Systems",
                    "Troubleshooting"
                  ]
                },
                {
                  "code": "MTEC 175B",
                  "name": "Integrated Robotic and Automated Technologies II",
                  "description": "This is the second course in a two-course sequence that covers robotic and automation applications with emphasis on imbedded electronics, microcontroller programming, sensors, manufacturing materials and processes. Students will construct, program, and test a vehicular or process robot to satisfy instructor assigned goals or tasks.",
                  "learning_outcomes": [],
                  "skills": [
                    "Electrical Systems"
                  ]
                }
              ],
              "aligned_skills": [
                "Electrical Systems",
                "Troubleshooting"
              ]
            },
            {
              "department": "Machine Tool Technology",
              "courses": [
                {
                  "code": "MTT 101",
                  "name": "Introduction to Conventional and CNC Machining",
                  "description": "In this course, students will be introduced to the principles and operation of conventional and Computer Numerically Controlled (CNC) machine tools with an emphasis on safety, measurement, hand tools, power saws, drilling machines, lathes, and milling and grinding machines focusing on practices and setups used in industry.",
                  "learning_outcomes": [],
                  "skills": [
                    "Workplace Safety"
                  ]
                },
                {
                  "code": "MTT 103",
                  "name": "Conventional and CNC Turning",
                  "description": "In this course, students will study at an advanced level the principles and operation of conventional and Computer Numerically Controlled (CNC) machine tools with an emphasis on the set up and operation of lathes. Topics will include safety, turning, drilling, boring, threading, cutting tools, CNC programming practices, and setups as applied in industry.",
                  "learning_outcomes": [],
                  "skills": [
                    "Workplace Safety"
                  ]
                },
                {
                  "code": "MTT 105",
                  "name": "Conventional and CNC Milling",
                  "description": "In this course, students will study at an advanced level the principles and operation of conventional and Computer Numerically Controlled (CNC) machine tools with an emphasis on the setup and operation of milling machines. Topics will include safety, drilling, milling, tapping, tooling, CNC programming practices, and setups as applied in industry.",
                  "learning_outcomes": [],
                  "skills": [
                    "Workplace Safety"
                  ]
                },
                {
                  "code": "MTT 146",
                  "name": "Basic Machine Tool Operation",
                  "description": "Students are introduced to the basic principles and operation of machine tools with a focus on bench operations, drilling, engine lathes, mills, and grinding machines. Standard industry practices and tool set-ups used are emphasized. Laboratory projects and exercises related to the lectures and demonstrations will be assigned.",
                  "learning_outcomes": [],
                  "skills": [
                    "Workplace Safety"
                  ]
                },
                {
                  "code": "MTT 160",
                  "name": "General Metals",
                  "description": "This course covers the general skills of metal working: machine shop practice, welding, bench work, art metal, foundry and sheet metal, design, construction, and occupational exploration.",
                  "learning_outcomes": [],
                  "skills": [
                    "Workplace Safety"
                  ]
                },
                {
                  "code": "MTT 201",
                  "name": "Introduction to Aerospace Fastener Technology",
                  "description": "In this course, students are introduced to fastener's standard measurement techniques, cold-heading (forging), thread-rolling, centerless grinding, turning, trimming, and interpretation of travelers (routers). Standard aerospace fastener industry practices, safety procedures, and set-ups are emphasized.",
                  "learning_outcomes": [],
                  "skills": [
                    "Workplace Safety"
                  ]
                }
              ],
              "aligned_skills": [
                "Workplace Safety"
              ]
            }
          ],
          "student_composition": "Students across the Engineering Technology and Manufacturing Technology departments are developing applied technical skills in electrical systems and troubleshooting that align with the roles SCE fills across Southern California. The Machine Tool Technology department adds a pipeline of students building workplace safety competencies relevant to facilities and infrastructure work. Together these programs represent a multi-pathway student population entering a regional labor market where SCE is an active employer.",
          "student_evidence": {
            "total_in_program": 167,
            "with_all_core_skills": 31,
            "top_students": [
              {
                "uuid": "83777529-e094-597f-8a70-20b3d9d57878",
                "display_number": 1,
                "primary_focus": "Engineering Technology",
                "courses_completed": 2,
                "gpa": 3.71,
                "matching_skills": 4,
                "enrollments": [
                  {
                    "code": "ETEC 114A",
                    "name": "Electronics for Engineering Technologists I",
                    "grade": "A",
                    "term": "2022-Fall"
                  },
                  {
                    "code": "CA 101",
                    "name": "Culinary Arts Orientation and Techniques",
                    "grade": "B",
                    "term": "2023-Fall"
                  }
                ],
                "relevant_skills": [
                  "Circuit Analysis",
                  "Electrical Systems",
                  "Troubleshooting",
                  "Workplace Safety"
                ]
              },
              {
                "uuid": "70decafd-a535-5dd4-8253-fc5f2efa4794",
                "display_number": 2,
                "primary_focus": "Engineering Technology",
                "courses_completed": 3,
                "gpa": 3.68,
                "matching_skills": 4,
                "enrollments": [
                  {
                    "code": "THEA 185",
                    "name": "Introduction to Stage Lighting",
                    "grade": "C",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "ETEC 114B",
                    "name": "Electronics for Engineering Technologists II",
                    "grade": "A",
                    "term": "2022-Fall"
                  },
                  {
                    "code": "COSM 112",
                    "name": "Advanced Cosmetology",
                    "grade": "A",
                    "term": "2023-Winter"
                  }
                ],
                "relevant_skills": [
                  "Circuit Analysis",
                  "Electrical Systems",
                  "Troubleshooting",
                  "Workplace Safety"
                ]
              },
              {
                "uuid": "a8e6b1c1-9bc3-5ed4-8ab3-46174979ec28",
                "display_number": 3,
                "primary_focus": "Engineering Technology",
                "courses_completed": 2,
                "gpa": 3.62,
                "matching_skills": 4,
                "enrollments": [
                  {
                    "code": "ETEC 114A",
                    "name": "Electronics for Engineering Technologists I",
                    "grade": "A",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "WELD 109",
                    "name": "Advanced Welding for Manufacturing",
                    "grade": "A",
                    "term": "2024-Fall"
                  }
                ],
                "relevant_skills": [
                  "Circuit Analysis",
                  "Electrical Systems",
                  "Troubleshooting",
                  "Workplace Safety"
                ]
              },
              {
                "uuid": "3183b718-1a40-520a-bf62-b2ecb493dc18",
                "display_number": 4,
                "primary_focus": "Engineering Technology",
                "courses_completed": 4,
                "gpa": 3.58,
                "matching_skills": 4,
                "enrollments": [
                  {
                    "code": "THEA 185",
                    "name": "Introduction to Stage Lighting",
                    "grade": "B",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "ETEC 114A",
                    "name": "Electronics for Engineering Technologists I",
                    "grade": "A",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "COSM 125",
                    "name": "Cosmetology Applications",
                    "grade": "A",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "COSM 112",
                    "name": "Advanced Cosmetology",
                    "grade": "W",
                    "term": "2024-Spring"
                  }
                ],
                "relevant_skills": [
                  "Circuit Analysis",
                  "Electrical Systems",
                  "Troubleshooting",
                  "Workplace Safety"
                ]
              },
              {
                "uuid": "76ba0462-6115-593c-bc73-f0e0f2199a5a",
                "display_number": 5,
                "primary_focus": "Engineering Technology",
                "courses_completed": 2,
                "gpa": 3.53,
                "matching_skills": 4,
                "enrollments": [
                  {
                    "code": "ETEC 114A",
                    "name": "Electronics for Engineering Technologists I",
                    "grade": "A",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "SOCI 208B",
                    "name": "Fieldwork in Social Work and Human Services Seminar",
                    "grade": "A",
                    "term": "2023-Winter"
                  }
                ],
                "relevant_skills": [
                  "Circuit Analysis",
                  "Electrical Systems",
                  "Troubleshooting",
                  "Workplace Safety"
                ]
              },
              {
                "uuid": "8df15589-5251-5971-903e-0485c472a806",
                "display_number": 6,
                "primary_focus": "Engineering Technology",
                "courses_completed": 2,
                "gpa": 3.5,
                "matching_skills": 4,
                "enrollments": [
                  {
                    "code": "ETEC 114B",
                    "name": "Electronics for Engineering Technologists II",
                    "grade": "A",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "COSM 114",
                    "name": "Advanced Cosmetology and Introduction to State Board Review",
                    "grade": "A",
                    "term": "2025-Spring"
                  }
                ],
                "relevant_skills": [
                  "Circuit Analysis",
                  "Electrical Systems",
                  "Troubleshooting",
                  "Workplace Safety"
                ]
              },
              {
                "uuid": "57ac3dae-4654-5ec5-8060-002f0395de94",
                "display_number": 7,
                "primary_focus": "Engineering Technology",
                "courses_completed": 3,
                "gpa": 3.5,
                "matching_skills": 4,
                "enrollments": [
                  {
                    "code": "ETEC 114A",
                    "name": "Electronics for Engineering Technologists I",
                    "grade": "A",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "ACR 123",
                    "name": "Commercial Refrigeration Applications",
                    "grade": "A",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "COSM 110",
                    "name": "Intermediate Cosmetology",
                    "grade": "A",
                    "term": "2023-Fall"
                  }
                ],
                "relevant_skills": [
                  "Circuit Analysis",
                  "Electrical Systems",
                  "Troubleshooting",
                  "Workplace Safety"
                ]
              },
              {
                "uuid": "ce06089a-9c0f-5e39-8584-05c8d345ca28",
                "display_number": 8,
                "primary_focus": "Engineering Technology",
                "courses_completed": 3,
                "gpa": 3.46,
                "matching_skills": 4,
                "enrollments": [
                  {
                    "code": "ETEC 114B",
                    "name": "Electronics for Engineering Technologists II",
                    "grade": "A",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "ETEC 114",
                    "name": "Electronics for Engineering Technologists",
                    "grade": "A",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "CA 100",
                    "name": "Sanitation and Safety",
                    "grade": "B",
                    "term": "2024-Fall"
                  }
                ],
                "relevant_skills": [
                  "Circuit Analysis",
                  "Electrical Systems",
                  "Troubleshooting",
                  "Workplace Safety"
                ]
              },
              {
                "uuid": "9e9433da-1e18-52b0-9cd0-008f6e9a6234",
                "display_number": 9,
                "primary_focus": "Engineering Technology",
                "courses_completed": 3,
                "gpa": 3.46,
                "matching_skills": 4,
                "enrollments": [
                  {
                    "code": "ETEC 114B",
                    "name": "Electronics for Engineering Technologists II",
                    "grade": "A",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "ETEC 114A",
                    "name": "Electronics for Engineering Technologists I",
                    "grade": "A",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "ACRP 132",
                    "name": "Automotive Refinishing Materials and Equipment",
                    "grade": "B",
                    "term": "2024-Winter"
                  }
                ],
                "relevant_skills": [
                  "Circuit Analysis",
                  "Electrical Systems",
                  "Troubleshooting",
                  "Workplace Safety"
                ]
              },
              {
                "uuid": "781f6230-a706-5f98-960c-41914f52e441",
                "display_number": 10,
                "primary_focus": "Engineering Technology",
                "courses_completed": 3,
                "gpa": 3.45,
                "matching_skills": 4,
                "enrollments": [
                  {
                    "code": "ETEC 114B",
                    "name": "Electronics for Engineering Technologists II",
                    "grade": "A",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "ETEC 114",
                    "name": "Electronics for Engineering Technologists",
                    "grade": "A",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "SOCI 208A",
                    "name": "Social Work and Human Services Seminar",
                    "grade": "C",
                    "term": "2023-Winter"
                  }
                ],
                "relevant_skills": [
                  "Circuit Analysis",
                  "Electrical Systems",
                  "Troubleshooting",
                  "Workplace Safety"
                ]
              }
            ]
          }
        },
        "roadmap": "A quarterly advisory board with SCE operational and technical leadership could give Compton College's programs sustained access to utility-industry perspective. Potential starting points for the inaugural meeting include which substation and relay protection tasks new hires perform in their first year, how SCE structures on-the-job troubleshooting protocols for powerhouse repairers, and what safety training facilities personnel complete before working near energized high-voltage equipment.",
        "selected_occupations": [
          "Electrical Engineers",
          "Electrical and Electronics Repairers, Powerhouse, Substation, and Relay",
          "Facilities Managers"
        ],
        "advisory_thesis": "Southern California Edison manages one of the largest electrical distribution networks in the country, requiring personnel who can design, maintain, and troubleshoot high-voltage infrastructure across a sprawling and densely populated region. This operational scale makes their perspective directly relevant to programs in electrical engineering, power systems technology, and facilities management, where students benefit from understanding the real-world demands of grid reliability and large-scale utility operations.",
        "agenda_topics": [
          {
            "topic": "Which substation and relay protection tasks do new hires perform in their first year that Engineering Technology graduates should be ready for?",
            "rationale": "SCE's operational experience with high-voltage substation workflows can help Engineering Technology refine the sequence and depth of its electrical systems coursework."
          },
          {
            "topic": "How does SCE structure on-the-job troubleshooting protocols for powerhouse repairers, and how closely do those mirror industry certification standards?",
            "rationale": "Understanding SCE's internal troubleshooting frameworks can help Engineering Technology and Manufacturing Technology align hands-on lab exercises with utility-grade expectations."
          },
          {
            "topic": "What workplace safety training do SCE facilities personnel complete before working near energized high-voltage equipment?",
            "rationale": "SCE's safety onboarding requirements can inform how Engineering Technology incorporates workplace safety standards into its existing facilities and electrical coursework."
          }
        ]
      },
      "engagementType": "advisory_board",
      "collegeId": "Compton College",
      "savedAt": "2026-04-20T00:00:00.000Z",
      "status": "saved",
      "schemaVersion": 8
    },
    {
      "id": "seed-compton-internship-01",
      "proposal": {
        "employer": "Kedren Community Health Center",
        "sector": "Professional Services",
        "partnership_type": "Internship Pipeline",
        "selected_occupation": "Registered Nurses",
        "selected_soc_code": "29-1141",
        "core_skills": [
          "Nursing Process",
          "Patient Assessment",
          "Medication Administration"
        ],
        "gap_skill": "",
        "regions": [
          "Los Angeles"
        ],
        "opportunity": "Kedren Community Health Center is a compelling internship partner for Compton College's Nursing program, given its community health focus and location within the Los Angeles region. Registered Nurses in the region earn $132,900 annually, with 5,090 openings projected each year and 5.3% growth. A structured internship at Kedren could place students in a community health environment where patient assessment, medication administration, and care coordination are central to daily clinical work.",
        "opportunity_evidence": [
          {
            "title": "Registered Nurses",
            "soc_code": "29-1141",
            "annual_wage": 132900,
            "employment": 80880,
            "annual_openings": 5090,
            "growth_rate": 0.053095652
          }
        ],
        "justification": {
          "curriculum_composition": "The Nursing department builds the clinical competencies most directly relevant to a Kedren internship across 18 courses. Its preparation in nursing process, patient assessment, and medication administration maps closely to the responsibilities students would encounter in a community health setting. That depth of preparation makes the Nursing department the natural anchor for this partnership.",
          "curriculum_evidence": [
            {
              "department": "Nursing",
              "courses": [
                {
                  "code": "NURS 143",
                  "name": "Introduction to Nursing",
                  "description": "In this introductory course students will examine the professional nurse's role and responsibilities in healthcare settings. Students will study the Nursing Program's philosophy which encompasses Maslow's and Kalish's Hierarchy of Human Needs and Watson's Theory of Human Caring. The students will apply and evaluate the impact of the nursing process when researching care of the patient with biophysical health conditions under the four domains of patient, professional nursing, health and illness and the healthcare environment. Specific emphasis will be placed on application of the nursing process, critical thinking, therapeutic communication, cultural, development, and diversity.",
                  "learning_outcomes": [],
                  "skills": [
                    "Nursing Process"
                  ]
                },
                {
                  "code": "NURS 144",
                  "name": "Dosage Calculations",
                  "description": "This course is designed to help students develop the necessary skills to calculate accurate and safe medication dosages. Advanced problem solving, application of algebraic concepts, formulas, proportional relationships, system of measurement, and measurement system conversions will be incorporated. Designated lab time will include clinical scenarios involving correct medication formulas and calculations, the selection of correct medical equipment to prepare and administer various types of medication, careful reading and interpretation of sample medication orders, and evaluation of medication labels for safe administration.",
                  "learning_outcomes": [],
                  "skills": [
                    "Medication Administration"
                  ]
                },
                {
                  "code": "NURS 146",
                  "name": "Health Assessment",
                  "description": "This course will help the student develop and utilize physical assessment and history-taking skills necessary to care for the biophysical needs of patients. The course focuses on the communication techniques and critical thinking skills necessary to elicit a health history. Concepts of patient, professional nursing, health and illness, and the healthcare environment will be introduced. Physical assessment skills will be developed to determine normal and abnormal findings of various body systems, including a general survey assessment. Enrollment to this course is only upon admission into the Nursing Program.",
                  "learning_outcomes": [],
                  "skills": [
                    "Nursing Process",
                    "Patient Assessment"
                  ]
                },
                {
                  "code": "NURS 149",
                  "name": "Advanced Placement in Nursing",
                  "description": "This course acquaints Licensed Vocational/Practical Nurses (LVN/LPN), and transfer students to concepts of nursing as they apply to the Compton College nursing program. Students will become familiar with the program philosophy, basic needs theory, nursing process, critical thinking, and communication. Course discussion will examine problems associated with ingestive, excretory, physical integrity and oxygenation (O2CO2) needs. Course discussion will also include transition to the registered nursing role and the impact of legal and ethical boundaries. Students will practice basic nursing skills and demonstrate competency.",
                  "learning_outcomes": [],
                  "skills": [
                    "Nursing Process"
                  ]
                },
                {
                  "code": "NURS 210",
                  "name": "Implications of Pathophysiology Concepts for Nurses",
                  "description": "In this course, the student will deepen their understanding of pathophysiology and the progressive effects of disease on the human body. Common single and multi-system disorders will be used to illustrate clinical relationships between the knowledge of pathophysiology, patient assessment, diagnostics, and management of care.",
                  "learning_outcomes": [],
                  "skills": [
                    "Patient Assessment"
                  ]
                },
                {
                  "code": "NURS 220",
                  "name": "Nursing Fundamentals",
                  "description": "This course introduces students to concepts related to the four domains of care which include the patient, professional nursing, health, and illness. The course further examines the nursing process as the foundation of nursing practice and emphasizes the delivery of care based on Maslow's and Kalish's Hierarchy of Human Needs and Watson's Model of Caring. Emphasis will be placed on the concepts of infection, thermoregulation, pain, tissue integrity, gas exchange, perfusion, safety, nutrition, elimination, mobility, sleep, culture, spirituality, caregiving, and the health care system. The student will gain a conceptual understanding of principles and be able to apply them in all areas of nursing practice.",
                  "learning_outcomes": [],
                  "skills": [
                    "Nursing Process"
                  ]
                },
                {
                  "code": "NURS 222",
                  "name": "Medical Surgical Nursing - Older Adult",
                  "description": "In this course, students will gain skills to assess and care for patients in the hospital setting. Emphasis will be placed on the care of the older adult population and includes critical thinking, legal and ethical issues within the nursing profession. Concepts include hormonal regulation, glucose regulation, perfusion, pain, communication, safety, functional ability, family dynamics, self-management and health promotion, intracranial regulation, cognition, interpersonal violence, ethics, health care law, sensory perception, mobility, and tissue integrity.",
                  "learning_outcomes": [],
                  "skills": [
                    "Nursing Process",
                    "Patient Assessment"
                  ]
                },
                {
                  "code": "NURS 224",
                  "name": "Nursing Pharmacology",
                  "description": "This course provides instruction from basic to advanced concepts and principles of pharmacology for nursing students. The knowledge and intervention needed to maximize therapeutic effects and prevent or minimize adverse effects of drugs will be emphasized. Major content areas will include advanced pharmacological principles, major drug classification, selected individual drugs, drug effects on body tissues, human responses to drug therapy, and the application of the nursing process. Anatomy, physiology, and microbiology concepts will be correlated with various pathologies, emphasizing the effects of drug therapy on body systems. Students will learn how to develop and present patient teaching plans. Legal and ethical issues will also be discussed.",
                  "learning_outcomes": [],
                  "skills": [
                    "Nursing Process"
                  ]
                },
                {
                  "code": "NURS 226",
                  "name": "Nursing Skills Practicum I",
                  "description": "Students will apply theoretical concepts and practice skills to maintain and promote the four domains of care including the patient, professional nursing, health, illness and the healthcare environment. Students will use the appropriate equipment and gain skill competency by practicing basic nursing skills in the skills lab. Competencies as related to physical assessment parenteral education administration wet-to-moist dressing change, nasogastric tube insertion, feeding and removal, and gastrostomy or jejunostomy feeding assessed. Emphasis placed on hands-on practice based on the following concepts: medical and surgical asepsis, physical hygiene, vital signs, oxygenation, nutrition, body mechanics, elimination, medication administration.",
                  "learning_outcomes": [],
                  "skills": [
                    "Medication Administration",
                    "Nursing Process",
                    "Patient Assessment"
                  ]
                },
                {
                  "code": "NURS 230",
                  "name": "Mental Health Nursing",
                  "description": "In this course, students will utilize the nursing process to care for clients with varying degrees of mental health problems Psychopharmacological therapies will be examined. Students will apply techniques of therapeutic communication and assume a leadership role in the clinical setting. In addition, students will utilize and maintain legal and ethical standards specific to mental health patients.",
                  "learning_outcomes": [],
                  "skills": [
                    "Nursing Process"
                  ]
                },
                {
                  "code": "NURS 232",
                  "name": "Obstetrical Patients and the Newborn",
                  "description": "This course focuses on the theory and practical application of concepts related to obstetrical patients and the newborn. The nursing process will be utilized as the foundation of study and emphasis will be placed on the concepts of reproduction, health promotion, self-management, infection, technology &; informatics, thermoregulation, perfusion, human sexuality, nutrition culture, and social/ethical aspects. The student will gain a conceptual understanding of principles in all areas specific to the obstetrical patient and the newborn.",
                  "learning_outcomes": [],
                  "skills": [
                    "Nursing Process"
                  ]
                },
                {
                  "code": "NURS 234",
                  "name": "Pediatric Nursing",
                  "description": "This course focuses on the theory and clinical application of concepts related to the nursing care of children and their families by emphasizing the holistic care of the child that include the developmental, physiological, psychosocial, cultural, and spiritual care of the child within the family unit. Health care concepts discussed in this course will include family dynamic development and functional abilities related to care of the child. Professional nursing concepts including clinical judgement, communication, ethical-legal, evidenced-based practice, health promotion, informatics, patient education, professionalism, safety, and collaboration will also be presented.",
                  "learning_outcomes": [],
                  "skills": [
                    "Nursing Process"
                  ]
                },
                {
                  "code": "NURS 238",
                  "name": "Nursing Skills Practicum II",
                  "description": "In this course, students will develop mastery of basic care principles and complex nursing skills to include the following nursing concepts; medical and surgical asepsis, physical hygiene, vital signs, oxygenation, nutrition, body mechanics, elimination, fluid and electrolyte, acid-base balance, and medication administration. Students will utilize the appropriate equipment and gain skill competency by practicing basic nursing skills in the skills lab. The nursing skills practicum course will assess the student's competencies, as they relate to physical assessment; urinary elimination, venipuncture, infusion pump and volitrol management, and glucose regulation.",
                  "learning_outcomes": [],
                  "skills": [
                    "Medication Administration",
                    "Nursing Process",
                    "Patient Assessment"
                  ]
                },
                {
                  "code": "NURS 240",
                  "name": "Intermediate Medical-Surgical Nursing I",
                  "description": "In this course, students are introduced to adult patients with moderate to severe disease states. Theory and clinical practice will focus on the biophysical concepts in medical-surgical conditions. Students will examine problems associated with tissue integrity, nutrition, inflammation, perfusion, acid-base balance, fluid and electrolytes, elimination, hormonal and glucose regulation, functional ability, safety, sexuality, and self-management.",
                  "learning_outcomes": [],
                  "skills": [
                    "Nursing Process"
                  ]
                },
                {
                  "code": "NURS 242",
                  "name": "Intermediate Medical-Surgical Nursing II",
                  "description": "In this course, students will learn about therapeutic care for patients with moderate to severe disease states by utilizing the nursing process, biophysical and medical/surgical concepts. Emphasis will be placed on the role of nurse as patient advocate and manager of care in the clinical setting.",
                  "learning_outcomes": [],
                  "skills": [
                    "Nursing Process"
                  ]
                },
                {
                  "code": "NURS 244",
                  "name": "Nursing Skills Practicum III",
                  "description": "In this course, students will apply persistent hands-on practice in the skills lab. They will assimilate mastery of the basic to complex nursing skills based on following nursing concepts: medical and surgical asepsis, physical hygiene, vital signs, nutrition, body mechanics, elimination, fluid and electrolyte, acid-base balance, and medication administration. Students will use the appropriate equipment and gain skill competency by practicing basic nursing skills in a safe, supportive, and supervised environment in the on-campus skills lab. The student's competency as it relates to physical assessment, administration of blood products, venipuncture of all variation, and oxygenation will be assessed.",
                  "learning_outcomes": [],
                  "skills": [
                    "Medication Administration",
                    "Nursing Process",
                    "Patient Assessment"
                  ]
                },
                {
                  "code": "NURS 247",
                  "name": "Advanced Medical-Surgical Nursing I",
                  "description": "In this course, students will explore biophysical concepts, knowledge of the critically ill patient across the life span and promoting wellness in culturally diverse populations and nursing management essential to the care of acute/chronic, critical, and emergency nursing. Clinical practice of critical care nursing will occur in a variety of settings.",
                  "learning_outcomes": [],
                  "skills": [
                    "Nursing Process"
                  ]
                },
                {
                  "code": "NURS 248",
                  "name": "Advanced Medical-Surgical Nursing II Preceptorship",
                  "description": "This preceptorship course provides the nursing student, enrolled in their last semester of nursing school, an opportunity to work directly with a RN preceptor. This experience allows students to apply knowledge and skills gained throughout the nursing program. The experience assists the student in making a smooth transition from the learner role to the entry-level registered nurses' role in a realistic clinical setting. Opportunities to implement leadership and management skills as well as decision-making and priority-setting utilizing legal and ethical principles will be provided.",
                  "learning_outcomes": [],
                  "skills": [
                    "Nursing Process"
                  ]
                }
              ],
              "aligned_skills": [
                "Medication Administration",
                "Nursing Process",
                "Patient Assessment"
              ]
            },
            {
              "department": "Fire and Emergency Technology",
              "courses": [
                {
                  "code": "FTEC 144",
                  "name": "Emergency Medical Technician",
                  "description": "In this course, students will study through lecture, role-play, simulations, field work, and hands-on practical training, the basic skills necessary for the assessment, rescue, immediate treatment, and transport of the urgently ill or injured person. Course content emphasizes emergency scene size-up, situational awareness, identifying and correcting life-threatening conditions, utilizing appropriate rescue techniques, and developing a systematic approach for providing pre-hospital care and safe transportation.",
                  "learning_outcomes": [],
                  "skills": [
                    "Patient Assessment"
                  ]
                }
              ],
              "aligned_skills": [
                "Patient Assessment"
              ]
            }
          ],
          "student_composition": "Students in the Nursing program are completing coursework aligned with the core competencies Kedren requires for registered nurse roles. The pipeline is concentrated in the program most relevant to this internship, and the community health context at Kedren reflects the populations many Compton College students are already familiar with.",
          "student_evidence": {
            "total_in_program": 294,
            "with_all_core_skills": 174,
            "top_students": [
              {
                "uuid": "421beea2-1c1b-51d1-9fc5-de768d08e2fb",
                "display_number": 1,
                "primary_focus": "Nursing",
                "courses_completed": 1,
                "gpa": 4.0,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "NURS 238",
                    "name": "Nursing Skills Practicum II",
                    "grade": "A",
                    "term": "2025-Spring"
                  }
                ],
                "relevant_skills": [
                  "Medication Administration",
                  "Nursing Process",
                  "Patient Assessment"
                ]
              },
              {
                "uuid": "7c9276cf-ab33-51c0-a550-4eb1d6a0de5a",
                "display_number": 2,
                "primary_focus": "Nursing",
                "courses_completed": 2,
                "gpa": 4.0,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "NURS 244",
                    "name": "Nursing Skills Practicum III",
                    "grade": "A",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "NURS 149",
                    "name": "Advanced Placement in Nursing",
                    "grade": "A",
                    "term": "2023-Winter"
                  }
                ],
                "relevant_skills": [
                  "Medication Administration",
                  "Nursing Process",
                  "Patient Assessment"
                ]
              },
              {
                "uuid": "408926d6-891e-52ef-a369-a4a40661e3f6",
                "display_number": 3,
                "primary_focus": "Nursing",
                "courses_completed": 5,
                "gpa": 3.88,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "NURS 242",
                    "name": "Intermediate Medical-Surgical Nursing II",
                    "grade": "B",
                    "term": "2022-Fall"
                  },
                  {
                    "code": "NURS 238",
                    "name": "Nursing Skills Practicum II",
                    "grade": "A",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "NURS 232",
                    "name": "Obstetrical Patients and the Newborn",
                    "grade": "A",
                    "term": "2022-Fall"
                  },
                  {
                    "code": "NURS 220",
                    "name": "Nursing Fundamentals",
                    "grade": "A",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "NURS 210",
                    "name": "Implications of Pathophysiology Concepts for Nurses",
                    "grade": "A",
                    "term": "2022-Fall"
                  }
                ],
                "relevant_skills": [
                  "Medication Administration",
                  "Nursing Process",
                  "Patient Assessment"
                ]
              },
              {
                "uuid": "164f8709-a092-5466-bc45-be1f526174f2",
                "display_number": 4,
                "primary_focus": "Nursing",
                "courses_completed": 3,
                "gpa": 3.75,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "NURS 238",
                    "name": "Nursing Skills Practicum II",
                    "grade": "B",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "NURS 220",
                    "name": "Nursing Fundamentals",
                    "grade": "A",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "NURS 146",
                    "name": "Health Assessment",
                    "grade": "B",
                    "term": "2023-Fall"
                  }
                ],
                "relevant_skills": [
                  "Medication Administration",
                  "Nursing Process",
                  "Patient Assessment"
                ]
              },
              {
                "uuid": "ce6b127a-7434-57de-bff9-6dc345e4a71d",
                "display_number": 5,
                "primary_focus": "Nursing",
                "courses_completed": 5,
                "gpa": 3.71,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "NURS 248",
                    "name": "Advanced Medical-Surgical Nursing II Preceptorship",
                    "grade": "A",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "NURS 242",
                    "name": "Intermediate Medical-Surgical Nursing II",
                    "grade": "A",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "NURS 238",
                    "name": "Nursing Skills Practicum II",
                    "grade": "A",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "NURS 222",
                    "name": "Medical Surgical Nursing - Older Adult",
                    "grade": "A",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "NURS 144",
                    "name": "Dosage Calculations",
                    "grade": "B",
                    "term": "2025-Spring"
                  }
                ],
                "relevant_skills": [
                  "Medication Administration",
                  "Nursing Process",
                  "Patient Assessment"
                ]
              },
              {
                "uuid": "5d7a2d3a-6051-59e0-8082-c25599faf1a4",
                "display_number": 6,
                "primary_focus": "Nursing",
                "courses_completed": 6,
                "gpa": 3.71,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "NURS 248",
                    "name": "Advanced Medical-Surgical Nursing II Preceptorship",
                    "grade": "B",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "NURS 244",
                    "name": "Nursing Skills Practicum III",
                    "grade": "A",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "NURS 242",
                    "name": "Intermediate Medical-Surgical Nursing II",
                    "grade": "A",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "NURS 234",
                    "name": "Pediatric Nursing",
                    "grade": "A",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "NURS 232",
                    "name": "Obstetrical Patients and the Newborn",
                    "grade": "B",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "NURS 222",
                    "name": "Medical Surgical Nursing - Older Adult",
                    "grade": "A",
                    "term": "2022-Winter"
                  }
                ],
                "relevant_skills": [
                  "Medication Administration",
                  "Nursing Process",
                  "Patient Assessment"
                ]
              },
              {
                "uuid": "37d5407e-96d8-5690-8766-a12d869cb0e8",
                "display_number": 7,
                "primary_focus": "Nursing",
                "courses_completed": 6,
                "gpa": 3.7,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "NURS 224",
                    "name": "Nursing Pharmacology",
                    "grade": "W",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "NURS 222",
                    "name": "Medical Surgical Nursing - Older Adult",
                    "grade": "A",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "NURS 220",
                    "name": "Nursing Fundamentals",
                    "grade": "A",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "NURS 143",
                    "name": "Introduction to Nursing",
                    "grade": "B",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "NURS 210",
                    "name": "Implications of Pathophysiology Concepts for Nurses",
                    "grade": "A",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "NURS 144",
                    "name": "Dosage Calculations",
                    "grade": "B",
                    "term": "2024-Fall"
                  }
                ],
                "relevant_skills": [
                  "Medication Administration",
                  "Nursing Process",
                  "Patient Assessment"
                ]
              },
              {
                "uuid": "dac74d2f-6b39-554d-9c3d-bcc6b112f750",
                "display_number": 8,
                "primary_focus": "Nursing",
                "courses_completed": 6,
                "gpa": 3.67,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "NURS 248",
                    "name": "Advanced Medical-Surgical Nursing II Preceptorship",
                    "grade": "B",
                    "term": "2022-Fall"
                  },
                  {
                    "code": "NURS 244",
                    "name": "Nursing Skills Practicum III",
                    "grade": "A",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "NURS 242",
                    "name": "Intermediate Medical-Surgical Nursing II",
                    "grade": "W",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "NURS 234",
                    "name": "Pediatric Nursing",
                    "grade": "A",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "NURS 220",
                    "name": "Nursing Fundamentals",
                    "grade": "A",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "NURS 143",
                    "name": "Introduction to Nursing",
                    "grade": "B",
                    "term": "2022-Fall"
                  }
                ],
                "relevant_skills": [
                  "Medication Administration",
                  "Nursing Process",
                  "Patient Assessment"
                ]
              },
              {
                "uuid": "27eee4f5-e589-5136-9e39-9e47e6d994ef",
                "display_number": 9,
                "primary_focus": "Nursing",
                "courses_completed": 3,
                "gpa": 3.67,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "NURS 248",
                    "name": "Advanced Medical-Surgical Nursing II Preceptorship",
                    "grade": "A",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "NURS 230",
                    "name": "Mental Health Nursing",
                    "grade": "B",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "NURS 226",
                    "name": "Nursing Skills Practicum I",
                    "grade": "B",
                    "term": "2023-Spring"
                  }
                ],
                "relevant_skills": [
                  "Medication Administration",
                  "Nursing Process",
                  "Patient Assessment"
                ]
              },
              {
                "uuid": "9c685575-e159-54cc-ac07-e45f397cffde",
                "display_number": 10,
                "primary_focus": "Nursing",
                "courses_completed": 1,
                "gpa": 3.67,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "NURS 226",
                    "name": "Nursing Skills Practicum I",
                    "grade": "A",
                    "term": "2025-Spring"
                  }
                ],
                "relevant_skills": [
                  "Medication Administration",
                  "Nursing Process",
                  "Patient Assessment"
                ]
              }
            ]
          }
        },
        "roadmap": "A conversation between the Nursing department chair and Kedren's clinical or workforce development team could establish site capacity and supervision structure for a first cohort. An internship of 10-16 weeks mapped to existing work experience or clinical practicum courses could serve an initial cohort of 8-12 students. Targeting a fall or spring semester launch within the next academic year is a reasonable starting point.",
        "selected_occupations": [],
        "advisory_thesis": "",
        "agenda_topics": []
      },
      "engagementType": "internship",
      "collegeId": "Compton College",
      "savedAt": "2026-04-20T00:00:00.000Z",
      "status": "saved",
      "schemaVersion": 8
    },
    {
      "id": "seed-compton-curriculum-01",
      "proposal": {
        "employer": "Monrovia Nursery",
        "sector": "Wholesale",
        "partnership_type": "Curriculum Co-Design",
        "selected_occupation": "Agricultural Technicians",
        "selected_soc_code": "19-4012",
        "core_skills": [
          "Agriculture",
          "Plant Science",
          "Equipment Operation"
        ],
        "gap_skill": "Irrigation Systems Management",
        "regions": [
          "Los Angeles",
          "Central Valley / Mother Lode"
        ],
        "opportunity": "Compton College's Biology department is well-positioned to partner with Monrovia Nursery through a curriculum co-design focused on irrigation systems management. The department already develops agriculture and plant science competencies relevant to wholesale ornamental production. Collaboration with Monrovia Nursery's production team could strengthen preparation in the irrigation skills that technicians use daily across large-scale growing operations.",
        "opportunity_evidence": [
          {
            "title": "Agricultural Technicians",
            "soc_code": "19-4012",
            "annual_wage": 50710,
            "employment": 600,
            "annual_openings": 90,
            "growth_rate": 0.006414609
          }
        ],
        "justification": {
          "curriculum_composition": "The Biology department provides the most relevant curricular foundation for this partnership, with coursework building the plant science and agriculture knowledge that agricultural technician roles require. Irrigation systems management is a practical, production-level competency at wholesale scale that can be more rigorously developed through direct collaboration with Monrovia Nursery. A co-design process could determine how drip, overhead, and micro-irrigation content fits within existing coursework or warrants dedicated treatment.",
          "curriculum_evidence": [
            {
              "department": "Biology",
              "courses": [
                {
                  "code": "BIOL 103",
                  "name": "Fundamentals of Molecular Biology",
                  "description": "This course is an introduction to molecular biology. The student will study DNA, RNA, and protein structure; protein biochemistry; protein purification and analysis; genome organization of viruses, prokaryotes and eukaryotes, DNA replication; transcription and splicing; regulation of transcription; translation; and recombinant DNA technology. The student will also explore the uses of DNA technology, such as forensics and agriculture, as well as the ethical considerations of these uses.",
                  "learning_outcomes": [],
                  "skills": [
                    "Agriculture"
                  ]
                },
                {
                  "code": "BIOL 118",
                  "name": "Marine Biology Laboratory",
                  "description": "This is an introductory marine biology laboratory course designed to complement the marine biology lecture course. The laboratory course will explore the animals and plants living in the ocean and their structure and adaptations for a marine environment. Local species will be identified and classified, and local aquariums will be visited.",
                  "learning_outcomes": [],
                  "skills": [
                    "Plant Science"
                  ]
                }
              ],
              "aligned_skills": [
                "Agriculture",
                "Plant Science"
              ]
            }
          ],
          "student_composition": "Students in the Biology department are completing coursework in agriculture and plant science aligned with the technical demands of this occupation. They represent a strong candidate pool for a co-design effort that deepens their preparation for production-scale horticultural roles.",
          "student_evidence": {
            "total_in_program": 112,
            "with_all_core_skills": 5,
            "top_students": [
              {
                "uuid": "0b2d412a-fdb9-5528-871b-1f291dba22cd",
                "display_number": 1,
                "primary_focus": "Biology",
                "courses_completed": 3,
                "gpa": 3.22,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "BIOL 103",
                    "name": "Fundamentals of Molecular Biology",
                    "grade": "A",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "BIOL 118",
                    "name": "Marine Biology Laboratory",
                    "grade": "A",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "ART 170",
                    "name": "Photography Fundamental I",
                    "grade": "A",
                    "term": "2025-Spring"
                  }
                ],
                "relevant_skills": [
                  "Agriculture",
                  "Equipment Operation",
                  "Plant Science"
                ]
              },
              {
                "uuid": "477f8dba-bdd1-5dfa-bc78-a24b9f5759fc",
                "display_number": 2,
                "primary_focus": "Biology",
                "courses_completed": 3,
                "gpa": 3.1,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "BIOL 103",
                    "name": "Fundamentals of Molecular Biology",
                    "grade": "B",
                    "term": "2022-Fall"
                  },
                  {
                    "code": "BIOL 118",
                    "name": "Marine Biology Laboratory",
                    "grade": "B",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "THEA 189",
                    "name": "Costuming for the Stage",
                    "grade": "C",
                    "term": "2025-Spring"
                  }
                ],
                "relevant_skills": [
                  "Agriculture",
                  "Equipment Operation",
                  "Plant Science"
                ]
              },
              {
                "uuid": "3c80adcb-524c-5715-900c-a11957c14dd2",
                "display_number": 3,
                "primary_focus": "Biology",
                "courses_completed": 3,
                "gpa": 3.09,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "BIOL 103",
                    "name": "Fundamentals of Molecular Biology",
                    "grade": "B",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "BIOL 118",
                    "name": "Marine Biology Laboratory",
                    "grade": "C",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "WELD 140",
                    "name": "Introduction to Gas Tungsten Arc Welding (GTAW)",
                    "grade": "A",
                    "term": "2023-Winter"
                  }
                ],
                "relevant_skills": [
                  "Agriculture",
                  "Equipment Operation",
                  "Plant Science"
                ]
              },
              {
                "uuid": "9c5fe1f5-05cd-5fb6-a942-3ebe78f6dc39",
                "display_number": 4,
                "primary_focus": "Biology",
                "courses_completed": 4,
                "gpa": 3.0,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "BIOL 103",
                    "name": "Fundamentals of Molecular Biology",
                    "grade": "A",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "BIOL 118",
                    "name": "Marine Biology Laboratory",
                    "grade": "B",
                    "term": "2022-Fall"
                  },
                  {
                    "code": "THEA 185",
                    "name": "Introduction to Stage Lighting",
                    "grade": "C",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "ASTR 128",
                    "name": "Astronomy Laboratory",
                    "grade": "F",
                    "term": "2024-Winter"
                  }
                ],
                "relevant_skills": [
                  "Agriculture",
                  "Equipment Operation",
                  "Plant Science"
                ]
              },
              {
                "uuid": "6e61e307-74bb-5d74-a56e-feb0b1f1cee5",
                "display_number": 5,
                "primary_focus": "Biology",
                "courses_completed": 4,
                "gpa": 2.77,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "BIOL 103",
                    "name": "Fundamentals of Molecular Biology",
                    "grade": "B",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "BIOL 118",
                    "name": "Marine Biology Laboratory",
                    "grade": "B",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "THEA 185",
                    "name": "Introduction to Stage Lighting",
                    "grade": "A",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "MTT 146",
                    "name": "Basic Machine Tool Operation",
                    "grade": "B",
                    "term": "2023-Winter"
                  }
                ],
                "relevant_skills": [
                  "Agriculture",
                  "Equipment Operation",
                  "Plant Science"
                ]
              },
              {
                "uuid": "084269ba-d044-5f2d-85b2-b196116043f2",
                "display_number": 6,
                "primary_focus": "Biology",
                "courses_completed": 2,
                "gpa": 3.67,
                "matching_skills": 2,
                "enrollments": [
                  {
                    "code": "BIOL 103",
                    "name": "Fundamentals of Molecular Biology",
                    "grade": "A",
                    "term": "2022-Fall"
                  },
                  {
                    "code": "BIOL 118",
                    "name": "Marine Biology Laboratory",
                    "grade": "A",
                    "term": "2023-Spring"
                  }
                ],
                "relevant_skills": [
                  "Agriculture",
                  "Plant Science"
                ]
              },
              {
                "uuid": "5c760b48-7617-5997-a7fe-3b41e34e99f2",
                "display_number": 7,
                "primary_focus": "Biology",
                "courses_completed": 2,
                "gpa": 3.5,
                "matching_skills": 2,
                "enrollments": [
                  {
                    "code": "BIOL 103",
                    "name": "Fundamentals of Molecular Biology",
                    "grade": "A",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "BIOL 118",
                    "name": "Marine Biology Laboratory",
                    "grade": "A",
                    "term": "2023-Winter"
                  }
                ],
                "relevant_skills": [
                  "Agriculture",
                  "Plant Science"
                ]
              },
              {
                "uuid": "d118b472-38d9-54d0-905e-448472a92f68",
                "display_number": 8,
                "primary_focus": "Biology",
                "courses_completed": 2,
                "gpa": 3.5,
                "matching_skills": 2,
                "enrollments": [
                  {
                    "code": "BIOL 103",
                    "name": "Fundamentals of Molecular Biology",
                    "grade": "A",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "BIOL 118",
                    "name": "Marine Biology Laboratory",
                    "grade": "B",
                    "term": "2025-Spring"
                  }
                ],
                "relevant_skills": [
                  "Agriculture",
                  "Plant Science"
                ]
              },
              {
                "uuid": "9c71cb2d-3745-5dc5-b673-f76aed389460",
                "display_number": 9,
                "primary_focus": "Biology",
                "courses_completed": 2,
                "gpa": 3.5,
                "matching_skills": 2,
                "enrollments": [
                  {
                    "code": "BIOL 103",
                    "name": "Fundamentals of Molecular Biology",
                    "grade": "A",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "BIOL 118",
                    "name": "Marine Biology Laboratory",
                    "grade": "A",
                    "term": "2025-Spring"
                  }
                ],
                "relevant_skills": [
                  "Agriculture",
                  "Plant Science"
                ]
              },
              {
                "uuid": "8d34fcf5-3bfc-5cdd-8aee-7ba725e2d0bd",
                "display_number": 10,
                "primary_focus": "Biology",
                "courses_completed": 3,
                "gpa": 3.43,
                "matching_skills": 2,
                "enrollments": [
                  {
                    "code": "BIOL 103",
                    "name": "Fundamentals of Molecular Biology",
                    "grade": "B",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "BIOL 118",
                    "name": "Marine Biology Laboratory",
                    "grade": "B",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "ACRP 146",
                    "name": "Intermediate Automotive Collision Repair II",
                    "grade": "W",
                    "term": "2023-Fall"
                  }
                ],
                "relevant_skills": [
                  "Agriculture",
                  "Plant Science"
                ]
              }
            ]
          }
        },
        "roadmap": "A working group between the Biology department and Monrovia Nursery's production leadership could evaluate how irrigation systems management can be more rigorously developed within the existing curriculum. One potential starting point is a collaborative review of current course content to identify where hands-on irrigation scheduling and maintenance could be introduced or expanded. Revised content could be piloted within the next catalog cycle.",
        "selected_occupations": [],
        "advisory_thesis": "",
        "agenda_topics": []
      },
      "engagementType": "curriculum_codesign",
      "collegeId": "Compton College",
      "savedAt": "2026-04-20T00:00:00.000Z",
      "status": "saved",
      "schemaVersion": 8
    }
  ],
  "San Diego City College": [
    {
      "id": "seed-sandiegocity-advisory-01",
      "proposal": {
        "employer": "Raytheon",
        "sector": "Manufacturing",
        "partnership_type": "Advisory Board",
        "selected_occupation": "Aerospace Engineers",
        "selected_soc_code": "17-2011",
        "core_skills": [
          "Design",
          "Materials Science",
          "Electrical Systems",
          "Circuit Analysis",
          "Troubleshooting"
        ],
        "gap_skill": "",
        "regions": [
          "Orange County",
          "San Diego / Imperial",
          "South Central Coast"
        ],
        "opportunity": "Raytheon's defense manufacturing operations make it a compelling advisory board partner for San Diego City College's technical programs, providing direct industry perspective on the precision fabrication and electrical systems work that define its production environment. The company's San Diego regional presence spans roles from avionics technicians to aerospace engineers, with electrical engineering positions growing at 6.4% annually and commanding median wages above $128,000. An advisory board requires no grant funding and would give the college a sustained channel into one of the region's most technically demanding manufacturing employers.",
        "opportunity_evidence": [
          {
            "title": "Avionics Technicians",
            "soc_code": "49-2091",
            "annual_wage": 90250,
            "employment": 950,
            "annual_openings": 80,
            "growth_rate": 0.010887111
          },
          {
            "title": "Electrical Engineers",
            "soc_code": "17-2071",
            "annual_wage": 128360,
            "employment": 2320,
            "annual_openings": 160,
            "growth_rate": 0.063584282
          },
          {
            "title": "Aerospace Engineers",
            "soc_code": "17-2011",
            "annual_wage": 132410,
            "employment": 820,
            "annual_openings": 60,
            "growth_rate": 0.080576205
          }
        ],
        "justification": {
          "curriculum_composition": "The Electronics Technology and Electromechanical Technology departments provide the closest match to Raytheon's production workforce, developing circuit analysis and troubleshooting skills that are central to avionics and electrical systems roles. The Electronics Technology department's depth across five courses building troubleshooting competency reflects the kind of applied technical preparation Raytheon's production floor demands. The Engineering Technology department's design coursework connects to the engineering and drafting functions that support Raytheon's fabrication pipeline.",
          "curriculum_evidence": [
            {
              "department": "Electronics Technology",
              "courses": [
                {
                  "code": "ELDT 124",
                  "name": "Basic DC Electronics",
                  "description": "This course covers the fundamental principles of DC electronics. Topics include basic electrical concepts, Ohm's Law, Kirchhoff's Laws, series and parallel circuits, voltage dividers, and basic circuit analysis techniques. Emphasis is placed on understanding DC circuit behavior and applying fundamental laws to solve circuit problems.",
                  "learning_outcomes": [],
                  "skills": [
                    "Circuit Analysis"
                  ]
                },
                {
                  "code": "ELDT 124L",
                  "name": "Basic DC Laboratory",
                  "description": "This laboratory course provides hands-on experience with basic DC circuits and components. Students build and test DC circuits, measure voltage and current, and verify electrical principles. Emphasis is placed on applying theoretical knowledge of DC electronics in practical laboratory exercises.",
                  "learning_outcomes": [],
                  "skills": [
                    "Circuit Analysis"
                  ]
                },
                {
                  "code": "ELDT 125",
                  "name": "AC Circuit Analysis",
                  "description": "This course covers the analysis of AC circuits. Topics include impedance, reactance, phasors, series and parallel AC circuits, resonance, and power calculations in AC circuits. Emphasis is placed on understanding AC circuit behavior and applying analytical techniques to solve AC circuit problems.",
                  "learning_outcomes": [],
                  "skills": [
                    "Circuit Analysis"
                  ]
                },
                {
                  "code": "ELDT 125L",
                  "name": "DC/AC Circuit Analysis Laboratory with Pspice",
                  "description": "This laboratory course provides hands-on experience with DC and AC circuit analysis using PSpice simulation software. Students analyze circuit behavior, verify theoretical calculations, and troubleshoot circuit designs. Emphasis is placed on developing proficiency in using simulation tools for circuit analysis.",
                  "learning_outcomes": [],
                  "skills": [
                    "Circuit Analysis"
                  ]
                },
                {
                  "code": "ELDT 228L",
                  "name": "Communication Circuits and Certification Laboratory",
                  "description": "This laboratory course provides hands-on experience with communication circuits and prepares students for industry certification. Students design, build, and test communication circuits, and practice troubleshooting techniques. Emphasis is placed on applying theoretical knowledge and developing practical skills for certification exams.",
                  "learning_outcomes": [],
                  "skills": [
                    "Troubleshooting"
                  ]
                }
              ],
              "aligned_skills": [
                "Circuit Analysis",
                "Troubleshooting"
              ]
            },
            {
              "department": "Electromechanical Technology",
              "courses": [
                {
                  "code": "ELDT 143",
                  "name": "Semiconductor Devices",
                  "description": "This course provides a comprehensive study of semiconductor devices, including diodes, transistors, and integrated circuits. Topics include device physics, characteristics, and applications in electronic circuits.",
                  "learning_outcomes": [
                    "Demonstrate the ability to prepare reports that include text, tables, and spreadsheets using productivity software on a computer.",
                    "Identify standard electronic components including resistors, capacitors, inductors, diodes, bipolar transistors, field effect transistors, and integrated circuits.",
                    "Analyze and explain basic electronic theory including Ohm's Law, the power formula, and calculation of voltage gain and power gain.",
                    "Demonstrate the proper use of basic electronic test instrumentation including an oscilloscope, a digital volt-ohm meter, a signal generator, and a dual power supply."
                  ],
                  "skills": [
                    "Circuit Analysis"
                  ]
                }
              ],
              "aligned_skills": [
                "Circuit Analysis"
              ]
            },
            {
              "department": "Engineering Technology",
              "courses": [
                {
                  "code": "ENGN 130",
                  "name": "Introduction to Design 1,2 (SDUSD)",
                  "description": "",
                  "learning_outcomes": [],
                  "skills": [
                    "Design"
                  ]
                }
              ],
              "aligned_skills": [
                "Design"
              ]
            }
          ],
          "student_composition": "Students across these three departments are building technical competencies in circuit analysis, design, and troubleshooting that align directly with Raytheon's identity-defining occupations. The aggregate pipeline spans electrical, mechanical, and engineering technology pathways, covering the range of roles from avionics technician to aerospace engineer that Raytheon fills in the San Diego region.",
          "student_evidence": {
            "total_in_program": 78,
            "with_all_core_skills": 0,
            "top_students": [
              {
                "uuid": "b429df97-7e86-54a9-ada8-39bb58aec399",
                "display_number": 1,
                "primary_focus": "Electronics Technology",
                "courses_completed": 9,
                "gpa": 3.27,
                "matching_skills": 4,
                "enrollments": [
                  {
                    "code": "DSGN 216B",
                    "name": "Design Studio II",
                    "grade": "B",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "TROL 302",
                    "name": "San Diego Trolley Light Rail Vehicle II",
                    "grade": "W",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "SDGE 312",
                    "name": "Electric Lineman IIB",
                    "grade": "A",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "SDGE 304",
                    "name": "Electric Lineman IB",
                    "grade": "B",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "SDGE 302",
                    "name": "Electric Lineman IA",
                    "grade": "C",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "ELDT 125L",
                    "name": "DC/AC Circuit Analysis Laboratory with Pspice",
                    "grade": "B",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "ELDT 143",
                    "name": "Semiconductor Devices",
                    "grade": "A",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "ELDT 124L",
                    "name": "Basic DC Laboratory",
                    "grade": "B",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "ELDT 228L",
                    "name": "Communication Circuits and Certification Laboratory",
                    "grade": "A",
                    "term": "2023-Fall"
                  }
                ],
                "relevant_skills": [
                  "Circuit Analysis",
                  "Design",
                  "Electrical Systems",
                  "Troubleshooting"
                ]
              },
              {
                "uuid": "84f83e7b-421f-5ef0-ba22-227ab061efb5",
                "display_number": 2,
                "primary_focus": "Electronics Technology",
                "courses_completed": 6,
                "gpa": 3.25,
                "matching_skills": 4,
                "enrollments": [
                  {
                    "code": "DSGN 210",
                    "name": "Branding and Packaging",
                    "grade": "A",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "TROL 302",
                    "name": "San Diego Trolley Light Rail Vehicle II",
                    "grade": "A",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "SDGE 310",
                    "name": "Electric Lineman IIA",
                    "grade": "A",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "SDGE 91",
                    "name": "Electric Lineman IB",
                    "grade": "A",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "ELDT 125L",
                    "name": "DC/AC Circuit Analysis Laboratory with Pspice",
                    "grade": "A",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "INWT 100",
                    "name": "Computing Fundamentals (A+)",
                    "grade": "A",
                    "term": "2024-Spring"
                  }
                ],
                "relevant_skills": [
                  "Circuit Analysis",
                  "Design",
                  "Electrical Systems",
                  "Troubleshooting"
                ]
              },
              {
                "uuid": "ad7d5934-33d1-5120-8c24-58ff78373ead",
                "display_number": 3,
                "primary_focus": "Electronics Technology",
                "courses_completed": 15,
                "gpa": 3.18,
                "matching_skills": 4,
                "enrollments": [
                  {
                    "code": "ARTF 202B",
                    "name": "Public Art II",
                    "grade": "A",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "DSGN 216B",
                    "name": "Design Studio II",
                    "grade": "A",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "SDGE 322",
                    "name": "Electric Lineman IIIB",
                    "grade": "A",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "SDGE 320",
                    "name": "Electric Lineman IIIA",
                    "grade": "C",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "SDGE 312",
                    "name": "Electric Lineman IIB",
                    "grade": "B",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "SDGE 304",
                    "name": "Electric Lineman IB",
                    "grade": "F",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "SDGE 302",
                    "name": "Electric Lineman IA",
                    "grade": "W",
                    "term": "2022-Fall"
                  },
                  {
                    "code": "SDGE 95",
                    "name": "Electric Lineman IIIB",
                    "grade": "A",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "SDGE 94",
                    "name": "Electric Lineman IIIA",
                    "grade": "B",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "SDGE 93",
                    "name": "Electric Lineman IIB",
                    "grade": "C",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "SDGE 92",
                    "name": "Electric Lineman IIA",
                    "grade": "A",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "SDGE 91",
                    "name": "Electric Lineman IB",
                    "grade": "A",
                    "term": "2022-Fall"
                  },
                  {
                    "code": "SDGE 90",
                    "name": "Electric Lineman IA",
                    "grade": "B",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "ELDT 143",
                    "name": "Semiconductor Devices",
                    "grade": "A",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "TROL 304",
                    "name": "San Diego Trolley Light Rail Vehicle IV",
                    "grade": "A",
                    "term": "2022-Fall"
                  }
                ],
                "relevant_skills": [
                  "Circuit Analysis",
                  "Design",
                  "Electrical Systems",
                  "Troubleshooting"
                ]
              },
              {
                "uuid": "be98c508-3be2-5bb5-ba6b-18ce291bb3d0",
                "display_number": 4,
                "primary_focus": "Electronics Technology",
                "courses_completed": 10,
                "gpa": 3.09,
                "matching_skills": 4,
                "enrollments": [
                  {
                    "code": "ARTF 208A",
                    "name": "Ceramic Production I",
                    "grade": "C",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "TROL 302",
                    "name": "San Diego Trolley Light Rail Vehicle II",
                    "grade": "C",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "SDGE 312",
                    "name": "Electric Lineman IIB",
                    "grade": "B",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "SDGE 302",
                    "name": "Electric Lineman IA",
                    "grade": "A",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "SDGE 94",
                    "name": "Electric Lineman IIIA",
                    "grade": "B",
                    "term": "2022-Fall"
                  },
                  {
                    "code": "SDGE 93",
                    "name": "Electric Lineman IIB",
                    "grade": "A",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "SDGE 92",
                    "name": "Electric Lineman IIA",
                    "grade": "B",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "SDGE 90",
                    "name": "Electric Lineman IA",
                    "grade": "B",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "ELDT 125L",
                    "name": "DC/AC Circuit Analysis Laboratory with Pspice",
                    "grade": "C",
                    "term": "2022-Fall"
                  },
                  {
                    "code": "ELDT 124L",
                    "name": "Basic DC Laboratory",
                    "grade": "B",
                    "term": "2023-Winter"
                  }
                ],
                "relevant_skills": [
                  "Circuit Analysis",
                  "Design",
                  "Electrical Systems",
                  "Troubleshooting"
                ]
              },
              {
                "uuid": "67ca50a3-0677-524c-a4b4-c9fa7a1d1267",
                "display_number": 5,
                "primary_focus": "Electronics Technology",
                "courses_completed": 16,
                "gpa": 3.05,
                "matching_skills": 4,
                "enrollments": [
                  {
                    "code": "DSGN 216A",
                    "name": "Design Studio I",
                    "grade": "A",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "TROL 302",
                    "name": "San Diego Trolley Light Rail Vehicle II",
                    "grade": "B",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "SDGE 312",
                    "name": "Electric Lineman IIB",
                    "grade": "B",
                    "term": "2022-Fall"
                  },
                  {
                    "code": "SDGE 310",
                    "name": "Electric Lineman IIA",
                    "grade": "F",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "SDGE 302",
                    "name": "Electric Lineman IA",
                    "grade": "A",
                    "term": "2022-Fall"
                  },
                  {
                    "code": "SDGE 95",
                    "name": "Electric Lineman IIIB",
                    "grade": "C",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "SDGE 94",
                    "name": "Electric Lineman IIIA",
                    "grade": "C",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "SDGE 93",
                    "name": "Electric Lineman IIB",
                    "grade": "A",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "SDGE 92",
                    "name": "Electric Lineman IIA",
                    "grade": "W",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "SDGE 91",
                    "name": "Electric Lineman IB",
                    "grade": "A",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "SDGE 90",
                    "name": "Electric Lineman IA",
                    "grade": "A",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "ELCT 111",
                    "name": "Electrical Theory I",
                    "grade": "A",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "ELDT 143",
                    "name": "Semiconductor Devices",
                    "grade": "A",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "TROL 303",
                    "name": "San Diego Trolley Light Rail Vehicle III",
                    "grade": "B",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "TROL 301",
                    "name": "San Diego Trolley Light Rail Vehicle I",
                    "grade": "B",
                    "term": "2022-Fall"
                  },
                  {
                    "code": "INWT 111",
                    "name": "Windows Desktop Administration",
                    "grade": "A",
                    "term": "2024-Winter"
                  }
                ],
                "relevant_skills": [
                  "Circuit Analysis",
                  "Design",
                  "Electrical Systems",
                  "Troubleshooting"
                ]
              },
              {
                "uuid": "8d1a3750-9e41-5a31-911c-f49b65878760",
                "display_number": 6,
                "primary_focus": "Electronics Technology",
                "courses_completed": 14,
                "gpa": 2.71,
                "matching_skills": 4,
                "enrollments": [
                  {
                    "code": "DANC 271A",
                    "name": "Stage Costuming for Dance",
                    "grade": "A",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "ARTF 111",
                    "name": "Art History: Renaissance to Modern",
                    "grade": "B",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "TROL 302",
                    "name": "San Diego Trolley Light Rail Vehicle II",
                    "grade": "A",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "SDGE 312",
                    "name": "Electric Lineman IIB",
                    "grade": "B",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "SDGE 310",
                    "name": "Electric Lineman IIA",
                    "grade": "W",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "SDGE 95",
                    "name": "Electric Lineman IIIB",
                    "grade": "W",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "SDGE 94",
                    "name": "Electric Lineman IIIA",
                    "grade": "C",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "SDGE 93",
                    "name": "Electric Lineman IIB",
                    "grade": "F",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "SDGE 90",
                    "name": "Electric Lineman IA",
                    "grade": "A",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "ELDT 125",
                    "name": "AC Circuit Analysis",
                    "grade": "B",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "ELDT 143",
                    "name": "Semiconductor Devices",
                    "grade": "B",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "ELDT 124L",
                    "name": "Basic DC Laboratory",
                    "grade": "A",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "TROL 304",
                    "name": "San Diego Trolley Light Rail Vehicle IV",
                    "grade": "A",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "ELDT 228L",
                    "name": "Communication Circuits and Certification Laboratory",
                    "grade": "W",
                    "term": "2022-Fall"
                  }
                ],
                "relevant_skills": [
                  "Circuit Analysis",
                  "Design",
                  "Electrical Systems",
                  "Troubleshooting"
                ]
              },
              {
                "uuid": "06a6cf12-c587-5366-9bf8-524be6720b70",
                "display_number": 7,
                "primary_focus": "Electronics Technology",
                "courses_completed": 5,
                "gpa": 2.5,
                "matching_skills": 4,
                "enrollments": [
                  {
                    "code": "DSGN 216C",
                    "name": "Design Studio III",
                    "grade": "C",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "SDGE 93",
                    "name": "Electric Lineman IIB",
                    "grade": "C",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "ELDT 124",
                    "name": "Basic DC Electronics",
                    "grade": "A",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "TROL 303",
                    "name": "San Diego Trolley Light Rail Vehicle III",
                    "grade": "C",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "TROL 301",
                    "name": "San Diego Trolley Light Rail Vehicle I",
                    "grade": "A",
                    "term": "2024-Winter"
                  }
                ],
                "relevant_skills": [
                  "Circuit Analysis",
                  "Design",
                  "Electrical Systems",
                  "Troubleshooting"
                ]
              },
              {
                "uuid": "bec40a80-0f3a-5f19-939d-5e2f253e0984",
                "display_number": 8,
                "primary_focus": "Electronics Technology",
                "courses_completed": 2,
                "gpa": 4.0,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "ARTF 210C",
                    "name": "Life Drawing III",
                    "grade": "A",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "TROL 302",
                    "name": "San Diego Trolley Light Rail Vehicle II",
                    "grade": "A",
                    "term": "2025-Spring"
                  }
                ],
                "relevant_skills": [
                  "Design",
                  "Electrical Systems",
                  "Troubleshooting"
                ]
              },
              {
                "uuid": "9f243027-49de-503b-8bbe-5a9766f40e99",
                "display_number": 9,
                "primary_focus": "Electronics Technology",
                "courses_completed": 4,
                "gpa": 3.75,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "SDGE 320",
                    "name": "Electric Lineman IIIA",
                    "grade": "A",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "ELDT 125L",
                    "name": "DC/AC Circuit Analysis Laboratory with Pspice",
                    "grade": "B",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "ELDT 125",
                    "name": "AC Circuit Analysis",
                    "grade": "A",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "TROL 303",
                    "name": "San Diego Trolley Light Rail Vehicle III",
                    "grade": "A",
                    "term": "2025-Spring"
                  }
                ],
                "relevant_skills": [
                  "Circuit Analysis",
                  "Electrical Systems",
                  "Troubleshooting"
                ]
              },
              {
                "uuid": "96b25ecf-e687-5be5-be35-2783deeb64fa",
                "display_number": 10,
                "primary_focus": "Electronics Technology",
                "courses_completed": 6,
                "gpa": 3.71,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "SDGE 322",
                    "name": "Electric Lineman IIIB",
                    "grade": "A",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "SDGE 320",
                    "name": "Electric Lineman IIIA",
                    "grade": "W",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "SDGE 312",
                    "name": "Electric Lineman IIB",
                    "grade": "A",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "SDGE 310",
                    "name": "Electric Lineman IIA",
                    "grade": "B",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "ELDT 124L",
                    "name": "Basic DC Laboratory",
                    "grade": "A",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "TROL 304",
                    "name": "San Diego Trolley Light Rail Vehicle IV",
                    "grade": "A",
                    "term": "2023-Fall"
                  }
                ],
                "relevant_skills": [
                  "Circuit Analysis",
                  "Electrical Systems",
                  "Troubleshooting"
                ]
              }
            ]
          }
        },
        "roadmap": "A quarterly advisory board with Raytheon's San Diego technical leadership could give the Electronics Technology, Electromechanical Technology, and Engineering Technology departments sustained access to defense manufacturing perspective. Potential starting points for the inaugural meeting include the tolerances and fabrication standards new hires encounter first on the production floor, which avionics troubleshooting scenarios require judgment beyond standard diagnostic procedure, and how Raytheon evaluates whether entry-level hires can apply electrical schematics in a defense manufacturing context.",
        "selected_occupations": [
          "Aerospace Engineers",
          "Electrical Engineers",
          "Avionics Technicians"
        ],
        "advisory_thesis": "Raytheon operates at the intersection of precision manufacturing and cutting-edge defense technology, producing advanced aerospace and weapons systems that require technicians and engineers trained to exacting standards in electrical systems, mechanical fabrication, and avionics. For a college preparing students for high-skilled manufacturing and engineering careers, Raytheon's perspective reflects the technical depth and applied problem-solving demanded by defense-sector production environments.",
        "agenda_topics": [
          {
            "topic": "What tolerances and fabrication standards do Raytheon technicians encounter first on the production floor?",
            "rationale": "Raytheon's production environment could inform how Electromechanical Technology and Electronics Technology sequence hands-on precision work earlier or more explicitly in their programs."
          },
          {
            "topic": "Which avionics troubleshooting scenarios most often require judgment calls that go beyond following a diagnostic procedure?",
            "rationale": "Raytheon's operational experience could strengthen how Electronics Technology designs scenario-based troubleshooting instruction that builds applied reasoning alongside technical procedure."
          },
          {
            "topic": "How does Raytheon assess whether an entry-level hire can read and apply electrical schematics in a defense manufacturing context?",
            "rationale": "Raytheon's assessment practices could inform how Engineering Technology and Electronics Technology calibrate the complexity and application context of circuit analysis coursework."
          }
        ]
      },
      "engagementType": "advisory_board",
      "collegeId": "San Diego City College",
      "savedAt": "2026-04-20T00:00:00.000Z",
      "status": "saved",
      "schemaVersion": 8
    },
    {
      "id": "seed-sandiegocity-internship-01",
      "proposal": {
        "employer": "Thermo Fisher Scientific",
        "sector": "Wholesale",
        "partnership_type": "Internship Pipeline",
        "selected_occupation": "Software Developers",
        "selected_soc_code": "15-1252",
        "core_skills": [
          "Programming",
          "Software Development",
          "Object-Oriented Programming"
        ],
        "gap_skill": "",
        "regions": [
          "San Diego / Imperial",
          "Los Angeles"
        ],
        "opportunity": "Thermo Fisher Scientific is a compelling internship partner for San Diego City College's software development programs, given its San Diego presence and the regional demand for software developers. The occupation generates 1,340 annual openings in California at a median wage of $158,680, with 4.5% projected growth. A structured 8-16 week internship could place students in the software engineering workflows Thermo Fisher uses to support its scientific instrumentation and diagnostics platforms.",
        "opportunity_evidence": [
          {
            "title": "Software Developers",
            "soc_code": "15-1252",
            "annual_wage": 158680,
            "employment": 21890,
            "annual_openings": 1340,
            "growth_rate": 0.044858829
          }
        ],
        "justification": {
          "curriculum_composition": "The Computer Information Systems department provides direct preparation for an internship at Thermo Fisher, building object-oriented programming, programming, and software development across nine courses. The Computer Science department reinforces the same core competencies through a more concentrated sequence. Together, they produce students with the technical foundation Thermo Fisher's software developer roles require.",
          "curriculum_evidence": [
            {
              "department": "Computer Information Systems",
              "courses": [
                {
                  "code": "CISC 179",
                  "name": "Introduction to Python Programming",
                  "description": "This course provides an introduction to programming using the Python language. Students learn fundamental programming concepts such as variables, data types, control structures, functions, and object-oriented programming. Emphasis is placed on developing problem-solving skills and writing efficient, readable Python code.",
                  "learning_outcomes": [],
                  "skills": [
                    "Programming",
                    "Software Development"
                  ]
                },
                {
                  "code": "CISC 187",
                  "name": "Data Structures in C++",
                  "description": "This course covers fundamental data structures and their implementation in C++. Topics include arrays, linked lists, stacks, queues, trees, and graphs.",
                  "learning_outcomes": [
                    "Effectively design and implement programming constructs, including functions, control structures, arrays/lists, classes, and objects for a given programming problem; and",
                    "Effectively implement the appropriate data structures using the principles and techniques of object-oriented programming for a given programming problem."
                  ],
                  "skills": [
                    "Object-Oriented Programming",
                    "Programming"
                  ]
                },
                {
                  "code": "CISC 191",
                  "name": "Intermediate Java Programming",
                  "description": "",
                  "learning_outcomes": [],
                  "skills": [
                    "Programming"
                  ]
                },
                {
                  "code": "CISC 192",
                  "name": "C/C++ Programming",
                  "description": "This course provides a comprehensive introduction to programming in C and C++. Topics include variables, data types, control structures, functions, pointers, and object-oriented programming concepts.",
                  "learning_outcomes": [
                    "Effectively design and implement programming constructs, including functions, control structures, arrays/lists, classes, and objects for a given programming problem; and",
                    "Effectively implement the appropriate data structures using the principles and techniques of object-oriented programming for a given programming problem."
                  ],
                  "skills": [
                    "Object-Oriented Programming",
                    "Programming"
                  ]
                },
                {
                  "code": "CISC 193",
                  "name": "Microsoft C# Software Engineering 1",
                  "description": "",
                  "learning_outcomes": [],
                  "skills": [
                    "Programming",
                    "Software Development"
                  ]
                },
                {
                  "code": "CISC 201",
                  "name": "Advanced C++ Programming",
                  "description": "This course covers advanced topics in C++ programming, including templates, exception handling, the Standard Template Library (STL), and design patterns.",
                  "learning_outcomes": [
                    "Effectively design and implement programming constructs, including functions, control structures, arrays/lists, classes, and objects for a given programming problem; and",
                    "Effectively implement the appropriate data structures using the principles and techniques of object-oriented programming for a given programming problem."
                  ],
                  "skills": [
                    "Object-Oriented Programming",
                    "Programming",
                    "Software Development"
                  ]
                },
                {
                  "code": "CISC 205",
                  "name": "Object Oriented Programming using C++",
                  "description": "This course focuses on object-oriented programming (OOP) concepts and their application in C++. Topics include classes, objects, inheritance, polymorphism, and design patterns.",
                  "learning_outcomes": [
                    "Effectively design and implement programming constructs, including functions, control structures, arrays/lists, classes, and objects for a given programming problem; and",
                    "Effectively implement the appropriate data structures using the principles and techniques of object-oriented programming for a given programming problem."
                  ],
                  "skills": [
                    "Object-Oriented Programming",
                    "Programming"
                  ]
                },
                {
                  "code": "CISC 220",
                  "name": "Fundamentals of Computer Game Programming",
                  "description": "This course introduces the fundamental concepts of computer game programming, including game design principles, programming languages (e.g., C++), game engines, and development tools. Emphasis is placed on creating basic game mechanics and logic.",
                  "learning_outcomes": [],
                  "skills": [
                    "Programming"
                  ]
                },
                {
                  "code": "CISC 221",
                  "name": "Intermediate Computer Game Programming",
                  "description": "This course builds upon the fundamentals of game programming, covering more advanced topics such as artificial intelligence, physics simulation, graphics programming, and network programming. Emphasis is placed on developing complex game systems.",
                  "learning_outcomes": [],
                  "skills": [
                    "Programming"
                  ]
                }
              ],
              "aligned_skills": [
                "Object-Oriented Programming",
                "Programming",
                "Software Development"
              ]
            },
            {
              "department": "Computer Science",
              "courses": [
                {
                  "code": "CISC 183",
                  "name": "Web Development with Ruby on Rails",
                  "description": "Attention is placed on the theory and practice of computer programming emphasizing business and computer applications. Students receive hands-on experience in the fundamentals of designing and developing dynamic website using the Ruby on Rails programming language.",
                  "learning_outcomes": [
                    "Analyze a complex computing problem and to apply principles of computing and other relevant disciplines to identify solutions.",
                    "Design, implement, and evaluate a computing-based solution to meet a given set of computing requirements in the context of the program's discipline.",
                    "Communicate effectively in a variety of professional contexts.",
                    "Recognize professional responsibilities and make informed judgments in computing practice, taking into account legal, ethical, diversity, equity, inclusion, and accessibility principles consistent with the mission of the institution.",
                    "Function effectively as a member or leader of a team engaged in activities appropriate to the program's discipline.",
                    "Apply security principles and practices to maintain operations in the presence of risks and threats."
                  ],
                  "skills": [
                    "Programming",
                    "Software Development"
                  ]
                },
                {
                  "code": "CISC 186",
                  "name": "Visual Basic Programming",
                  "description": "Attention is placed on the theory and practice of computer programming emphasizing business and computer applications. Students receive hands-on experience in the fundamentals of designing and developing dynamic website using the Ruby on Rails programming language.",
                  "learning_outcomes": [
                    "Analyze a complex computing problem and to apply principles of computing and other relevant disciplines to identify solutions.",
                    "Design, implement, and evaluate a computing-based solution to meet a given set of computing requirements in the context of the program's discipline.",
                    "Communicate effectively in a variety of professional contexts.",
                    "Recognize professional responsibilities and make informed judgments in computing practice, taking into account legal, ethical, diversity, equity, inclusion, and accessibility principles consistent with the mission of the institution.",
                    "Function effectively as a member or leader of a team engaged in activities appropriate to the program's discipline.",
                    "Apply security principles and practices to maintain operations in the presence of risks and threats."
                  ],
                  "skills": [
                    "Programming",
                    "Software Development"
                  ]
                },
                {
                  "code": "CISC 190",
                  "name": "Java Programming",
                  "description": "Attention is placed on the theory and practice of computer programming emphasizing business and computer applications. Students receive hands-on experience in the fundamentals of designing and developing dynamic website using the Ruby on Rails programming language.",
                  "learning_outcomes": [
                    "Analyze a complex computing problem and to apply principles of computing and other relevant disciplines to identify solutions.",
                    "Design, implement, and evaluate a computing-based solution to meet a given set of computing requirements in the context of the program's discipline.",
                    "Communicate effectively in a variety of professional contexts.",
                    "Recognize professional responsibilities and make informed judgments in computing practice, taking into account legal, ethical, diversity, equity, inclusion, and accessibility principles consistent with the mission of the institution.",
                    "Function effectively as a member or leader of a team engaged in activities appropriate to the program's discipline.",
                    "Apply security principles and practices to maintain operations in the presence of risks and threats."
                  ],
                  "skills": [
                    "Object-Oriented Programming",
                    "Programming",
                    "Software Development"
                  ]
                }
              ],
              "aligned_skills": [
                "Object-Oriented Programming",
                "Programming",
                "Software Development"
              ]
            },
            {
              "department": "Mathematics",
              "courses": [
                {
                  "code": "MATH 107",
                  "name": "Introduction to Scientific Programming",
                  "description": "This course introduces the fundamentals of scientific programming using a high-level language (e.g., Python). Emphasis is placed on developing algorithms, writing code, and using programming for data analysis and visualization.",
                  "learning_outcomes": [],
                  "skills": [
                    "Programming"
                  ]
                },
                {
                  "code": "MATH 107L",
                  "name": "Introduction to Scientific Programming Lab",
                  "description": "This laboratory course complements Introduction to Scientific Programming (MATH 107) by providing hands-on practice in writing and debugging code, implementing algorithms, and using programming tools for scientific applications.",
                  "learning_outcomes": [],
                  "skills": [
                    "Programming",
                    "Software Development"
                  ]
                }
              ],
              "aligned_skills": [
                "Programming",
                "Software Development"
              ]
            }
          ],
          "student_composition": "Students in the Computer Information Systems and Computer Science programs are actively developing the programming and software development skills central to this role. The pipeline spans two departments, broadening the pool of eligible candidates for a first cohort.",
          "student_evidence": {
            "total_in_program": 531,
            "with_all_core_skills": 63,
            "top_students": [
              {
                "uuid": "a2096db4-66ff-572c-ae97-327f570b45f8",
                "display_number": 1,
                "primary_focus": "Computer Information Systems",
                "courses_completed": 5,
                "gpa": 4.0,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "CISC 186",
                    "name": "Visual Basic Programming",
                    "grade": "A",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "CISC 220",
                    "name": "Fundamentals of Computer Game Programming",
                    "grade": "A",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "CISC 190",
                    "name": "Java Programming",
                    "grade": "A",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "CISC 201",
                    "name": "Advanced C++ Programming",
                    "grade": "A",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "CISC 187",
                    "name": "Data Structures in C++",
                    "grade": "A",
                    "term": "2025-Spring"
                  }
                ],
                "relevant_skills": [
                  "Object-Oriented Programming",
                  "Programming",
                  "Software Development"
                ]
              },
              {
                "uuid": "e9c2567b-9505-534a-af03-87440cab8cea",
                "display_number": 2,
                "primary_focus": "Computer Information Systems",
                "courses_completed": 2,
                "gpa": 4.0,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "CISC 205",
                    "name": "Object Oriented Programming using C++",
                    "grade": "A",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "CISC 201",
                    "name": "Advanced C++ Programming",
                    "grade": "A",
                    "term": "2025-Spring"
                  }
                ],
                "relevant_skills": [
                  "Object-Oriented Programming",
                  "Programming",
                  "Software Development"
                ]
              },
              {
                "uuid": "b34e2047-3358-5a38-b66a-8dfbc7eb3a36",
                "display_number": 3,
                "primary_focus": "Computer Information Systems",
                "courses_completed": 3,
                "gpa": 4.0,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "CISC 193",
                    "name": "Microsoft C# Software Engineering 1",
                    "grade": "A",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "CISC 205",
                    "name": "Object Oriented Programming using C++",
                    "grade": "A",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "CISC 201",
                    "name": "Advanced C++ Programming",
                    "grade": "A",
                    "term": "2025-Spring"
                  }
                ],
                "relevant_skills": [
                  "Object-Oriented Programming",
                  "Programming",
                  "Software Development"
                ]
              },
              {
                "uuid": "e6e56605-4f47-5d6f-bf52-328b93f7fe7e",
                "display_number": 4,
                "primary_focus": "Computer Information Systems",
                "courses_completed": 2,
                "gpa": 4.0,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "CISC 201",
                    "name": "Advanced C++ Programming",
                    "grade": "A",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "CISC 187",
                    "name": "Data Structures in C++",
                    "grade": "W",
                    "term": "2025-Spring"
                  }
                ],
                "relevant_skills": [
                  "Object-Oriented Programming",
                  "Programming",
                  "Software Development"
                ]
              },
              {
                "uuid": "a62b14d2-5715-513b-8c93-8e82efece0a7",
                "display_number": 5,
                "primary_focus": "Computer Information Systems",
                "courses_completed": 3,
                "gpa": 4.0,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "CISC 221",
                    "name": "Intermediate Computer Game Programming",
                    "grade": "A",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "CISC 179",
                    "name": "Introduction to Python Programming",
                    "grade": "A",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "CISC 192",
                    "name": "C/C++ Programming",
                    "grade": "A",
                    "term": "2022-Winter"
                  }
                ],
                "relevant_skills": [
                  "Object-Oriented Programming",
                  "Programming",
                  "Software Development"
                ]
              },
              {
                "uuid": "7a334715-a4c1-50d4-a8f7-23f35b41cc6f",
                "display_number": 6,
                "primary_focus": "Computer Information Systems",
                "courses_completed": 4,
                "gpa": 4.0,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "CISC 186",
                    "name": "Visual Basic Programming",
                    "grade": "A",
                    "term": "2022-Fall"
                  },
                  {
                    "code": "CISC 191",
                    "name": "Intermediate Java Programming",
                    "grade": "W",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "CISC 179",
                    "name": "Introduction to Python Programming",
                    "grade": "A",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "CISC 192",
                    "name": "C/C++ Programming",
                    "grade": "A",
                    "term": "2022-Fall"
                  }
                ],
                "relevant_skills": [
                  "Object-Oriented Programming",
                  "Programming",
                  "Software Development"
                ]
              },
              {
                "uuid": "d4906c4f-e754-53e8-a139-dcf09878d8e3",
                "display_number": 7,
                "primary_focus": "Computer Information Systems",
                "courses_completed": 3,
                "gpa": 4.0,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "CISC 220",
                    "name": "Fundamentals of Computer Game Programming",
                    "grade": "A",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "CISC 205",
                    "name": "Object Oriented Programming using C++",
                    "grade": "A",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "CISC 201",
                    "name": "Advanced C++ Programming",
                    "grade": "A",
                    "term": "2024-Fall"
                  }
                ],
                "relevant_skills": [
                  "Object-Oriented Programming",
                  "Programming",
                  "Software Development"
                ]
              },
              {
                "uuid": "b0c1163a-d6c6-5ff6-83f7-b1d9aa3c3d7c",
                "display_number": 8,
                "primary_focus": "Computer Information Systems",
                "courses_completed": 3,
                "gpa": 3.75,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "CISC 186",
                    "name": "Visual Basic Programming",
                    "grade": "B",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "CISC 201",
                    "name": "Advanced C++ Programming",
                    "grade": "A",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "CISC 187",
                    "name": "Data Structures in C++",
                    "grade": "A",
                    "term": "2023-Fall"
                  }
                ],
                "relevant_skills": [
                  "Object-Oriented Programming",
                  "Programming",
                  "Software Development"
                ]
              },
              {
                "uuid": "730bf08f-54ff-5e4c-97ff-c5f36a49c37c",
                "display_number": 9,
                "primary_focus": "Computer Information Systems",
                "courses_completed": 6,
                "gpa": 3.67,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "CISC 186",
                    "name": "Visual Basic Programming",
                    "grade": "B",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "CISC 221",
                    "name": "Intermediate Computer Game Programming",
                    "grade": "B",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "CISC 220",
                    "name": "Fundamentals of Computer Game Programming",
                    "grade": "A",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "CISC 190",
                    "name": "Java Programming",
                    "grade": "B",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "CISC 183",
                    "name": "Web Development with Ruby on Rails",
                    "grade": "A",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "CISC 205",
                    "name": "Object Oriented Programming using C++",
                    "grade": "A",
                    "term": "2023-Winter"
                  }
                ],
                "relevant_skills": [
                  "Object-Oriented Programming",
                  "Programming",
                  "Software Development"
                ]
              },
              {
                "uuid": "ecccc6ef-dff1-5f3b-a4a1-46c9f4744011",
                "display_number": 10,
                "primary_focus": "Computer Information Systems",
                "courses_completed": 5,
                "gpa": 3.67,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "CISC 186",
                    "name": "Visual Basic Programming",
                    "grade": "A",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "CISC 191",
                    "name": "Intermediate Java Programming",
                    "grade": "W",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "CISC 179",
                    "name": "Introduction to Python Programming",
                    "grade": "A",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "CISC 192",
                    "name": "C/C++ Programming",
                    "grade": "B",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "CISC 187",
                    "name": "Data Structures in C++",
                    "grade": "A",
                    "term": "2024-Fall"
                  }
                ],
                "relevant_skills": [
                  "Object-Oriented Programming",
                  "Programming",
                  "Software Development"
                ]
              }
            ]
          }
        },
        "roadmap": "A conversation between the Computer Information Systems department chair and Thermo Fisher's workforce or university relations team could clarify site capacity and intern responsibilities. An internship structured at 8-16 weeks could map to existing work experience courses in either department, with a first cohort feasible within one to two semesters.",
        "selected_occupations": [],
        "advisory_thesis": "",
        "agenda_topics": []
      },
      "engagementType": "internship",
      "collegeId": "San Diego City College",
      "savedAt": "2026-04-20T00:00:00.000Z",
      "status": "saved",
      "schemaVersion": 8
    },
    {
      "id": "seed-sandiegocity-curriculum-01",
      "proposal": {
        "employer": "Konica Minolta",
        "sector": "Wholesale",
        "partnership_type": "Curriculum Co-Design",
        "selected_occupation": "Software Developers",
        "selected_soc_code": "15-1252",
        "core_skills": [
          "Programming",
          "Software Development",
          "Object-Oriented Programming"
        ],
        "gap_skill": "Cloud Services Integration (e.g., Azure or AWS APIs)",
        "regions": [
          "Orange County",
          "San Diego / Imperial"
        ],
        "opportunity": "San Diego City College's Computer Science department is well-positioned to partner with Konica Minolta on a curriculum co-design effort focused on cloud services integration. The department builds the foundational programming skills that software developer roles at Konica Minolta require. Collaboration with Konica Minolta's technical team could strengthen student preparation in cloud platform API integration, an area central to Konica Minolta's document management and IoT product lines.",
        "opportunity_evidence": [
          {
            "title": "Software Developers",
            "soc_code": "15-1252",
            "annual_wage": 158680,
            "employment": 21890,
            "annual_openings": 1340,
            "growth_rate": 0.044858829
          }
        ],
        "justification": {
          "curriculum_composition": "The Computer Science department is the right home for this partnership. Its coursework develops the object-oriented programming and software development competencies that form the technical core of this occupation. Cloud services integration can be more rigorously developed through structured collaboration with Konica Minolta, whose engineers work directly with Azure and AWS APIs in production environments.",
          "curriculum_evidence": [
            {
              "department": "Computer Science",
              "courses": [
                {
                  "code": "CISC 183",
                  "name": "Web Development with Ruby on Rails",
                  "description": "Attention is placed on the theory and practice of computer programming emphasizing business and computer applications. Students receive hands-on experience in the fundamentals of designing and developing dynamic website using the Ruby on Rails programming language.",
                  "learning_outcomes": [
                    "Analyze a complex computing problem and to apply principles of computing and other relevant disciplines to identify solutions.",
                    "Design, implement, and evaluate a computing-based solution to meet a given set of computing requirements in the context of the program's discipline.",
                    "Communicate effectively in a variety of professional contexts.",
                    "Recognize professional responsibilities and make informed judgments in computing practice, taking into account legal, ethical, diversity, equity, inclusion, and accessibility principles consistent with the mission of the institution.",
                    "Function effectively as a member or leader of a team engaged in activities appropriate to the program's discipline.",
                    "Apply security principles and practices to maintain operations in the presence of risks and threats."
                  ],
                  "skills": [
                    "Programming",
                    "Software Development"
                  ]
                },
                {
                  "code": "CISC 186",
                  "name": "Visual Basic Programming",
                  "description": "Attention is placed on the theory and practice of computer programming emphasizing business and computer applications. Students receive hands-on experience in the fundamentals of designing and developing dynamic website using the Ruby on Rails programming language.",
                  "learning_outcomes": [
                    "Analyze a complex computing problem and to apply principles of computing and other relevant disciplines to identify solutions.",
                    "Design, implement, and evaluate a computing-based solution to meet a given set of computing requirements in the context of the program's discipline.",
                    "Communicate effectively in a variety of professional contexts.",
                    "Recognize professional responsibilities and make informed judgments in computing practice, taking into account legal, ethical, diversity, equity, inclusion, and accessibility principles consistent with the mission of the institution.",
                    "Function effectively as a member or leader of a team engaged in activities appropriate to the program's discipline.",
                    "Apply security principles and practices to maintain operations in the presence of risks and threats."
                  ],
                  "skills": [
                    "Programming",
                    "Software Development"
                  ]
                },
                {
                  "code": "CISC 190",
                  "name": "Java Programming",
                  "description": "Attention is placed on the theory and practice of computer programming emphasizing business and computer applications. Students receive hands-on experience in the fundamentals of designing and developing dynamic website using the Ruby on Rails programming language.",
                  "learning_outcomes": [
                    "Analyze a complex computing problem and to apply principles of computing and other relevant disciplines to identify solutions.",
                    "Design, implement, and evaluate a computing-based solution to meet a given set of computing requirements in the context of the program's discipline.",
                    "Communicate effectively in a variety of professional contexts.",
                    "Recognize professional responsibilities and make informed judgments in computing practice, taking into account legal, ethical, diversity, equity, inclusion, and accessibility principles consistent with the mission of the institution.",
                    "Function effectively as a member or leader of a team engaged in activities appropriate to the program's discipline.",
                    "Apply security principles and practices to maintain operations in the presence of risks and threats."
                  ],
                  "skills": [
                    "Object-Oriented Programming",
                    "Programming",
                    "Software Development"
                  ]
                }
              ],
              "aligned_skills": [
                "Object-Oriented Programming",
                "Programming",
                "Software Development"
              ]
            }
          ],
          "student_composition": "Students in the Computer Science department are building software development skills across multiple courses aligned to this occupation. They are the direct audience for curriculum that deepens preparation in cloud-based development practices Konica Minolta's projects require.",
          "student_evidence": {
            "total_in_program": 0,
            "with_all_core_skills": 0,
            "top_students": []
          }
        },
        "roadmap": "A working group between the Computer Science department chair and Konica Minolta's technical leadership could examine how cloud services integration might be incorporated into existing coursework. Revised or supplemental content could be piloted within the next catalog cycle. A collaborative review would determine the appropriate scope and curricular approach.",
        "selected_occupations": [],
        "advisory_thesis": "",
        "agenda_topics": []
      },
      "engagementType": "curriculum_codesign",
      "collegeId": "San Diego City College",
      "savedAt": "2026-04-20T00:00:00.000Z",
      "status": "saved",
      "schemaVersion": 8
    }
  ],
  "Irvine Valley College": [
    {
      "id": "seed-irvinevalley-advisory-01",
      "proposal": {
        "employer": "Mentor Worldwide",
        "sector": "Manufacturing",
        "partnership_type": "Advisory Board",
        "selected_occupation": "Bioengineers and Biomedical Engineers",
        "selected_soc_code": "17-2031",
        "core_skills": [
          "Biology",
          "Research Methods",
          "Regulatory Compliance",
          "Safety Protocols",
          "Leadership"
        ],
        "gap_skill": "",
        "regions": [
          "Orange County"
        ],
        "opportunity": "Mentor Worldwide's work producing breast implants and reconstructive surgery products under FDA regulatory oversight makes it a compelling advisory board partner for Irvine Valley College's biomedical and health-aligned programs. The company operates at the intersection of bioengineering precision, materials validation, and regulatory compliance in one of the more technically demanding segments of medical device manufacturing. An advisory board formalized around that expertise would give the college a direct channel to industry perspective at no grant funding required.",
        "opportunity_evidence": [
          {
            "title": "Medical Equipment Repairers",
            "soc_code": "49-9062",
            "annual_wage": 72310,
            "employment": 810,
            "annual_openings": 80,
            "growth_rate": 0.076149686
          },
          {
            "title": "Bioengineers and Biomedical Engineers",
            "soc_code": "17-2031",
            "annual_wage": 118350,
            "employment": 410,
            "annual_openings": 30,
            "growth_rate": 0.050387661
          },
          {
            "title": "Medical and Health Services Managers",
            "soc_code": "11-9111",
            "annual_wage": 126760,
            "employment": 6240,
            "annual_openings": 690,
            "growth_rate": 0.172525851
          }
        ],
        "justification": {
          "curriculum_composition": "The Biotechnology department provides the closest match to Mentor Worldwide's compliance-intensive operations, with coursework that builds regulatory compliance skills directly relevant to medical device manufacturing contexts. The Biology department contributes strong preparation in biology and research methods across a broad course inventory, which connects to the materials validation and applied science work Mentor Worldwide bioengineers perform. The Health department rounds out the alignment by developing research methods skills within a health services context.",
          "curriculum_evidence": [
            {
              "department": "Biology",
              "courses": [
                {
                  "code": "BIO 1",
                  "name": "THE LIFE SCIENCES",
                  "description": "This course is an integrated survey of the major principles of biology. General topics include molecular and cell biology, physiology, genetics, ecology/environmental science and evolution. This course is recommended for students seeking to fulfill the general education requirement in life sciences or as an introductory course for students pursuing advanced study in the life sciences and related fields. Credit may be earned in either BIO 1 or 1H, but not both. NR",
                  "learning_outcomes": [],
                  "skills": [
                    "Biology"
                  ]
                },
                {
                  "code": "BIO 19H",
                  "name": "MARINE BIOLOGY HONORS",
                  "description": "Marine Biology Honors presents the biology and natural history of marine organisms. A habitat approach emphasizes the physical features of each marine environment, the community structure of the habitat and adaptations of organisms. Emphasis is on California marine life. The laboratory component of the course emphasizes observation and experimentation. Experiments address general biological principles in the context of the marine environment. Students study the classification, anatomy, physiology and behavior of marine organisms. Field trips focus on the structure of marine ecosystems. This honors course is enriched through additional reading of primary literature, critical thinking, investigative experimentation, and a research presentation. Credit may be earned in either BIO 19 or BIO 19H, but not both. NR",
                  "learning_outcomes": [],
                  "skills": [
                    "Research Methods"
                  ]
                },
                {
                  "code": "BIO 1H",
                  "name": "THE LIFE SCIENCES HONORS",
                  "description": "This Honors course is an integrated survey of the major principles of biology. Students focus on cellular and molecular biology, biochemistry, reproduction, genetics, evolution, population biology, and ecology. This course is recommended for students seeking to fulfill the general education requirement in life sciences or as an introductory course for students pursuing advanced study in life sciences. In this Honors course, students are expected read and summarize topical articles, perform literature searches and reviews, and complete associated writing assignments. Credit may be earned in either BIO 1 or 1H, but not both. NR",
                  "learning_outcomes": [],
                  "skills": [
                    "Biology",
                    "Research Methods"
                  ]
                },
                {
                  "code": "BIO 1L",
                  "name": "THE LIFE SCIENCES LABORATORY",
                  "description": "This is a laboratory survey of the major principles of biology. It is the recommended course to accompany BIO 1 or BIO 1H. Topics include the application of laboratory equipment and procedures to the investigation of biological systems from the biochemical, cellular, organismal, ecological, and evolutionary perspective. Students may take BIO 1L concurrently with the BIO 1 or BIO 1H lecture or after, but not prior to either. NR",
                  "learning_outcomes": [],
                  "skills": [
                    "Biology"
                  ]
                },
                {
                  "code": "BIO 3",
                  "name": "HUMANS AND THE BIOLOGICAL WORLD",
                  "description": "This general education course examines the basic principles of the biological sciences with emphasis on their relationship to humans. Topics range from cellular biology, physiology, genetics, evolution, ecology and the environment. This course is intended for those non-majors students seeking a comprehensive course in the biological sciences. NR",
                  "learning_outcomes": [],
                  "skills": [
                    "Biology"
                  ]
                },
                {
                  "code": "BIO 5",
                  "name": "ANIMAL BIOLOGY",
                  "description": "This course is a survey of protozoans and animals. Lectures focus on the form and function, physiology, development, classification, evolution, ecology, behavior, and natural history of major animal and protozoan taxa. Field trips may be required to fulfill the course objectives.",
                  "learning_outcomes": [],
                  "skills": [
                    "Biology"
                  ]
                },
                {
                  "code": "BIO 521",
                  "name": "BEE HIVE MANAGEMENT",
                  "description": "Students will learn how to manage bee hives during the different seasons of Southern California, while using the appropriate tools and exercising proper safety protocols. Bee suits and gloves will be provided, in addition to all the required tools. Students will utilize particular inspection techniques, regularly visit an apiary for hive inspections and will learn to identify and anticipate hive needs. Additional topics include honey bee food sources and nutrition, pests, predators, diseases and parasites and their treatments. R-D-99",
                  "learning_outcomes": [],
                  "skills": [
                    "Safety Protocols"
                  ]
                },
                {
                  "code": "BIO 522",
                  "name": "ADVANCED BEEKEEPING, APIARY SAFETY & TECHNOLOGY",
                  "description": "Advanced seasonal beekeeping practices will be covered, including honey harvesting procedures, like re-queening a colony, swarm removal, splitting/combining colonies and building projects. Safety in and around the apiary will be discussed to enhance everyone's beekeeping experience, which includes proper care and storage of equipment. Students will also learn about the different monitoring systems available to beekeeping, with an introduction to and practice of the scientific method, as well as data collection and interpretation. R-D-99",
                  "learning_outcomes": [],
                  "skills": [
                    "Safety Protocols"
                  ]
                },
                {
                  "code": "BIO 7",
                  "name": "STATISTICS AND EXPERIMENTAL DESIGN FOR THE BIOLOGICAL AND HEALTH SCIENCES",
                  "description": "This course provides an introduction to statistical theory and experimental methods as applied to the biological and health sciences. Topics include experimental design for the study of biological systems in the field and the laboratory, hypothesis testing, graphical and numerical approaches to presenting data sets, statistical methods, discrete and continuous data, and the distinction between parametric and nonparametric data. The course includes instruction in the presentation and interpretation of results. NR",
                  "learning_outcomes": [],
                  "skills": [
                    "Biology"
                  ]
                },
                {
                  "code": "BIO 71",
                  "name": "STEM CELLS AND SOCIETY",
                  "description": "This course offers an introduction to stem cell research, including the origins and potential uses of stem cells in medicine, research, reproduction, agriculture, environment preservation, and other applications. Course topics include different sources and forms of stem cells, the technologies used to generate these remarkable cells, their use in a wide variety of fields, and the ethical and social concerns that have been and continue to be raised about the use of stem cells and related biotechnologies. This course is intended for majors and non-majors. NR",
                  "learning_outcomes": [],
                  "skills": [
                    "Research Methods"
                  ]
                },
                {
                  "code": "BIO 80",
                  "name": "INTEGRATED BIOLOGY: ORGANISMS TO ECOSYSTEMS",
                  "description": "This course introduces students to the diversity of life and provides the framework to understand its origins from underlying processes in organic evolution. Topics include natural selection, population genetics, systematics, speciation, history of life of Earth, morphological, physiological, and behavioral adaptation, and the principles of evolutionary ecology. Field trips may be required to fulfill objectives of this course. Credit for BIO 80 or 80H, but not both. C-ID: BIOL 140. NR",
                  "learning_outcomes": [],
                  "skills": [
                    "Biology"
                  ]
                },
                {
                  "code": "BIO 80H",
                  "name": "INTEGRATED BIOLOGY: ORGANISMS TO ECOSYSTEMS HONORS",
                  "description": "This Honors course introduces students to the diversity of life and provides the framework to understand its origins from underlying processes in organic evolution. Topics include natural selection, population genetics, systematics, speciation, history of life of Earth, morphological, physiological, and behavioral adaptation, and the principles of evolutionary ecology. As an Honors course, students will be completing advanced reading and writing assignments, will conduct more rigorous laboratory exercises, and perform more in-depth data analyses than in BIO 80. Field trips may be required to fulfill objectives of this course. Credit for BIO 80 or BIO 80H, but not both. NR",
                  "learning_outcomes": [],
                  "skills": [
                    "Biology",
                    "Research Methods"
                  ]
                },
                {
                  "code": "BIO 81",
                  "name": "INTEGRATED BIOLOGY: FROM DNA TO ORGANISMS",
                  "description": "This combined lecture and lab course integrates four broadly defined levels of organismal structure and function into a coherent framework. Biochemistry, cell biology, genetics, and organismal structure and function (with emphasis on organ systems and physiology) are woven together using basic themes of structural/functional hierarchy, energetics, and information flow. BIO 81 was formerly offered as BIO 93 and 93L. Credit for BIO 81 or 81H, but not both. C-ID: BIOL 190 NR",
                  "learning_outcomes": [],
                  "skills": [
                    "Biology"
                  ]
                },
                {
                  "code": "BIO 81H",
                  "name": "INTEGRATED BIOLOGY: FROM DNA TO ORGANISMS",
                  "description": "This combined lecture and lab course integrates four broadly defined levels of organismal structure and function into a coherent framework. Biochemistry, cell biology, genetics, and organismal structure and function (with emphasis on organ systems and physiology) are woven together using basics themes of structural/functional hierarchy, energetics, and information flow. As an Honors course, students will be completing advanced reading and writing assignments, will conduct more rigorous laboratory exercises, and perform more in-depth data analyses than in BIO 81. BIO 81 was formerly offered as BIO 93 and 93L. Credit for BIO 81 or BIO 81H, but not both. C-ID: BIOL 190 NR",
                  "learning_outcomes": [],
                  "skills": [
                    "Biology",
                    "Research Methods"
                  ]
                }
              ],
              "aligned_skills": [
                "Biology",
                "Research Methods",
                "Safety Protocols"
              ]
            },
            {
              "department": "Biotechnology",
              "courses": [
                {
                  "code": "BIOT 276",
                  "name": "QUALITY AND REGULATORY COMPLIANCE IN BIOSCIENCE",
                  "description": "This course will cover quality assurance and regulatory compliance for the bioscience industries. Topics will span quality control and FDA, USDA, EPA, MSP, OSHA and EPA regulations for the biotechnology, biopharmaceutical, biomedical devices and food industries. Theories and applications of quality assurance and quality control will be presented and several different quality systems will be discussed such as CAPA and cGMP (good manufacturing practices), ISO9000, ISO1435 (International Standards Organization). Six Sigma and Lean, OSHA and Industry safety. NR",
                  "learning_outcomes": [],
                  "skills": [
                    "Regulatory Compliance"
                  ]
                },
                {
                  "code": "BIOT 279",
                  "name": "QUALITY ASSURANCE OF MEDICAL DEVICES",
                  "description": "Medical device manufacturers are always working to balance the demands of meeting government regulations and containing production costs, in an effort to produce the most reliable and safest medical devices. This course is designed to introduce the basic elements of medical devise quality initiatives and quality-control methodologies to ensure compliance with federal guidelines for individuals working with medical devices in the biomanufacturing industry. NR",
                  "learning_outcomes": [],
                  "skills": [
                    "Regulatory Compliance"
                  ]
                }
              ],
              "aligned_skills": [
                "Regulatory Compliance"
              ]
            },
            {
              "department": "Health",
              "courses": [
                {
                  "code": "HLTH 10",
                  "name": "STATISTICS FOR PUBLIC HEALTH",
                  "description": "This course emphasizes the calculation, interpretation, and application of descriptive and inferential statistics in public health science, population-based research and practice, and related fields. Topics include statistical principles and use of probability techniques, hypothesis testing, and predictive techniques to facilitate evidence-based practices. Topics include descriptive statistics; probability and sampling distributions; statistical inference; correlation and linear regression; analysis of variance, chi-square and t-tests. Application of statistical concepts will incorporate data from public health sources including research and governmental datasets. The use and application of technology for statistical analysis including the interpretation of the relevance of the statistical findings will be covered. NR",
                  "learning_outcomes": [],
                  "skills": [
                    "Research Methods"
                  ]
                }
              ],
              "aligned_skills": [
                "Research Methods"
              ]
            }
          ],
          "student_composition": "Students across these three departments are building technical foundations in biology, research methods, regulatory compliance, and safety protocols. They are pursuing pathways in biomedical engineering, biotechnology, and health services that feed directly into the occupational categories Mentor Worldwide staffs. The aggregate pipeline spans students at different stages of preparation, from applied lab coursework in Biotechnology to health services training in the Health program.",
          "student_evidence": {
            "total_in_program": 616,
            "with_all_core_skills": 0,
            "top_students": [
              {
                "uuid": "62c652a4-4807-5c4f-be34-762c8da74d55",
                "display_number": 1,
                "primary_focus": "Biology",
                "courses_completed": 9,
                "gpa": 3.2,
                "matching_skills": 4,
                "enrollments": [
                  {
                    "code": "HD 190",
                    "name": "ADMINISTRATION OF SCHOOLS FOR YOUNG CHILDREN - PROGRAM",
                    "grade": "A",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "BIO 69",
                    "name": "FIELD STUDIES: A 21ST CENTURY LOOK AT THE AMERICAN WEST",
                    "grade": "D",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "BIO 80H",
                    "name": "INTEGRATED BIOLOGY: ORGANISMS TO ECOSYSTEMS HONORS",
                    "grade": "C",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "BIO 1L",
                    "name": "THE LIFE SCIENCES LABORATORY",
                    "grade": "D",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "BIO 1H",
                    "name": "THE LIFE SCIENCES HONORS",
                    "grade": "A",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "BIOT 276",
                    "name": "QUALITY AND REGULATORY COMPLIANCE IN BIOSCIENCE",
                    "grade": "A",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "BIO 19H",
                    "name": "MARINE BIOLOGY HONORS",
                    "grade": "B",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "BIO 14",
                    "name": "ADVANCED RESEARCH IN BIOLOGICAL AND HEALTH SCIENCES",
                    "grade": "B",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "BIO 4",
                    "name": "RESEARCH METHODS IN THE BIOLOGICAL SCIENCES",
                    "grade": "A",
                    "term": "2024-Spring"
                  }
                ],
                "relevant_skills": [
                  "Biology",
                  "Leadership",
                  "Regulatory Compliance",
                  "Research Methods"
                ]
              },
              {
                "uuid": "5714a2f0-3dcc-5efe-93f7-27a495a26eb2",
                "display_number": 2,
                "primary_focus": "Biology",
                "courses_completed": 6,
                "gpa": 3.19,
                "matching_skills": 4,
                "enrollments": [
                  {
                    "code": "BIO 69",
                    "name": "FIELD STUDIES: A 21ST CENTURY LOOK AT THE AMERICAN WEST",
                    "grade": "C",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "BIO 80H",
                    "name": "INTEGRATED BIOLOGY: ORGANISMS TO ECOSYSTEMS HONORS",
                    "grade": "A",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "HD 150",
                    "name": "HEALTH, SAFETY AND NUTRITION OF CHILDREN",
                    "grade": "A",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "BIO 19H",
                    "name": "MARINE BIOLOGY HONORS",
                    "grade": "C",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "BIO 14",
                    "name": "ADVANCED RESEARCH IN BIOLOGICAL AND HEALTH SCIENCES",
                    "grade": "A",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "BIO 4",
                    "name": "RESEARCH METHODS IN THE BIOLOGICAL SCIENCES",
                    "grade": "A",
                    "term": "2024-Winter"
                  }
                ],
                "relevant_skills": [
                  "Biology",
                  "Regulatory Compliance",
                  "Research Methods",
                  "Safety Protocols"
                ]
              },
              {
                "uuid": "3990acb6-0d7f-53ab-876e-75ddd3c7705e",
                "display_number": 3,
                "primary_focus": "Biology",
                "courses_completed": 10,
                "gpa": 3.03,
                "matching_skills": 4,
                "enrollments": [
                  {
                    "code": "BIO 69",
                    "name": "FIELD STUDIES: A 21ST CENTURY LOOK AT THE AMERICAN WEST",
                    "grade": "B",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "BIO 81H",
                    "name": "INTEGRATED BIOLOGY: FROM DNA TO ORGANISMS",
                    "grade": "W",
                    "term": "2022-Fall"
                  },
                  {
                    "code": "BIO 1L",
                    "name": "THE LIFE SCIENCES LABORATORY",
                    "grade": "A",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "LGL 240",
                    "name": "CANNABIS LAW & POLICY",
                    "grade": "A",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "HD 150",
                    "name": "HEALTH, SAFETY AND NUTRITION OF CHILDREN",
                    "grade": "C",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "ETHN 10H",
                    "name": "INTRODUCTION TO ETHNIC STUDIES HONORS",
                    "grade": "A",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "BIO 4",
                    "name": "RESEARCH METHODS IN THE BIOLOGICAL SCIENCES",
                    "grade": "P",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "PSYC 6",
                    "name": "DEVELOPMENTAL PSYCHOLOGY-LIFESPAN",
                    "grade": "W",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "WR 1H",
                    "name": "COLLEGE WRITING 1 HONORS",
                    "grade": "P",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "COMM 1H",
                    "name": "COMMUNICATION FUNDAMENTALS HONORS",
                    "grade": "A",
                    "term": "2023-Winter"
                  }
                ],
                "relevant_skills": [
                  "Biology",
                  "Regulatory Compliance",
                  "Research Methods",
                  "Safety Protocols"
                ]
              },
              {
                "uuid": "fc7d3ba3-1950-55af-a5d7-1680fe56295a",
                "display_number": 4,
                "primary_focus": "Biology",
                "courses_completed": 5,
                "gpa": 3.0,
                "matching_skills": 4,
                "enrollments": [
                  {
                    "code": "BIO 81",
                    "name": "INTEGRATED BIOLOGY: FROM DNA TO ORGANISMS",
                    "grade": "A",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "BIO 80",
                    "name": "INTEGRATED BIOLOGY: ORGANISMS TO ECOSYSTEMS",
                    "grade": "A",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "BIO 1",
                    "name": "THE LIFE SCIENCES",
                    "grade": "A",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "HD 150",
                    "name": "HEALTH, SAFETY AND NUTRITION OF CHILDREN",
                    "grade": "A",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "BIO 4",
                    "name": "RESEARCH METHODS IN THE BIOLOGICAL SCIENCES",
                    "grade": "A",
                    "term": "2025-Spring"
                  }
                ],
                "relevant_skills": [
                  "Biology",
                  "Regulatory Compliance",
                  "Research Methods",
                  "Safety Protocols"
                ]
              },
              {
                "uuid": "1ec31179-5672-568a-85f0-677ea3bb480c",
                "display_number": 5,
                "primary_focus": "Biology",
                "courses_completed": 5,
                "gpa": 2.86,
                "matching_skills": 4,
                "enrollments": [
                  {
                    "code": "BIO 7",
                    "name": "STATISTICS AND EXPERIMENTAL DESIGN FOR THE BIOLOGICAL AND HEALTH SCIENCES",
                    "grade": "B",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "BIO 81H",
                    "name": "INTEGRATED BIOLOGY: FROM DNA TO ORGANISMS",
                    "grade": "C",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "BIO 3",
                    "name": "HUMANS AND THE BIOLOGICAL WORLD",
                    "grade": "A",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "HD 150",
                    "name": "HEALTH, SAFETY AND NUTRITION OF CHILDREN",
                    "grade": "A",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "BIO 14",
                    "name": "ADVANCED RESEARCH IN BIOLOGICAL AND HEALTH SCIENCES",
                    "grade": "F",
                    "term": "2024-Winter"
                  }
                ],
                "relevant_skills": [
                  "Biology",
                  "Regulatory Compliance",
                  "Research Methods",
                  "Safety Protocols"
                ]
              },
              {
                "uuid": "be6b576d-f401-5bae-824a-35984bbaed91",
                "display_number": 6,
                "primary_focus": "Biology",
                "courses_completed": 7,
                "gpa": 2.77,
                "matching_skills": 4,
                "enrollments": [
                  {
                    "code": "RE 122",
                    "name": "REAL ESTATE BUSINESS MANAGEMENT",
                    "grade": "A",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "BIO 69",
                    "name": "FIELD STUDIES: A 21ST CENTURY LOOK AT THE AMERICAN WEST",
                    "grade": "B",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "BIO 81H",
                    "name": "INTEGRATED BIOLOGY: FROM DNA TO ORGANISMS",
                    "grade": "W",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "LGL 240",
                    "name": "CANNABIS LAW & POLICY",
                    "grade": "C",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "ESL 80",
                    "name": "ACADEMIC WRITING III FOR MULTILINGUAL WRITERS",
                    "grade": "A",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "BIO 14",
                    "name": "ADVANCED RESEARCH IN BIOLOGICAL AND HEALTH SCIENCES",
                    "grade": "C",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "BIO 4",
                    "name": "RESEARCH METHODS IN THE BIOLOGICAL SCIENCES",
                    "grade": "B",
                    "term": "2024-Fall"
                  }
                ],
                "relevant_skills": [
                  "Biology",
                  "Leadership",
                  "Regulatory Compliance",
                  "Research Methods"
                ]
              },
              {
                "uuid": "5101d467-35d4-5882-bb92-f57418838900",
                "display_number": 7,
                "primary_focus": "Biology",
                "courses_completed": 4,
                "gpa": 3.62,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "BIO 1H",
                    "name": "THE LIFE SCIENCES HONORS",
                    "grade": "A",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "BIO 1",
                    "name": "THE LIFE SCIENCES",
                    "grade": "B",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "ELEC 203",
                    "name": "COMMERCIAL AND INDUSTRIAL WIRING",
                    "grade": "B",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "GEOG 3H",
                    "name": "WORLD REGIONAL GEOGRAPHY HONORS",
                    "grade": "W",
                    "term": "2025-Spring"
                  }
                ],
                "relevant_skills": [
                  "Biology",
                  "Research Methods",
                  "Safety Protocols"
                ]
              },
              {
                "uuid": "2ca9419e-a4ec-5ecd-92b9-993a3af95012",
                "display_number": 8,
                "primary_focus": "Biology",
                "courses_completed": 10,
                "gpa": 3.5,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "COMM 10",
                    "name": "GROUP DYNAMICS AND LEADERSHIP",
                    "grade": "A",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "BIO 69",
                    "name": "FIELD STUDIES: A 21ST CENTURY LOOK AT THE AMERICAN WEST",
                    "grade": "A",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "BIO 81H",
                    "name": "INTEGRATED BIOLOGY: FROM DNA TO ORGANISMS",
                    "grade": "C",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "BIO 81",
                    "name": "INTEGRATED BIOLOGY: FROM DNA TO ORGANISMS",
                    "grade": "A",
                    "term": "2022-Fall"
                  },
                  {
                    "code": "BIO 71",
                    "name": "STEM CELLS AND SOCIETY",
                    "grade": "A",
                    "term": "2022-Fall"
                  },
                  {
                    "code": "BIO 19H",
                    "name": "MARINE BIOLOGY HONORS",
                    "grade": "C",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "BIO 4",
                    "name": "RESEARCH METHODS IN THE BIOLOGICAL SCIENCES",
                    "grade": "A",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "PSYC 5H",
                    "name": "PSYCHOLOGICAL ASPECTS OF HUMAN SEXUALITY HONORS",
                    "grade": "B",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "MATH 3AH",
                    "name": "ANALYTIC GEOMETRY AND CALCULUS I HONORS",
                    "grade": "A",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "COMM 1H",
                    "name": "COMMUNICATION FUNDAMENTALS HONORS",
                    "grade": "A",
                    "term": "2023-Spring"
                  }
                ],
                "relevant_skills": [
                  "Biology",
                  "Leadership",
                  "Research Methods"
                ]
              },
              {
                "uuid": "ee8d0e32-a9fb-574c-945c-14d7bbd24def",
                "display_number": 9,
                "primary_focus": "Health",
                "courses_completed": 3,
                "gpa": 3.5,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "BIO 81H",
                    "name": "INTEGRATED BIOLOGY: FROM DNA TO ORGANISMS",
                    "grade": "A",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "ACCT 275A",
                    "name": "AUDITING: INTERNAL CONTROLS UNDER SARBANES-OXLEY",
                    "grade": "A",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "HLTH 10",
                    "name": "STATISTICS FOR PUBLIC HEALTH",
                    "grade": "A",
                    "term": "2024-Spring"
                  }
                ],
                "relevant_skills": [
                  "Biology",
                  "Regulatory Compliance",
                  "Research Methods"
                ]
              },
              {
                "uuid": "f3f4a120-a747-53e8-b353-bec4651a71e7",
                "display_number": 10,
                "primary_focus": "Biology",
                "courses_completed": 14,
                "gpa": 3.49,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "MGT 115",
                    "name": "DIVERSITY, BUSINESS AND THE WORKPLACE",
                    "grade": "P",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "COMM 10",
                    "name": "GROUP DYNAMICS AND LEADERSHIP",
                    "grade": "B",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "BIO 5",
                    "name": "ANIMAL BIOLOGY",
                    "grade": "B",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "BIO 1L",
                    "name": "THE LIFE SCIENCES LABORATORY",
                    "grade": "B",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "BIO 1H",
                    "name": "THE LIFE SCIENCES HONORS",
                    "grade": "B",
                    "term": "2022-Fall"
                  },
                  {
                    "code": "HIST 60",
                    "name": "INTRODUCTION TO THE HISTORY OF SCIENCE",
                    "grade": "A",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "BIO 71",
                    "name": "STEM CELLS AND SOCIETY",
                    "grade": "B",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "BIO 14",
                    "name": "ADVANCED RESEARCH IN BIOLOGICAL AND HEALTH SCIENCES",
                    "grade": "A",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "BIO 4",
                    "name": "RESEARCH METHODS IN THE BIOLOGICAL SCIENCES",
                    "grade": "W",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "PSYC 30",
                    "name": "SOCIAL PSYCHOLOGY",
                    "grade": "A",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "PSYC 6",
                    "name": "DEVELOPMENTAL PSYCHOLOGY-LIFESPAN",
                    "grade": "A",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "GEOG 3H",
                    "name": "WORLD REGIONAL GEOGRAPHY HONORS",
                    "grade": "A",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "ACCT 1BH",
                    "name": "MANAGERIAL ACCOUNTING HONORS",
                    "grade": "P",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "MATH 3BH",
                    "name": "ANALYTIC GEOMETRY AND CALCULUS II HONORS",
                    "grade": "A",
                    "term": "2024-Spring"
                  }
                ],
                "relevant_skills": [
                  "Biology",
                  "Leadership",
                  "Research Methods"
                ]
              }
            ]
          }
        },
        "roadmap": "A quarterly advisory board with Mentor Worldwide could give the Biotechnology, Biology, and Health departments sustained access to applied industry perspective on regulatory and bioengineering practice. Potential starting points for the inaugural meeting include which regulatory compliance frameworks Mentor Worldwide technicians navigate most frequently, how the company structures safety protocol onboarding for new biomedical manufacturing employees, and which research methods its bioengineers rely on when validating materials against FDA standards.",
        "selected_occupations": [
          "Bioengineers and Biomedical Engineers",
          "Medical Equipment Repairers",
          "Medical and Health Services Managers"
        ],
        "advisory_thesis": "Mentor Worldwide operates at the intersection of medical device manufacturing and surgical outcomes, producing breast implants and reconstructive surgery products that must meet rigorous bioengineering standards and strict regulatory requirements at every stage of development and distribution. Their work offers students in biomedical, health services, and equipment repair programs direct insight into how safety protocols, compliance frameworks, and engineering precision function together in a highly specialized segment of medical manufacturing.",
        "agenda_topics": [
          {
            "topic": "What specific regulatory compliance frameworks do Mentor Worldwide technicians navigate most frequently when maintaining or repairing medical manufacturing equipment?",
            "rationale": "Mentor Worldwide's firsthand experience with compliance requirements in medical device manufacturing could strengthen how the Health department sequences and contextualizes regulatory training for Medical Equipment Repairers."
          },
          {
            "topic": "How does Mentor Worldwide structure internal safety protocol training for new employees entering biomedical manufacturing roles?",
            "rationale": "Insight into Mentor Worldwide's onboarding safety practices could inform how the Biotechnology department frames safety protocols within its existing lab and applied coursework."
          },
          {
            "topic": "Which research methods do Mentor Worldwide bioengineers rely on most when validating materials or processes against FDA standards?",
            "rationale": "Mentor Worldwide's applied research experience in regulated medical device development could help the Biology department calibrate how research methods are framed for students pursuing biomedical career pathways."
          }
        ]
      },
      "engagementType": "advisory_board",
      "collegeId": "Irvine Valley College",
      "savedAt": "2026-04-20T00:00:00.000Z",
      "status": "saved",
      "schemaVersion": 8
    },
    {
      "id": "seed-irvinevalley-internship-01",
      "proposal": {
        "employer": "Confluent Medical Technologies",
        "sector": "Manufacturing",
        "partnership_type": "Internship Pipeline",
        "selected_occupation": "Bioengineers and Biomedical Engineers",
        "selected_soc_code": "17-2031.00",
        "core_skills": [
          "Design",
          "Biology",
          "Anatomy & Physiology"
        ],
        "gap_skill": "",
        "regions": [
          "Orange County"
        ],
        "opportunity": "Confluent Medical Technologies is a compelling internship partner for Irvine Valley College's biomedical programs given its focus on cardiovascular and peripheral vascular device manufacturing in Orange County. The region supports 410 employed biomedical engineers, 30 annual openings, and 5.0% projected growth at a median wage of $118,350. An internship at Confluent could place students directly in medical device design and manufacturing workflows.",
        "opportunity_evidence": [
          {
            "title": "Bioengineers and Biomedical Engineers",
            "soc_code": "17-2031",
            "annual_wage": 118350,
            "employment": 410,
            "annual_openings": 30,
            "growth_rate": 0.050387661
          }
        ],
        "justification": {
          "curriculum_composition": "Irvine Valley College's preparation for this internship spans three departments, each contributing a distinct core skill required for the biomedical engineer role. The Biology department builds depth in anatomy and physiology across a broad course catalog, grounding students in the biological systems that medical device design must account for. The Engineering department develops design competency, which connects directly to the product development work students would encounter at Confluent.",
          "curriculum_evidence": [
            {
              "department": "Biology",
              "courses": [
                {
                  "code": "BIO 1",
                  "name": "THE LIFE SCIENCES",
                  "description": "This course is an integrated survey of the major principles of biology. General topics include molecular and cell biology, physiology, genetics, ecology/environmental science and evolution. This course is recommended for students seeking to fulfill the general education requirement in life sciences or as an introductory course for students pursuing advanced study in the life sciences and related fields. Credit may be earned in either BIO 1 or 1H, but not both. NR",
                  "learning_outcomes": [],
                  "skills": [
                    "Biology"
                  ]
                },
                {
                  "code": "BIO 12",
                  "name": "HUMAN PHYSIOLOGY",
                  "description": "This course applies an integrated systems approach to the study of function in the human body. Emphasis is on major organ systems, their negative feedback controls, and their significance in maintaining homeostasis of the whole body. Each system is analyzed at the molecular, cellular, tissue and organ levels of function. The lab component of the course emphasizes experimental design, data collection and analysis, and evaluation and interpretation of experimental results.",
                  "learning_outcomes": [],
                  "skills": [
                    "Anatomy & Physiology"
                  ]
                },
                {
                  "code": "BIO 19",
                  "name": "MARINE BIOLOGY",
                  "description": "This course presents the biology and natural history of marine organisms within an ecological context. A habitat approach emphasizes the physical features of each marine environment, the community structure of the habitat and adaptations of the constituent organisms. Emphasis is on California marine life. The laboratory component of the course emphasizes observation and experimentation. Experiments address general biological/ecological principles in the context of the marine environment. Students study the classification, anatomy, physiology and behavior of marine organisms. Field trips, an integral part of the course, focus on the structure of marine ecosystems. Credit may be earned in either BIO 19 or BIO 19H, but not both. NR",
                  "learning_outcomes": [],
                  "skills": [
                    "Anatomy & Physiology"
                  ]
                },
                {
                  "code": "BIO 19H",
                  "name": "MARINE BIOLOGY HONORS",
                  "description": "Marine Biology Honors presents the biology and natural history of marine organisms. A habitat approach emphasizes the physical features of each marine environment, the community structure of the habitat and adaptations of organisms. Emphasis is on California marine life. The laboratory component of the course emphasizes observation and experimentation. Experiments address general biological principles in the context of the marine environment. Students study the classification, anatomy, physiology and behavior of marine organisms. Field trips focus on the structure of marine ecosystems. This honors course is enriched through additional reading of primary literature, critical thinking, investigative experimentation, and a research presentation. Credit may be earned in either BIO 19 or BIO 19H, but not both. NR",
                  "learning_outcomes": [],
                  "skills": [
                    "Anatomy & Physiology"
                  ]
                },
                {
                  "code": "BIO 1H",
                  "name": "THE LIFE SCIENCES HONORS",
                  "description": "This Honors course is an integrated survey of the major principles of biology. Students focus on cellular and molecular biology, biochemistry, reproduction, genetics, evolution, population biology, and ecology. This course is recommended for students seeking to fulfill the general education requirement in life sciences or as an introductory course for students pursuing advanced study in life sciences. In this Honors course, students are expected read and summarize topical articles, perform literature searches and reviews, and complete associated writing assignments. Credit may be earned in either BIO 1 or 1H, but not both. NR",
                  "learning_outcomes": [],
                  "skills": [
                    "Biology"
                  ]
                },
                {
                  "code": "BIO 1L",
                  "name": "THE LIFE SCIENCES LABORATORY",
                  "description": "This is a laboratory survey of the major principles of biology. It is the recommended course to accompany BIO 1 or BIO 1H. Topics include the application of laboratory equipment and procedures to the investigation of biological systems from the biochemical, cellular, organismal, ecological, and evolutionary perspective. Students may take BIO 1L concurrently with the BIO 1 or BIO 1H lecture or after, but not prior to either. NR",
                  "learning_outcomes": [],
                  "skills": [
                    "Biology"
                  ]
                },
                {
                  "code": "BIO 21",
                  "name": "HUMAN ANATOMY AND PHYSIOLOGY",
                  "description": "This basic course shows the interrelationships between the anatomical and physiological systems of humans. The course presents an analysis that integrates cellular, tissue, organ, and organ system levels of structure and relates structure to function. Laboratory emphasis is on the histology, gross anatomy, and physiology of major systems. This course does not meet the requirements of either anatomy or physiology for nursing students or biology majors. NR",
                  "learning_outcomes": [],
                  "skills": [
                    "Anatomy & Physiology"
                  ]
                },
                {
                  "code": "BIO 3",
                  "name": "HUMANS AND THE BIOLOGICAL WORLD",
                  "description": "This general education course examines the basic principles of the biological sciences with emphasis on their relationship to humans. Topics range from cellular biology, physiology, genetics, evolution, ecology and the environment. This course is intended for those non-majors students seeking a comprehensive course in the biological sciences. NR",
                  "learning_outcomes": [],
                  "skills": [
                    "Biology"
                  ]
                },
                {
                  "code": "BIO 5",
                  "name": "ANIMAL BIOLOGY",
                  "description": "This course is a survey of protozoans and animals. Lectures focus on the form and function, physiology, development, classification, evolution, ecology, behavior, and natural history of major animal and protozoan taxa. Field trips may be required to fulfill the course objectives.",
                  "learning_outcomes": [],
                  "skills": [
                    "Biology"
                  ]
                },
                {
                  "code": "BIO 7",
                  "name": "STATISTICS AND EXPERIMENTAL DESIGN FOR THE BIOLOGICAL AND HEALTH SCIENCES",
                  "description": "This course provides an introduction to statistical theory and experimental methods as applied to the biological and health sciences. Topics include experimental design for the study of biological systems in the field and the laboratory, hypothesis testing, graphical and numerical approaches to presenting data sets, statistical methods, discrete and continuous data, and the distinction between parametric and nonparametric data. The course includes instruction in the presentation and interpretation of results. NR",
                  "learning_outcomes": [],
                  "skills": [
                    "Biology"
                  ]
                },
                {
                  "code": "BIO 80",
                  "name": "INTEGRATED BIOLOGY: ORGANISMS TO ECOSYSTEMS",
                  "description": "This course introduces students to the diversity of life and provides the framework to understand its origins from underlying processes in organic evolution. Topics include natural selection, population genetics, systematics, speciation, history of life of Earth, morphological, physiological, and behavioral adaptation, and the principles of evolutionary ecology. Field trips may be required to fulfill objectives of this course. Credit for BIO 80 or 80H, but not both. C-ID: BIOL 140. NR",
                  "learning_outcomes": [],
                  "skills": [
                    "Biology"
                  ]
                },
                {
                  "code": "BIO 80H",
                  "name": "INTEGRATED BIOLOGY: ORGANISMS TO ECOSYSTEMS HONORS",
                  "description": "This Honors course introduces students to the diversity of life and provides the framework to understand its origins from underlying processes in organic evolution. Topics include natural selection, population genetics, systematics, speciation, history of life of Earth, morphological, physiological, and behavioral adaptation, and the principles of evolutionary ecology. As an Honors course, students will be completing advanced reading and writing assignments, will conduct more rigorous laboratory exercises, and perform more in-depth data analyses than in BIO 80. Field trips may be required to fulfill objectives of this course. Credit for BIO 80 or BIO 80H, but not both. NR",
                  "learning_outcomes": [],
                  "skills": [
                    "Biology"
                  ]
                },
                {
                  "code": "BIO 81",
                  "name": "INTEGRATED BIOLOGY: FROM DNA TO ORGANISMS",
                  "description": "This combined lecture and lab course integrates four broadly defined levels of organismal structure and function into a coherent framework. Biochemistry, cell biology, genetics, and organismal structure and function (with emphasis on organ systems and physiology) are woven together using basic themes of structural/functional hierarchy, energetics, and information flow. BIO 81 was formerly offered as BIO 93 and 93L. Credit for BIO 81 or 81H, but not both. C-ID: BIOL 190 NR",
                  "learning_outcomes": [],
                  "skills": [
                    "Biology"
                  ]
                },
                {
                  "code": "BIO 81H",
                  "name": "INTEGRATED BIOLOGY: FROM DNA TO ORGANISMS",
                  "description": "This combined lecture and lab course integrates four broadly defined levels of organismal structure and function into a coherent framework. Biochemistry, cell biology, genetics, and organismal structure and function (with emphasis on organ systems and physiology) are woven together using basics themes of structural/functional hierarchy, energetics, and information flow. As an Honors course, students will be completing advanced reading and writing assignments, will conduct more rigorous laboratory exercises, and perform more in-depth data analyses than in BIO 81. BIO 81 was formerly offered as BIO 93 and 93L. Credit for BIO 81 or BIO 81H, but not both. C-ID: BIOL 190 NR",
                  "learning_outcomes": [],
                  "skills": [
                    "Biology"
                  ]
                }
              ],
              "aligned_skills": [
                "Anatomy & Physiology",
                "Biology"
              ]
            },
            {
              "department": "Engineering",
              "courses": [
                {
                  "code": "DR 52",
                  "name": "ENGINEERING DRAWING AND DESIGN",
                  "description": "This course is designed to develop the basic skills needed for industrial-level engineering drawing and conceptual design, including assembly drawings and detail drawings. The course introduces the fundamentals of mechanical design and strategies for creative design. It includes the basic design process used for machine drawings, castings, cams, weldments, and power transmissions, with integrated problems and solutions. DR 52 was formerly offered as DR 101. NR",
                  "learning_outcomes": [],
                  "skills": [
                    "Design"
                  ]
                },
                {
                  "code": "ENGR 54",
                  "name": "PRINCIPLES OF MATERIALS SCIENCE AND ENGINEERING",
                  "description": "This course covers major topics related to engineering design, manufacturing, and the properties of materials used in modern component construction. Students will learn to implement design methods required to efficiently use manufacturing methods such as machining, forming, and molding. students will conduct analysis of material used for practical application of manufacturing processes. Atomic structure, bonding, defects, phase equilibria, mechanical properties, electrical properties, and optical properties are key elements which students study in detail to provide a firm support for student assumptions during analysis. NR",
                  "learning_outcomes": [],
                  "skills": [
                    "Design"
                  ]
                },
                {
                  "code": "ENGR 7",
                  "name": "INTRODUCTION TO ENGINEERING METHODS",
                  "description": "This course provides practical experience for students majoring in engineering and applied sciences. It focuses on modeling and designing with a physical element such as a robot or quad-copter. Students will develop skills such as analyzing physical structures, manufacturing small components, testing, team building, planning, scheduling, management, and implementation of a final design. Projects may include data collection, design reviews, analysis, report writing, group construction projects, and participation in competitions based on related criteria. NR",
                  "learning_outcomes": [],
                  "skills": [
                    "Design"
                  ]
                }
              ],
              "aligned_skills": [
                "Design"
              ]
            },
            {
              "department": "Kinesiology",
              "courses": [
                {
                  "code": "KNES 93",
                  "name": "MOVEMENT ANATOMY",
                  "description": "This course, part of the Fitness Professional Certificate Program, discusses movement as it relates to exercise and sports. The course examines the composition, structure, function and movements of bones and joints; the structure and actions of skeletal muscle; and the practical application of kinesiological principles in developing structurally sound exercise program.",
                  "learning_outcomes": [],
                  "skills": [
                    "Anatomy & Physiology"
                  ]
                }
              ],
              "aligned_skills": [
                "Anatomy & Physiology"
              ]
            }
          ],
          "student_composition": "Students pursuing coursework across the Biology, Engineering, and Kinesiology departments are building the skill profile that a Confluent internship targets. The pipeline is distributed across programs with complementary preparation, meaning cohort candidates are likely already double-enrolled across departments. That cross-program pattern aligns with the multidisciplinary nature of the biomedical engineer role.",
          "student_evidence": {
            "total_in_program": 635,
            "with_all_core_skills": 18,
            "top_students": [
              {
                "uuid": "26b4df11-a752-5ff9-9a49-c95d18935376",
                "display_number": 1,
                "primary_focus": "Engineering",
                "courses_completed": 2,
                "gpa": 3.5,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "ENGR 54",
                    "name": "PRINCIPLES OF MATERIALS SCIENCE AND ENGINEERING",
                    "grade": "A",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "ANTH 1",
                    "name": "INTRODUCTION TO BIOLOGICAL ANTHROPOLOGY",
                    "grade": "A",
                    "term": "2024-Spring"
                  }
                ],
                "relevant_skills": [
                  "Anatomy & Physiology",
                  "Biology",
                  "Design"
                ]
              },
              {
                "uuid": "036cd663-860a-57f0-ac18-dc7a5d6c92cb",
                "display_number": 2,
                "primary_focus": "Engineering",
                "courses_completed": 2,
                "gpa": 3.48,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "ART 40",
                    "name": "2-D DESIGN AND COLOR",
                    "grade": "A",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "ANTH 1H",
                    "name": "INTRODUCTION TO BIOLOGICAL ANTHROPOLOGY HONORS",
                    "grade": "A",
                    "term": "2023-Winter"
                  }
                ],
                "relevant_skills": [
                  "Anatomy & Physiology",
                  "Biology",
                  "Design"
                ]
              },
              {
                "uuid": "11ad6cda-ce49-5e1f-b1d1-3d2e8b41c2b5",
                "display_number": 3,
                "primary_focus": "Biology",
                "courses_completed": 6,
                "gpa": 3.44,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "ENGR 54",
                    "name": "PRINCIPLES OF MATERIALS SCIENCE AND ENGINEERING",
                    "grade": "A",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "BIO 69",
                    "name": "FIELD STUDIES: A 21ST CENTURY LOOK AT THE AMERICAN WEST",
                    "grade": "A",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "BIO 7",
                    "name": "STATISTICS AND EXPERIMENTAL DESIGN FOR THE BIOLOGICAL AND HEALTH SCIENCES",
                    "grade": "B",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "BIO 21",
                    "name": "HUMAN ANATOMY AND PHYSIOLOGY",
                    "grade": "A",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "BIO 19",
                    "name": "MARINE BIOLOGY",
                    "grade": "B",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "BIO 12",
                    "name": "HUMAN PHYSIOLOGY",
                    "grade": "A",
                    "term": "2023-Spring"
                  }
                ],
                "relevant_skills": [
                  "Anatomy & Physiology",
                  "Biology",
                  "Design"
                ]
              },
              {
                "uuid": "319772f4-c0c2-5f6d-a8bd-830f94ee2679",
                "display_number": 4,
                "primary_focus": "Engineering",
                "courses_completed": 2,
                "gpa": 3.43,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "ENGR 54",
                    "name": "PRINCIPLES OF MATERIALS SCIENCE AND ENGINEERING",
                    "grade": "A",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "ANTH 1",
                    "name": "INTRODUCTION TO BIOLOGICAL ANTHROPOLOGY",
                    "grade": "A",
                    "term": "2025-Spring"
                  }
                ],
                "relevant_skills": [
                  "Anatomy & Physiology",
                  "Biology",
                  "Design"
                ]
              },
              {
                "uuid": "339136f1-4996-5b8d-8d27-6f263e343b00",
                "display_number": 5,
                "primary_focus": "Biology",
                "courses_completed": 4,
                "gpa": 3.42,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "DR 52",
                    "name": "ENGINEERING DRAWING AND DESIGN",
                    "grade": "A",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "BIO 80",
                    "name": "INTEGRATED BIOLOGY: ORGANISMS TO ECOSYSTEMS",
                    "grade": "B",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "BIO 1",
                    "name": "THE LIFE SCIENCES",
                    "grade": "B",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "BIO 19",
                    "name": "MARINE BIOLOGY",
                    "grade": "B",
                    "term": "2024-Spring"
                  }
                ],
                "relevant_skills": [
                  "Anatomy & Physiology",
                  "Biology",
                  "Design"
                ]
              },
              {
                "uuid": "1a577f62-6951-5ea2-b4af-21dff1ba1ca6",
                "display_number": 6,
                "primary_focus": "Engineering",
                "courses_completed": 2,
                "gpa": 3.42,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "ENGR 54",
                    "name": "PRINCIPLES OF MATERIALS SCIENCE AND ENGINEERING",
                    "grade": "A",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "ANTH 1H",
                    "name": "INTRODUCTION TO BIOLOGICAL ANTHROPOLOGY HONORS",
                    "grade": "C",
                    "term": "2025-Spring"
                  }
                ],
                "relevant_skills": [
                  "Anatomy & Physiology",
                  "Biology",
                  "Design"
                ]
              },
              {
                "uuid": "51aad30f-a836-5ceb-a2c4-28a2e2de8892",
                "display_number": 7,
                "primary_focus": "Engineering",
                "courses_completed": 4,
                "gpa": 3.27,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "ENGR 7",
                    "name": "INTRODUCTION TO ENGINEERING METHODS",
                    "grade": "W",
                    "term": "2022-Fall"
                  },
                  {
                    "code": "IMA 79",
                    "name": "CHARACTER DESIGN AND LAYOUT",
                    "grade": "B",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "ANTH 1",
                    "name": "INTRODUCTION TO BIOLOGICAL ANTHROPOLOGY",
                    "grade": "A",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "PSYC 5H",
                    "name": "PSYCHOLOGICAL ASPECTS OF HUMAN SEXUALITY HONORS",
                    "grade": "A",
                    "term": "2024-Fall"
                  }
                ],
                "relevant_skills": [
                  "Anatomy & Physiology",
                  "Biology",
                  "Design"
                ]
              },
              {
                "uuid": "4ef36f32-6b27-5c7a-a435-b6162ff0ace7",
                "display_number": 8,
                "primary_focus": "Biology",
                "courses_completed": 4,
                "gpa": 3.24,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "DMP 130",
                    "name": "SOLIDWORKS",
                    "grade": "A",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "BIO 3",
                    "name": "HUMANS AND THE BIOLOGICAL WORLD",
                    "grade": "A",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "BIO 19",
                    "name": "MARINE BIOLOGY",
                    "grade": "A",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "BIO 12",
                    "name": "HUMAN PHYSIOLOGY",
                    "grade": "A",
                    "term": "2024-Fall"
                  }
                ],
                "relevant_skills": [
                  "Anatomy & Physiology",
                  "Biology",
                  "Design"
                ]
              },
              {
                "uuid": "1c75c3a5-1ef8-56f9-b332-293d452183d9",
                "display_number": 9,
                "primary_focus": "Biology",
                "courses_completed": 5,
                "gpa": 3.24,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "ENGR 54",
                    "name": "PRINCIPLES OF MATERIALS SCIENCE AND ENGINEERING",
                    "grade": "A",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "BIO 81H",
                    "name": "INTEGRATED BIOLOGY: FROM DNA TO ORGANISMS",
                    "grade": "C",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "BIO 1H",
                    "name": "THE LIFE SCIENCES HONORS",
                    "grade": "A",
                    "term": "2022-Fall"
                  },
                  {
                    "code": "BIO 19H",
                    "name": "MARINE BIOLOGY HONORS",
                    "grade": "B",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "BIO 12",
                    "name": "HUMAN PHYSIOLOGY",
                    "grade": "P",
                    "term": "2023-Spring"
                  }
                ],
                "relevant_skills": [
                  "Anatomy & Physiology",
                  "Biology",
                  "Design"
                ]
              },
              {
                "uuid": "fece2f25-a415-5f41-83b6-b69c70de8074",
                "display_number": 10,
                "primary_focus": "Biology",
                "courses_completed": 7,
                "gpa": 3.13,
                "matching_skills": 3,
                "enrollments": [
                  {
                    "code": "ART 40",
                    "name": "2-D DESIGN AND COLOR",
                    "grade": "B",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "BIO 69",
                    "name": "FIELD STUDIES: A 21ST CENTURY LOOK AT THE AMERICAN WEST",
                    "grade": "B",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "BIO 81",
                    "name": "INTEGRATED BIOLOGY: FROM DNA TO ORGANISMS",
                    "grade": "B",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "BIO 80H",
                    "name": "INTEGRATED BIOLOGY: ORGANISMS TO ECOSYSTEMS HONORS",
                    "grade": "B",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "BIO 1L",
                    "name": "THE LIFE SCIENCES LABORATORY",
                    "grade": "A",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "BIO 19H",
                    "name": "MARINE BIOLOGY HONORS",
                    "grade": "B",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "BIO 19",
                    "name": "MARINE BIOLOGY",
                    "grade": "B",
                    "term": "2024-Winter"
                  }
                ],
                "relevant_skills": [
                  "Anatomy & Physiology",
                  "Biology",
                  "Design"
                ]
              }
            ]
          }
        },
        "roadmap": "A potential starting point is a conversation between the Engineering department chair and Confluent's workforce or HR team to define internship scope and site capacity. A 12-16 week structure mapped to existing cooperative work experience units could accommodate a first cohort within one to two semesters. Targeting students with concurrent enrollment in Engineering and Biology coursework could strengthen cohort alignment for an initial placement of 5-10 students.",
        "selected_occupations": [],
        "advisory_thesis": "",
        "agenda_topics": []
      },
      "engagementType": "internship",
      "collegeId": "Irvine Valley College",
      "savedAt": "2026-04-20T00:00:00.000Z",
      "status": "saved",
      "schemaVersion": 8
    },
    {
      "id": "seed-irvinevalley-curriculum-01",
      "proposal": {
        "employer": "Applied Medical Resources Corporation",
        "sector": "Manufacturing",
        "partnership_type": "Curriculum Co-Design",
        "selected_occupation": "Software Developers",
        "selected_soc_code": "15-1252",
        "core_skills": [
          "Programming",
          "Algorithms",
          "Software Development"
        ],
        "gap_skill": "Regulatory Compliance Software Development (FDA 21 CFR Part 11)",
        "regions": [
          "Orange County"
        ],
        "opportunity": "Irvine Valley College's Computer Science department is well-positioned to deepen its alignment with Applied Medical Resources through a co-design partnership focused on regulatory compliance software development. The department builds strong programming and algorithms foundations across its curriculum. Collaboration with Applied Medical Resources could strengthen preparation in FDA 21 CFR Part 11 requirements, a domain-specific area central to software roles in medical device manufacturing.",
        "opportunity_evidence": [
          {
            "title": "Software Developers",
            "soc_code": "15-1252",
            "annual_wage": 154250,
            "employment": 18210,
            "annual_openings": 1050,
            "growth_rate": 0.029692514
          }
        ],
        "justification": {
          "curriculum_composition": "The Computer Science department is the right home for this partnership, with coursework in programming and algorithms distributed across multiple courses that serve this occupation well. Software development for regulated medical device environments carries compliance obligations that go beyond general programming practice. Regulatory compliance software development under FDA 21 CFR Part 11 is an area that could be more rigorously developed through direct collaboration with Applied Medical Resources.",
          "curriculum_evidence": [
            {
              "department": "Computer Science",
              "courses": [
                {
                  "code": "CS 1",
                  "name": "INTRODUCTION TO COMPUTER SYSTEMS",
                  "description": "This course provides an overview of computer information systems and introduces hardware, software, networking, and Internet terminology. The course introduces Windows and Microsoft Office software, focusing particularly on spreadsheet and database applications. It also introduces program development and programming languages. Students write and execute elementary programs in a programming language. Credit may be earned in CS 1 or 1H, but not both.C-ID: BUS 140 and ITIS 120 C-ID: BUS 140 and ITIS 120 NR",
                  "learning_outcomes": [],
                  "skills": [
                    "Programming"
                  ]
                },
                {
                  "code": "CS 10",
                  "name": "INTRODUCTION TO PROGRAMMING USING PYTHON",
                  "description": "This course provides an introduction to computers and programming using Python. The course focuses on planning, creating and debugging programs using the grammar and syntax of the Python language. Topics include types and variables, input and output statements, control statements, functions and parameter passing, looping structures, text files, classes, lists, tuples, sets, dictionaries, algorithms, and graphics. C-ID: COMP 112 NR",
                  "learning_outcomes": [],
                  "skills": [
                    "Algorithms",
                    "Programming"
                  ]
                },
                {
                  "code": "CS 1H",
                  "name": "INTRODUCTION TO COMPUTER SYSTEMS HONORS",
                  "description": "This course provides an overview of computer information systems and introduces hardware, software, networking, and Internet terminology. The course introduces Windows and Microsoft Office software, focusing particularly on spreadsheet and database applications. It also introduces program development and programming languages. Students write and execute elementary programs in a programming language. Credit may be earned in CS 1 or 1H, but not both.C-ID: BUS 140 and ITIS 120 C-ID: BUS 140 and ITIS 120 NR",
                  "learning_outcomes": [],
                  "skills": [
                    "Programming"
                  ]
                },
                {
                  "code": "CS 30",
                  "name": "VISUAL BASIC PROGRAMMING",
                  "description": "This course focuses on the development of programming applications using Visual Basic. The course covers Visual Basic structure, syntax and operating procedures, as well as design and programming techniques for event-driven and object-oriented programs in Visual Basic. NR",
                  "learning_outcomes": [],
                  "skills": [
                    "Programming"
                  ]
                },
                {
                  "code": "CS 36",
                  "name": "C PROGRAMMING",
                  "description": "This course introduces the C programming language, focusing on how to create, execute, and debug C programs. Topics include input and output statements; control statements; random numbers; functions and parameter passing; recursion; loops; arrays; structures; text, binary, and header files; pointers; and linked lists. NR",
                  "learning_outcomes": [],
                  "skills": [
                    "Algorithms",
                    "Programming"
                  ]
                },
                {
                  "code": "CS 40B",
                  "name": "COMPUTER ORGANIZATION AND ASSEMBLY LANGUAGE II",
                  "description": "This course is a continuation of Computer Science 40A. Students will further study computer organization and advanced assembly language programming. The course will also examine logical expressions, arrays, procedures, decimal numbers and fractions, floating point numbers, dynamic storage, strings, input/output, signed numbers, and numeric approximations. C-ID: COMP 142. NR",
                  "learning_outcomes": [],
                  "skills": [
                    "Algorithms"
                  ]
                },
                {
                  "code": "CS 41",
                  "name": "DATA STRUCTURES",
                  "description": "This course examines the basic concepts of data structures and related algorithms. Students use arrays, structures, stacks, queues, linked lists, trees, graphs, and tables to design algorithms and then write complete programs to implement these algorithms. Recursion, searching, sorting, timing and space analysis for algorithms, and memory management are also discussed. C-ID: COMP 132. NR",
                  "learning_outcomes": [],
                  "skills": [
                    "Algorithms",
                    "Programming"
                  ]
                }
              ],
              "aligned_skills": [
                "Algorithms",
                "Programming"
              ]
            }
          ],
          "student_composition": "Students in the Computer Science department are building the programming and algorithmic foundations that software developer roles at Applied Medical Resources require. They represent a strong candidate pool for a co-design effort that deepens their preparation for regulated software environments.",
          "student_evidence": {
            "total_in_program": 14,
            "with_all_core_skills": 0,
            "top_students": [
              {
                "uuid": "e2a1ec09-9718-5853-854f-221a2f21c877",
                "display_number": 1,
                "primary_focus": "Computer Science",
                "courses_completed": 2,
                "gpa": 3.5,
                "matching_skills": 2,
                "enrollments": [
                  {
                    "code": "CS 41",
                    "name": "DATA STRUCTURES",
                    "grade": "B",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "CS 1",
                    "name": "INTRODUCTION TO COMPUTER SYSTEMS",
                    "grade": "A",
                    "term": "2025-Spring"
                  }
                ],
                "relevant_skills": [
                  "Algorithms",
                  "Programming"
                ]
              },
              {
                "uuid": "74851fb1-9e4a-5403-b2c4-b58064bab7df",
                "display_number": 2,
                "primary_focus": "Computer Science",
                "courses_completed": 3,
                "gpa": 3.38,
                "matching_skills": 2,
                "enrollments": [
                  {
                    "code": "CS 1H",
                    "name": "INTRODUCTION TO COMPUTER SYSTEMS HONORS",
                    "grade": "A",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "CS 1",
                    "name": "INTRODUCTION TO COMPUTER SYSTEMS",
                    "grade": "D",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "CS 6B",
                    "name": "COMPUTER DISCRETE MATHEMATICS II",
                    "grade": "C",
                    "term": "2025-Spring"
                  }
                ],
                "relevant_skills": [
                  "Algorithms",
                  "Programming"
                ]
              },
              {
                "uuid": "a6316ef5-c811-5e17-ba65-441854274f2a",
                "display_number": 3,
                "primary_focus": "Computer Science",
                "courses_completed": 6,
                "gpa": 3.05,
                "matching_skills": 2,
                "enrollments": [
                  {
                    "code": "CS 41",
                    "name": "DATA STRUCTURES",
                    "grade": "B",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "CS 1",
                    "name": "INTRODUCTION TO COMPUTER SYSTEMS",
                    "grade": "F",
                    "term": "2022-Fall"
                  },
                  {
                    "code": "CS 40B",
                    "name": "COMPUTER ORGANIZATION AND ASSEMBLY LANGUAGE II",
                    "grade": "B",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "CS 6B",
                    "name": "COMPUTER DISCRETE MATHEMATICS II",
                    "grade": "W",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "MATH 6A",
                    "name": "COMPUTER DISCRETE MATHEMATICS I",
                    "grade": "A",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "CS 6A",
                    "name": "COMPUTER DISCRETE MATHEMATICS I",
                    "grade": "B",
                    "term": "2023-Winter"
                  }
                ],
                "relevant_skills": [
                  "Algorithms",
                  "Programming"
                ]
              },
              {
                "uuid": "2ccd292d-3da9-5c59-bbdb-3f2b64d1769b",
                "display_number": 4,
                "primary_focus": "Computer Science",
                "courses_completed": 5,
                "gpa": 2.36,
                "matching_skills": 2,
                "enrollments": [
                  {
                    "code": "CS 41",
                    "name": "DATA STRUCTURES",
                    "grade": "A",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "CS 10",
                    "name": "INTRODUCTION TO PROGRAMMING USING PYTHON",
                    "grade": "D",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "CS 40B",
                    "name": "COMPUTER ORGANIZATION AND ASSEMBLY LANGUAGE II",
                    "grade": "F",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "CS 6B",
                    "name": "COMPUTER DISCRETE MATHEMATICS II",
                    "grade": "W",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "CS 6A",
                    "name": "COMPUTER DISCRETE MATHEMATICS I",
                    "grade": "B",
                    "term": "2023-Fall"
                  }
                ],
                "relevant_skills": [
                  "Algorithms",
                  "Programming"
                ]
              },
              {
                "uuid": "32897b28-18a6-5880-8b37-df2d29594324",
                "display_number": 5,
                "primary_focus": "Computer Science",
                "courses_completed": 5,
                "gpa": 1.73,
                "matching_skills": 2,
                "enrollments": [
                  {
                    "code": "CS 36",
                    "name": "C PROGRAMMING",
                    "grade": "A",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "CS 10",
                    "name": "INTRODUCTION TO PROGRAMMING USING PYTHON",
                    "grade": "W",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "CS 1",
                    "name": "INTRODUCTION TO COMPUTER SYSTEMS",
                    "grade": "B",
                    "term": "2024-Spring"
                  },
                  {
                    "code": "CS 6B",
                    "name": "COMPUTER DISCRETE MATHEMATICS II",
                    "grade": "B",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "CS 6A",
                    "name": "COMPUTER DISCRETE MATHEMATICS I",
                    "grade": "F",
                    "term": "2024-Spring"
                  }
                ],
                "relevant_skills": [
                  "Algorithms",
                  "Programming"
                ]
              },
              {
                "uuid": "75b27edb-3901-595f-a209-8c983f5f7feb",
                "display_number": 6,
                "primary_focus": "Computer Science",
                "courses_completed": 4,
                "gpa": 3.0,
                "matching_skills": 1,
                "enrollments": [
                  {
                    "code": "CS 36",
                    "name": "C PROGRAMMING",
                    "grade": "W",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "CS 30",
                    "name": "VISUAL BASIC PROGRAMMING",
                    "grade": "A",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "CS 1H",
                    "name": "INTRODUCTION TO COMPUTER SYSTEMS HONORS",
                    "grade": "A",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "MATH 6A",
                    "name": "COMPUTER DISCRETE MATHEMATICS I",
                    "grade": "F",
                    "term": "2024-Fall"
                  }
                ],
                "relevant_skills": [
                  "Programming"
                ]
              },
              {
                "uuid": "a97f5b0f-5ad2-5587-a164-104f5a56eb21",
                "display_number": 7,
                "primary_focus": "Computer Science",
                "courses_completed": 3,
                "gpa": 2.67,
                "matching_skills": 1,
                "enrollments": [
                  {
                    "code": "CS 1H",
                    "name": "INTRODUCTION TO COMPUTER SYSTEMS HONORS",
                    "grade": "A",
                    "term": "2025-Spring"
                  },
                  {
                    "code": "CS 1",
                    "name": "INTRODUCTION TO COMPUTER SYSTEMS",
                    "grade": "F",
                    "term": "2024-Winter"
                  },
                  {
                    "code": "CS 6B",
                    "name": "COMPUTER DISCRETE MATHEMATICS II",
                    "grade": "W",
                    "term": "2025-Spring"
                  }
                ],
                "relevant_skills": [
                  "Programming"
                ]
              },
              {
                "uuid": "5a14c9a0-16c8-51f0-a214-4dc9d54b295d",
                "display_number": 8,
                "primary_focus": "Computer Science",
                "courses_completed": 4,
                "gpa": 2.5,
                "matching_skills": 1,
                "enrollments": [
                  {
                    "code": "CS 30",
                    "name": "VISUAL BASIC PROGRAMMING",
                    "grade": "D",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "CS 1H",
                    "name": "INTRODUCTION TO COMPUTER SYSTEMS HONORS",
                    "grade": "F",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "CS 6B",
                    "name": "COMPUTER DISCRETE MATHEMATICS II",
                    "grade": "A",
                    "term": "2024-Fall"
                  },
                  {
                    "code": "CS 6A",
                    "name": "COMPUTER DISCRETE MATHEMATICS I",
                    "grade": "F",
                    "term": "2023-Winter"
                  }
                ],
                "relevant_skills": [
                  "Algorithms"
                ]
              },
              {
                "uuid": "1070d41a-a302-5736-a1f0-aa41965fa70f",
                "display_number": 9,
                "primary_focus": "Computer Science",
                "courses_completed": 4,
                "gpa": 2.29,
                "matching_skills": 1,
                "enrollments": [
                  {
                    "code": "CS 40B",
                    "name": "COMPUTER ORGANIZATION AND ASSEMBLY LANGUAGE II",
                    "grade": "B",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "CS 6B",
                    "name": "COMPUTER DISCRETE MATHEMATICS II",
                    "grade": "F",
                    "term": "2023-Spring"
                  },
                  {
                    "code": "MATH 6A",
                    "name": "COMPUTER DISCRETE MATHEMATICS I",
                    "grade": "F",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "CS 6A",
                    "name": "COMPUTER DISCRETE MATHEMATICS I",
                    "grade": "A",
                    "term": "2023-Fall"
                  }
                ],
                "relevant_skills": [
                  "Algorithms"
                ]
              },
              {
                "uuid": "ccd5db2c-1353-58c4-b0c6-a4b72eec4262",
                "display_number": 10,
                "primary_focus": "Computer Science",
                "courses_completed": 4,
                "gpa": 1.93,
                "matching_skills": 1,
                "enrollments": [
                  {
                    "code": "CS 36",
                    "name": "C PROGRAMMING",
                    "grade": "F",
                    "term": "2022-Winter"
                  },
                  {
                    "code": "CS 41",
                    "name": "DATA STRUCTURES",
                    "grade": "W",
                    "term": "2023-Fall"
                  },
                  {
                    "code": "CS 6B",
                    "name": "COMPUTER DISCRETE MATHEMATICS II",
                    "grade": "F",
                    "term": "2023-Winter"
                  },
                  {
                    "code": "CS 6A",
                    "name": "COMPUTER DISCRETE MATHEMATICS I",
                    "grade": "A",
                    "term": "2023-Spring"
                  }
                ],
                "relevant_skills": [
                  "Algorithms"
                ]
              }
            ]
          }
        },
        "roadmap": "A working group between the Computer Science department and Applied Medical Resources' software engineering leadership could evaluate how FDA 21 CFR Part 11 compliance requirements might be introduced into existing software development coursework. A revised module or course component could be piloted within the next catalog cycle.",
        "selected_occupations": [],
        "advisory_thesis": "",
        "agenda_topics": []
      },
      "engagementType": "curriculum_codesign",
      "collegeId": "Irvine Valley College",
      "savedAt": "2026-04-20T00:00:00.000Z",
      "status": "saved",
      "schemaVersion": 8
    }
  ]
};

// Keyed by college display name. Auto-fills any featured college that
// lacks a seeded entry with an empty array so downstream lookups never
// return undefined for a valid college.
export const SEEDED_PARTNERSHIPS: Record<string, SavedProposal[]> = {
  ...Object.fromEntries(FEATURED_NAMES.map((name) => [name, [] as SavedProposal[]])),
  ...SEEDED_BY_NAME,
};

export function getSeededProposals(collegeName: string): SavedProposal[] {
  return SEEDED_PARTNERSHIPS[collegeName] ?? [];
}
