# Old vs New Methodology — Per-SOC Quality Comparison

For every direct-CTE supported SOC, compares the existing Neo4j-graph employer pool (LLM-curated, F+ size, current `CTE_NAICS_CODES`) against the expanded methodology pool (0% pct_total filter, E+ size, expanded NAICS). Both restricted to SD/I + LA regions for apples-to-apples comparison.

## Aggregate findings

- Direct-CTE supported SOCs (SD/I + LA): **281**
- Median candidate count (old): **1**
- Median candidate count (new): **645**
- SOCs where new method has ≥ old count: **281 (100.0%)**
- SOCs where new method has ≥2× old count: **155 (55.2%)**
- SOCs where new top-10 includes ≥1 old-method employer: **27 (9.6%)**
- SOCs where old method had employers but new method has none (coverage regression): **61**
- SOCs newly seeded by new method (old=0, new>0): **126**

## Coverage distribution by band

**Strong CTE** (76 SOCs)
- With ≥1 candidate: old 54/76, new 76/76
- Median candidates: old 2, new 673

**Moderate CTE** (205 SOCs)
- With ≥1 candidate: old 101/205, new 205/205
- Median candidates: old 0, new 632

## Per-SOC counts: every direct-CTE SOC

Table includes: SOC, title, band, # supporting colleges, old count, new count, ratio (new/old or 'NEW' if old was 0), top-10 overlap with old, and top pct_total in new method.

