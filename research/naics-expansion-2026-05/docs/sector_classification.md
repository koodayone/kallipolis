# Occupation → SWP Sector Classification
Plurality classification of every `Occupation` in the graph to a Strong Workforce / Doing-What-MATTERS sector, computed off the institutional crosswalk directly. For each SOC, the full set of TOP6 codes that reach it via TOP6→CIP→SOC is collected; each TOP6's sector is looked up in the PCAH *TOP Codes to Sectors* file; the plurality sector wins.
**Method.** One vote per TOP6 in the crosswalk that reaches the SOC. College-independent — the result does not depend on which colleges are currently loaded into the graph. Inputs are exclusively the TOP-CIP (Chancellor's Office), CIP-SOC (NCES/BLS), and PCAH (Chancellor's Office) crosswalks shipped in `backend/ontology/data/`.
**Inputs.**
- `Occupation` nodes: 506
- Crosswalks: `top_cip_crosswalk.csv`, `CIP2020_SOC2018_Crosswalk.xlsx`, `TOP Codes to Sectors.xlsx`

## Coverage summary
| Bucket | Count | Pct |
|---|---:|---:|
| Single-sector (clean plurality) | 451 | 89.1% |
| Tied across two or more sectors | 49 | 9.7% |
| Untraceable (TOPs exist but none in PCAH CTE set) | 6 | 1.2% |
| No crosswalk path at all | 0 | 0.0% |

## Sector totals (single-winner SOCs only)
| Sector | SOCs |
|---|---:|
| Business and Entrepreneurship | 74 |
| Information and Communication Technologies - Digital Media | 56 |
| Advanced Manufacturing | 53 |
| Advanced Transportation and Logistics | 51 |
| Energy, Construction and Utilities | 49 |
| Health | 46 |
| Unassigned | 30 |
| Agriculture, Water and Environmental Technologies | 28 |
| Education and Human Development | 23 |
| Public Safety | 18 |
| Retail, Hospitality and Tourism | 16 |
| Life Sciences - Biotechnology | 7 |

---

