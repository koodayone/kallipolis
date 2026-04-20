// Curated SWP (Strong Workforce) project artifacts shipped with the atlas
// bundle for preview mode. Each entry's `partnershipId` must reference an
// id in SEEDED_PARTNERSHIPS so the Manage Mode view can resolve the
// originating partnership.
//
// Keyed by college *display name* to match the existing
// `saveSwpProject(school.name, ...)` convention.

import type { SavedSwpProject } from "@/college-atlas/strong-workforce/savedSwpProjects";
import { CALIFORNIA_COLLEGES } from "@/state-atlas/californiaColleges";
import { FEATURED_COLLEGES } from "@/state-atlas/featuredColleges";

const FEATURED_NAMES = CALIFORNIA_COLLEGES.filter((c) =>
  FEATURED_COLLEGES.has(c.id),
).map((c) => c.name);

const SEEDED_BY_NAME: Record<string, SavedSwpProject[]> = {
  "Shasta College": [
    {
      "id": "seed-swp-shasta-01",
      "project": {
        "employer": "Mayers Memorial Hospital",
        "college": "Shasta College",
        "partnership_type": "Internship Pipeline",
        "sections": [
          {
            "key": "project_name",
            "title": "Project Name",
            "content": "Mayers Memorial Hospital Internship Pipeline \u2014 Registered Nursing",
            "char_limit": 100
          },
          {
            "key": "project_description",
            "title": "Project Description",
            "content": "Shasta College will establish a structured internship pipeline with Mayers Memorial Hospital to improve career readiness and job placement for Registered Nursing students. This partnership will connect students to supervised hospital placements that develop the core clinical competencies required for regional employment as registered nurses.",
            "char_limit": 500
          },
          {
            "key": "rationale",
            "title": "Project Rationale",
            "content": "Regional demand for registered nurses (SOC 29-1141) substantially exceeds the annual supply of program completions, producing a measurable gap this project directly addresses. Annual openings in the Far North region far outpace projected completions across the aligned TOP codes \u2014 Registered Nursing (123010), Licensed Vocational Nursing (123020), and Medical Assisting (120800) \u2014 leaving a gap of nearly 380 positions annually unfilled by local program output.\n\nMayers Memorial Hospital is the right employer partner for this gap. As a regional hospital in the Far North, it operates in the same labor market these students will enter and offers direct exposure to the patient care workflows that define the registered nurse role. A structured 8\u201316 week internship placement will allow students to apply the nursing process, medication administration, and patient assessment skills built across the Registered Nursing and Allied Health programs in a supervised clinical environment.\n\nThe curriculum alignment is already in place. Courses across the Registered Nursing department map directly to the core competencies this employer requires. This partnership is not a new programmatic direction \u2014 it is a structured bridge between existing preparation and regional employment demand.",
            "char_limit": 3000
          },
          {
            "key": "student_impact",
            "title": "Student Impact",
            "content": "Up to 1,519 students enrolled across the Registered Nursing, Vocational Nursing, and Allied Health departments are in the pipeline this project serves. These students are enrolled in courses that develop the patient assessment, nursing process, and medication administration skills required by Mayers Memorial Hospital for registered nursing roles.",
            "char_limit": 600
          },
          {
            "key": "vision_goal",
            "title": "Vision for Success Goal",
            "content": "This project advances the Vision for Success Workforce goal. The internship pipeline will increase the number of students who complete programs with verified employer connections and transition directly into regional healthcare employment.",
            "char_limit": 400
          },
          {
            "key": "objective",
            "title": "Objective",
            "content": "Objective Type: Improve career readiness and job placement\n\nShasta College will place an initial cohort of Registered Nursing students in structured internships at Mayers Memorial Hospital within two semesters, with success measured by SWP metrics: Employed in Field of Study and Median Annual Earnings. This objective directly addresses the registered nurse supply gap in the Far North region by increasing the number of locally trained candidates with verified clinical experience and employer relationships at the point of hire.",
            "char_limit": 800
          },
          {
            "key": "activity",
            "title": "Activity",
            "content": "The Registered Nursing department chair will convene with Mayers Memorial Hospital nursing leadership to establish site capacity, supervision structures, and placement eligibility criteria. Coordination meetings will occur on a defined semester cadence beginning in the current or immediately following term. The first student cohort will be placed within two semesters, aligned to existing practicum or work experience course sequences in the Registered Nursing program.",
            "char_limit": 600
          }
        ],
        "lmi_context": {
          "occupations": [
            {
              "soc_code": "29-1141",
              "title": "Registered Nurses",
              "annual_wage": 133680,
              "employment": 6980,
              "growth_rate": 0.066071046,
              "annual_openings": 460,
              "education_level": null,
              "region": "FN"
            }
          ],
          "supply_estimates": [
            {
              "top_code": "120800",
              "top_title": "Medical Assisting",
              "award_level": "Certificate (16<30 semester units)",
              "annual_projected_supply": 17.0
            },
            {
              "top_code": "123010",
              "top_title": "Registered Nursing",
              "award_level": "Associate Degree",
              "annual_projected_supply": 54.0
            },
            {
              "top_code": "123020",
              "top_title": "Licensed Vocational Nursing",
              "award_level": "Certificate (30<60 semester units)",
              "annual_projected_supply": 9.67
            }
          ],
          "department_enrollments": [
            {
              "department": "Registered Nursing",
              "student_count": 949
            },
            {
              "department": "ALLIED HEALTH",
              "student_count": 474
            },
            {
              "department": "Vocational Nursing",
              "student_count": 96
            }
          ],
          "total_demand": 460,
          "total_supply": 80.67,
          "gap": 379.33,
          "gap_eligible": true
        },
        "goal": "Workforce",
        "metrics": [
          "Employed in Field of Study",
          "Median Annual Earnings"
        ]
      },
      "partnershipId": "seed-shasta-internship-01",
      "collegeId": "Shasta College",
      "savedAt": "2026-04-20T00:00:00.000Z"
    }
  ],
  "College of the Sequoias": [
    {
      "id": "seed-swp-sequoias-01",
      "project": {
        "employer": "Saputo Cheese USA",
        "college": "College of the Sequoias",
        "partnership_type": "Internship Pipeline",
        "sections": [
          {
            "key": "project_name",
            "title": "Project Name",
            "content": "Saputo Cheese USA Internship Pipeline \u2014 Food Science Technicians",
            "char_limit": 100
          },
          {
            "key": "project_description",
            "title": "Project Description",
            "content": "This project establishes a structured internship pipeline between College of the Sequoias and Saputo Cheese USA to place students in Food Science Technician roles. The Agriculture, Chemistry, and Biology departments will coordinate to prepare and recruit an initial cohort, improving career readiness and job placement outcomes in the Central Valley food manufacturing sector.",
            "char_limit": 500
          },
          {
            "key": "rationale",
            "title": "Project Rationale",
            "content": "Regional demand for Food Science Technicians (SOC 19-4013) substantially exceeds current program supply. Annual job openings in the Central Valley/Mother Lode region are not being met by projected completions from the closest aligned program, Chemistry, General (TOP 190500), creating a measurable gap that this project directly addresses.\n\nSaputo Cheese USA operates in this regional labor market and requires the core competencies \u2014 food safety, food production, and laboratory techniques \u2014 that College of the Sequoias students are already developing across the Agriculture, Chemistry, and Biology departments. A structured internship placement at Saputo provides the applied, site-based experience that converts academic preparation into job-ready competency.\n\nThis partnership is the appropriate response to the gap because it connects an active regional employer with an existing multi-department student pipeline, accelerating placement into occupations where demand consistently outpaces local supply.",
            "char_limit": 3000
          },
          {
            "key": "student_impact",
            "title": "Student Impact",
            "content": "Up to 4,872 students enrolled in the Agriculture, Chemistry, and Biology departments represent the eligible pipeline, as these programs develop the laboratory techniques, food production, and food safety skills required for Food Science Technician roles at Saputo. An initial cohort of 5\u201310 students will be recruited for placement within the first two semesters of implementation.",
            "char_limit": 600
          },
          {
            "key": "vision_goal",
            "title": "Vision for Success Goal",
            "content": "This project addresses the Workforce Vision for Success goal. It will increase the number of students who gain employment in their field of study and improve median annual earnings outcomes by connecting program completers to a regional employer with documented, sustained hiring demand.",
            "char_limit": 400
          },
          {
            "key": "objective",
            "title": "Objective",
            "content": "Objective Type: Improve career readiness and job placement\n\nCollege of the Sequoias will place an initial cohort of students into a credit-bearing internship at Saputo Cheese USA within two semesters, with success measured by the SWP metrics Employed in Field of Study and Median Annual Earnings. This objective directly addresses the regional supply gap in Food Science Technicians by increasing the number of program completers who transition into occupied roles within the Central Valley food manufacturing sector.",
            "char_limit": 800
          }
        ],
        "lmi_context": {
          "occupations": [
            {
              "soc_code": "19-4013",
              "title": "Food Science Technicians",
              "annual_wage": 47950,
              "employment": 1260,
              "growth_rate": 0.024915091,
              "annual_openings": 190,
              "education_level": null,
              "region": "CVML"
            }
          ],
          "supply_estimates": [
            {
              "top_code": "190500",
              "top_title": "Chemistry, General",
              "award_level": "Associate Degree for Transfer",
              "annual_projected_supply": 4.33
            }
          ],
          "department_enrollments": [
            {
              "department": "Chemistry",
              "student_count": 2693
            },
            {
              "department": "Biology",
              "student_count": 1920
            },
            {
              "department": "Agriculture",
              "student_count": 259
            }
          ],
          "total_demand": 190,
          "total_supply": 4.33,
          "gap": 185.67,
          "gap_eligible": true
        },
        "goal": "Workforce",
        "metrics": [
          "Employed in Field of Study",
          "Median Annual Earnings"
        ]
      },
      "partnershipId": "seed-sequoias-internship-01",
      "collegeId": "College of the Sequoias",
      "savedAt": "2026-04-20T00:00:00.000Z"
    }
  ],
  "College of the Desert": [
    {
      "id": "seed-swp-desert-01",
      "project": {
        "employer": "Collins Aerospace",
        "college": "College of the Desert",
        "partnership_type": "Internship Pipeline",
        "sections": [
          {
            "key": "project_name",
            "title": "Project Name",
            "content": "Collins Aerospace Internship Pipeline \u2014 Software Development",
            "char_limit": 100
          },
          {
            "key": "project_description",
            "title": "Project Description",
            "content": "College of the Desert will partner with Collins Aerospace to establish a structured internship pipeline connecting Computer Information Systems and Computer Science students to software development roles in the aerospace and defense sector. This partnership targets improved career readiness and job placement in a high-wage, high-demand occupational cluster.",
            "char_limit": 500
          },
          {
            "key": "rationale",
            "title": "Project Rationale",
            "content": "Regional demand for Software Developers (SOC 15-1252) substantially exceeds the annual supply of program completers across aligned TOP codes (070200, 070600, 070810), creating a measurable gap this project directly addresses.\n\nCollins Aerospace represents an employment destination for graduates with software development, programming, and algorithms skills \u2014 the same skills built across the Computer Information Systems and Computer Science departments. An internship pipeline creates a structured pathway from instruction to employment, converting existing coursework into verified work-based learning outcomes.\n\nThe gap between regional openings and annual completions confirms that scaling placement activity is a higher-leverage response than curriculum development alone. This partnership is the right response because it connects an employer with active hiring demand to a college with the academic infrastructure to prepare and credential students for that demand.",
            "char_limit": 3000
          },
          {
            "key": "student_impact",
            "title": "Student Impact",
            "content": "Up to 1,822 students enrolled in the Computer Information Systems and Computer Science departments represent the pipeline from which internship cohorts will be drawn. These students are actively developing the software development, programming, and algorithms skills required for Software Developer roles at Collins Aerospace.",
            "char_limit": 600
          },
          {
            "key": "vision_goal",
            "title": "Vision for Success Goal",
            "content": "This project advances the SWP Workforce goal under Vision for Success. By connecting students to a structured internship with a regional employer, the project increases the number of students who achieve employment in their field of study at high-wage outcomes.",
            "char_limit": 400
          },
          {
            "key": "objective",
            "title": "Objective",
            "content": "Objective Type: Improve career readiness and job placement\n\nCollege of the Desert will place an initial cohort of students into paid internships at Collins Aerospace, tracking outcomes against the SWP metrics of Employed in Field of Study and Median Annual Earnings. Cohort placement counts and post-program employment data will serve as the primary quantifiable measures of progress.\n\nThis objective directly addresses the regional supply gap in Software Developers by converting enrolled students into work-ready candidates prepared to fill high-demand roles in the Inland Empire and Desert region.",
            "char_limit": 800
          },
          {
            "key": "activity",
            "title": "Activity",
            "content": "The Computer Information Systems or Computer Science department chair will convene with Collins Aerospace's workforce development or university relations team to establish internship site capacity, project scope, and cohort criteria. Coordination meetings will occur on a recurring basis each semester to align academic calendars with internship cycles. The first cohort placement is targeted within two semesters of project launch, with students earning credit through existing cooperative education or work experience course sequences.",
            "char_limit": 600
          }
        ],
        "lmi_context": {
          "occupations": [
            {
              "soc_code": "15-1252",
              "title": "Software Developers",
              "annual_wage": 135210,
              "employment": 4860,
              "growth_rate": 0.126706091,
              "annual_openings": 390,
              "education_level": null,
              "region": "IE/D"
            }
          ],
          "supply_estimates": [
            {
              "top_code": "070200",
              "top_title": "Computer Information Systems",
              "award_level": "Associate Degree",
              "annual_projected_supply": 5.67
            },
            {
              "top_code": "070200",
              "top_title": "Computer Information Systems",
              "award_level": "Certificate (30<60 semester units)",
              "annual_projected_supply": 1.0
            },
            {
              "top_code": "070600",
              "top_title": "Computer Science (transfer)",
              "award_level": "Associate Degree for Transfer",
              "annual_projected_supply": 13.67
            },
            {
              "top_code": "070810",
              "top_title": "Computer Networking",
              "award_level": "Associate Degree",
              "annual_projected_supply": 10.33
            }
          ],
          "department_enrollments": [
            {
              "department": "Computer Information Systems",
              "student_count": 1060
            },
            {
              "department": "Computer Science",
              "student_count": 762
            }
          ],
          "total_demand": 390,
          "total_supply": 30.67,
          "gap": 359.33,
          "gap_eligible": true
        },
        "goal": "Workforce",
        "metrics": [
          "Employed in Field of Study",
          "Median Annual Earnings"
        ]
      },
      "partnershipId": "seed-desert-internship-01",
      "collegeId": "College of the Desert",
      "savedAt": "2026-04-20T00:00:00.000Z"
    }
  ],
  "Oxnard College": [
    {
      "id": "seed-swp-oxnard-01",
      "project": {
        "employer": "Technicolor",
        "college": "Oxnard College",
        "partnership_type": "Internship Pipeline",
        "sections": [
          {
            "key": "project_name",
            "title": "Project Name",
            "content": "Technicolor Internship Pipeline \u2013 Audio and Video Technicians",
            "char_limit": 100
          },
          {
            "key": "project_description",
            "title": "Project Description",
            "content": "Oxnard College will establish a structured internship pipeline with Technicolor to place students from its film, media, music, and art programs into professional audio and video production environments, improving career readiness and job placement in the Audio and Video Technicians occupation.",
            "char_limit": 500
          },
          {
            "key": "rationale",
            "title": "Project Rationale",
            "content": "Regional demand for Audio and Video Technicians (SOC 27-4011) exceeds the annual supply of program completions from Television and related programs (TOP 060420), producing a measurable gap that limits the region's ability to fill open positions with locally trained workers. The LMI data confirms this demand-supply imbalance and establishes funding eligibility.\n\nTechnicolor's post-production and content distribution operations in the Los Angeles region represent direct, accessible industry demand for the skills Oxnard College already develops. The Film, Television, and Electronic Media, Music, and Art + Design departments collectively prepare students in audio production, video production, and equipment operation \u2014 the core competencies required for placement at Technicolor.\n\nA structured internship partnership is the appropriate response because it converts existing academic preparation into verified work-based learning, accelerates student entry into the occupation, and strengthens the pipeline between Oxnard College completers and regional employer demand.",
            "char_limit": 3000
          },
          {
            "key": "student_impact",
            "title": "Student Impact",
            "content": "This project will positively impact approximately 2,035 students enrolled in the Film, Television, and Electronic Media, Music, and Art + Design departments, whose coursework directly develops the audio production, video production, and equipment operation skills required for internship placement at Technicolor.",
            "char_limit": 600
          },
          {
            "key": "vision_goal",
            "title": "Vision for Success Goal",
            "content": "This project addresses the Vision for Success Workforce goal. It will increase the number of students who complete career-aligned education and transition into employment in their field of study.",
            "char_limit": 400
          },
          {
            "key": "objective",
            "title": "Objective",
            "content": "Objective Type: Improve career readiness and job placement\n\nOxnard College will establish a credit-bearing internship placement with Technicolor and place an initial cohort of students within two semesters of project launch, with success measured by SWP metrics for Employed in Field of Study and Median Annual Earnings. This objective directly addresses the regional gap between annual job openings in Audio and Video Technicians (SOC 27-4011) and annual completions in Television programs (TOP 060420).",
            "char_limit": 800
          },
          {
            "key": "activity",
            "title": "Activity",
            "content": "The Film, Television, and Electronic Media department chair will convene with Technicolor's workforce or production operations team to establish site capacity and define the scope of the first cohort. Coordination meetings will occur on a semester cadence beginning in the first project term to align placement timelines with existing work experience and cooperative education course schedules. The internship structure will target an 8-16 week placement duration to fulfill credit requirements and deliver meaningful industry exposure.",
            "char_limit": 600
          }
        ],
        "lmi_context": {
          "occupations": [
            {
              "soc_code": "27-4011",
              "title": "Audio and Video Technicians",
              "annual_wage": 54260,
              "employment": 300,
              "growth_rate": 0.048543414,
              "annual_openings": 30,
              "education_level": null,
              "region": "SCC"
            }
          ],
          "supply_estimates": [
            {
              "top_code": "060420",
              "top_title": "Television (including combined TV/film/video)",
              "award_level": "Certificate (16<30 semester units)",
              "annual_projected_supply": 4.33
            },
            {
              "top_code": "060420",
              "top_title": "Television (including combined TV/film/video)",
              "award_level": "Associate Degree for Transfer",
              "annual_projected_supply": 15.0
            },
            {
              "top_code": "060420",
              "top_title": "Television (including combined TV/film/video)",
              "award_level": "Associate Degree",
              "annual_projected_supply": 6.67
            }
          ],
          "department_enrollments": [
            {
              "department": "Music",
              "student_count": 1005
            },
            {
              "department": "Film, Television, and Electronic Media",
              "student_count": 556
            },
            {
              "department": "Art + Design",
              "student_count": 474
            }
          ],
          "total_demand": 30,
          "total_supply": 26.0,
          "gap": 4.0,
          "gap_eligible": true
        },
        "goal": "Workforce",
        "metrics": [
          "Employed in Field of Study",
          "Median Annual Earnings"
        ]
      },
      "partnershipId": "seed-oxnard-internship-01",
      "collegeId": "Oxnard College",
      "savedAt": "2026-04-20T00:00:00.000Z"
    }
  ],
  "Foothill College": [
    {
      "id": "seed-swp-foothill-01",
      "project": {
        "employer": "Alpha Teknova",
        "college": "Foothill College",
        "partnership_type": "Internship Pipeline",
        "sections": [
          {
            "key": "project_name",
            "title": "Project Name",
            "content": "Alpha Teknova Internship Pipeline \u2014 Chemical Technicians",
            "char_limit": 100
          },
          {
            "key": "project_description",
            "title": "Project Description",
            "content": "Foothill College will establish a structured internship pipeline with Alpha Teknova to place Chemistry, Biology, and Engineering students in chemical technician roles. The partnership targets improved career readiness and job placement in the Bay Area life science sector.",
            "char_limit": 500
          },
          {
            "key": "rationale",
            "title": "Project Rationale",
            "content": "Regional demand for Chemical Technicians (SOC 19-4031) substantially exceeds the annual supply of program completers across aligned TOP codes (040100 Biology, General; 190500 Chemistry, General), creating a measurable gap this project directly addresses.\n\nAlpha Teknova operates in biotechnology production and R&D, environments that require the laboratory techniques, quality control, and safety protocols that Foothill College's Chemistry, Biology, and Engineering departments already develop through existing coursework. The alignment between employer skill needs and program-level preparation is direct and documented.\n\nA structured internship pipeline is the appropriate response to this gap because it converts existing academic preparation into verified workplace experience, accelerating the pathway from enrollment to employment in the field of study. This partnership gives students access to a working life science environment while giving the region a mechanism to increase the supply of credentialed chemical technicians.",
            "char_limit": 3000
          },
          {
            "key": "student_impact",
            "title": "Student Impact",
            "content": "Up to 6,443 students enrolled in Chemistry, Biology, and Engineering programs are in the pipeline, as these departments deliver the laboratory techniques, quality control, and safety protocols required by Chemical Technicians at Alpha Teknova. This figure represents the total population from which internship cohorts will be recruited and placed.",
            "char_limit": 600
          },
          {
            "key": "vision_goal",
            "title": "Vision for Success Goal",
            "content": "This project addresses the Vision for Success Workforce goal. It will increase the number of students who complete career-aligned programs and secure employment in their field of study in the Bay Area life science sector.",
            "char_limit": 400
          },
          {
            "key": "objective",
            "title": "Objective",
            "content": "Objective Type: Improve career readiness and job placement\n\nFoothill College will place an initial cohort of students in a structured internship at Alpha Teknova within two semesters of project launch, with success measured against the SWP metrics of Employed in Field of Study and Median Annual Earnings. This objective directly responds to the regional supply gap in Chemical Technicians by converting existing academic preparation into documented work-based learning outcomes.",
            "char_limit": 800
          },
          {
            "key": "activity",
            "title": "Activity",
            "content": "The Engineering or Chemistry Department chair will convene an initial coordination meeting with Alpha Teknova's HR or workforce team to confirm site capacity and define first-cohort scope. The internship will be structured at 10\u201316 weeks and mapped to existing cooperative work experience course credits, with placement targeting the next two semesters. The Strong Workforce coordinator will track cohort progress against the Employed in Field of Study and Median Annual Earnings metrics throughout the activity period.",
            "char_limit": 600
          }
        ],
        "lmi_context": {
          "occupations": [
            {
              "soc_code": "19-4031",
              "title": "Chemical Technicians",
              "annual_wage": 63690,
              "employment": 1930,
              "growth_rate": 0.019812217,
              "annual_openings": 240,
              "education_level": null,
              "region": "Bay"
            }
          ],
          "supply_estimates": [
            {
              "top_code": "040100",
              "top_title": "Biology, General",
              "award_level": "Associate Degree for Transfer",
              "annual_projected_supply": 18.33
            },
            {
              "top_code": "040100",
              "top_title": "Biology, General",
              "award_level": "Associate Degree",
              "annual_projected_supply": 7.33
            },
            {
              "top_code": "190500",
              "top_title": "Chemistry, General",
              "award_level": "Associate Degree",
              "annual_projected_supply": 5.67
            }
          ],
          "department_enrollments": [
            {
              "department": "Chemistry",
              "student_count": 3378
            },
            {
              "department": "Biology",
              "student_count": 2419
            },
            {
              "department": "Engineering",
              "student_count": 646
            }
          ],
          "total_demand": 240,
          "total_supply": 31.33,
          "gap": 208.67000000000002,
          "gap_eligible": true
        },
        "goal": "Workforce",
        "metrics": [
          "Employed in Field of Study",
          "Median Annual Earnings"
        ]
      },
      "partnershipId": "seed-foothill-internship-01",
      "collegeId": "Foothill College",
      "savedAt": "2026-04-20T00:00:00.000Z"
    }
  ],
  "Compton College": [
    {
      "id": "seed-swp-compton-01",
      "project": {
        "employer": "Kedren Community Health Center",
        "college": "Compton College",
        "partnership_type": "Internship Pipeline",
        "sections": [
          {
            "key": "project_name",
            "title": "Project Name",
            "content": "Kedren Community Health Center Nursing Internship Pipeline",
            "char_limit": 100
          },
          {
            "key": "project_description",
            "title": "Project Description",
            "content": "Compton College's Nursing department will establish a structured internship pipeline with Kedren Community Health Center to place nursing students in a community health setting, improving clinical readiness and job placement outcomes for Registered Nurse candidates.",
            "char_limit": 500
          },
          {
            "key": "rationale",
            "title": "Project Rationale",
            "content": "Regional demand for Registered Nurses (SOC 29-1141) substantially exceeds the supply produced by Compton College's Registered Nursing program (TOP 123010), creating a measurable annual gap that this project directly addresses. The LMI table documents the scale of that gap.\n\nKedren Community Health Center operates within the Los Angeles region and provides services that require the core competencies Compton College's Nursing department already develops: nursing process, patient assessment, and medication administration. These skills are embedded across the Nursing curriculum, making Kedren a directly aligned internship site rather than an aspirational one.\n\nA structured internship pipeline converts existing curriculum into verified, employer-validated clinical experience. This strengthens student placement outcomes in an occupation where regional demand is sustained and documented.",
            "char_limit": 3000
          },
          {
            "key": "student_impact",
            "title": "Student Impact",
            "content": "Up to 1,655 students enrolled in Compton College's Nursing department are in the pipeline this partnership serves. These students are enrolled in courses that directly develop the nursing process, patient assessment, and medication administration skills required for Registered Nurse roles at Kedren.",
            "char_limit": 600
          },
          {
            "key": "vision_goal",
            "title": "Vision for Success Goal",
            "content": "This project advances the Workforce Vision for Success goal. By connecting Nursing students to a structured employer internship, the project supports their transition into employment in their field of study at competitive regional wage levels.",
            "char_limit": 400
          },
          {
            "key": "objective",
            "title": "Objective",
            "content": "Objective Type: Improve career readiness and job placement\n\nThe Nursing department will place an initial cohort of students into a structured internship at Kedren Community Health Center, with success measured through the SWP metrics of Employed in Field of Study and Median Annual Earnings for participating students.\n\nThis objective directly addresses the documented regional gap between Registered Nurse demand and program supply in the Los Angeles area.",
            "char_limit": 800
          },
          {
            "key": "activity",
            "title": "Activity",
            "content": "The Nursing department chair will convene with Kedren's clinical or workforce development team to establish site capacity, supervision structure, and cohort size for the first internship cycle. The internship will be mapped to existing work experience or clinical practicum courses and structured as a 10-16 week placement for an initial cohort. The partnership will target a launch within the next academic year, beginning with a fall or spring semester.",
            "char_limit": 600
          }
        ],
        "lmi_context": {
          "occupations": [
            {
              "soc_code": "29-1141",
              "title": "Registered Nurses",
              "annual_wage": 132900,
              "employment": 80880,
              "growth_rate": 0.053095652,
              "annual_openings": 5090,
              "education_level": null,
              "region": "LA"
            }
          ],
          "supply_estimates": [
            {
              "top_code": "123010",
              "top_title": "Registered Nursing",
              "award_level": "Associate Degree",
              "annual_projected_supply": 55.0
            }
          ],
          "department_enrollments": [
            {
              "department": "Nursing",
              "student_count": 1655
            }
          ],
          "total_demand": 5090,
          "total_supply": 55.0,
          "gap": 5035.0,
          "gap_eligible": true
        },
        "goal": "Workforce",
        "metrics": [
          "Employed in Field of Study",
          "Median Annual Earnings"
        ]
      },
      "partnershipId": "seed-compton-internship-01",
      "collegeId": "Compton College",
      "savedAt": "2026-04-20T00:00:00.000Z"
    }
  ],
  "San Diego City College": [
    {
      "id": "seed-swp-sandiegocity-01",
      "project": {
        "employer": "Thermo Fisher Scientific",
        "college": "San Diego City College",
        "partnership_type": "Internship Pipeline",
        "sections": [
          {
            "key": "project_name",
            "title": "Project Name",
            "content": "Thermo Fisher Scientific Internship Pipeline \u2014 Software Development",
            "char_limit": 100
          },
          {
            "key": "project_description",
            "title": "Project Description",
            "content": "San Diego City College will establish a structured internship pipeline with Thermo Fisher Scientific to place software development students in applied technical roles. This partnership targets improved career readiness and job placement for students in the Computer Information Systems and Computer Science departments.",
            "char_limit": 500
          },
          {
            "key": "rationale",
            "title": "Project Rationale",
            "content": "Regional demand for Software Developers (SOC 15-1252) substantially exceeds the annual supply of program completers, creating a measurable gap this project directly addresses. Annual job openings in the San Diego/Imperial region are tracked against projected completions from Mathematics, General programs (TOP 170100), the primary aligned supply-side credential. The gap between demand and supply confirms funding eligibility and establishes the urgency of expanding student pathways into this occupation.\n\nThermo Fisher Scientific operates in San Diego and employs software developers to support its scientific instrumentation and diagnostics platforms. This employer profile aligns directly with the programming, software development, and object-oriented programming skills built across courses in the Computer Information Systems and Computer Science departments. The match between employer skill needs and existing curriculum means the college can activate this pipeline without requiring new course development.\n\nA structured internship is the appropriate response to the gap because it converts existing academic preparation into verified work-based experience, improving both placement rates and earnings outcomes for completers. This project connects a demonstrated regional employer need to a ready student population.",
            "char_limit": 3000
          },
          {
            "key": "student_impact",
            "title": "Student Impact",
            "content": "Up to 5,785 students enrolled in aligned courses across the Computer Information Systems, Computer Science, and Mathematics departments represent the potential pipeline for this internship partnership. These students are developing the programming, software development, and object-oriented programming skills that Thermo Fisher Scientific's software developer roles require.",
            "char_limit": 600
          },
          {
            "key": "vision_goal",
            "title": "Vision for Success Goal",
            "content": "This project advances the Workforce Vision for Success goal. By connecting students to structured work-based learning with a regional employer, the project increases the proportion of completers who are employed in their field of study at improved wage levels.",
            "char_limit": 400
          },
          {
            "key": "objective",
            "title": "Objective",
            "content": "Objective Type: Improve career readiness and job placement\n\nSan Diego City College will increase the number of students employed in the field of study and improve median annual earnings among completers from aligned programs by establishing a formal internship pipeline with Thermo Fisher Scientific. Progress will be measured using the SWP metrics Employed in Field of Study and Median Annual Earnings.\n\nThis objective directly addresses the regional gap between employer demand for Software Developers (SOC 15-1252) and the current supply of program completers (TOP 170100) in the San Diego/Imperial region.",
            "char_limit": 800
          }
        ],
        "lmi_context": {
          "occupations": [
            {
              "soc_code": "15-1252",
              "title": "Software Developers",
              "annual_wage": 158680,
              "employment": 21890,
              "growth_rate": 0.044858829,
              "annual_openings": 1340,
              "education_level": null,
              "region": "SD/I"
            }
          ],
          "supply_estimates": [
            {
              "top_code": "170100",
              "top_title": "Mathematics, General",
              "award_level": "Associate Degree",
              "annual_projected_supply": 3.0
            },
            {
              "top_code": "170100",
              "top_title": "Mathematics, General",
              "award_level": "Associate Degree for Transfer",
              "annual_projected_supply": 12.33
            }
          ],
          "department_enrollments": [
            {
              "department": "Mathematics",
              "student_count": 5153
            },
            {
              "department": "Computer Information Systems",
              "student_count": 484
            },
            {
              "department": "Computer Science",
              "student_count": 148
            }
          ],
          "total_demand": 1340,
          "total_supply": 15.33,
          "gap": 1324.67,
          "gap_eligible": true
        },
        "goal": "Workforce",
        "metrics": [
          "Employed in Field of Study",
          "Median Annual Earnings"
        ]
      },
      "partnershipId": "seed-sandiegocity-internship-01",
      "collegeId": "San Diego City College",
      "savedAt": "2026-04-20T00:00:00.000Z"
    }
  ],
  "Irvine Valley College": [
    {
      "id": "seed-swp-irvinevalley-01",
      "project": {
        "employer": "Confluent Medical Technologies",
        "college": "Irvine Valley College",
        "partnership_type": "Internship Pipeline",
        "sections": [
          {
            "key": "project_name",
            "title": "Project Name",
            "content": "Confluent Medical Technologies Biomedical Engineering Internship Pipeline",
            "char_limit": 100
          },
          {
            "key": "project_description",
            "title": "Project Description",
            "content": "Irvine Valley College will partner with Confluent Medical Technologies to establish an internship pipeline for students pursuing biomedical engineering, improving career readiness and job placement in Orange County's medical device sector.",
            "char_limit": 500
          },
          {
            "key": "rationale",
            "title": "Project Rationale",
            "content": "Regional demand for Bioengineers and Biomedical Engineers (SOC 17-2031) substantially exceeds the current supply of program completions (TOP 0935.00), producing a measurable annual gap this project directly addresses.\n\nConfluent Medical Technologies operates in cardiovascular and peripheral vascular device manufacturing in Orange County, placing it at the center of regional biomedical engineering demand. The skills Confluent requires \u2014 design, biology, and anatomy & physiology \u2014 are already developed across Irvine Valley College's Engineering, Biology, and Kinesiology departments. This alignment makes the internship pipeline a targeted, practical response to the documented gap rather than a general workforce initiative.\n\nAn internship structure maps students from existing coursework directly into medical device design and manufacturing workflows, bridging the gap between program supply and employer demand at the occupational level.",
            "char_limit": 3000
          },
          {
            "key": "student_impact",
            "title": "Student Impact",
            "content": "Up to 8,247 students enrolled in the Biology, Engineering, and Kinesiology departments represent the potential pipeline, as these programs develop the design, biology, and anatomy & physiology skills required by the Bioengineers and Biomedical Engineers occupation at Confluent Medical Technologies.",
            "char_limit": 600
          },
          {
            "key": "vision_goal",
            "title": "Vision for Success Goal",
            "content": "This project addresses the Workforce Vision for Success goal. It will increase the number of students who complete career-aligned experiences and enter employment in their field of study.",
            "char_limit": 400
          },
          {
            "key": "objective",
            "title": "Objective",
            "content": "Objective Type: Improve career readiness and job placement\n\nIrvine Valley College will place an initial cohort of students into structured internships at Confluent Medical Technologies, tracking outcomes against the SWP metrics of Employed in Field of Study and Median Annual Earnings. This objective responds directly to the regional gap between annual openings and program completions in the Bioengineers and Biomedical Engineers occupational cluster.",
            "char_limit": 800
          },
          {
            "key": "activity",
            "title": "Activity",
            "content": "The Engineering department chair will convene with Confluent Medical Technologies' workforce or HR team to establish internship scope, site capacity, and cohort criteria. The partnership will target students with concurrent enrollment in Engineering and Biology coursework, launching an initial cohort within one to two semesters using a 12-16 week structure mapped to existing cooperative work experience units. Coordination meetings will occur on a recurring basis throughout the academic year to monitor placements and track progress toward employment outcomes.",
            "char_limit": 600
          }
        ],
        "lmi_context": {
          "occupations": [
            {
              "soc_code": "17-2031",
              "title": "Bioengineers and Biomedical Engineers",
              "annual_wage": 118350,
              "employment": 410,
              "growth_rate": 0.050387661,
              "annual_openings": 30,
              "education_level": null,
              "region": "OC"
            }
          ],
          "supply_estimates": [],
          "department_enrollments": [
            {
              "department": "Biology",
              "student_count": 3406
            },
            {
              "department": "Kinesiology",
              "student_count": 3203
            },
            {
              "department": "Engineering",
              "student_count": 1638
            }
          ],
          "total_demand": 30,
          "total_supply": 0.0,
          "gap": 30.0,
          "gap_eligible": true
        },
        "goal": "Workforce",
        "metrics": [
          "Employed in Field of Study",
          "Median Annual Earnings"
        ]
      },
      "partnershipId": "seed-irvinevalley-internship-01",
      "collegeId": "Irvine Valley College",
      "savedAt": "2026-04-20T00:00:00.000Z"
    }
  ]
};

export const SEEDED_SWP_PROJECTS: Record<string, SavedSwpProject[]> = {
  ...Object.fromEntries(FEATURED_NAMES.map((name) => [name, [] as SavedSwpProject[]])),
  ...SEEDED_BY_NAME,
};

export function getSeededSwpProjects(collegeName: string): SavedSwpProject[] {
  return SEEDED_SWP_PROJECTS[collegeName] ?? [];
}