| SOC | Title | Band | Coll | Old | New | Δ | Top10∩Old | Top % |
|---|---|---|---:|---:|---:|---|---:|---:|
| `43-3031` | Bookkeeping, Accounting, and Auditing  | Moder | 8/8 | 0 | 4992 | NEW(4992) | 0/10 | 8.9% |
| `43-6014` | Secretaries and Administrative Assista | Moder | 8/8 | 14 | 4992 | 356.6x | 0/10 | 12.1% |
| `43-9061` | Office Clerks, General | Moder | 8/8 | 6 | 4992 | 832.0x | 0/10 | 6.4% |
| `43-1011` | First-Line Supervisors of Office and A | Moder | 8/8 | 0 | 4990 | NEW(4990) | 0/10 | 4.8% |
| `43-4051` | Customer Service Representatives | Moder | 2/8 | 117 | 4925 | 42.1x | 0/10 | 35.9% |
| `43-4171` | Receptionists and Information Clerks | Moder | 2/8 | 31 | 4902 | 158.1x | 1/10 | 9.7% |
| `49-9071` | Maintenance and Repair Workers, Genera | Moder | 8/8 | 161 | 4898 | 30.4x | 0/10 | 14.4% |
| `15-1232` | Computer User Support Specialists | Moder | 8/8 | 0 | 4836 | NEW(4836) | 0/10 | 6.2% |
| `49-1011` | First-Line Supervisors of Mechanics, I | Moder | 8/8 | 43 | 4811 | 111.9x | 0/10 | 4.7% |
| `43-5061` | Production, Planning, and Expediting C | Moder | 2/8 | 8 | 4807 | 600.9x | 0/10 | 1.9% |
| `43-6011` | Executive Secretaries and Executive Ad | Moder | 8/8 | 0 | 4713 | NEW(4713) | 0/10 | 2.5% |
| `41-3091` | Sales Representatives of Services, Exc | Moder | 5/8 | 22 | 4711 | 214.1x | 0/10 | 16.3% |
| `43-3051` | Payroll and Timekeeping Clerks | Moder | 8/8 | 2 | 4699 | 2349.5x | 0/10 | 1.6% |
| `43-4161` | Human Resources Assistants, Except Pay | Stron | 8/8 | 0 | 4386 | NEW(4386) | 0/10 | 0.3% |
| `33-9032` | Security Guards | Moder | 5/8 | 22 | 4376 | 198.9x | 2/10 | 73.7% |
| `53-3033` | Light Truck Drivers | Moder | 2/8 | 35 | 4368 | 124.8x | 0/10 | 30.2% |
| `43-9021` | Data Entry Keyers | Moder | 8/8 | 0 | 4365 | NEW(4365) | 0/10 | 1.7% |
| `11-3071` | Transportation, Storage, and Distribut | Moder | 8/8 | 42 | 3962 | 94.3x | 0/10 | 2.3% |
| `41-1012` | First-Line Supervisors of Non-Retail S | Moder | 5/8 | 0 | 3942 | NEW(3942) | 0/10 | 3.8% |
| `43-3061` | Procurement Clerks | Moder | 8/8 | 0 | 3843 | NEW(3843) | 0/10 | 1.6% |
| `41-4012` | Sales Representatives, Wholesale and M | Moder | 8/8 | 31 | 3835 | 123.7x | 0/10 | 25.9% |
| `51-1011` | First-Line Supervisors of Production a | Moder | 7/8 | 65 | 3828 | 58.9x | 0/10 | 5.9% |
| `15-1231` | Computer Network Support Specialists | Stron | 8/8 | 3 | 3724 | 1241.3x | 0/10 | 2.1% |
| `43-4071` | File Clerks | Moder | 8/8 | 1 | 3678 | 3678.0x | 0/10 | 0.9% |
| `51-9061` | Inspectors, Testers, Sorters, Samplers | Moder | 2/8 | 134 | 3476 | 25.9x | 0/10 | 6.4% |
| `53-3032` | Heavy and Tractor-Trailer Truck Driver | Stron | 2/8 | 52 | 3440 | 66.2x | 0/10 | 58.1% |
| `43-3011` | Bill and Account Collectors | Moder | 8/8 | 0 | 3426 | NEW(3426) | 0/10 | 6.2% |
| `37-3011` | Landscaping and Groundskeeping Workers | Moder | 4/8 | 0 | 3418 | NEW(3418) | 0/10 | 25.1% |
| `41-9099` | Sales and Related Workers, All Other | Moder | 5/8 | 0 | 3202 | NEW(3202) | 0/10 | 1.6% |
| `43-4151` | Order Clerks | Moder | 8/8 | 0 | 3110 | NEW(3110) | 0/10 | 1.0% |
| `41-1011` | First-Line Supervisors of Retail Sales | Moder | 8/8 | 53 | 3051 | 57.6x | 0/10 | 13.2% |
| `47-2111` | Electricians | Moder | 4/8 | 11 | 2936 | 266.9x | 1/10 | 21.5% |
| `49-9099` | Installation, Maintenance, and Repair  | Moder | 8/8 | 2 | 2934 | 1467.0x | 0/10 | 2.7% |
| `47-1011` | First-Line Supervisors of Construction | Moder | 8/8 | 30 | 2671 | 89.0x | 0/10 | 11.8% |
| `49-9041` | Industrial Machinery Mechanics | Moder | 8/8 | 49 | 2619 | 53.4x | 0/10 | 19.7% |
| `49-9021` | Heating, Air Conditioning, and Refrige | Stron | 6/8 | 8 | 2385 | 298.1x | 1/10 | 13.5% |
| `53-3053` | Shuttle Drivers and Chauffeurs | Moder | 2/8 | 0 | 2327 | NEW(2327) | 0/10 | 52.8% |
| `49-3023` | Automotive Service Technicians and Mec | Stron | 8/8 | 35 | 2297 | 65.6x | 2/10 | 23.7% |
| `49-3031` | Bus and Truck Mechanics and Diesel Eng | Moder | 1/8 | 21 | 2269 | 108.0x | 1/10 | 6.9% |
| `51-4121` | Welders, Cutters, Solderers, and Braze | Moder | 4/8 | 23 | 2238 | 97.3x | 0/10 | 14.8% |
| `47-2031` | Carpenters | Moder | 2/8 | 6 | 2228 | 371.3x | 0/10 | 23.6% |
| `37-1011` | First-Line Supervisors of Housekeeping | Moder | 8/8 | 7 | 2216 | 316.6x | 0/10 | 2.7% |
| `47-2152` | Plumbers, Pipefitters, and Steamfitter | Moder | 3/8 | 24 | 2146 | 89.4x | 1/10 | 13.1% |
| `49-9043` | Maintenance Workers, Machinery | Moder | 8/8 | 0 | 2108 | NEW(2108) | 0/10 | 4.4% |
| `51-4041` | Machinists | Moder | 3/8 | 38 | 2081 | 54.8x | 0/10 | 21.9% |
| `35-1012` | First-Line Supervisors of Food Prepara | Moder | 7/8 | 69 | 1997 | 28.9x | 1/10 | 8.3% |
| `23-2011` | Paralegals and Legal Assistants | Stron | 5/8 | 5 | 1994 | 398.8x | 0/10 | 23.0% |
| `51-9124` | Coating, Painting, and Spraying Machin | Moder | 3/8 | 3 | 1953 | 651.0x | 0/10 | 11.8% |
| `19-4099` | Life, Physical, and Social Science Tec | Stron | 8/8 | 3 | 1941 | 647.0x | 0/10 | 1.5% |
| `27-4011` | Audio and Video Technicians | Stron | 8/8 | 8 | 1847 | 230.9x | 0/10 | 3.3% |
| `35-2012` | Cooks, Institution and Cafeteria | Moder | 7/8 | 0 | 1837 | NEW(1837) | 0/10 | 9.3% |
| `19-5012` | Occupational Health and Safety Technic | Moder | 1/8 | 0 | 1798 | NEW(1798) | 0/10 | 0.3% |
| `49-2094` | Electrical and Electronics Repairers,  | Stron | 2/8 | 3 | 1746 | 582.0x | 0/10 | 2.8% |
| `49-3042` | Mobile Heavy Equipment Mechanics, Exce | Moder | 2/8 | 1 | 1738 | 1738.0x | 0/10 | 6.0% |
| `11-9141` | Property, Real Estate, and Community A | Moder | 3/8 | 1 | 1719 | 1719.0x | 0/10 | 4.2% |
| `17-3026` | Industrial Engineering Technologists a | Stron | 8/8 | 5 | 1640 | 328.0x | 0/10 | 2.1% |
| `35-1011` | Chefs and Head Cooks | Moder | 7/8 | 46 | 1622 | 35.3x | 0/10 | 2.6% |
| `17-3029` | Engineering Technologists and Technici | Stron | 8/8 | 1 | 1616 | 1616.0x | 0/10 | 0.7% |
| `51-9161` | Computer Numerically Controlled Tool O | Moder | 3/8 | 22 | 1609 | 73.1x | 0/10 | 11.9% |
| `17-3013` | Mechanical Drafters | Stron | 8/8 | 3 | 1576 | 525.3x | 0/10 | 0.7% |
| `47-2073` | Operating Engineers and Other Construc | Moder | 2/8 | 15 | 1553 | 103.5x | 0/10 | 15.1% |
| `29-2072` | Medical Records Specialists | Stron | 3/8 | 3 | 1540 | 513.3x | 0/10 | 1.3% |
| `33-1091` | First-Line Supervisors of Security Wor | Moder | 5/8 | 7 | 1534 | 219.1x | 2/10 | 2.9% |
| `17-3023` | Electrical and Electronic Engineering  | Stron | 8/8 | 37 | 1528 | 41.3x | 0/10 | 3.3% |
| `39-1022` | First-Line Supervisors of Personal Ser | Moder | 3/8 | 4 | 1512 | 378.0x | 0/10 | 3.3% |
| `43-6013` | Medical Secretaries and Administrative | Moder | 8/8 | 9 | 1469 | 163.2x | 0/10 | 8.9% |
| `19-4031` | Chemical Technicians | Stron | 8/8 | 19 | 1463 | 77.0x | 1/10 | 1.4% |
| `37-1012` | First-Line Supervisors of Landscaping, | Moder | 4/8 | 12 | 1396 | 116.3x | 0/10 | 3.8% |
| `27-4021` | Photographers | Moder | 8/8 | 0 | 1363 | NEW(1363) | 0/10 | 3.1% |
| `29-2061` | Licensed Practical and Licensed Vocati | Stron | 5/8 | 62 | 1350 | 21.8x | 0/10 | 12.4% |
| `11-9051` | Food Service Managers | Moder | 7/8 | 43 | 1324 | 30.8x | 0/10 | 2.3% |
| `21-1093` | Social and Human Service Assistants | Moder | 8/8 | 35 | 1323 | 37.8x | 0/10 | 15.7% |
| `21-1094` | Community Health Workers | Moder | 8/8 | 14 | 1314 | 93.9x | 0/10 | 0.8% |
| `31-9099` | Healthcare Support Workers, All Other | Moder | 8/8 | 2 | 1314 | 657.0x | 0/10 | 1.4% |
| `51-9162` | Computer Numerically Controlled Tool P | Stron | 3/8 | 2 | 1289 | 644.5x | 0/10 | 1.6% |
| `17-3027` | Mechanical Engineering Technologists a | Stron | 8/8 | 6 | 1275 | 212.5x | 0/10 | 0.6% |
| `31-9092` | Medical Assistants | Stron | 2/8 | 49 | 1274 | 26.0x | 0/10 | 15.2% |
| `17-3019` | Drafters, All Other | Stron | 8/8 | 0 | 1246 | NEW(1246) | 0/10 | 0.2% |
| `35-2014` | Cooks, Restaurant | Moder | 7/8 | 0 | 1243 | NEW(1243) | 0/10 | 11.0% |
| `39-9031` | Exercise Trainers and Group Fitness In | Moder | 8/8 | 5 | 1240 | 248.0x | 1/10 | 13.8% |
| `51-4031` | Cutting, Punching, and Press Machine S | Moder | 6/8 | 4 | 1229 | 307.2x | 0/10 | 7.8% |
| `17-3011` | Architectural and Civil Drafters | Stron | 8/8 | 2 | 1220 | 610.0x | 0/10 | 4.9% |
| `39-9011` | Childcare Workers | Moder | 8/8 | 11 | 1219 | 110.8x | 0/10 | 28.6% |
| `51-4081` | Multiple Machine Tool Setters, Operato | Moder | 3/8 | 1 | 1199 | 1199.0x | 0/10 | 4.6% |
| `41-2022` | Parts Salespersons | Moder | 5/8 | 0 | 1163 | NEW(1163) | 0/10 | 20.1% |
| `43-9041` | Insurance Claims and Policy Processing | Moder | 8/8 | 0 | 1163 | NEW(1163) | 0/10 | 7.6% |
| `53-7021` | Crane and Tower Operators | Moder | 2/8 | 1 | 1140 | 1140.0x | 0/10 | 2.7% |
| `29-2052` | Pharmacy Technicians | Moder | 4/8 | 3 | 1134 | 378.0x | 0/10 | 21.4% |
| `47-4011` | Construction and Building Inspectors | Moder | 3/8 | 6 | 1123 | 187.2x | 1/10 | 2.5% |
| `31-1131` | Nursing Assistants | Stron | 6/8 | 74 | 1118 | 15.1x | 0/10 | 33.2% |
| `49-9044` | Millwrights | Moder | 8/8 | 0 | 1089 | NEW(1089) | 0/10 | 2.6% |
| `17-3024` | Electro-Mechanical and Mechatronics Te | Stron | 8/8 | 3 | 1077 | 359.0x | 0/10 | 0.3% |
| `53-7199` | Material Moving Workers, All Other | Moder | 2/8 | 0 | 1071 | NEW(1071) | 0/10 | 1.2% |
| `29-9021` | Health Information Technologists and M | Stron | 3/8 | 0 | 1071 | NEW(1071) | 0/10 | 0.3% |
| `29-2099` | Health Technologists and Technicians,  | Stron | 6/8 | 5 | 1063 | 212.6x | 0/10 | 4.8% |
| `41-9011` | Demonstrators and Product Promoters | Moder | 5/8 | 0 | 1054 | NEW(1054) | 0/10 | 3.4% |
| `39-2021` | Animal Caretakers | Moder | 2/8 | 2 | 1044 | 522.0x | 0/10 | 33.4% |
| `51-8031` | Water and Wastewater Treatment Plant a | Moder | 2/8 | 7 | 1022 | 146.0x | 3/10 | 26.5% |
| `49-2011` | Computer, Automated Teller, and Office | Moder | 2/8 | 0 | 1020 | NEW(1020) | 0/10 | 11.4% |
| `41-3011` | Advertising Sales Agents | Moder | 5/8 | 3 | 1007 | 335.7x | 0/10 | 10.4% |
| `45-1011` | First-Line Supervisors of Farming, Fis | Moder | 8/8 | 6 | 984 | 164.0x | 1/10 | 3.7% |
| `51-2041` | Structural Metal Fabricators and Fitte | Moder | 3/8 | 9 | 968 | 107.6x | 1/10 | 3.8% |
| `27-3099` | Media and Communication Workers, All O | Moder | 8/8 | 0 | 951 | NEW(951) | 0/10 | 1.6% |
| `25-2011` | Preschool Teachers, Except Special Edu | Stron | 8/8 | 4 | 931 | 232.8x | 0/10 | 32.0% |
| `29-2042` | Emergency Medical Technicians | Stron | 6/8 | 3 | 902 | 300.7x | 1/10 | 23.1% |
| `23-2099` | Legal Support Workers, All Other | Stron | 8/8 | 1 | 899 | 899.0x | 0/10 | 1.0% |
| `51-4111` | Tool and Die Makers | Stron | 3/8 | 3 | 893 | 297.7x | 0/10 | 6.3% |
| `43-6012` | Legal Secretaries and Administrative A | Moder | 8/8 | 2 | 873 | 436.5x | 0/10 | 10.4% |
| `17-3028` | Calibration Technologists and Technici | Stron | 8/8 | 1 | 871 | 871.0x | 0/10 | 0.9% |
| `35-2019` | Cooks, All Other | Moder | 7/8 | 0 | 850 | NEW(850) | 0/10 | 4.5% |
| `51-4199` | Metal Workers and Plastic Workers, All | Moder | 3/8 | 1 | 834 | 834.0x | 0/10 | 0.8% |
| `47-2211` | Sheet Metal Workers | Moder | 5/8 | 6 | 827 | 137.8x | 0/10 | 2.2% |
| `49-9062` | Medical Equipment Repairers | Stron | 8/8 | 18 | 821 | 45.6x | 0/10 | 10.0% |
| `33-9021` | Private Detectives and Investigators | Moder | 8/8 | 0 | 819 | NEW(819) | 0/10 | 0.1% |
| `31-2021` | Physical Therapist Assistants | Stron | 3/8 | 2 | 815 | 407.5x | 0/10 | 4.3% |
| `51-4122` | Welding, Soldering, and Brazing Machin | Moder | 4/8 | 0 | 812 | NEW(812) | 0/10 | 1.0% |
| `51-3011` | Bakers | Moder | 5/8 | 0 | 807 | NEW(807) | 0/10 | 21.9% |
| `43-4041` | Credit Authorizers, Checkers, and Cler | Moder | 8/8 | 0 | 803 | NEW(803) | 0/10 | 0.4% |
| `49-9012` | Control and Valve Installers and Repai | Moder | 8/8 | 5 | 797 | 159.4x | 1/10 | 11.6% |
| `17-3012` | Electrical and Electronics Drafters | Stron | 8/8 | 2 | 791 | 395.5x | 0/10 | 0.5% |
| `33-1099` | First-Line Supervisors of Protective S | Moder | 5/8 | 0 | 785 | NEW(785) | 0/10 | 0.4% |
| `51-4033` | Grinding, Lapping, Polishing, and Buff | Moder | 3/8 | 0 | 783 | NEW(783) | 0/10 | 8.2% |
| `49-3021` | Automotive Body and Related Repairers | Moder | 3/8 | 6 | 782 | 130.3x | 1/10 | 11.1% |
| `51-4021` | Extruding and Drawing Machine Setters, | Moder | 3/8 | 4 | 782 | 195.5x | 0/10 | 10.5% |
| `53-3052` | Bus Drivers, Transit and Intercity | Moder | 2/8 | 3 | 780 | 260.0x | 0/10 | 55.6% |
| `43-9022` | Word Processors and Typists | Moder | 8/8 | 0 | 771 | NEW(771) | 0/10 | 0.2% |
| `49-3011` | Aircraft Mechanics and Service Technic | Stron | 2/8 | 11 | 765 | 69.5x | 0/10 | 17.4% |
| `51-4035` | Milling and Planing Machine Setters, O | Moder | 3/8 | 0 | 758 | NEW(758) | 0/10 | 1.8% |
| `51-9011` | Chemical Equipment Operators and Tende | Moder | 8/8 | 9 | 734 | 81.6x | 0/10 | 8.7% |
| `49-2092` | Electric Motor, Power Tool, and Relate | Moder | 8/8 | 0 | 724 | NEW(724) | 0/10 | 1.1% |
| `31-9091` | Dental Assistants | Stron | 2/8 | 0 | 711 | NEW(711) | 0/10 | 33.2% |
| `47-2221` | Structural Iron and Steel Workers | Moder | 1/8 | 4 | 695 | 173.8x | 0/10 | 3.3% |
| `19-4012` | Agricultural Technicians | Stron | 8/8 | 1 | 679 | 679.0x | 0/10 | 2.4% |
| `29-2034` | Radiologic Technologists and Technicia | Stron | 1/8 | 30 | 676 | 22.5x | 1/10 | 5.2% |
| `31-9094` | Medical Transcriptionists | Stron | 8/8 | 1 | 673 | 673.0x | 0/10 | 2.2% |
| `17-3031` | Surveying and Mapping Technicians | Moder | 8/8 | 6 | 670 | 111.7x | 0/10 | 2.1% |
| `31-9097` | Phlebotomists | Stron | 5/8 | 3 | 670 | 223.3x | 0/10 | 13.7% |
| `47-4041` | Hazardous Materials Removal Workers | Moder | 3/8 | 2 | 658 | 329.0x | 0/10 | 17.4% |
| `51-7011` | Cabinetmakers and Bench Carpenters | Moder | 2/8 | 1 | 656 | 656.0x | 0/10 | 3.1% |
| `27-4014` | Sound Engineering Technicians | Stron | 8/8 | 5 | 649 | 129.8x | 1/10 | 11.3% |
| `23-2093` | Title Examiners, Abstractors, and Sear | Moder | 4/8 | 0 | 645 | NEW(645) | 0/10 | 1.8% |
| `51-5111` | Prepress Technicians and Workers | Stron | 8/8 | 6 | 644 | 107.3x | 1/10 | 4.0% |
| `19-4042` | Environmental Science and Protection T | Stron | 8/8 | 4 | 637 | 159.2x | 1/10 | 0.8% |
| `53-3051` | Bus Drivers, School | Moder | 2/8 | 0 | 633 | NEW(633) | 0/10 | 65.5% |
| `43-4131` | Loan Interviewers and Clerks | Moder | 8/8 | 0 | 632 | NEW(632) | 0/10 | 11.6% |
| `39-5012` | Hairdressers, Hairstylists, and Cosmet | Stron | 3/8 | 0 | 629 | NEW(629) | 0/10 | 36.2% |
| `41-9022` | Real Estate Sales Agents | Moder | 3/8 | 0 | 615 | NEW(615) | 0/10 | 3.2% |
| `17-3022` | Civil Engineering Technologists and Te | Stron | 8/8 | 4 | 615 | 153.8x | 0/10 | 1.9% |
| `19-4013` | Food Science Technicians | Stron | 8/8 | 4 | 604 | 151.0x | 0/10 | 1.2% |
| `29-1126` | Respiratory Therapists | Stron | 1/8 | 6 | 588 | 98.0x | 0/10 | 2.6% |
| `51-7042` | Woodworking Machine Setters, Operators | Moder | 2/8 | 1 | 581 | 581.0x | 0/10 | 10.8% |
| `51-9012` | Separating, Filtering, Clarifying, Pre | Moder | 3/8 | 0 | 580 | NEW(580) | 0/10 | 7.4% |
| `27-2099` | Entertainers and Performers, Sports an | Moder | 8/8 | 0 | 567 | NEW(567) | 0/10 | 2.3% |
| `29-2051` | Dietetic Technicians | Stron | 7/8 | 0 | 559 | NEW(559) | 0/10 | 0.4% |
| `47-2071` | Paving, Surfacing, and Tamping Equipme | Moder | 2/8 | 0 | 552 | NEW(552) | 0/10 | 3.8% |
| `51-4034` | Lathe and Turning Machine Tool Setters | Moder | 3/8 | 0 | 551 | NEW(551) | 0/10 | 1.9% |
| `43-5011` | Cargo and Freight Agents | Moder | 8/8 | 10 | 537 | 53.7x | 0/10 | 22.9% |
| `49-9069` | Precision Instrument and Equipment Rep | Moder | 7/8 | 0 | 536 | NEW(536) | 0/10 | 2.4% |
| `51-4023` | Rolling Machine Setters, Operators, an | Moder | 6/8 | 1 | 525 | 525.0x | 0/10 | 7.8% |
| `51-4191` | Heat Treating Equipment Setters, Opera | Moder | 3/8 | 0 | 520 | NEW(520) | 0/10 | 3.1% |
| `27-4015` | Lighting Technicians | Moder | 6/8 | 1 | 514 | 514.0x | 0/10 | 1.9% |
| `43-9031` | Desktop Publishers | Stron | 8/8 | 0 | 513 | NEW(513) | 0/10 | 0.6% |
| `51-7041` | Sawing Machine Setters, Operators, and | Moder | 2/8 | 1 | 511 | 511.0x | 0/10 | 16.6% |
| `29-1292` | Dental Hygienists | Stron | 3/8 | 0 | 495 | NEW(495) | 0/10 | 19.6% |
| `51-4061` | Model Makers, Metal and Plastic | Moder | 5/8 | 0 | 491 | NEW(491) | 0/10 | 0.1% |
| `17-3025` | Environmental Engineering Technologist | Stron | 8/8 | 0 | 479 | NEW(479) | 0/10 | 0.6% |
| `49-3041` | Farm Equipment Mechanics and Service T | Moder | 2/8 | 5 | 470 | 94.0x | 0/10 | 3.5% |
| `51-3092` | Food Batchmakers | Moder | 3/8 | 34 | 467 | 13.7x | 0/10 | 19.8% |
| `39-5094` | Skincare Specialists | Stron | 3/8 | 1 | 464 | 464.0x | 0/10 | 6.7% |
| `17-3021` | Aerospace Engineering and Operations T | Stron | 8/8 | 5 | 462 | 92.4x | 0/10 | 0.9% |
| `29-2043` | Paramedics | Stron | 6/8 | 2 | 462 | 231.0x | 1/10 | 11.4% |
| `47-5022` | Excavating and Loading Machine and Dra | Moder | 2/8 | 0 | 457 | NEW(457) | 0/10 | 14.1% |
| `47-2011` | Boilermakers | Moder | 7/8 | 0 | 451 | NEW(451) | 0/10 | 0.4% |
| `27-1019` | Artists and Related Workers, All Other | Moder | 8/8 | 0 | 449 | NEW(449) | 0/10 | 0.5% |
| `27-4012` | Broadcast Technicians | Stron | 8/8 | 0 | 449 | NEW(449) | 0/10 | 7.7% |
| `43-4021` | Correspondence Clerks | Moder | 8/8 | 0 | 448 | NEW(448) | 0/10 | 0.0% |
| `47-5032` | Explosives Workers, Ordnance Handling  | Moder | 2/8 | 0 | 430 | NEW(430) | 0/10 | 0.2% |
| `51-4032` | Drilling and Boring Machine Tool Sette | Moder | 3/8 | 0 | 429 | NEW(429) | 0/10 | 0.5% |
| `11-9013` | Farmers, Ranchers, and Other Agricultu | Moder | 8/8 | 8 | 424 | 53.0x | 1/10 | 1.6% |
| `39-2011` | Animal Trainers | Moder | 8/8 | 1 | 420 | 420.0x | 0/10 | 6.0% |
| `49-2098` | Security and Fire Alarm Systems Instal | Moder | 4/8 | 4 | 415 | 103.8x | 0/10 | 5.3% |
| `51-4192` | Layout Workers, Metal and Plastic | Moder | 3/8 | 0 | 410 | NEW(410) | 0/10 | 2.0% |
| `51-4071` | Foundry Mold and Coremakers | Moder | 3/8 | 0 | 409 | NEW(409) | 0/10 | 7.5% |
| `33-2011` | Firefighters | Stron | 5/8 | 1 | 408 | 408.0x | 0/10 | 5.8% |
| `51-4022` | Forging Machine Setters, Operators, an | Moder | 3/8 | 0 | 407 | NEW(407) | 0/10 | 0.3% |
| `47-2231` | Solar Photovoltaic Installers | Moder | 8/8 | 1 | 402 | 402.0x | 0/10 | 0.6% |
| `27-2042` | Musicians and Singers | Moder | 8/8 | 0 | 400 | NEW(400) | 0/10 | 15.8% |
| `37-3012` | Pesticide Handlers, Sprayers, and Appl | Moder | 2/8 | 1 | 397 | 397.0x | 0/10 | 0.6% |
| `31-1133` | Psychiatric Aides | Moder | 2/8 | 5 | 396 | 79.2x | 0/10 | 5.3% |
| `29-2032` | Diagnostic Medical Sonographers | Stron | 1/8 | 1 | 394 | 394.0x | 1/10 | 3.0% |
| `27-2011` | Actors | Moder | 8/8 | 0 | 393 | NEW(393) | 0/10 | 4.9% |
| `31-2022` | Physical Therapist Aides | Moder | 3/8 | 0 | 385 | NEW(385) | 0/10 | 2.5% |
| `31-9096` | Veterinary Assistants and Laboratory A | Moder | 2/8 | 3 | 373 | 124.3x | 0/10 | 12.4% |
| `45-2091` | Agricultural Equipment Operators | Moder | 2/8 | 0 | 373 | NEW(373) | 0/10 | 4.2% |
| `47-2131` | Insulation Workers, Floor, Ceiling, an | Moder | 6/8 | 0 | 370 | NEW(370) | 0/10 | 3.3% |
| `29-2056` | Veterinary Technologists and Technicia | Stron | 2/8 | 1 | 370 | 370.0x | 0/10 | 13.1% |
| `47-5023` | Earth Drillers, Except Oil and Gas | Moder | 2/8 | 1 | 368 | 368.0x | 0/10 | 1.3% |
| `33-3051` | Police and Sheriff's Patrol Officers | Moder | 8/8 | 5 | 362 | 72.4x | 0/10 | 6.3% |
| `19-4071` | Forest and Conservation Technicians | Stron | 8/8 | 0 | 361 | NEW(361) | 0/10 | 0.3% |
| `49-2093` | Electrical and Electronics Installers  | Stron | 5/8 | 0 | 356 | NEW(356) | 0/10 | 1.6% |
| `51-7099` | Woodworkers, All Other | Moder | 2/8 | 0 | 350 | NEW(350) | 0/10 | 1.4% |
| `51-8013` | Power Plant Operators | Moder | 7/8 | 4 | 347 | 86.8x | 0/10 | 5.6% |
| `27-1012` | Craft Artists | Moder | 8/8 | 0 | 345 | NEW(345) | 0/10 | 2.3% |
| `29-1124` | Radiation Therapists | Stron | 1/8 | 1 | 338 | 338.0x | 0/10 | 0.3% |
| `51-4194` | Tool Grinders, Filers, and Sharpeners | Moder | 3/8 | 0 | 327 | NEW(327) | 0/10 | 1.5% |
| `29-2057` | Ophthalmic Medical Technicians | Stron | 2/8 | 1 | 316 | 316.0x | 0/10 | 1.8% |
| `11-9081` | Lodging Managers | Moder | 5/8 | 35 | 298 | 8.5x | 0/10 | 2.2% |
| `29-2035` | Magnetic Resonance Imaging Technologis | Stron | 1/8 | 1 | 298 | 298.0x | 1/10 | 2.5% |
| `43-3071` | Tellers | Moder | 8/8 | 0 | 297 | NEW(297) | 0/10 | 0.6% |
| `47-4071` | Septic Tank Servicers and Sewer Pipe C | Moder | 3/8 | 2 | 293 | 146.5x | 0/10 | 8.7% |
| `33-2021` | Fire Inspectors and Investigators | Stron | 5/8 | 0 | 290 | NEW(290) | 0/10 | 0.1% |
| `29-2081` | Opticians, Dispensing | Moder | 2/8 | 0 | 284 | NEW(284) | 0/10 | 2.8% |
| `47-2132` | Insulation Workers, Mechanical | Moder | 6/8 | 0 | 280 | NEW(280) | 0/10 | 0.6% |
| `19-4043` | Geological Technicians, Except Hydrolo | Stron | 8/8 | 0 | 278 | NEW(278) | 0/10 | 0.6% |
| `43-4011` | Brokerage Clerks | Moder | 8/8 | 0 | 267 | NEW(267) | 0/10 | 0.1% |
| `47-4051` | Highway Maintenance Workers | Moder | 2/8 | 1 | 249 | 249.0x | 0/10 | 1.5% |
| `13-2082` | Tax Preparers | Moder | 8/8 | 3 | 245 | 81.7x | 1/10 | 7.1% |
| `33-1012` | First-Line Supervisors of Police and D | Moder | 8/8 | 5 | 242 | 48.4x | 0/10 | 1.4% |
| `49-2095` | Electrical and Electronics Repairers,  | Stron | 7/8 | 4 | 239 | 59.8x | 0/10 | 3.6% |
| `51-9141` | Semiconductor Processing Technicians | Moder | 1/8 | 13 | 238 | 18.3x | 0/10 | 6.2% |
| `41-9021` | Real Estate Brokers | Moder | 3/8 | 0 | 237 | NEW(237) | 0/10 | 0.6% |
| `49-9051` | Electrical Power-Line Installers and R | Moder | 8/8 | 8 | 231 | 28.9x | 0/10 | 14.5% |
| `47-4021` | Elevator and Escalator Installers and  | Moder | 8/8 | 2 | 225 | 112.5x | 0/10 | 0.9% |
| `49-2096` | Electronic Equipment Installers and Re | Moder | 5/8 | 0 | 205 | NEW(205) | 0/10 | 0.7% |
| `51-8091` | Chemical Plant and System Operators | Moder | 8/8 | 2 | 203 | 101.5x | 0/10 | 0.9% |
| `33-9031` | Gambling Surveillance Officers and Gam | Moder | 6/8 | 1 | 194 | 194.0x | 0/10 | 2.2% |
| `45-4011` | Forest and Conservation Workers | Moder | 2/8 | 0 | 190 | NEW(190) | 0/10 | 0.2% |
| `51-4062` | Patternmakers, Metal and Plastic | Moder | 5/8 | 0 | 190 | NEW(190) | 0/10 | 0.7% |
| `27-2031` | Dancers | Moder | 8/8 | 0 | 185 | NEW(185) | 0/10 | 2.5% |
| `27-3092` | Court Reporters and Simultaneous Capti | Stron | 8/8 | 1 | 183 | 183.0x | 0/10 | 0.5% |
| `49-3022` | Automotive Glass Installers and Repair | Moder | 3/8 | 0 | 178 | NEW(178) | 0/10 | 1.5% |
| `53-6041` | Traffic Technicians | Moder | 8/8 | 1 | 178 | 178.0x | 0/10 | 0.1% |
| `39-1013` | First-Line Supervisors of Gambling Ser | Moder | 1/8 | 1 | 175 | 175.0x | 0/10 | 4.8% |
| `27-2091` | Disc Jockeys, Except Radio | Moder | 8/8 | 0 | 173 | NEW(173) | 0/10 | 4.0% |
| `29-2036` | Medical Dosimetrists | Stron | 1/8 | 1 | 173 | 173.0x | 0/10 | 0.1% |
| `33-1021` | First-Line Supervisors of Firefighting | Stron | 5/8 | 1 | 167 | 167.0x | 0/10 | 0.9% |
| `33-3021` | Detectives and Criminal Investigators | Moder | 8/8 | 5 | 163 | 32.6x | 0/10 | 1.1% |
| `29-2033` | Nuclear Medicine Technologists | Stron | 1/8 | 0 | 163 | NEW(163) | 0/10 | 0.3% |
| `39-5091` | Makeup Artists, Theatrical and Perform | Stron | 3/8 | 0 | 156 | NEW(156) | 0/10 | 0.3% |
| `19-4051` | Nuclear Technicians | Stron | 3/8 | 0 | 146 | NEW(146) | 0/10 | 0.8% |
| `49-9081` | Wind Turbine Service Technicians | Stron | 8/8 | 0 | 145 | NEW(145) | 0/10 | 1.0% |
| `39-5092` | Manicurists and Pedicurists | Stron | 3/8 | 0 | 138 | NEW(138) | 0/10 | 19.4% |
| `53-7041` | Hoist and Winch Operators | Moder | 2/8 | 0 | 138 | NEW(138) | 0/10 | 0.3% |
| `51-6092` | Fabric and Apparel Patternmakers | Moder | 1/8 | 0 | 135 | NEW(135) | 0/10 | 1.6% |
| `45-4022` | Logging Equipment Operators | Moder | 2/8 | 0 | 128 | NEW(128) | 0/10 | 4.4% |
| `51-8011` | Nuclear Power Reactor Operators | Moder | 3/8 | 0 | 127 | NEW(127) | 0/10 | 1.1% |
| `33-3012` | Correctional Officers and Jailers | Moder | 6/8 | 3 | 123 | 41.0x | 0/10 | 7.4% |
| `27-2021` | Athletes and Sports Competitors | Moder | 8/8 | 0 | 120 | NEW(120) | 0/10 | 8.5% |
| `47-2072` | Pile Driver Operators | Moder | 2/8 | 0 | 120 | NEW(120) | 0/10 | 0.8% |
| `33-1011` | First-Line Supervisors of Correctional | Moder | 6/8 | 1 | 117 | 117.0x | 0/10 | 0.8% |
| `13-1032` | Insurance Appraisers, Auto Damage | Stron | 3/8 | 0 | 115 | NEW(115) | 0/10 | 0.4% |
| `41-3041` | Travel Agents | Moder | 7/8 | 0 | 109 | NEW(109) | 0/10 | 25.4% |
| `49-3043` | Rail Car Repairers | Moder | 1/8 | 0 | 97 | NEW(97) | 0/10 | 16.4% |
| `47-5099` | Extraction Workers, All Other | Moder | 2/8 | 0 | 91 | NEW(91) | 0/10 | 1.9% |
| `53-4041` | Subway and Streetcar Operators | Moder | 1/8 | 3 | 91 | 30.3x | 0/10 | 1.5% |
| `47-4061` | Rail-Track Laying and Maintenance Equi | Moder | 2/8 | 0 | 90 | NEW(90) | 0/10 | 5.1% |
| `11-9071` | Gambling Managers | Moder | 1/8 | 0 | 83 | NEW(83) | 0/10 | 1.0% |
| `43-3041` | Gambling Cage Workers | Moder | 1/8 | 0 | 83 | NEW(83) | 0/10 | 3.2% |
| `49-9097` | Signal and Track Switch Repairers | Moder | 4/8 | 0 | 83 | NEW(83) | 0/10 | 3.3% |
| `53-4022` | Railroad Brake, Signal, and Switch Ope | Moder | 1/8 | 0 | 83 | NEW(83) | 0/10 | 6.4% |
| `53-4031` | Railroad Conductors and Yardmasters | Moder | 1/8 | 0 | 83 | NEW(83) | 0/10 | 20.1% |
| `43-4141` | New Accounts Clerks | Moder | 8/8 | 0 | 82 | NEW(82) | 0/10 | 0.1% |
| `27-2032` | Choreographers | Moder | 8/8 | 1 | 80 | 80.0x | 0/10 | 0.9% |
| `49-9045` | Refractory Materials Repairers, Except | Moder | 8/8 | 0 | 80 | NEW(80) | 0/10 | 0.2% |
| `51-7032` | Patternmakers, Wood | Moder | 2/8 | 0 | 70 | NEW(70) | 0/10 | 0.0% |
| `45-2021` | Animal Breeders | Moder | 8/8 | 0 | 65 | NEW(65) | 0/10 | 3.1% |
| `33-3052` | Transit and Railroad Police | Moder | 5/8 | 0 | 64 | NEW(64) | 0/10 | 0.2% |
| `33-2022` | Forest Fire Inspectors and Prevention  | Moder | 5/8 | 0 | 63 | NEW(63) | 0/10 | 0.0% |
| `33-3011` | Bailiffs | Moder | 8/8 | 1 | 63 | 63.0x | 0/10 | 0.2% |
| `49-9095` | Manufactured Building and Mobile Home  | Moder | 3/8 | 0 | 63 | NEW(63) | 0/10 | 0.3% |
| `51-7031` | Model Makers, Wood | Moder | 2/8 | 0 | 62 | NEW(62) | 0/10 | 0.0% |
| `53-4099` | Rail Transportation Workers, All Other | Moder | 1/8 | 0 | 48 | NEW(48) | 0/10 | 2.0% |
| `39-5011` | Barbers | Stron | 3/8 | 0 | 45 | NEW(45) | 0/10 | 2.0% |
| `35-2013` | Cooks, Private Household | Stron | 5/8 | 0 | 39 | NEW(39) | 0/10 | 0.1% |
| `39-5093` | Shampooers | Moder | 3/8 | 0 | 31 | NEW(31) | 0/10 | 1.0% |
| `53-4011` | Locomotive Engineers | Moder | 1/8 | 0 | 23 | NEW(23) | 0/10 | 17.1% |
| `53-4013` | Rail Yard Engineers, Dinkey Operators, | Moder | 1/8 | 0 | 20 | NEW(20) | 0/10 | 2.2% |
| `47-5049` | Underground Mining Machine Operators,  | Moder | 2/8 | 0 | 18 | NEW(18) | 0/10 | 0.4% |
| `47-5041` | Continuous Mining Machine Operators | Moder | 2/8 | 0 | 11 | NEW(11) | 0/10 | 4.1% |
| `53-7031` | Dredge Operators | Moder | 2/8 | 0 | 10 | NEW(10) | 0/10 | 0.4% |
| `11-9131` | Postmasters and Mail Superintendents | Moder | 1/8 | 0 | 2 | NEW(2) | 0/10 | 2.2% |