## Occupations by sector
Each row shows the count of TOP6 codes voting for the winning sector vs the total CTE-classified TOPs that reach the SOC, and the contributing TOPs (with Chancellor's Office titles).

### Business and Entrepreneurship  (74 occupations)
| SOC | Title | Vote | Contributing TOPs |
|---|---|---|---|
| `11-1011` | Chief Executives | 8/12 | `050100` Business and Commerce, General; `050200` Accounting; `050400` Banking and Finance; `050500` Business Administration; `050600` Business Management; `050630` Management Development and Supervision; `050640` Small Business and Entrepreneurship; `050900` Marketing and Distribution |
| `11-1021` | General and Operations Managers | 9/17 | `050100` Business and Commerce, General; `050200` Accounting; `050400` Banking and Finance; `050500` Business Administration; `050600` Business Management; `050630` Management Development and Supervision; `050640` Small Business and Entrepreneurship; `050900` Marketing and Distribution; `051200` Insurance |
| `11-2011` | Advertising and Promotions Managers | 2/3 | `050900` Marketing and Distribution; `050910` Advertising |
| `11-2022` | Sales Managers | 7/9 | `050100` Business and Commerce, General; `050200` Accounting; `050500` Business Administration; `050600` Business Management; `050630` Management Development and Supervision; `050640` Small Business and Entrepreneurship; `050900` Marketing and Distribution |
| `11-2033` | Fundraising Managers | 2/3 | `050900` Marketing and Distribution; `050910` Advertising |
| `11-3012` | Administrative Services Managers | 8/13 | `050100` Business and Commerce, General; `050200` Accounting; `050500` Business Administration; `050600` Business Management; `050630` Management Development and Supervision; `050640` Small Business and Entrepreneurship; `050900` Marketing and Distribution; `050920` Purchasing |
| `11-3013` | Facilities Managers | 10/20 | `050100` Business and Commerce, General; `050200` Accounting; `050500` Business Administration; `050600` Business Management; `050630` Management Development and Supervision; `050640` Small Business and Entrepreneurship; `050900` Marketing and Distribution; `050920` Purchasing; `051800` Customer Service; `300500` Custodial Services |
| `11-3031` | Financial Managers | 2/2 | `050400` Banking and Finance; `051200` Insurance |
| `11-3051` | Industrial Production Managers | 8/11 | `050100` Business and Commerce, General; `050200` Accounting; `050500` Business Administration; `050600` Business Management; `050630` Management Development and Supervision; `050640` Small Business and Entrepreneurship; `050900` Marketing and Distribution; `051800` Customer Service |
| `11-3061` | Purchasing Managers | 1/1 | `050920` Purchasing |
| `11-3071` | Transportation, Storage, and Distribution Managers | 7/13 | `050100` Business and Commerce, General; `050200` Accounting; `050500` Business Administration; `050600` Business Management; `050630` Management Development and Supervision; `050640` Small Business and Entrepreneurship; `050900` Marketing and Distribution |
| `11-3111` | Compensation and Benefits Managers | 7/9 | `050100` Business and Commerce, General; `050500` Business Administration; `050600` Business Management; `050630` Management Development and Supervision; `050640` Small Business and Entrepreneurship; `050900` Marketing and Distribution; `051200` Insurance |
| `11-3121` | Human Resources Managers | 6/8 | `050100` Business and Commerce, General; `050500` Business Administration; `050600` Business Management; `050630` Management Development and Supervision; `050640` Small Business and Entrepreneurship; `050900` Marketing and Distribution |
| `11-3131` | Training and Development Managers | 6/7 | `050100` Business and Commerce, General; `050500` Business Administration; `050600` Business Management; `050630` Management Development and Supervision; `050640` Small Business and Entrepreneurship; `050900` Marketing and Distribution |
| `11-9021` | Construction Managers | 8/15 | `050100` Business and Commerce, General; `050200` Accounting; `050500` Business Administration; `050600` Business Management; `050630` Management Development and Supervision; `050640` Small Business and Entrepreneurship; `050900` Marketing and Distribution; `051800` Customer Service |
| `11-9072` | Entertainment and Recreation Managers, Except Gambling | 7/17 | `050100` Business and Commerce, General; `050200` Accounting; `050500` Business Administration; `050600` Business Management; `050630` Management Development and Supervision; `050640` Small Business and Entrepreneurship; `050900` Marketing and Distribution |
| `11-9141` | Property, Real Estate, and Community Association Managers | 2/2 | `051100` Real Estate; `051110` Escrow |
| `11-9151` | Social and Community Service Managers | 7/13 | `050100` Business and Commerce, General; `050200` Accounting; `050500` Business Administration; `050600` Business Management; `050630` Management Development and Supervision; `050640` Small Business and Entrepreneurship; `050900` Marketing and Distribution |
| `11-9171` | Funeral Home Managers | 1/1 | `125500` Mortuary Science |
| `11-9179` | Personal Service Managers, All Other | 8/14 | `050100` Business and Commerce, General; `050200` Accounting; `050500` Business Administration; `050600` Business Management; `050630` Management Development and Supervision; `050640` Small Business and Entrepreneurship; `050900` Marketing and Distribution; `300700` Cosmetology and Barbering |
| `13-1011` | Agents and Business Managers of Artists, Performers, and Athletes | 1/1 | `050920` Purchasing |
| `13-1031` | Claims Adjusters, Examiners, and Investigators | 1/1 | `051200` Insurance |
| `13-1051` | Cost Estimators | 7/9 | `050100` Business and Commerce, General; `050200` Accounting; `050500` Business Administration; `050600` Business Management; `050630` Management Development and Supervision; `050640` Small Business and Entrepreneurship; `050900` Marketing and Distribution |
| `13-1071` | Human Resources Specialists | 6/7 | `050100` Business and Commerce, General; `050500` Business Administration; `050600` Business Management; `050630` Management Development and Supervision; `050640` Small Business and Entrepreneurship; `050900` Marketing and Distribution |
| `13-1081` | Logisticians | 7/9 | `050100` Business and Commerce, General; `050500` Business Administration; `050600` Business Management; `050630` Management Development and Supervision; `050640` Small Business and Entrepreneurship; `050900` Marketing and Distribution; `051800` Customer Service |
| `13-1082` | Project Management Specialists | 7/11 | `050100` Business and Commerce, General; `050200` Accounting; `050500` Business Administration; `050600` Business Management; `050630` Management Development and Supervision; `050640` Small Business and Entrepreneurship; `050900` Marketing and Distribution |
| `13-1111` | Management Analysts | 7/13 | `050100` Business and Commerce, General; `050200` Accounting; `050500` Business Administration; `050600` Business Management; `050630` Management Development and Supervision; `050640` Small Business and Entrepreneurship; `050900` Marketing and Distribution |
| `13-1131` | Fundraisers | 2/3 | `050900` Marketing and Distribution; `050910` Advertising |
| `13-1141` | Compensation, Benefits, and Job Analysis Specialists | 8/9 | `050100` Business and Commerce, General; `050400` Banking and Finance; `050500` Business Administration; `050600` Business Management; `050630` Management Development and Supervision; `050640` Small Business and Entrepreneurship; `050900` Marketing and Distribution; `051200` Insurance |
| `13-1161` | Market Research Analysts and Marketing Specialists | 5/9 | `050100` Business and Commerce, General; `050500` Business Administration; `050600` Business Management; `050900` Marketing and Distribution; `050970` e-commerce (business emphasis) |
| `13-1199` | Business Operations Specialists, All Other | 7/12 | `050100` Business and Commerce, General; `050500` Business Administration; `050600` Business Management; `050630` Management Development and Supervision; `050640` Small Business and Entrepreneurship; `050900` Marketing and Distribution; `050970` e-commerce (business emphasis) |
| `13-2011` | Accountants and Auditors | 2/3 | `050200` Accounting; `050210` Tax Studies |
| `13-2031` | Budget Analysts | 2/2 | `050200` Accounting; `050400` Banking and Finance |
| `13-2041` | Credit Analysts | 2/2 | `050200` Accounting; `050400` Banking and Finance |
| `13-2051` | Financial and Investment Analysts | 1/1 | `050400` Banking and Finance |
| `13-2053` | Insurance Underwriters | 2/2 | `050400` Banking and Finance; `051200` Insurance |
| `13-2054` | Financial Risk Specialists | 3/3 | `050200` Accounting; `050400` Banking and Finance; `051200` Insurance |
| `13-2061` | Financial Examiners | 2/3 | `050200` Accounting; `050210` Tax Studies |
| `13-2071` | Credit Counselors | 1/1 | `050400` Banking and Finance |
| `13-2072` | Loan Officers | 1/1 | `050400` Banking and Finance |
| `13-2081` | Tax Examiners and Collectors, and Revenue Agents | 2/2 | `050200` Accounting; `050210` Tax Studies |
| `13-2082` | Tax Preparers | 3/3 | `050200` Accounting; `050210` Tax Studies; `050640` Small Business and Entrepreneurship |
| `13-2099` | Financial Specialists, All Other | 1/1 | `050400` Banking and Finance |
| `15-2011` | Actuaries | 1/1 | `051200` Insurance |
| `31-9011` | Massage Therapists | 1/1 | `126200` Massage Therapy |
| `39-1022` | First-Line Supervisors of Personal Service Workers | 1/1 | `300700` Cosmetology and Barbering |
| `39-4011` | Embalmers | 1/1 | `125500` Mortuary Science |
| `39-4031` | Morticians, Undertakers, and Funeral Arrangers | 1/1 | `125500` Mortuary Science |
| `39-5011` | Barbers | 1/1 | `300700` Cosmetology and Barbering |
| `39-5012` | Hairdressers, Hairstylists, and Cosmetologists | 1/1 | `300700` Cosmetology and Barbering |
| `39-5091` | Makeup Artists, Theatrical and Performance | 1/1 | `300700` Cosmetology and Barbering |
| `39-5092` | Manicurists and Pedicurists | 1/1 | `300700` Cosmetology and Barbering |
| `39-5093` | Shampooers | 1/1 | `300700` Cosmetology and Barbering |
| `39-5094` | Skincare Specialists | 1/1 | `300700` Cosmetology and Barbering |
| `41-2022` | Parts Salespersons | 1/1 | `050940` Sales and Salesmanship |
| `41-3011` | Advertising Sales Agents | 1/1 | `050940` Sales and Salesmanship |
| `41-3021` | Insurance Sales Agents | 1/1 | `051200` Insurance |
| `41-4011` | Sales Representatives, Wholesale and Manufacturing, Technical and Scientific Products | 1/1 | `050940` Sales and Salesmanship |
| `41-9021` | Real Estate Brokers | 2/2 | `051100` Real Estate; `051110` Escrow |
| `41-9022` | Real Estate Sales Agents | 2/2 | `051100` Real Estate; `051110` Escrow |
| `43-3011` | Bill and Account Collectors | 1/1 | `050400` Banking and Finance |
| `43-3031` | Bookkeeping, Accounting, and Auditing Clerks | 2/2 | `050200` Accounting; `050640` Small Business and Entrepreneurship |
| `43-3051` | Payroll and Timekeeping Clerks | 2/2 | `050200` Accounting; `050640` Small Business and Entrepreneurship |
| `43-3071` | Tellers | 1/1 | `050400` Banking and Finance |
| `43-4011` | Brokerage Clerks | 2/2 | `050200` Accounting; `050640` Small Business and Entrepreneurship |
| `43-4041` | Credit Authorizers, Checkers, and Clerks | 1/1 | `050400` Banking and Finance |
| `43-4051` | Customer Service Representatives | 1/1 | `051800` Customer Service |
| `43-4131` | Loan Interviewers and Clerks | 1/1 | `050400` Banking and Finance |
| `43-4141` | New Accounts Clerks | 1/1 | `050400` Banking and Finance |
| `43-4161` | Human Resources Assistants, Except Payroll and Timekeeping | 2/4 | `050100` Business and Commerce, General; `050630` Management Development and Supervision |
| `43-6011` | Executive Secretaries and Executive Administrative Assistants | 2/4 | `050100` Business and Commerce, General; `050630` Management Development and Supervision |
| `43-6014` | Secretaries and Administrative Assistants, Except Legal, Medical, and Executive | 2/4 | `050100` Business and Commerce, General; `050630` Management Development and Supervision |
| `43-9111` | Statistical Assistants | 2/2 | `050200` Accounting; `050640` Small Business and Entrepreneurship |
| `51-1011` | First-Line Supervisors of Production and Operating Workers | 2/2 | `050630` Management Development and Supervision; `051800` Customer Service |

### Information and Communication Technologies - Digital Media  (56 occupations)
| SOC | Title | Vote | Contributing TOPs |
|---|---|---|---|
| `11-2032` | Public Relations Managers | 2/4 | `060200` Journalism; `061000` Mass Communications |
| `11-3021` | Computer and Information Systems Managers | 12/14 | `051400` Office Technology-Office Computer Applications; `070100` Information Technology, General; `070200` Computer Information Systems; `070210` Software Applications; `070700` Computer Software Development; `070710` Computer Programming; `070720` Database Design and Administration; `070730` Computer Systems Analysis; `070800` Computer Infrastructure and Support; `070810` Computer Networking; `070820` Computer Support; `070900` World Wide Web Administration |
| `11-9121` | Natural Sciences Managers | 4/6 | `070200` Computer Information Systems; `070700` Computer Software Development; `070710` Computer Programming; `070720` Database Design and Administration |
| `15-1211` | Computer Systems Analysts | 10/10 | `051400` Office Technology-Office Computer Applications; `070100` Information Technology, General; `070200` Computer Information Systems; `070210` Software Applications; `070700` Computer Software Development; `070710` Computer Programming; `070730` Computer Systems Analysis; `070800` Computer Infrastructure and Support; `070810` Computer Networking; `070900` World Wide Web Administration |
| `15-1212` | Information Security Analysts | 10/11 | `051400` Office Technology-Office Computer Applications; `070100` Information Technology, General; `070200` Computer Information Systems; `070210` Software Applications; `070710` Computer Programming; `070730` Computer Systems Analysis; `070800` Computer Infrastructure and Support; `070810` Computer Networking; `070820` Computer Support; `070900` World Wide Web Administration |
| `15-1221` | Computer and Information Research Scientists | 12/12 | `051400` Office Technology-Office Computer Applications; `070100` Information Technology, General; `070200` Computer Information Systems; `070210` Software Applications; `070700` Computer Software Development; `070710` Computer Programming; `070720` Database Design and Administration; `070730` Computer Systems Analysis; `070800` Computer Infrastructure and Support; `070810` Computer Networking; `070900` World Wide Web Administration; `079900` Other Information Technology |
| `15-1231` | Computer Network Support Specialists | 11/11 | `070100` Information Technology, General; `070200` Computer Information Systems; `070210` Software Applications; `070700` Computer Software Development; `070710` Computer Programming; `070720` Database Design and Administration; `070730` Computer Systems Analysis; `070800` Computer Infrastructure and Support; `070810` Computer Networking; `070820` Computer Support; `070900` World Wide Web Administration |
| `15-1232` | Computer User Support Specialists | 5/7 | `070200` Computer Information Systems; `070720` Database Design and Administration; `070800` Computer Infrastructure and Support; `070810` Computer Networking; `070820` Computer Support |
| `15-1241` | Computer Network Architects | 11/11 | `051400` Office Technology-Office Computer Applications; `070100` Information Technology, General; `070200` Computer Information Systems; `070210` Software Applications; `070700` Computer Software Development; `070710` Computer Programming; `070730` Computer Systems Analysis; `070800` Computer Infrastructure and Support; `070810` Computer Networking; `070820` Computer Support; `070900` World Wide Web Administration |
| `15-1242` | Database Administrators | 11/11 | `070100` Information Technology, General; `070200` Computer Information Systems; `070210` Software Applications; `070700` Computer Software Development; `070710` Computer Programming; `070720` Database Design and Administration; `070730` Computer Systems Analysis; `070800` Computer Infrastructure and Support; `070810` Computer Networking; `070820` Computer Support; `070900` World Wide Web Administration |
| `15-1243` | Database Architects | 12/12 | `051400` Office Technology-Office Computer Applications; `070100` Information Technology, General; `070200` Computer Information Systems; `070210` Software Applications; `070700` Computer Software Development; `070710` Computer Programming; `070720` Database Design and Administration; `070730` Computer Systems Analysis; `070800` Computer Infrastructure and Support; `070810` Computer Networking; `070820` Computer Support; `070900` World Wide Web Administration |
| `15-1244` | Network and Computer Systems Administrators | 10/10 | `070100` Information Technology, General; `070200` Computer Information Systems; `070210` Software Applications; `070700` Computer Software Development; `070710` Computer Programming; `070730` Computer Systems Analysis; `070800` Computer Infrastructure and Support; `070810` Computer Networking; `070820` Computer Support; `070900` World Wide Web Administration |
| `15-1251` | Computer Programmers | 12/13 | `061410` Multimedia; `061420` Electronic Game Design; `061460` Computer Graphics and Digital Imagery; `070100` Information Technology, General; `070200` Computer Information Systems; `070210` Software Applications; `070700` Computer Software Development; `070710` Computer Programming; `070720` Database Design and Administration; `070800` Computer Infrastructure and Support; `070810` Computer Networking; `070900` World Wide Web Administration |
| `15-1252` | Software Developers | 13/13 | `051400` Office Technology-Office Computer Applications; `061420` Electronic Game Design; `070100` Information Technology, General; `070200` Computer Information Systems; `070210` Software Applications; `070700` Computer Software Development; `070710` Computer Programming; `070720` Database Design and Administration; `070730` Computer Systems Analysis; `070800` Computer Infrastructure and Support; `070810` Computer Networking; `070900` World Wide Web Administration; `079900` Other Information Technology |
| `15-1253` | Software Quality Assurance Analysts and Testers | 11/12 | `051400` Office Technology-Office Computer Applications; `061420` Electronic Game Design; `070100` Information Technology, General; `070200` Computer Information Systems; `070210` Software Applications; `070700` Computer Software Development; `070710` Computer Programming; `070730` Computer Systems Analysis; `070800` Computer Infrastructure and Support; `070810` Computer Networking; `070900` World Wide Web Administration |
| `15-1254` | Web Developers | 10/10 | `061400` Digital Media; `061430` Website Design and Development; `070100` Information Technology, General; `070200` Computer Information Systems; `070210` Software Applications; `070700` Computer Software Development; `070710` Computer Programming; `070810` Computer Networking; `070900` World Wide Web Administration; `070910` E-Commerce (technology emphasis) |
| `15-1255` | Web and Digital Interface Designers | 15/18 | `061400` Digital Media; `061410` Multimedia; `061430` Website Design and Development; `061460` Computer Graphics and Digital Imagery; `070100` Information Technology, General; `070200` Computer Information Systems; `070210` Software Applications; `070700` Computer Software Development; `070710` Computer Programming; `070730` Computer Systems Analysis; `070800` Computer Infrastructure and Support; `070810` Computer Networking; `070900` World Wide Web Administration; `070910` E-Commerce (technology emphasis); `103000` Graphic Art and Design |
| `15-1299` | Computer Occupations, All Other | 7/9 | `070100` Information Technology, General; `070200` Computer Information Systems; `070210` Software Applications; `070700` Computer Software Development; `070710` Computer Programming; `070730` Computer Systems Analysis; `070800` Computer Infrastructure and Support |
| `15-2041` | Statisticians | 4/7 | `070200` Computer Information Systems; `070700` Computer Software Development; `070710` Computer Programming; `070720` Database Design and Administration |
| `15-2051` | Data Scientists | 11/15 | `051400` Office Technology-Office Computer Applications; `070100` Information Technology, General; `070200` Computer Information Systems; `070210` Software Applications; `070700` Computer Software Development; `070710` Computer Programming; `070720` Database Design and Administration; `070730` Computer Systems Analysis; `070810` Computer Networking; `070900` World Wide Web Administration; `079900` Other Information Technology |
| `19-3092` | Geographers | 1/1 | `220610` Geographic Information Systems |
| `27-1011` | Art Directors | 7/7 | `061400` Digital Media; `061410` Multimedia; `061430` Website Design and Development; `061460` Computer Graphics and Digital Imagery; `070900` World Wide Web Administration; `101200` Applied Photography; `103000` Graphic Art and Design |
| `27-1014` | Special Effects Artists and Animators | 11/11 | `061400` Digital Media; `061410` Multimedia; `061420` Electronic Game Design; `061430` Website Design and Development; `061440` Animation; `061460` Computer Graphics and Digital Imagery; `070210` Software Applications; `070900` World Wide Web Administration; `070910` E-Commerce (technology emphasis); `101200` Applied Photography; `103000` Graphic Art and Design |
| `27-1019` | Artists and Related Workers, All Other | 8/10 | `061400` Digital Media; `061410` Multimedia; `061430` Website Design and Development; `061460` Computer Graphics and Digital Imagery; `070900` World Wide Web Administration; `101200` Applied Photography; `101300` Commercial Art; `103000` Graphic Art and Design |
| `27-1024` | Graphic Designers | 10/13 | `061400` Digital Media; `061410` Multimedia; `061430` Website Design and Development; `061460` Computer Graphics and Digital Imagery; `070210` Software Applications; `070900` World Wide Web Administration; `070910` E-Commerce (technology emphasis); `101200` Applied Photography; `101300` Commercial Art; `103000` Graphic Art and Design |
| `27-2012` | Producers and Directors | 4/5 | `060400` Radio and Television; `060410` Radio; `060420` Television (including combined TV-film-video); `061220` Film Production |
| `27-2091` | Disc Jockeys, Except Radio | 1/1 | `100500` Commercial Music |
| `27-3011` | Broadcast Announcers and Radio Disc Jockeys | 4/4 | `060400` Radio and Television; `060410` Radio; `060420` Television (including combined TV-film-video); `060430` Broadcast Journalism |
| `27-3023` | News Analysts, Reporters, and Journalists | 6/6 | `060200` Journalism; `060400` Radio and Television; `060410` Radio; `060420` Television (including combined TV-film-video); `060430` Broadcast Journalism; `061000` Mass Communications |
| `27-3041` | Editors | 5/5 | `060200` Journalism; `060430` Broadcast Journalism; `060700` Technical Communication; `061000` Mass Communications; `069900` Other Media and Communications |
| `27-3042` | Technical Writers | 1/1 | `060700` Technical Communication |
| `27-3043` | Writers and Authors | 6/6 | `060200` Journalism; `060430` Broadcast Journalism; `060700` Technical Communication; `061000` Mass Communications; `061220` Film Production; `069900` Other Media and Communications |
| `27-3099` | Media and Communication Workers, All Other | 6/7 | `061000` Mass Communications; `061400` Digital Media; `061410` Multimedia; `061430` Website Design and Development; `061460` Computer Graphics and Digital Imagery; `070200` Computer Information Systems |
| `27-4011` | Audio and Video Technicians | 2/2 | `100500` Commercial Music; `101200` Applied Photography |
| `27-4012` | Broadcast Technicians | 6/7 | `060400` Radio and Television; `060410` Radio; `060420` Television (including combined TV-film-video); `060430` Broadcast Journalism; `061000` Mass Communications; `070200` Computer Information Systems |
| `27-4014` | Sound Engineering Technicians | 3/4 | `061000` Mass Communications; `070200` Computer Information Systems; `100500` Commercial Music |
| `27-4015` | Lighting Technicians | 5/5 | `060400` Radio and Television; `060410` Radio; `060420` Television (including combined TV-film-video); `060430` Broadcast Journalism; `101200` Applied Photography |
| `27-4021` | Photographers | 5/5 | `061400` Digital Media; `061410` Multimedia; `061460` Computer Graphics and Digital Imagery; `070900` World Wide Web Administration; `101200` Applied Photography |
| `27-4031` | Camera Operators, Television, Video, and Film | 5/5 | `060400` Radio and Television; `060410` Radio; `060420` Television (including combined TV-film-video); `060430` Broadcast Journalism; `061220` Film Production |
| `27-4032` | Film and Video Editors | 7/8 | `060400` Radio and Television; `060410` Radio; `060420` Television (including combined TV-film-video); `060430` Broadcast Journalism; `061000` Mass Communications; `061220` Film Production; `070200` Computer Information Systems |
| `43-2099` | Communications Equipment Operators, All Other | 1/1 | `093430` Telecommunications Technology |
| `43-3061` | Procurement Clerks | 1/1 | `051400` Office Technology-Office Computer Applications |
| `43-4021` | Correspondence Clerks | 1/1 | `051400` Office Technology-Office Computer Applications |
| `43-4071` | File Clerks | 1/1 | `051400` Office Technology-Office Computer Applications |
| `43-5011` | Cargo and Freight Agents | 1/1 | `051400` Office Technology-Office Computer Applications |
| `43-9021` | Data Entry Keyers | 3/4 | `051400` Office Technology-Office Computer Applications; `070210` Software Applications; `070710` Computer Programming |
| `43-9022` | Word Processors and Typists | 1/1 | `051400` Office Technology-Office Computer Applications |
| `43-9031` | Desktop Publishers | 4/5 | `061400` Digital Media; `061410` Multimedia; `061450` Desktop Publishing; `061460` Computer Graphics and Digital Imagery |
| `43-9041` | Insurance Claims and Policy Processing Clerks | 1/1 | `051400` Office Technology-Office Computer Applications |
| `43-9061` | Office Clerks, General | 1/1 | `051400` Office Technology-Office Computer Applications |
| `43-9081` | Proofreaders and Copy Markers | 1/1 | `060200` Journalism |
| `49-2021` | Radio, Cellular, and Tower Equipment Installers and Repairers | 1/1 | `093430` Telecommunications Technology |
| `49-2022` | Telecommunications Equipment Installers and Repairers, Except Line Installers | 1/1 | `093430` Telecommunications Technology |
| `49-2097` | Audiovisual Equipment Installers and Repairers | 1/1 | `093430` Telecommunications Technology |
| `49-9052` | Telecommunications Line Installers and Repairers | 1/1 | `093430` Telecommunications Technology |
| `51-5111` | Prepress Technicians and Workers | 4/5 | `061400` Digital Media; `061410` Multimedia; `061450` Desktop Publishing; `061460` Computer Graphics and Digital Imagery |

### Advanced Manufacturing  (53 occupations)
| SOC | Title | Vote | Contributing TOPs |
|---|---|---|---|
| `11-9041` | Architectural and Engineering Managers | 3/5 | `092400` Engineering Technology, General; `093400` Electronics and Electric Technology; `095000` Aeronautical and Aviation Technology |
| `17-1022` | Surveyors | 1/1 | `095730` Surveying |
| `17-2011` | Aerospace Engineers | 1/1 | `095000` Aeronautical and Aviation Technology |
| `17-2061` | Computer Hardware Engineers | 1/1 | `093400` Electronics and Electric Technology |
| `17-2071` | Electrical Engineers | 1/1 | `093400` Electronics and Electric Technology |
| `17-2199` | Engineers, All Other | 2/3 | `092400` Engineering Technology, General; `093400` Electronics and Electric Technology |
| `17-3012` | Electrical and Electronics Drafters | 5/8 | `092400` Engineering Technology, General; `093400` Electronics and Electric Technology; `093410` Computer Electronics; `095330` Electrical, Electronic, and Electro-Mechanical Drafting; `095600` Manufacturing and Industrial Technology |
| `17-3013` | Mechanical Drafters | 6/9 | `092400` Engineering Technology, General; `094500` Industrial Systems Technology and Maintenance; `095000` Aeronautical and Aviation Technology; `095040` Aircraft Electronics (Avionics); `095340` Mechanical Drafting; `095600` Manufacturing and Industrial Technology |
| `17-3019` | Drafters, All Other | 3/5 | `092400` Engineering Technology, General; `095600` Manufacturing and Industrial Technology; `095730` Surveying |
| `17-3021` | Aerospace Engineering and Operations Technologists and Technicians | 5/5 | `092400` Engineering Technology, General; `093400` Electronics and Electric Technology; `093410` Computer Electronics; `095000` Aeronautical and Aviation Technology; `095040` Aircraft Electronics (Avionics) |
| `17-3024` | Electro-Mechanical and Mechatronics Technologists and Technicians | 6/8 | `092400` Engineering Technology, General; `093400` Electronics and Electric Technology; `093410` Computer Electronics; `094300` Instrumentation Technology; `094500` Industrial Systems Technology and Maintenance; `095600` Manufacturing and Industrial Technology |
| `17-3026` | Industrial Engineering Technologists and Technicians | 7/8 | `092400` Engineering Technology, General; `093420` Industrial Electronics; `094500` Industrial Systems Technology and Maintenance; `095050` Aircraft Fabrication; `095600` Manufacturing and Industrial Technology; `095630` Machining and Machine Tools; `095670` Industrial and Occupational Safety and Health |
| `17-3027` | Mechanical Engineering Technologists and Technicians | 3/4 | `092400` Engineering Technology, General; `094500` Industrial Systems Technology and Maintenance; `095600` Manufacturing and Industrial Technology |
| `17-3028` | Calibration Technologists and Technicians | 4/7 | `093400` Electronics and Electric Technology; `093410` Computer Electronics; `094300` Instrumentation Technology; `094500` Industrial Systems Technology and Maintenance |
| `17-3029` | Engineering Technologists and Technicians, Except Drafters, All Other | 8/21 | `092400` Engineering Technology, General; `093400` Electronics and Electric Technology; `093410` Computer Electronics; `093480` Laser and Optical Technology; `094500` Industrial Systems Technology and Maintenance; `095420` Plastics and Composites; `095600` Manufacturing and Industrial Technology; `095650` Welding Technology |
| `19-2042` | Geoscientists, Except Hydrologists and Geographers | 1/1 | `192000` Ocean Technology |
| `19-2099` | Physical Scientists, All Other | 1/1 | `192000` Ocean Technology |
| `19-4043` | Geological Technicians, Except Hydrologic Technicians | 3/5 | `095430` Petroleum Technology; `095600` Manufacturing and Industrial Technology; `192000` Ocean Technology |
| `19-4044` | Hydrologic Technicians | 1/1 | `192000` Ocean Technology |
| `19-5011` | Occupational Health and Safety Specialists | 1/1 | `095670` Industrial and Occupational Safety and Health |
| `19-5012` | Occupational Health and Safety Technicians | 1/1 | `095670` Industrial and Occupational Safety and Health |
| `27-1029` | Designers, All Other | 2/5 | `095360` Technical Illustration; `095600` Manufacturing and Industrial Technology |
| `47-2011` | Boilermakers | 1/1 | `095600` Manufacturing and Industrial Technology |
| `49-2011` | Computer, Automated Teller, and Office Machine Repairers | 1/1 | `093410` Computer Electronics |
| `49-2091` | Avionics Technicians | 2/2 | `095000` Aeronautical and Aviation Technology; `095040` Aircraft Electronics (Avionics) |
| `49-2094` | Electrical and Electronics Repairers, Commercial and Industrial Equipment | 2/3 | `093410` Computer Electronics; `093420` Industrial Electronics |
| `49-9031` | Home Appliance Repairers | 1/1 | `093510` Appliance Repair |
| `49-9069` | Precision Instrument and Equipment Repairers, All Other | 2/4 | `094300` Instrumentation Technology; `094500` Industrial Systems Technology and Maintenance |
| `51-2011` | Aircraft Structure, Surfaces, Rigging, and Systems Assemblers | 3/5 | `095000` Aeronautical and Aviation Technology; `095040` Aircraft Electronics (Avionics); `095050` Aircraft Fabrication |
| `51-2041` | Structural Metal Fabricators and Fitters | 1/1 | `095630` Machining and Machine Tools |
| `51-4021` | Extruding and Drawing Machine Setters, Operators, and Tenders, Metal and Plastic | 1/1 | `095630` Machining and Machine Tools |
| `51-4022` | Forging Machine Setters, Operators, and Tenders, Metal and Plastic | 1/1 | `095630` Machining and Machine Tools |
| `51-4023` | Rolling Machine Setters, Operators, and Tenders, Metal and Plastic | 2/3 | `095630` Machining and Machine Tools; `095650` Welding Technology |
| `51-4031` | Cutting, Punching, and Press Machine Setters, Operators, and Tenders, Metal and Plastic | 2/3 | `095630` Machining and Machine Tools; `095650` Welding Technology |
| `51-4032` | Drilling and Boring Machine Tool Setters, Operators, and Tenders, Metal and Plastic | 1/1 | `095630` Machining and Machine Tools |
| `51-4033` | Grinding, Lapping, Polishing, and Buffing Machine Tool Setters, Operators, and Tenders, Metal and Plastic | 1/1 | `095630` Machining and Machine Tools |
| `51-4034` | Lathe and Turning Machine Tool Setters, Operators, and Tenders, Metal and Plastic | 1/1 | `095630` Machining and Machine Tools |
| `51-4035` | Milling and Planing Machine Setters, Operators, and Tenders, Metal and Plastic | 1/1 | `095630` Machining and Machine Tools |
| `51-4041` | Machinists | 1/1 | `095630` Machining and Machine Tools |
| `51-4081` | Multiple Machine Tool Setters, Operators, and Tenders, Metal and Plastic | 1/1 | `095630` Machining and Machine Tools |
| `51-4111` | Tool and Die Makers | 1/1 | `095630` Machining and Machine Tools |
| `51-4121` | Welders, Cutters, Solderers, and Brazers | 1/1 | `095650` Welding Technology |
| `51-4122` | Welding, Soldering, and Brazing Machine Setters, Operators, and Tenders | 1/1 | `095650` Welding Technology |
| `51-4191` | Heat Treating Equipment Setters, Operators, and Tenders, Metal and Plastic | 1/1 | `095630` Machining and Machine Tools |
| `51-4192` | Layout Workers, Metal and Plastic | 1/1 | `095630` Machining and Machine Tools |
| `51-4194` | Tool Grinders, Filers, and Sharpeners | 1/1 | `095630` Machining and Machine Tools |
| `51-4199` | Metal Workers and Plastic Workers, All Other | 1/1 | `095630` Machining and Machine Tools |
| `51-5112` | Printing Press Operators | 1/1 | `093600` Printing and Lithography |
| `51-8092` | Gas Plant Operators | 1/1 | `095430` Petroleum Technology |
| `51-9061` | Inspectors, Testers, Sorters, Samplers, and Weighers | 1/1 | `095680` Industrial Quality Control |
| `51-9083` | Ophthalmic Laboratory Technicians | 1/1 | `096100` Optics |
| `51-9161` | Computer Numerically Controlled Tool Operators | 1/1 | `095630` Machining and Machine Tools |
| `51-9162` | Computer Numerically Controlled Tool Programmers | 1/1 | `095630` Machining and Machine Tools |

### Advanced Transportation and Logistics  (51 occupations)
| SOC | Title | Vote | Contributing TOPs |
|---|---|---|---|
| `13-1032` | Insurance Appraisers, Auto Damage | 2/3 | `094700` Diesel Technology; `094900` Automotive Collision Repair |
| `43-5061` | Production, Planning, and Expediting Clerks | 1/1 | `051000` Logistics and Materials Transportation |
| `45-2091` | Agricultural Equipment Operators | 2/3 | `094720` Heavy Equipment Maintenance; `094730` Heavy Equipment Operation |
| `45-4022` | Logging Equipment Operators | 2/2 | `094700` Diesel Technology; `094730` Heavy Equipment Operation |
| `47-2071` | Paving, Surfacing, and Tamping Equipment Operators | 2/2 | `094700` Diesel Technology; `094730` Heavy Equipment Operation |
| `47-2072` | Pile Driver Operators | 2/2 | `094700` Diesel Technology; `094730` Heavy Equipment Operation |
| `47-2073` | Operating Engineers and Other Construction Equipment Operators | 2/2 | `094700` Diesel Technology; `094730` Heavy Equipment Operation |
| `47-4051` | Highway Maintenance Workers | 2/3 | `094700` Diesel Technology; `094730` Heavy Equipment Operation |
| `47-4061` | Rail-Track Laying and Maintenance Equipment Operators | 2/2 | `094700` Diesel Technology; `094730` Heavy Equipment Operation |
| `47-5022` | Excavating and Loading Machine and Dragline Operators, Surface Mining | 2/2 | `094700` Diesel Technology; `094730` Heavy Equipment Operation |
| `47-5023` | Earth Drillers, Except Oil and Gas | 2/2 | `094700` Diesel Technology; `094730` Heavy Equipment Operation |
| `47-5032` | Explosives Workers, Ordnance Handling Experts, and Blasters | 2/2 | `094700` Diesel Technology; `094730` Heavy Equipment Operation |
| `47-5041` | Continuous Mining Machine Operators | 2/2 | `094700` Diesel Technology; `094730` Heavy Equipment Operation |
| `47-5049` | Underground Mining Machine Operators, All Other | 2/2 | `094700` Diesel Technology; `094730` Heavy Equipment Operation |
| `47-5099` | Extraction Workers, All Other | 2/2 | `094700` Diesel Technology; `094730` Heavy Equipment Operation |
| `49-2093` | Electrical and Electronics Installers and Repairers, Transportation Equipment | 2/2 | `094800` Automotive Technology; `094840` Alternative Fuels and Advanced Transportation Technology |
| `49-2096` | Electronic Equipment Installers and Repairers, Motor Vehicles | 2/2 | `094800` Automotive Technology; `094840` Alternative Fuels and Advanced Transportation Technology |
| `49-3021` | Automotive Body and Related Repairers | 2/2 | `094700` Diesel Technology; `094900` Automotive Collision Repair |
| `49-3022` | Automotive Glass Installers and Repairers | 2/2 | `094700` Diesel Technology; `094900` Automotive Collision Repair |
| `49-3023` | Automotive Service Technicians and Mechanics | 2/3 | `094800` Automotive Technology; `094840` Alternative Fuels and Advanced Transportation Technology |
| `49-3031` | Bus and Truck Mechanics and Diesel Engine Specialists | 1/1 | `094700` Diesel Technology |
| `49-3042` | Mobile Heavy Equipment Mechanics, Except Engines | 2/3 | `094700` Diesel Technology; `094720` Heavy Equipment Maintenance |
| `49-3043` | Rail Car Repairers | 2/2 | `094700` Diesel Technology; `094720` Heavy Equipment Maintenance |
| `49-3051` | Motorboat Mechanics and Service Technicians | 2/2 | `094830` Motorcycle, Outboard and Small Engine Repair; `095900` Marine Technology |
| `49-3052` | Motorcycle Mechanics | 1/1 | `094830` Motorcycle, Outboard and Small Engine Repair |
| `49-3053` | Outdoor Power Equipment and Other Small Engine Mechanics | 1/1 | `094830` Motorcycle, Outboard and Small Engine Repair |
| `49-3092` | Recreational Vehicle Service Technicians | 1/1 | `094850` Recreational Vehicle Service |
| `51-6093` | Upholsterers | 1/1 | `094910` Upholstery Repair - Automotive |
| `51-9124` | Coating, Painting, and Spraying Machine Setters, Operators, and Tenders | 2/2 | `094700` Diesel Technology; `094900` Automotive Collision Repair |
| `53-2011` | Airline Pilots, Copilots, and Flight Engineers | 1/1 | `302020` Piloting |
| `53-2012` | Commercial Pilots | 1/1 | `302020` Piloting |
| `53-2021` | Air Traffic Controllers | 1/1 | `302030` Air Traffic Control |
| `53-2022` | Airfield Operations Specialists | 1/1 | `302030` Air Traffic Control |
| `53-3032` | Heavy and Tractor-Trailer Truck Drivers | 1/1 | `094750` Truck and Bus Driving |
| `53-3033` | Light Truck Drivers | 1/1 | `094750` Truck and Bus Driving |
| `53-3051` | Bus Drivers, School | 1/1 | `094750` Truck and Bus Driving |
| `53-3052` | Bus Drivers, Transit and Intercity | 1/1 | `094750` Truck and Bus Driving |
| `53-3053` | Shuttle Drivers and Chauffeurs | 1/1 | `094750` Truck and Bus Driving |
| `53-4011` | Locomotive Engineers | 1/1 | `094740` Railroad and Light Rail Operations |
| `53-4013` | Rail Yard Engineers, Dinkey Operators, and Hostlers | 1/1 | `094740` Railroad and Light Rail Operations |
| `53-4022` | Railroad Brake, Signal, and Switch Operators and Locomotive Firers | 1/1 | `094740` Railroad and Light Rail Operations |
| `53-4031` | Railroad Conductors and Yardmasters | 1/1 | `094740` Railroad and Light Rail Operations |
| `53-4041` | Subway and Streetcar Operators | 1/1 | `094740` Railroad and Light Rail Operations |
| `53-4099` | Rail Transportation Workers, All Other | 1/1 | `094740` Railroad and Light Rail Operations |
| `53-5021` | Captains, Mates, and Pilots of Water Vessels | 1/1 | `095900` Marine Technology |
| `53-5022` | Motorboat Operators | 1/1 | `095900` Marine Technology |
| `53-5031` | Ship Engineers | 1/1 | `095900` Marine Technology |
| `53-7021` | Crane and Tower Operators | 2/2 | `094700` Diesel Technology; `094730` Heavy Equipment Operation |
| `53-7031` | Dredge Operators | 2/2 | `094700` Diesel Technology; `094730` Heavy Equipment Operation |
| `53-7041` | Hoist and Winch Operators | 2/2 | `094700` Diesel Technology; `094730` Heavy Equipment Operation |
| `53-7199` | Material Moving Workers, All Other | 2/2 | `094700` Diesel Technology; `094730` Heavy Equipment Operation |

### Energy, Construction and Utilities  (49 occupations)
| SOC | Title | Vote | Contributing TOPs |
|---|---|---|---|
| `17-1011` | Architects, Except Landscape and Naval | 1/1 | `020100` Architecture and Architectural Technology |
| `17-1012` | Landscape Architects | 1/1 | `020100` Architecture and Architectural Technology |
| `17-3011` | Architectural and Civil Drafters | 4/8 | `020100` Architecture and Architectural Technology; `095300` Drafting Technology; `095310` Architectural Drafting; `095320` Civil Drafting |
| `17-3022` | Civil Engineering Technologists and Technicians | 5/6 | `020100` Architecture and Architectural Technology; `095200` Construction Crafts Technology; `095700` Civil and Construction Management Technology; `095720` Construction Inspection; `210210` Public Works |
| `17-3025` | Environmental Engineering Technologists and Technicians | 2/4 | `094610` Energy Systems Technology; `095800` Water and Wastewater Technology |
| `19-4051` | Nuclear Technicians | 1/1 | `094610` Energy Systems Technology |
| `27-1021` | Commercial and Industrial Designers | 3/8 | `094600` Environmental Control Technology; `094610` Energy Systems Technology; `095300` Drafting Technology |
| `37-1011` | First-Line Supervisors of Housekeeping and Janitorial Workers | 2/4 | `095200` Construction Crafts Technology; `095700` Civil and Construction Management Technology |
| `47-1011` | First-Line Supervisors of Construction Trades and Extraction Workers | 13/15 | `094600` Environmental Control Technology; `095200` Construction Crafts Technology; `095210` Carpentry; `095220` Electrical; `095230` Plumbing, Pipefitting and Steamfitting; `095240` Glazing; `095260` Masonry, Tile, Cement, Lath and Plaster; `095270` Painting, Decorating, and Flooring; `095280` Drywall and Insulation; `095290` Roofing; `095700` Civil and Construction Management Technology; `095720` Construction Inspection; `210210` Public Works |
| `47-2021` | Brickmasons and Blockmasons | 1/1 | `095260` Masonry, Tile, Cement, Lath and Plaster |
| `47-2022` | Stonemasons | 1/1 | `095260` Masonry, Tile, Cement, Lath and Plaster |
| `47-2031` | Carpenters | 1/1 | `095210` Carpentry |
| `47-2041` | Carpet Installers | 2/2 | `095260` Masonry, Tile, Cement, Lath and Plaster; `095270` Painting, Decorating, and Flooring |
| `47-2042` | Floor Layers, Except Carpet, Wood, and Hard Tiles | 2/2 | `095260` Masonry, Tile, Cement, Lath and Plaster; `095270` Painting, Decorating, and Flooring |
| `47-2043` | Floor Sanders and Finishers | 2/2 | `095260` Masonry, Tile, Cement, Lath and Plaster; `095270` Painting, Decorating, and Flooring |
| `47-2044` | Tile and Stone Setters | 2/2 | `095260` Masonry, Tile, Cement, Lath and Plaster; `095270` Painting, Decorating, and Flooring |
| `47-2051` | Cement Masons and Concrete Finishers | 1/1 | `095260` Masonry, Tile, Cement, Lath and Plaster |
| `47-2053` | Terrazzo Workers and Finishers | 2/2 | `095260` Masonry, Tile, Cement, Lath and Plaster; `095270` Painting, Decorating, and Flooring |
| `47-2081` | Drywall and Ceiling Tile Installers | 1/1 | `095280` Drywall and Insulation |
| `47-2111` | Electricians | 1/1 | `095220` Electrical |
| `47-2121` | Glaziers | 1/1 | `095240` Glazing |
| `47-2131` | Insulation Workers, Floor, Ceiling, and Wall | 1/1 | `094600` Environmental Control Technology |
| `47-2132` | Insulation Workers, Mechanical | 1/1 | `094600` Environmental Control Technology |
| `47-2141` | Painters, Construction and Maintenance | 1/1 | `095270` Painting, Decorating, and Flooring |
| `47-2142` | Paperhangers | 1/1 | `095270` Painting, Decorating, and Flooring |
| `47-2152` | Plumbers, Pipefitters, and Steamfitters | 1/1 | `095230` Plumbing, Pipefitting and Steamfitting |
| `47-2181` | Roofers | 1/1 | `095290` Roofing |
| `47-2221` | Structural Iron and Steel Workers | 1/1 | `095640` Sheet Metal and Structural Metal |
| `47-2231` | Solar Photovoltaic Installers | 3/4 | `094610` Energy Systems Technology; `095200` Construction Crafts Technology; `095290` Roofing |
| `47-4011` | Construction and Building Inspectors | 2/2 | `095720` Construction Inspection; `210210` Public Works |
| `47-4071` | Septic Tank Servicers and Sewer Pipe Cleaners | 1/1 | `095230` Plumbing, Pipefitting and Steamfitting |
| `49-1011` | First-Line Supervisors of Mechanics, Installers, and Repairers | 3/8 | `093440` Electrical Systems and Power Transmission; `094610` Energy Systems Technology; `095220` Electrical |
| `49-2092` | Electric Motor, Power Tool, and Related Repairers | 2/4 | `093440` Electrical Systems and Power Transmission; `095220` Electrical |
| `49-2098` | Security and Fire Alarm Systems Installers | 1/1 | `095220` Electrical |
| `49-9021` | Heating, Air Conditioning, and Refrigeration Mechanics and Installers | 2/2 | `094600` Environmental Control Technology; `094610` Energy Systems Technology |
| `49-9051` | Electrical Power-Line Installers and Repairers | 3/4 | `093440` Electrical Systems and Power Transmission; `094610` Energy Systems Technology; `095220` Electrical |
| `49-9071` | Maintenance and Repair Workers, General | 2/4 | `095200` Construction Crafts Technology; `095700` Civil and Construction Management Technology |
| `49-9095` | Manufactured Building and Mobile Home Installers | 1/1 | `095700` Civil and Construction Management Technology |
| `49-9097` | Signal and Track Switch Repairers | 1/1 | `095220` Electrical |
| `49-9099` | Installation, Maintenance, and Repair Workers, All Other | 3/5 | `093440` Electrical Systems and Power Transmission; `094610` Energy Systems Technology; `095220` Electrical |
| `51-4071` | Foundry Mold and Coremakers | 1/1 | `095200` Construction Crafts Technology |
| `51-7011` | Cabinetmakers and Bench Carpenters | 1/1 | `095250` Mill and Cabinet Work |
| `51-7031` | Model Makers, Wood | 1/1 | `095250` Mill and Cabinet Work |
| `51-7032` | Patternmakers, Wood | 1/1 | `095250` Mill and Cabinet Work |
| `51-7041` | Sawing Machine Setters, Operators, and Tenders, Wood | 1/1 | `095250` Mill and Cabinet Work |
| `51-7042` | Woodworking Machine Setters, Operators, and Tenders, Except Sawing | 1/1 | `095250` Mill and Cabinet Work |
| `51-7099` | Woodworkers, All Other | 1/1 | `095250` Mill and Cabinet Work |
| `51-8011` | Nuclear Power Reactor Operators | 1/1 | `094610` Energy Systems Technology |
| `51-8031` | Water and Wastewater Treatment Plant and System Operators | 1/1 | `095800` Water and Wastewater Technology |

### Health  (46 occupations)
| SOC | Title | Vote | Contributing TOPs |
|---|---|---|---|
| `11-9111` | Medical and Health Services Managers | 6/7 | `120100` Health Occupations, General; `120200` Hospital and Health Care Administration; `120830` Health Facility Unit Coordinator; `122300` Health Information Technology; `122400` School Health Clerk; `126100` Community Health Care Worker |
| `19-1042` | Medical Scientists, Except Epidemiologists | 1/1 | `130900` Gerontology |
| `21-1091` | Health Education Specialists | 1/1 | `120100` Health Occupations, General |
| `21-1094` | Community Health Workers | 2/2 | `120100` Health Occupations, General; `126100` Community Health Care Worker |
| `27-2021` | Athletes and Sports Competitors | 1/1 | `120100` Health Occupations, General |
| `27-2022` | Coaches and Scouts | 2/4 | `120100` Health Occupations, General; `122800` Athletic Training and Sports Medicine |
| `29-1031` | Dietitians and Nutritionists | 3/5 | `130600` Nutrition, Foods, and Culinary Arts; `130620` Dietetic Services and Management; `130660` Dietetic Technology |
| `29-1071` | Physician Assistants | 1/1 | `120600` Physicians Assistant |
| `29-1124` | Radiation Therapists | 2/2 | `122500` Radiologic Technology; `122600` Radiation Therapy Technician |
| `29-1126` | Respiratory Therapists | 1/1 | `121000` Respiratory Care-Therapy |
| `29-1127` | Speech-Language Pathologists | 1/1 | `122000` Speech-Language Pathology and Audiology |
| `29-1141` | Registered Nurses | 2/2 | `123000` Nursing; `123010` Registered Nursing |
| `29-1181` | Audiologists | 1/1 | `122000` Speech-Language Pathology and Audiology |
| `29-1292` | Dental Hygienists | 2/2 | `124000` Dental Occupations; `124020` Dental Hygienist |
| `29-2031` | Cardiovascular Technologists and Technicians | 2/2 | `121300` Cardiovascular Technician; `121500` Electrocardiography |
| `29-2032` | Diagnostic Medical Sonographers | 1/1 | `122700` Diagnostic Medical Sonography |
| `29-2033` | Nuclear Medicine Technologists | 1/1 | `122500` Radiologic Technology |
| `29-2034` | Radiologic Technologists and Technicians | 2/2 | `122500` Radiologic Technology; `122600` Radiation Therapy Technician |
| `29-2035` | Magnetic Resonance Imaging Technologists | 1/1 | `122700` Diagnostic Medical Sonography |
| `29-2036` | Medical Dosimetrists | 2/2 | `122500` Radiologic Technology; `122600` Radiation Therapy Technician |
| `29-2042` | Emergency Medical Technicians | 2/2 | `125000` Emergency Medical Services; `125100` Paramedic |
| `29-2043` | Paramedics | 2/2 | `125000` Emergency Medical Services; `125100` Paramedic |
| `29-2051` | Dietetic Technicians | 3/3 | `130600` Nutrition, Foods, and Culinary Arts; `130620` Dietetic Services and Management; `130660` Dietetic Technology |
| `29-2052` | Pharmacy Technicians | 1/1 | `122100` Pharmacy Technology |
| `29-2053` | Psychiatric Technicians | 1/1 | `123900` Psychiatric Technician |
| `29-2055` | Surgical Technologists | 2/2 | `120900` Hospital Central Service Technician; `121700` Surgical Technician |
| `29-2057` | Ophthalmic Medical Technicians | 1/1 | `121900` Optical Technology |
| `29-2061` | Licensed Practical and Licensed Vocational Nurses | 2/2 | `123000` Nursing; `123020` Licensed Vocational Nursing |
| `29-2072` | Medical Records Specialists | 4/4 | `051420` Medical Office Technology; `120200` Hospital and Health Care Administration; `122300` Health Information Technology; `122310` Health Information Coding |
| `29-2099` | Health Technologists and Technicians, All Other | 6/6 | `121000` Respiratory Care-Therapy; `121100` Polysomnography; `121200` Electro-Neurodiagnostic Technology; `122500` Radiologic Technology; `122600` Radiation Therapy Technician; `129900` Other Health Occupations |
| `29-9021` | Health Information Technologists and Medical Registrars | 4/4 | `051420` Medical Office Technology; `120200` Hospital and Health Care Administration; `122300` Health Information Technology; `122310` Health Information Coding |
| `29-9093` | Surgical Assistants | 1/1 | `121700` Surgical Technician |
| `29-9099` | Healthcare Practitioners and Technical Workers, All Other | 1/1 | `120830` Health Facility Unit Coordinator |
| `31-1131` | Nursing Assistants | 4/4 | `122400` School Health Clerk; `123000` Nursing; `123030` Certified Nurse Assistant; `123080` Home Health Aide |
| `31-1133` | Psychiatric Aides | 2/2 | `123080` Home Health Aide; `123900` Psychiatric Technician |
| `31-2011` | Occupational Therapy Assistants | 1/1 | `121800` Occupational Therapy Technology |
| `31-2012` | Occupational Therapy Aides | 1/1 | `121800` Occupational Therapy Technology |
| `31-2021` | Physical Therapist Assistants | 2/2 | `121400` Orthopedic Assistant; `122200` Physical Therapist Assistant |
| `31-2022` | Physical Therapist Aides | 2/2 | `121800` Occupational Therapy Technology; `122200` Physical Therapist Assistant |
| `31-9091` | Dental Assistants | 2/2 | `124000` Dental Occupations; `124010` Dental Assistant |
| `31-9092` | Medical Assistants | 4/4 | `120800` Medical Assisting; `120810` Clinical Medical Assisting; `120820` Administrative Medical Assisting; `120830` Health Facility Unit Coordinator |
| `31-9093` | Medical Equipment Preparers | 1/1 | `120900` Hospital Central Service Technician |
| `31-9097` | Phlebotomists | 2/2 | `120510` Phlebotomy; `129900` Other Health Occupations |
| `31-9099` | Healthcare Support Workers, All Other | 8/8 | `120100` Health Occupations, General; `120800` Medical Assisting; `120820` Administrative Medical Assisting; `120830` Health Facility Unit Coordinator; `120900` Hospital Central Service Technician; `121800` Occupational Therapy Technology; `122310` Health Information Coding; `129900` Other Health Occupations |
| `43-6013` | Medical Secretaries and Administrative Assistants | 5/7 | `051420` Medical Office Technology; `120800` Medical Assisting; `120820` Administrative Medical Assisting; `120830` Health Facility Unit Coordinator; `122310` Health Information Coding |
| `51-9081` | Dental Laboratory Technicians | 1/1 | `124030` Dental Laboratory Technician |

### Unassigned  (30 occupations)
| SOC | Title | Vote | Contributing TOPs |
|---|---|---|---|
| `11-1031` | Legislators | 1/1 | `210200` Public Administration |
| `11-9131` | Postmasters and Mail Superintendents | 1/1 | `210200` Public Administration |
| `21-1013` | Marriage and Family Therapists | 2/4 | `210400` Human Services; `210450` Disability Services |
| `21-1019` | Counselors, All Other | 2/4 | `210400` Human Services; `210450` Disability Services |
| `21-1021` | Child, Family, and School Social Workers | 2/5 | `210400` Human Services; `210450` Disability Services |
| `21-1022` | Healthcare Social Workers | 2/3 | `210400` Human Services; `210450` Disability Services |
| `21-1023` | Mental Health and Substance Abuse Social Workers | 2/3 | `210400` Human Services; `210450` Disability Services |
| `21-1029` | Social Workers, All Other | 2/3 | `210400` Human Services; `210450` Disability Services |
| `21-1092` | Probation Officers and Correctional Treatment Specialists | 2/3 | `210400` Human Services; `210450` Disability Services |
| `21-1093` | Social and Human Service Assistants | 1/1 | `210400` Human Services |
| `23-2011` | Paralegals and Legal Assistants | 1/1 | `140200` Paralegal |
| `23-2093` | Title Examiners, Abstractors, and Searchers | 1/1 | `140200` Paralegal |
| `23-2099` | Legal Support Workers, All Other | 2/3 | `140200` Paralegal; `214000` Legal and Community Interpretation |
| `25-4011` | Archivists | 1/1 | `109900` Other Fine and Applied Arts |
| `25-4012` | Curators | 1/1 | `109900` Other Fine and Applied Arts |
| `25-4013` | Museum Technicians and Conservators | 1/1 | `109900` Other Fine and Applied Arts |
| `25-4031` | Library Technicians | 1/1 | `160200` Library Technician (Aide) |
| `27-1013` | Fine Artists, Including Painters, Sculptors, and Illustrators | 1/1 | `109900` Other Fine and Applied Arts |
| `27-1027` | Set and Exhibit Designers | 2/4 | `100600` Technical Theater; `100900` Applied Design |
| `27-2011` | Actors | 1/1 | `100600` Technical Theater |
| `27-2031` | Dancers | 2/2 | `100600` Technical Theater; `100810` Commercial Dance |
| `27-2032` | Choreographers | 2/2 | `100600` Technical Theater; `100810` Commercial Dance |
| `27-2042` | Musicians and Singers | 1/1 | `100600` Technical Theater |
| `27-2099` | Entertainers and Performers, Sports and Related Workers, All Other | 1/1 | `100600` Technical Theater |
| `27-3092` | Court Reporters and Simultaneous Captioners | 2/3 | `051430` Court Reporting; `214000` Legal and Community Interpretation |
| `29-1129` | Therapists, All Other | 2/3 | `210400` Human Services; `210450` Disability Services |
| `39-6012` | Concierges | 1/1 | `309900` Other Commercial Services |
| `49-9061` | Camera and Photographic Equipment Repairers | 1/1 | `309900` Other Commercial Services |
| `49-9063` | Musical Instrument Repairers and Tuners | 1/1 | `096200` Musical Instrument Repair |
| `49-9094` | Locksmiths and Safe Repairers | 1/1 | `309900` Other Commercial Services |

### Agriculture, Water and Environmental Technologies  (28 occupations)
| SOC | Title | Vote | Contributing TOPs |
|---|---|---|---|
| `11-9013` | Farmers, Ranchers, and Other Agricultural Managers | 13/13 | `010100` Agriculture Technology and Sciences, General; `010200` Animal Science; `010220` Artificial Inseminator; `010230` Dairy Science; `010240` Equine Science; `010300` Plant Science; `010310` Agricultural Pest Control Advisor and Operator; `010400` Viticulture, Enology, and Wine Business; `010900` Horticulture; `010930` Nursery Technology; `011200` Agriculture Business, Sales and Service; `011500` Natural Resources; `011510` Parks and Outdoor Recreation |
| `13-1041` | Compliance Officers | 2/3 | `011520` Wildlife and Fisheries; `030300` Environmental Technology |
| `19-1011` | Animal Scientists | 1/1 | `010100` Agriculture Technology and Sciences, General |
| `19-1012` | Food Scientists and Technologists | 3/3 | `010100` Agriculture Technology and Sciences, General; `010400` Viticulture, Enology, and Wine Business; `011300` Food Processing and Related Technologies |
| `19-1013` | Soil and Plant Scientists | 5/5 | `010100` Agriculture Technology and Sciences, General; `010300` Plant Science; `010310` Agricultural Pest Control Advisor and Operator; `010400` Viticulture, Enology, and Wine Business; `011500` Natural Resources |
| `19-1031` | Conservation Scientists | 3/3 | `011400` Forestry; `011500` Natural Resources; `011520` Wildlife and Fisheries |
| `19-1032` | Foresters | 2/2 | `011400` Forestry; `011500` Natural Resources |
| `19-4012` | Agricultural Technicians | 3/3 | `010100` Agriculture Technology and Sciences, General; `010300` Plant Science; `019900` Other Agriculture and Natural Resources |
| `19-4013` | Food Science Technicians | 2/2 | `010400` Viticulture, Enology, and Wine Business; `011300` Food Processing and Related Technologies |
| `19-4071` | Forest and Conservation Technicians | 3/3 | `011400` Forestry; `011500` Natural Resources; `030300` Environmental Technology |
| `25-9021` | Farm and Home Management Educators | 9/23 | `010200` Animal Science; `010220` Artificial Inseminator; `010230` Dairy Science; `010240` Equine Science; `010300` Plant Science; `010310` Agricultural Pest Control Advisor and Operator; `010900` Horticulture; `010930` Nursery Technology; `011200` Agriculture Business, Sales and Service |
| `29-2056` | Veterinary Technologists and Technicians | 2/2 | `010210` Veterinary Technician (Licensed); `010220` Artificial Inseminator |
| `31-9096` | Veterinary Assistants and Laboratory Animal Caretakers | 2/2 | `010210` Veterinary Technician (Licensed); `010220` Artificial Inseminator |
| `33-3031` | Fish and Game Wardens | 1/1 | `011520` Wildlife and Fisheries |
| `33-9092` | Lifeguards, Ski Patrol, and Other Recreational Protective Service Workers | 1/1 | `011520` Wildlife and Fisheries |
| `37-1012` | First-Line Supervisors of Landscaping, Lawn Service, and Groundskeeping Workers | 4/5 | `010900` Horticulture; `010910` Landscape Design and Maintenance; `010930` Nursery Technology; `010940` Turfgrass Technology |
| `37-3011` | Landscaping and Groundskeeping Workers | 4/5 | `010900` Horticulture; `010910` Landscape Design and Maintenance; `010930` Nursery Technology; `010940` Turfgrass Technology |
| `37-3012` | Pesticide Handlers, Sprayers, and Applicators, Vegetation | 3/3 | `010910` Landscape Design and Maintenance; `010930` Nursery Technology; `010940` Turfgrass Technology |
| `39-2011` | Animal Trainers | 1/1 | `010200` Animal Science |
| `39-2021` | Animal Caretakers | 1/1 | `010240` Equine Science |
| `43-4171` | Receptionists and Information Clerks | 1/1 | `010210` Veterinary Technician (Licensed) |
| `45-1011` | First-Line Supervisors of Farming, Fishing, and Forestry Workers | 13/13 | `010200` Animal Science; `010220` Artificial Inseminator; `010230` Dairy Science; `010240` Equine Science; `010300` Plant Science; `010310` Agricultural Pest Control Advisor and Operator; `010400` Viticulture, Enology, and Wine Business; `010930` Nursery Technology; `011200` Agriculture Business, Sales and Service; `011300` Food Processing and Related Technologies; `011400` Forestry; `011500` Natural Resources; `011510` Parks and Outdoor Recreation |
| `45-2011` | Agricultural Inspectors | 1/1 | `011300` Food Processing and Related Technologies |
| `45-2021` | Animal Breeders | 3/3 | `010200` Animal Science; `010220` Artificial Inseminator; `010240` Equine Science |
| `45-4011` | Forest and Conservation Workers | 2/2 | `010930` Nursery Technology; `011400` Forestry |
| `47-4041` | Hazardous Materials Removal Workers | 1/1 | `030300` Environmental Technology |
| `51-3092` | Food Batchmakers | 2/2 | `010400` Viticulture, Enology, and Wine Business; `011300` Food Processing and Related Technologies |
| `51-9012` | Separating, Filtering, Clarifying, Precipitating, and Still Machine Setters, Operators, and Tenders | 2/2 | `010400` Viticulture, Enology, and Wine Business; `011300` Food Processing and Related Technologies |

### Education and Human Development  (23 occupations)
| SOC | Title | Vote | Contributing TOPs |
|---|---|---|---|
| `11-9031` | Education and Childcare Administrators, Preschool and Daycare | 1/1 | `130580` Child Development Administration and Management |
| `11-9032` | Education Administrators, Kindergarten through Secondary | 1/1 | `130580` Child Development Administration and Management |
| `11-9039` | Education Administrators, All Other | 2/2 | `086000` Educational Technology; `130580` Child Development Administration and Management |
| `13-1151` | Training and Development Specialists | 2/2 | `086000` Educational Technology; `130500` Child Development-Early Care and Education |
| `19-3039` | Psychologists, All Other | 5/8 | `130500` Child Development-Early Care and Education; `130540` Preschool Age Child; `130550` The School Age Child; `130580` Child Development Administration and Management; `130590` Infants and Toddlers |
| `21-1099` | Community and Social Service Specialists, All Other | 2/3 | `130500` Child Development-Early Care and Education; `130560` Parenting and Family Education |
| `25-2011` | Preschool Teachers, Except Special Education | 7/7 | `080200` Educational Aide (Teacher Assistant); `080210` Educational Aide (Teacher Assistant), Bilingual; `130500` Child Development-Early Care and Education; `130540` Preschool Age Child; `130550` The School Age Child; `130580` Child Development Administration and Management; `130590` Infants and Toddlers |
| `25-2012` | Kindergarten Teachers, Except Special Education | 7/7 | `080200` Educational Aide (Teacher Assistant); `080210` Educational Aide (Teacher Assistant), Bilingual; `130500` Child Development-Early Care and Education; `130540` Preschool Age Child; `130550` The School Age Child; `130580` Child Development Administration and Management; `130590` Infants and Toddlers |
| `25-2021` | Elementary School Teachers, Except Special Education | 7/7 | `080200` Educational Aide (Teacher Assistant); `080210` Educational Aide (Teacher Assistant), Bilingual; `130500` Child Development-Early Care and Education; `130540` Preschool Age Child; `130550` The School Age Child; `130580` Child Development Administration and Management; `130590` Infants and Toddlers |
| `25-2022` | Middle School Teachers, Except Special and Career/Technical Education | 1/1 | `080210` Educational Aide (Teacher Assistant), Bilingual |
| `25-2031` | Secondary School Teachers, Except Special and Career/Technical Education | 4/5 | `080210` Educational Aide (Teacher Assistant), Bilingual; `085010` Sign Language Interpreting; `130560` Parenting and Family Education; `130800` Family Studies |
| `25-2051` | Special Education Teachers, Preschool | 3/3 | `080900` Special Education; `130500` Child Development-Early Care and Education; `130520` Children with Special Needs |
| `25-2057` | Special Education Teachers, Middle School | 2/2 | `080900` Special Education; `130520` Children with Special Needs |
| `25-2058` | Special Education Teachers, Secondary School | 2/2 | `080900` Special Education; `130520` Children with Special Needs |
| `25-2059` | Special Education Teachers, All Other | 2/2 | `080900` Special Education; `130520` Children with Special Needs |
| `25-3011` | Adult Basic Education, Adult Secondary Education, and English as a Second Language Instructors | 1/1 | `080210` Educational Aide (Teacher Assistant), Bilingual |
| `25-3099` | Teachers and Instructors, All Other | 3/3 | `080200` Educational Aide (Teacher Assistant); `080210` Educational Aide (Teacher Assistant), Bilingual; `089900` Other Education |
| `25-4022` | Librarians and Media Collections Specialists | 2/2 | `086000` Educational Technology; `130500` Child Development-Early Care and Education |
| `25-9031` | Instructional Coordinators | 2/2 | `086000` Educational Technology; `130500` Child Development-Early Care and Education |
| `25-9044` | Teaching Assistants, Postsecondary | 1/1 | `080200` Educational Aide (Teacher Assistant) |
| `25-9099` | Educational Instruction and Library Workers, All Other | 1/1 | `080200` Educational Aide (Teacher Assistant) |
| `29-1128` | Exercise Physiologists | 1/1 | `083560` Coaching |
| `39-9011` | Childcare Workers | 6/6 | `130500` Child Development-Early Care and Education; `130520` Children with Special Needs; `130540` Preschool Age Child; `130550` The School Age Child; `130580` Child Development Administration and Management; `130590` Infants and Toddlers |

### Public Safety  (18 occupations)
| SOC | Title | Vote | Contributing TOPs |
|---|---|---|---|
| `11-9161` | Emergency Management Directors | 3/4 | `210500` Administration of Justice; `210530` Industrial and Transportation Security; `210550` Police Academy |
| `19-4092` | Forensic Science Technicians | 2/2 | `210500` Administration of Justice; `210540` Forensics, Evidence, and Investigation |
| `33-1011` | First-Line Supervisors of Correctional Officers | 2/2 | `210500` Administration of Justice; `210510` Corrections |
| `33-1012` | First-Line Supervisors of Police and Detectives | 5/8 | `210500` Administration of Justice; `210510` Corrections; `210530` Industrial and Transportation Security; `210540` Forensics, Evidence, and Investigation; `210550` Police Academy |
| `33-1021` | First-Line Supervisors of Firefighting and Prevention Workers | 3/4 | `213300` Fire Technology; `213310` Wildland Fire Technology; `213350` Fire Academy |
| `33-1091` | First-Line Supervisors of Security Workers | 2/2 | `210530` Industrial and Transportation Security; `219900` Other Public and Protective Services |
| `33-1099` | First-Line Supervisors of Protective Service Workers, All Other | 1/1 | `210530` Industrial and Transportation Security |
| `33-2011` | Firefighters | 3/4 | `213300` Fire Technology; `213310` Wildland Fire Technology; `213350` Fire Academy |
| `33-2021` | Fire Inspectors and Investigators | 3/3 | `213300` Fire Technology; `213310` Wildland Fire Technology; `213350` Fire Academy |
| `33-2022` | Forest Fire Inspectors and Prevention Specialists | 3/4 | `213300` Fire Technology; `213310` Wildland Fire Technology; `213350` Fire Academy |
| `33-3011` | Bailiffs | 3/3 | `210500` Administration of Justice; `210540` Forensics, Evidence, and Investigation; `210550` Police Academy |
| `33-3012` | Correctional Officers and Jailers | 3/3 | `210500` Administration of Justice; `210510` Corrections; `210520` Probation and Parole |
| `33-3021` | Detectives and Criminal Investigators | 4/6 | `210500` Administration of Justice; `210510` Corrections; `210540` Forensics, Evidence, and Investigation; `210550` Police Academy |
| `33-3051` | Police and Sheriff's Patrol Officers | 3/4 | `210500` Administration of Justice; `210540` Forensics, Evidence, and Investigation; `210550` Police Academy |
| `33-3052` | Transit and Railroad Police | 2/2 | `210530` Industrial and Transportation Security; `219900` Other Public and Protective Services |
| `33-9021` | Private Detectives and Investigators | 4/4 | `210500` Administration of Justice; `210510` Corrections; `210540` Forensics, Evidence, and Investigation; `210550` Police Academy |
| `33-9031` | Gambling Surveillance Officers and Gambling Investigators | 2/3 | `210530` Industrial and Transportation Security; `219900` Other Public and Protective Services |
| `33-9032` | Security Guards | 2/2 | `210530` Industrial and Transportation Security; `219900` Other Public and Protective Services |

### Retail, Hospitality and Tourism  (16 occupations)
| SOC | Title | Vote | Contributing TOPs |
|---|---|---|---|
| `11-9051` | Food Service Managers | 4/7 | `130630` Culinary Arts; `130700` Hospitality; `130710` Restaurant and Food Services and Management; `130720` Lodging Management |
| `11-9071` | Gambling Managers | 1/1 | `130730` Resort and Club Management |
| `11-9081` | Lodging Managers | 5/5 | `130630` Culinary Arts; `130700` Hospitality; `130710` Restaurant and Food Services and Management; `130720` Lodging Management; `130730` Resort and Club Management |
| `13-1075` | Labor Relations Specialists | 1/1 | `051600` Labor and Industrial Relations |
| `27-1022` | Fashion Designers | 3/4 | `130300` Fashion; `130310` Fashion Design; `130320` Fashion Merchandising |
| `27-1025` | Interior Designers | 1/1 | `130200` Interior Design and Merchandising |
| `35-1011` | Chefs and Head Cooks | 3/4 | `130630` Culinary Arts; `130700` Hospitality; `130710` Restaurant and Food Services and Management |
| `35-1012` | First-Line Supervisors of Food Preparation and Serving Workers | 3/5 | `130630` Culinary Arts; `130700` Hospitality; `130710` Restaurant and Food Services and Management |
| `35-2013` | Cooks, Private Household | 3/3 | `130630` Culinary Arts; `130700` Hospitality; `130710` Restaurant and Food Services and Management |
| `39-1013` | First-Line Supervisors of Gambling Services Workers | 1/1 | `130730` Resort and Club Management |
| `41-3041` | Travel Agents | 2/3 | `130700` Hospitality; `300900` Travel Services and Tourism |
| `41-9011` | Demonstrators and Product Promoters | 1/1 | `050650` Retail Store Operations and Management |
| `43-3041` | Gambling Cage Workers | 1/1 | `130730` Resort and Club Management |
| `49-9092` | Commercial Divers | 1/1 | `095910` Diving and Underwater Safety |
| `51-3011` | Bakers | 1/1 | `130630` Culinary Arts |
| `53-2031` | Flight Attendants | 1/1 | `302040` Flight Attendant |

### Life Sciences - Biotechnology  (7 occupations)
| SOC | Title | Vote | Contributing TOPs |
|---|---|---|---|
| `15-2099` | Mathematical Science Occupations, All Other | 1/1 | `043000` Biotechnology and Biomedical Technology |
| `19-1099` | Life Scientists, All Other | 1/1 | `043000` Biotechnology and Biomedical Technology |
| `19-4021` | Biological Technicians | 2/2 | `043000` Biotechnology and Biomedical Technology; `095500` Laboratory Science Technology |
| `19-4031` | Chemical Technicians | 2/3 | `095400` Chemical Technology; `095500` Laboratory Science Technology |
| `49-9062` | Medical Equipment Repairers | 2/2 | `043000` Biotechnology and Biomedical Technology; `093460` Biomedical Instrumentation |
| `51-8091` | Chemical Plant and System Operators | 2/3 | `095400` Chemical Technology; `095500` Laboratory Science Technology |
| `51-9011` | Chemical Equipment Operators and Tenders | 2/3 | `095400` Chemical Technology; `095500` Laboratory Science Technology |

---

## Tied occupations  (49)
These SOCs have no single-sector plurality — multiple sectors are tied for the top vote count. Each row shows the full sector breakdown with contributing TOPs.
| SOC | Title | Sector breakdown |
|---|---|---|
| `11-9199` | Managers, All Other | **Business and Entrepreneurship** (7): `050100` Business and Commerce, General; `050200` Accounting; `050500` Business Administration; `050600` Business Management; `050630` Management Development and Supervision; `050640` Small Business and Entrepreneurship; `050900` Marketing and Distribution<br>**Information and Communication Technologies - Digital Media** (7): `051400` Office Technology-Office Computer Applications; `061400` Digital Media; `061410` Multimedia; `061430` Website Design and Development; `061460` Computer Graphics and Digital Imagery; `070100` Information Technology, General; `220610` Geographic Information Systems<br>**Public Safety** (4): `210500` Administration of Justice; `210530` Industrial and Transportation Security; `210540` Forensics, Evidence, and Investigation; `213300` Fire Technology<br>**Retail, Hospitality and Tourism** (2): `050650` Retail Store Operations and Management; `300900` Travel Services and Tourism<br>**Education and Human Development** (1): `089900` Other Education<br>**Unassigned** (1): `210200` Public Administration<br>**Energy, Construction and Utilities** (1): `210210` Public Works<br>**Health** (1): `210440` Alcohol and Controlled Substances |
| `43-1011` | First-Line Supervisors of Office and Administrative Support Workers | **Business and Entrepreneurship** (3): `050100` Business and Commerce, General; `050630` Management Development and Supervision; `050970` e-commerce (business emphasis)<br>**Information and Communication Technologies - Digital Media** (3): `051400` Office Technology-Office Computer Applications; `060700` Technical Communication; `070910` E-Commerce (technology emphasis)<br>**Health** (3): `051420` Medical Office Technology; `120820` Administrative Medical Assisting; `120830` Health Facility Unit Coordinator<br>**Agriculture, Water and Environmental Technologies** (2): `010210` Veterinary Technician (Licensed); `011200` Agriculture Business, Sales and Service<br>**Retail, Hospitality and Tourism** (1): `051440` Office Management |
| `41-1011` | First-Line Supervisors of Retail Sales Workers | **Business and Entrepreneurship** (3): `050640` Small Business and Entrepreneurship; `050940` Sales and Salesmanship; `050970` e-commerce (business emphasis)<br>**Retail, Hospitality and Tourism** (3): `050650` Retail Store Operations and Management; `050960` Display; `130320` Fashion Merchandising<br>**Agriculture, Water and Environmental Technologies** (1): `010920` Floriculture - Floristry<br>**Information and Communication Technologies - Digital Media** (1): `070910` E-Commerce (technology emphasis) |
| `19-4042` | Environmental Science and Protection Technicians, Including Health | **Advanced Manufacturing** (2): `092400` Engineering Technology, General; `192000` Ocean Technology<br>**Energy, Construction and Utilities** (2): `094610` Energy Systems Technology; `095800` Water and Wastewater Technology<br>**Agriculture, Water and Environmental Technologies** (1): `030300` Environmental Technology |
| `19-4099` | Life, Physical, and Social Science Technicians, All Other | **Life Sciences - Biotechnology** (2): `095400` Chemical Technology; `095500` Laboratory Science Technology<br>**Advanced Manufacturing** (2): `095600` Manufacturing and Industrial Technology; `192000` Ocean Technology<br>**Public Safety** (2): `210500` Administration of Justice; `210540` Forensics, Evidence, and Investigation |
| `39-9031` | Exercise Trainers and Group Fitness Instructors | **Unassigned** (1): `083520` Fitness Trainer<br>**Education and Human Development** (1): `083560` Coaching<br>**Health** (1): `120100` Health Occupations, General |
| `41-4012` | Sales Representatives, Wholesale and Manufacturing, Except Technical and Scientific Products | **Agriculture, Water and Environmental Technologies** (2): `010400` Viticulture, Enology, and Wine Business; `011200` Agriculture Business, Sales and Service<br>**Retail, Hospitality and Tourism** (2): `050960` Display; `130320` Fashion Merchandising<br>**Business and Entrepreneurship** (1): `050900` Marketing and Distribution |
| `49-3011` | Aircraft Mechanics and Service Technicians | **Advanced Manufacturing** (2): `095000` Aeronautical and Aviation Technology; `095050` Aircraft Fabrication<br>**Advanced Transportation and Logistics** (2): `095010` Aviation Airframe Mechanics; `095020` Aviation Powerplant Mechanics<br>**Agriculture, Water and Environmental Technologies** (1): `011600` Agricultural Power Equipment Technology |
| `49-9012` | Control and Valve Installers and Repairers, Except Mechanical Door | **Energy, Construction and Utilities** (2): `093500` Electro-Mechanical Technology; `094610` Energy Systems Technology<br>**Advanced Manufacturing** (2): `094500` Industrial Systems Technology and Maintenance; `095600` Manufacturing and Industrial Technology<br>**Advanced Transportation and Logistics** (2): `094700` Diesel Technology; `094720` Heavy Equipment Maintenance |
| `11-2021` | Marketing Managers | **Business and Entrepreneurship** (2): `050900` Marketing and Distribution; `050970` e-commerce (business emphasis)<br>**Retail, Hospitality and Tourism** (2): `130310` Fashion Design; `130320` Fashion Merchandising |
| `11-9033` | Education Administrators, Postsecondary | **Health** (1): `120200` Hospital and Health Care Administration<br>**Education and Human Development** (1): `130580` Child Development Administration and Management |
| `13-1121` | Meeting, Convention, and Event Planners | **Business and Entrepreneurship** (1): `050600` Business Management<br>**Retail, Hospitality and Tourism** (1): `130700` Hospitality |
| `13-2052` | Personal Financial Advisors | **Business and Entrepreneurship** (1): `050400` Banking and Finance<br>**Education and Human Development** (1): `130800` Family Studies |
| `17-1021` | Cartographers and Photogrammetrists | **Advanced Manufacturing** (1): `095730` Surveying<br>**Information and Communication Technologies - Digital Media** (1): `220610` Geographic Information Systems |
| `17-3023` | Electrical and Electronic Engineering Technologists and Technicians | **Information and Communication Technologies - Digital Media** (3): `070100` Information Technology, General; `070200` Computer Information Systems; `093430` Telecommunications Technology<br>**Advanced Manufacturing** (3): `092400` Engineering Technology, General; `093400` Electronics and Electric Technology; `093410` Computer Electronics |
| `17-3031` | Surveying and Mapping Technicians | **Advanced Manufacturing** (1): `095730` Surveying<br>**Information and Communication Technologies - Digital Media** (1): `220610` Geographic Information Systems |
| `19-1023` | Zoologists and Wildlife Biologists | **Agriculture, Water and Environmental Technologies** (1): `011520` Wildlife and Fisheries<br>**Advanced Manufacturing** (1): `192000` Ocean Technology |
| `19-1029` | Biological Scientists, All Other | **Life Sciences - Biotechnology** (1): `043000` Biotechnology and Biomedical Technology<br>**Advanced Manufacturing** (1): `192000` Ocean Technology |
| `19-2041` | Environmental Scientists and Specialists, Including Health | **Agriculture, Water and Environmental Technologies** (1): `030300` Environmental Technology<br>**Advanced Manufacturing** (1): `192000` Ocean Technology |
| `19-3099` | Social Scientists and Related Workers, All Other | **Education and Human Development** (1): `089900` Other Education<br>**Health** (1): `130900` Gerontology |
| `27-2041` | Music Directors and Composers | **Information and Communication Technologies - Digital Media** (1): `100500` Commercial Music<br>**Unassigned** (1): `100600` Technical Theater |
| `27-3031` | Public Relations Specialists | **Business and Entrepreneurship** (1): `050910` Advertising<br>**Retail, Hospitality and Tourism** (1): `060600` Public Relations |
| `27-3091` | Interpreters and Translators | **Education and Human Development** (1): `085010` Sign Language Interpreting<br>**Unassigned** (1): `214000` Legal and Community Interpretation |
| `29-2081` | Opticians, Dispensing | **Advanced Manufacturing** (1): `096100` Optics<br>**Health** (1): `121900` Optical Technology |
| `29-9091` | Athletic Trainers | **Unassigned** (1): `083520` Fitness Trainer<br>**Health** (1): `122800` Athletic Training and Sports Medicine |
| `31-9094` | Medical Transcriptionists | **Business and Entrepreneurship** (1): `050600` Business Management<br>**Health** (1): `120200` Hospital and Health Care Administration |
| `35-2012` | Cooks, Institution and Cafeteria | **Health** (2): `130600` Nutrition, Foods, and Culinary Arts; `130620` Dietetic Services and Management<br>**Retail, Hospitality and Tourism** (2): `130630` Culinary Arts; `130710` Restaurant and Food Services and Management |
| `35-2014` | Cooks, Restaurant | **Health** (1): `130600` Nutrition, Foods, and Culinary Arts<br>**Retail, Hospitality and Tourism** (1): `130630` Culinary Arts |
| `35-2019` | Cooks, All Other | **Health** (1): `130600` Nutrition, Foods, and Culinary Arts<br>**Retail, Hospitality and Tourism** (1): `130630` Culinary Arts |
| `41-1012` | First-Line Supervisors of Non-Retail Sales Workers | **Business and Entrepreneurship** (1): `050940` Sales and Salesmanship<br>**Retail, Hospitality and Tourism** (1): `050960` Display |
| `41-3091` | Sales Representatives of Services, Except Advertising, Insurance, Financial Services, and Travel | **Retail, Hospitality and Tourism** (1): `050650` Retail Store Operations and Management<br>**Business and Entrepreneurship** (1): `050940` Sales and Salesmanship |
| `41-9099` | Sales and Related Workers, All Other | **Retail, Hospitality and Tourism** (1): `050650` Retail Store Operations and Management<br>**Business and Entrepreneurship** (1): `050940` Sales and Salesmanship |
| `43-4151` | Order Clerks | **Information and Communication Technologies - Digital Media** (1): `051400` Office Technology-Office Computer Applications<br>**Business and Entrepreneurship** (1): `051800` Customer Service |
| `43-6012` | Legal Secretaries and Administrative Assistants | **Information and Communication Technologies - Digital Media** (1): `051400` Office Technology-Office Computer Applications<br>**Business and Entrepreneurship** (1): `051410` Legal Office Technology |
| `47-2211` | Sheet Metal Workers | **Energy, Construction and Utilities** (1): `095640` Sheet Metal and Structural Metal<br>**Advanced Manufacturing** (1): `095650` Welding Technology |
| `47-4021` | Elevator and Escalator Installers and Repairers | **Energy, Construction and Utilities** (2): `093500` Electro-Mechanical Technology; `094610` Energy Systems Technology<br>**Advanced Manufacturing** (2): `094500` Industrial Systems Technology and Maintenance; `095600` Manufacturing and Industrial Technology |
| `49-2095` | Electrical and Electronics Repairers, Powerhouse, Substation, and Relay | **Advanced Manufacturing** (2): `093400` Electronics and Electric Technology; `093410` Computer Electronics<br>**Energy, Construction and Utilities** (2): `093440` Electrical Systems and Power Transmission; `094610` Energy Systems Technology |
| `49-3041` | Farm Equipment Mechanics and Service Technicians | **Agriculture, Water and Environmental Technologies** (2): `010910` Landscape Design and Maintenance; `011600` Agricultural Power Equipment Technology<br>**Advanced Transportation and Logistics** (2): `094720` Heavy Equipment Maintenance; `094730` Heavy Equipment Operation |
| `49-9041` | Industrial Machinery Mechanics | **Energy, Construction and Utilities** (2): `093500` Electro-Mechanical Technology; `094610` Energy Systems Technology<br>**Advanced Manufacturing** (2): `094500` Industrial Systems Technology and Maintenance; `095600` Manufacturing and Industrial Technology |
| `49-9043` | Maintenance Workers, Machinery | **Energy, Construction and Utilities** (2): `093500` Electro-Mechanical Technology; `094610` Energy Systems Technology<br>**Advanced Manufacturing** (2): `094500` Industrial Systems Technology and Maintenance; `095600` Manufacturing and Industrial Technology |
| `49-9044` | Millwrights | **Energy, Construction and Utilities** (2): `093500` Electro-Mechanical Technology; `094610` Energy Systems Technology<br>**Advanced Manufacturing** (2): `094500` Industrial Systems Technology and Maintenance; `095600` Manufacturing and Industrial Technology |
| `49-9045` | Refractory Materials Repairers, Except Brickmasons | **Energy, Construction and Utilities** (2): `093500` Electro-Mechanical Technology; `094610` Energy Systems Technology<br>**Advanced Manufacturing** (2): `094500` Industrial Systems Technology and Maintenance; `095600` Manufacturing and Industrial Technology |
| `49-9081` | Wind Turbine Service Technicians | **Energy, Construction and Utilities** (2): `093500` Electro-Mechanical Technology; `094610` Energy Systems Technology<br>**Advanced Manufacturing** (2): `094500` Industrial Systems Technology and Maintenance; `095600` Manufacturing and Industrial Technology |
| `51-4061` | Model Makers, Metal and Plastic | **Energy, Construction and Utilities** (1): `095640` Sheet Metal and Structural Metal<br>**Advanced Manufacturing** (1): `095650` Welding Technology |
| `51-4062` | Patternmakers, Metal and Plastic | **Energy, Construction and Utilities** (1): `095640` Sheet Metal and Structural Metal<br>**Advanced Manufacturing** (1): `095650` Welding Technology |
| `51-6092` | Fabric and Apparel Patternmakers | **Retail, Hospitality and Tourism** (1): `130320` Fashion Merchandising<br>**Advanced Manufacturing** (1): `130330` Fashion Production |
| `51-8013` | Power Plant Operators | **Advanced Manufacturing** (1): `093400` Electronics and Electric Technology<br>**Energy, Construction and Utilities** (1): `094610` Energy Systems Technology |
| `51-9141` | Semiconductor Processing Technicians | **Advanced Manufacturing** (1): `093420` Industrial Electronics<br>**Energy, Construction and Utilities** (1): `093500` Electro-Mechanical Technology |
| `53-6041` | Traffic Technicians | **Advanced Manufacturing** (1): `092400` Engineering Technology, General<br>**Energy, Construction and Utilities** (1): `210210` Public Works |

---

## Untraceable occupations  (6)
These SOCs have TOPs in the crosswalk, but none of those TOPs appear in the PCAH CTE sector file — they would need either a non-CTE sector mapping or exclusion from the classification.
| SOC | Title | TOP6 codes |
|---|---|---|
| `19-2043` | Hydrologists | `030100` Environmental Science; `191400` Geology; `191900` Oceangraphy; `193000` Earth Science; `220600` Geography |
| `27-1012` | Craft Artists | `060100` Media and Communications, General; `100100` Fine Arts, General; `100200` Art; `100210` Painting and Drawing; `100220` Sculpture; `100230` Ceramics; `100700` Dramatic Arts; `100910` Jewelry; `490100` Liberal Arts and Sciences, General |
| `29-1125` | Recreational Therapists | `083580` Adapted Physical Education |
| `49-9064` | Watch and Clock Repairers | `100910` Jewelry |
| `51-2061` | Timing Device Assemblers and Adjusters | `100910` Jewelry |
| `51-9071` | Jewelers and Precious Stone and Metal Workers | `100910` Jewelry |

---

## SOCs with no crosswalk path  (0)
These SOCs have no TOP6→CIP→SOC path at all in the institutional crosswalk. They cannot be classified by this method without an alternate route (e.g., the OEWS industry-occupation matrix).