## Coverage regressions (96 SOCs)

SOCs where less than 30% of the old-method employers survive in the new method's full pool. May indicate the old LLM-curated picks were identity-aligned but in NAICS the new method doesn't reach. Sample of old employers absent from new pool shown.

| SOC | Title | n_old | n_new | old_in_new | old_only | Old sample (lost) |
|---|---|---:|---:|---:|---:|---|
| `31-1131` | Nursing Assistants | 74 | 1118 | 15 | 59 | accent care; adventist health glendale; adventist health white memorial |
| `35-1012` | First-Line Supervisors of Food Prep | 69 | 1997 | 16 | 53 | abbey food & bar; andaz san diego; barleymash |
| `51-1011` | First-Line Supervisors of Productio | 65 | 3828 | 18 | 47 | alphatec spine; alta dena certified dairy; anthony international |
| `29-2061` | Licensed Practical and Licensed Voc | 62 | 1350 | 11 | 51 | accent care; all saints healthcare; altamed medical group |
| `49-9041` | Industrial Machinery Mechanics | 49 | 2619 | 11 | 38 | abbott laboratories; alphatec spine; anthony international |
| `31-9092` | Medical Assistants | 49 | 1274 | 8 | 41 | adventist health glendale; adventist health white memorial; ahmc healthcare |
| `35-1011` | Chefs and Head Cooks | 46 | 1622 | 11 | 35 | abbey food & bar; andaz san diego; barleymash |
| `11-9051` | Food Service Managers | 43 | 1324 | 8 | 35 | 99 ranch market; abbey food & bar; barleymash |
| `17-3023` | Electrical and Electronic Engineeri | 37 | 1528 | 6 | 31 | ad art; advanced bionics; aem |
| `53-3033` | Light Truck Drivers | 35 | 4368 | 10 | 25 | airgas store; albertsons; american medical response |
| `21-1093` | Social and Human Service Assistants | 35 | 1323 | 4 | 31 | adult protective services; all heart home care san diego ca; altamed medical gro |
| `11-9081` | Lodging Managers | 35 | 298 | 7 | 28 | andaz san diego; best western plus isla palms; best western seven seas |
| `51-3092` | Food Batchmakers | 34 | 467 | 10 | 24 | alta dena certified dairy; baked in the sun wholesale bakery; bimbo bakeries usa |
| `43-4171` | Receptionists and Information Clerk | 31 | 4902 | 4 | 27 | best western plus isla palms; beverly hills hotel; brookdale carlsbad |
| `41-4012` | Sales Representatives, Wholesale an | 31 | 3835 | 8 | 23 | airgas store; altman specialty plants; anheuser-busch sales beach |
| `47-1011` | First-Line Supervisors of Construct | 30 | 2671 | 4 | 26 | acco engineered systems; am ortega construction; american landscape |
| `19-4031` | Chemical Technicians | 19 | 1463 | 3 | 16 | ajinomoto althea; biolegend; catalent |
| `49-9062` | Medical Equipment Repairers | 18 | 821 | 4 | 14 | abbott laboratories; advanced bionics; alphatec spine |
| `47-2073` | Operating Engineers and Other Const | 15 | 1553 | 4 | 11 | am ortega construction; american landscape; doty brothers construction |
| `43-6014` | Secretaries and Administrative Assi | 14 | 4992 | 1 | 13 | baldwin park unified school district; bell middle school; black mountain middle  |
| `21-1094` | Community Health Workers | 14 | 1314 | 1 | 13 | adult protective services; all heart home care san diego ca; eastern los angeles |
| `51-9141` | Semiconductor Processing Technician | 13 | 238 | 1 | 12 | aem; broadcom corporation; cohu |
| `37-1012` | First-Line Supervisors of Landscapi | 12 | 1396 | 2 | 10 | american landscape; aztec landscaping; brightview landscape services |
| `39-9011` | Childcare Workers | 11 | 1219 | 3 | 8 | arc of san diego north county; arcadia montessori preschool; camp mountain chai |
| `43-6013` | Medical Secretaries and Administrat | 9 | 1469 | 2 | 7 | antelope valley healthcare district; brault can emergency physicians medical gro |
| `51-9011` | Chemical Equipment Operators and Te | 9 | 734 | 0 | 9 | ajinomoto althea; baker commodities; catalent |
| `11-9013` | Farmers, Ranchers, and Other Agricu | 8 | 424 | 1 | 7 | altman specialty plants; armstrong growers; dole food |
| `37-1011` | First-Line Supervisors of Housekeep | 7 | 2216 | 1 | 6 | advance building maintenance; best western plus isla palms; beverly wilshire, a  |
| `33-1091` | First-Line Supervisors of Security  | 7 | 1534 | 2 | 5 | adt security services; allied universal; bald eagle security services |
| `47-2031` | Carpenters | 6 | 2228 | 0 | 6 | dixieline lumber & home center; hamann; marmol radziner |
