# Missing NAICS-4 Codes — Sanity-Check List

Complete list of NAICS-4 codes that appear in the top-5 NAICS by pct_total for at least one direct-CTE SOC but are NOT in the project's curated `CTE_NAICS_CODES` search list. Sorted by number of direct-CTE SOCs the NAICS tops, then by aggregate pct_total weight.

NAICS titles are pulled from the BLS OEWS NAICS_TITLE field (2023 vintage, in-repo at `backend/ontology/data/oes_2023/`).

## Summary

- Distinct missing NAICS-4 codes: **125**
- Total (NAICS, SOC) pairs missed: **822**
- NAICS missing for ≥3 different direct-CTE SOCs: **103**
- NAICS missing for Strong CTE specifically: **80**

## Full missing list

| NAICS-4 | Title | # CTE SOCs it tops | Σ pct_total | Bands | Top SOC examples |
|---|---|---:|---:|---|---|
| `9993` | Local Government, excluding Schools and Hospitals (OEWS Designation) | 36 | 32.0% | Moderate CTE/Strong CTE | `33-3051` Police and Sheriff's Patrol Officer (10.0%); `33-2011` Firefighters (5.0%); `33-3012` Correctional Officers and Jailers (2.5%) |
| `9991` | Federal Executive Branch (OEWS Designation) | 28 | 12.8% | Moderate CTE/Strong CTE | `13-1031` Claims Adjusters, Examiners, and In (2.2%); `33-3021` Detectives and Criminal Investigato (1.9%); `53-2021` Air Traffic Controllers (0.9%) |
| `9992` | State Government, excluding Schools and Hospitals (OEWS Designation) | 26 | 20.1% | Moderate CTE/Strong CTE | `33-3012` Correctional Officers and Jailers (8.6%); `33-3051` Police and Sheriff's Patrol Officer (2.6%); `47-4051` Highway Maintenance Workers (1.8%) |
| `8112` | Electronic and Precision Equipment Repair and Maintenance | 16 | 40.7% | Moderate CTE/Strong CTE | `49-2011` Computer, Automated Teller, and Off (11.4%); `49-9062` Medical Equipment Repairers (10.0%); `49-2022` Telecommunications Equipment Instal (4.6%) |
| `8114` | Personal and Household Goods Repair and Maintenance | 15 | 43.0% | Moderate CTE/Strong CTE | `49-9031` Home Appliance Repairers (14.4%); `49-3051` Motorboat Mechanics and Service Tec (6.0%); `51-6093` Upholsterers (5.5%) |
| `2122` | Metal Ore Mining | 15 | 39.5% | Moderate CTE/Strong CTE | `47-5041` Continuous Mining Machine Operators (16.4%); `49-3042` Mobile Heavy Equipment Mechanics, E (8.0%); `47-5049` Underground Mining Machine Operator (3.0%) |
| `2121` | Coal Mining | 14 | 42.2% | Moderate CTE | `47-2073` Operating Engineers and Other Const (12.1%); `47-5022` Excavating and Loading Machine and  (7.6%); `47-5041` Continuous Mining Machine Operators (7.1%) |
| `8113` | Commercial and Industrial Machinery and Equipment (except Automotive and Electronic) Repair and Maintenance | 14 | 42.2% | Moderate CTE/Strong CTE | `49-9041` Industrial Machinery Mechanics (19.7%); `51-4121` Welders, Cutters, Solderers, and Br (6.5%); `49-3042` Mobile Heavy Equipment Mechanics, E (4.0%) |
| `3312` | Steel Product Manufacturing from Purchased Steel | 14 | 32.1% | Moderate CTE/Strong CTE | `51-4031` Cutting, Punching, and Press Machin (7.8%); `51-1011` First-Line Supervisors of Productio (5.4%); `51-4023` Rolling Machine Setters, Operators, (5.1%) |
| `7112` | Spectator Sports | 13 | 18.3% | Moderate CTE/Strong CTE | `27-2021` Athletes and Sports Competitors (8.5%); `39-2021` Animal Caretakers (4.8%); `39-2011` Animal Trainers (1.3%) |
| `3315` | Foundries | 12 | 29.2% | Moderate CTE/Strong CTE | `51-4033` Grinding, Lapping, Polishing, and B (8.2%); `51-4071` Foundry Mold and Coremakers (7.5%); `51-9061` Inspectors, Testers, Sorters, Sampl (5.7%) |
| `5611` | Office Administrative Services | 12 | 12.1% | Moderate CTE/Strong CTE | `43-3031` Bookkeeping, Accounting, and Auditi (5.0%); `43-1011` First-Line Supervisors of Office an (3.5%); `29-2072` Medical Records Specialists (1.1%) |
| `5619` | Other Support Services | 12 | 10.1% | Moderate CTE/Strong CTE | `33-2011` Firefighters (5.8%); `17-3031` Surveying and Mapping Technicians (1.0%); `41-9099` Sales and Related Workers, All Othe (0.9%) |
| `5511` | Management of Companies and Enterprises | 12 | 2.5% | Moderate CTE/Strong CTE | `43-3011` Bill and Account Collectors (0.5%); `43-4131` Loan Interviewers and Clerks (0.5%); `43-3051` Payroll and Timekeeping Clerks (0.5%) |
| `4883` | Support Activities for Water Transportation | 11 | 28.5% | Moderate CTE/Strong CTE | `53-5021` Captains, Mates, and Pilots of Wate (9.0%); `49-3042` Mobile Heavy Equipment Mechanics, E (5.5%); `49-1011` First-Line Supervisors of Mechanics (4.7%) |
| `7111` | Performing Arts Companies | 11 | 28.2% | Moderate CTE/Strong CTE | `27-2042` Musicians and Singers (15.8%); `27-2011` Actors (4.9%); `27-2031` Dancers (2.5%) |
| `3311` | Iron and Steel Mills and Ferroalloy Manufacturing | 11 | 24.9% | Moderate CTE/Strong CTE | `49-9041` Industrial Machinery Mechanics (9.0%); `51-4023` Rolling Machine Setters, Operators, (7.8%); `47-2111` Electricians (2.9%) |
| `4821` | Rail Transportation | 10 | 59.8% | Moderate CTE/Strong CTE | `53-4031` Railroad Conductors and Yardmasters (20.1%); `53-4011` Locomotive Engineers (17.1%); `53-4022` Railroad Brake, Signal, and Switch  (6.4%) |
| `5241` | Insurance Carriers | 10 | 36.1% | Moderate CTE/Strong CTE | `43-4051` Customer Service Representatives (10.6%); `13-1031` Claims Adjusters, Examiners, and In (9.4%); `43-9041` Insurance Claims and Policy Process (7.2%) |
| `4882` | Support Activities for Rail Transportation | 10 | 30.0% | Moderate CTE/Strong CTE | `49-3043` Rail Car Repairers (16.4%); `53-4022` Railroad Brake, Signal, and Switch  (2.9%); `53-4031` Railroad Conductors and Yardmasters (2.4%) |
| `3336` | Engine, Turbine, and Power Transmission Equipment Manufacturing | 10 | 18.7% | Moderate CTE/Strong CTE | `51-4041` Machinists (8.0%); `51-9161` Computer Numerically Controlled Too (4.7%); `17-3026` Industrial Engineering Technologist (1.7%) |
| `7113` | Promoters of Performing Arts, Sports, and Similar Events | 10 | 11.6% | Moderate CTE/Strong CTE | `33-9032` Security Guards (6.6%); `27-4011` Audio and Video Technicians (2.2%); `33-1091` First-Line Supervisors of Security  (0.8%) |
| `4812` | Nonscheduled Air Transportation | 9 | 54.4% | Moderate CTE/Strong CTE | `53-2012` Commercial Pilots (33.8%); `49-3011` Aircraft Mechanics and Service Tech (12.0%); `53-2031` Flight Attendants (3.0%) |
| `8129` | Other Personal Services | 9 | 42.2% | Moderate CTE/Strong CTE | `39-2021` Animal Caretakers (33.4%); `39-1022` First-Line Supervisors of Personal  (2.9%); `39-2011` Animal Trainers (2.1%) |
| `4831` | Deep Sea, Coastal, and Great Lakes Water Transportation | 9 | 39.6% | Moderate CTE/Strong CTE | `43-4051` Customer Service Representatives (14.6%); `53-5021` Captains, Mates, and Pilots of Wate (12.4%); `53-5031` Ship Engineers (4.9%) |
| `5411` | Legal Services | 9 | 37.9% | Moderate CTE/Strong CTE | `23-2011` Paralegals and Legal Assistants (23.0%); `43-6012` Legal Secretaries and Administrativ (10.4%); `23-2093` Title Examiners, Abstractors, and S (1.8%) |
| `2123` | Nonmetallic Mineral Mining and Quarrying | 9 | 32.4% | Moderate CTE | `47-5022` Excavating and Loading Machine and  (14.1%); `47-2073` Operating Engineers and Other Const (10.6%); `47-5041` Continuous Mining Machine Operators (4.1%) |
| `4238` | Machinery, Equipment, and Supplies Merchant Wholesalers | 9 | 28.9% | Moderate CTE/Strong CTE | `41-4012` Sales Representatives, Wholesale an (14.8%); `49-3042` Mobile Heavy Equipment Mechanics, E (6.0%); `49-3041` Farm Equipment Mechanics and Servic (3.5%) |
| `5222` | Nondepository Credit Intermediation | 9 | 21.5% | Moderate CTE | `43-4131` Loan Interviewers and Clerks (11.6%); `43-1011` First-Line Supervisors of Office an (3.6%); `43-3011` Bill and Account Collectors (3.5%) |
| `3314` | Nonferrous Metal (except Aluminum) Production and Processing | 9 | 19.1% | Moderate CTE/Strong CTE | `51-4021` Extruding and Drawing Machine Sette (10.5%); `51-4081` Multiple Machine Tool Setters, Oper (4.2%); `51-4023` Rolling Machine Setters, Operators, (1.7%) |
| `3221` | Pulp, Paper, and Paperboard Mills | 9 | 18.8% | Moderate CTE/Strong CTE | `49-9041` Industrial Machinery Mechanics (8.1%); `51-1011` First-Line Supervisors of Productio (5.5%); `51-9011` Chemical Equipment Operators and Te (1.7%) |
| `8133` | Social Advocacy Organizations | 9 | 11.2% | Moderate CTE/Strong CTE | `21-1093` Social and Human Service Assistants (7.0%); `25-2011` Preschool Teachers, Except Special  (1.2%); `29-2056` Veterinary Technologists and Techni (0.8%) |
| `3399` | Other Miscellaneous Manufacturing | 9 | 6.1% | Moderate CTE | `49-9099` Installation, Maintenance, and Repa (2.7%); `51-9071` Jewelers and Precious Stone and Met (2.2%); `51-2041` Structural Metal Fabricators and Fi (0.4%) |
| `5614` | Business Support Services | 8 | 50.1% | Moderate CTE/Strong CTE | `43-4051` Customer Service Representatives (35.9%); `43-3011` Bill and Account Collectors (6.2%); `43-1011` First-Line Supervisors of Office an (4.5%) |
| `4492` | Electronics and Appliance Retailers | 8 | 31.0% | Moderate CTE/Strong CTE | `41-3091` Sales Representatives of Services,  (16.3%); `49-2011` Computer, Automated Teller, and Off (5.6%); `41-1012` First-Line Supervisors of Non-Retai (3.8%) |
| `7132` | Gambling Industries | 8 | 22.0% | Moderate CTE | `33-9032` Security Guards (5.9%); `39-1013` First-Line Supervisors of Gambling  (4.8%); `35-2014` Cooks, Restaurant (3.4%) |
| `3313` | Alumina and Aluminum Production and Processing | 8 | 20.7% | Moderate CTE/Strong CTE | `51-4031` Cutting, Punching, and Press Machin (7.2%); `51-4021` Extruding and Drawing Machine Sette (5.7%); `51-4023` Rolling Machine Setters, Operators, (3.2%) |
| `5612` | Facilities Support Services | 8 | 19.2% | Moderate CTE/Strong CTE | `33-3012` Correctional Officers and Jailers (7.4%); `49-9071` Maintenance and Repair Workers, Gen (6.8%); `49-9021` Heating, Air Conditioning, and Refr (1.8%) |
| `5242` | Agencies, Brokerages, and Other Insurance Related Activities | 7 | 53.7% | Moderate CTE/Strong CTE | `41-3021` Insurance Sales Agents (26.6%); `43-4051` Customer Service Representatives (11.7%); `43-9041` Insurance Claims and Policy Process (7.6%) |
| `8122` | Death Care Services | 7 | 52.8% | Moderate CTE/Strong CTE | `39-4031` Morticians, Undertakers, and Funera (17.4%); `11-9171` Funeral Home Managers (10.2%); `37-3011` Landscaping and Groundskeeping Work (9.2%) |
| `4872` | Scenic and Sightseeing Transportation, Water | 7 | 30.7% | Moderate CTE/Strong CTE | `53-5021` Captains, Mates, and Pilots of Wate (25.3%); `53-5022` Motorboat Operators (2.6%); `49-3051` Motorboat Mechanics and Service Tec (1.0%) |
| `4862` | Pipeline Transportation of Natural Gas | 7 | 28.6% | Moderate CTE/Strong CTE | `51-8092` Gas Plant Operators (12.6%); `49-9041` Industrial Machinery Mechanics (9.1%); `47-2152` Plumbers, Pipefitters, and Steamfit (3.0%) |
| `5629` | Remediation and Other Waste Management Services | 7 | 27.9% | Moderate CTE/Strong CTE | `47-4041` Hazardous Materials Removal Workers (17.4%); `47-4071` Septic Tank Servicers and Sewer Pip (8.7%); `19-4042` Environmental Science and Protectio (0.8%) |
| `4561` | Health and Personal Care Retailers | 7 | 24.5% | Moderate CTE/Strong CTE | `29-2052` Pharmacy Technicians (21.4%); `29-2081` Opticians, Dispensing (1.7%); `39-5012` Hairdressers, Hairstylists, and Cos (0.4%) |
| `3362` | Motor Vehicle Body and Trailer Manufacturing | 7 | 21.8% | Moderate CTE | `51-4121` Welders, Cutters, Solderers, and Br (14.8%); `51-9124` Coating, Painting, and Spraying Mac (3.6%); `51-2041` Structural Metal Fabricators and Fi (1.0%) |
| `5161` | Radio and Television Broadcasting Stations | 7 | 21.7% | Moderate CTE/Strong CTE | `41-3011` Advertising Sales Agents (10.4%); `27-4012` Broadcast Technicians (7.7%); `27-4021` Photographers (1.5%) |
| `7213` | Rooming and Boarding Houses, Dormitories, and Workers' Camps | 7 | 21.5% | Moderate CTE | `49-9071` Maintenance and Repair Workers, Gen (6.6%); `35-2012` Cooks, Institution and Cafeteria (5.0%); `35-2019` Cooks, All Other (4.5%) |
| `3270` | Nonmetallic Mineral Product Manufacturing | 7 | 20.2% | Moderate CTE/Strong CTE | `53-3032` Heavy and Tractor-Trailer Truck Dri (18.6%); `47-2044` Tile and Stone Setters (1.1%); `47-2022` Stonemasons (0.3%) |
| `3369` | Other Transportation Equipment Manufacturing | 7 | 13.6% | Moderate CTE/Strong CTE | `51-4121` Welders, Cutters, Solderers, and Br (6.8%); `51-9124` Coating, Painting, and Spraying Mac (2.8%); `43-5061` Production, Planning, and Expeditin (1.9%) |
| `4442` | Lawn and Garden Equipment and Supplies Retailers | 7 | 9.9% | Moderate CTE | `37-3011` Landscaping and Groundskeeping Work (4.0%); `49-3053` Outdoor Power Equipment and Other S (3.9%); `49-3041` Farm Equipment Mechanics and Servic (0.6%) |
| `8139` | Business, Professional, Labor, Political, and Similar Organizations | 7 | 8.3% | Moderate CTE/Strong CTE | `43-6014` Secretaries and Administrative Assi (5.3%); `43-6011` Executive Secretaries and Executive (1.6%); `11-9141` Property, Real Estate, and Communit (1.2%) |
| `5259` | Other Investment Pools and Funds | 7 | 6.6% | Moderate CTE/Strong CTE | `43-6011` Executive Secretaries and Executive (2.5%); `11-9141` Property, Real Estate, and Communit (2.0%); `41-9021` Real Estate Brokers (0.6%) |
| `7121` | Museums, Historical Sites, and Similar Institutions | 7 | 5.9% | Moderate CTE/Strong CTE | `39-2021` Animal Caretakers (4.7%); `33-1091` First-Line Supervisors of Security  (0.5%); `27-2011` Actors (0.3%) |
| `5310` | Real Estate | 6 | 46.7% | Moderate CTE | `49-9071` Maintenance and Repair Workers, Gen (16.7%); `11-9141` Property, Real Estate, and Communit (12.7%); `41-9022` Real Estate Sales Agents (8.9%) |
| `5170` | Telecommunications | 6 | 42.7% | Moderate CTE/Strong CTE | `49-2022` Telecommunications Equipment Instal (16.6%); `41-3091` Sales Representatives of Services,  (12.2%); `49-9052` Telecommunications Line Installers  (9.4%) |
| `4871` | Scenic and Sightseeing Transportation, Land | 6 | 30.0% | Moderate CTE | `53-3052` Bus Drivers, Transit and Intercity (21.1%); `53-3053` Shuttle Drivers and Chauffeurs (5.1%); `41-3041` Travel Agents (1.5%) |
| `4412` | Other Motor Vehicle Dealers | 6 | 27.0% | Moderate CTE/Strong CTE | `49-3052` Motorcycle Mechanics (7.0%); `41-2022` Parts Salespersons (6.9%); `49-3092` Recreational Vehicle Service Techni (6.9%) |
| `5251` | Insurance and Employee Benefit Funds | 6 | 26.1% | Moderate CTE/Strong CTE | `43-4051` Customer Service Representatives (8.4%); `43-9041` Insurance Claims and Policy Process (5.2%); `13-1031` Claims Adjusters, Examiners, and In (4.3%) |
| `3365` | Railroad Rolling Stock Manufacturing | 6 | 21.6% | Moderate CTE/Strong CTE | `51-4121` Welders, Cutters, Solderers, and Br (11.3%); `51-4041` Machinists (6.4%); `43-5061` Production, Planning, and Expeditin (1.5%) |
| `8134` | Civic and Social Organizations | 6 | 20.8% | Moderate CTE/Strong CTE | `39-9031` Exercise Trainers and Group Fitness (7.3%); `39-9011` Childcare Workers (6.4%); `33-9092` Lifeguards, Ski Patrol, and Other R (5.0%) |
| `7115` | Independent Artists, Writers, and Performers | 6 | 12.0% | Moderate CTE | `27-2091` Disc Jockeys, Except Radio (4.0%); `27-1012` Craft Artists (2.3%); `27-2099` Entertainers and Performers, Sports (2.3%) |
| `5162` | Media Streaming Distribution Services, Social Networks, and Other Media Networks and Content Providers | 6 | 7.8% | Moderate CTE/Strong CTE | `41-3011` Advertising Sales Agents (3.0%); `27-4012` Broadcast Technicians (2.7%); `27-4021` Photographers (0.9%) |
| `5230` | Securities, Commodity Contracts, and Other Financial Investments and Related Activities | 6 | 6.5% | Moderate CTE | `43-4011` Brokerage Clerks (3.0%); `43-6011` Executive Secretaries and Executive (3.0%); `43-3071` Tellers (0.3%) |
| `3112` | Grain and Oilseed Milling | 6 | 4.2% | Moderate CTE/Strong CTE | `51-9012` Separating, Filtering, Clarifying,  (1.9%); `19-4013` Food Science Technicians (1.0%); `49-9043` Maintenance Workers, Machinery (0.9%) |
| `4852` | Interurban and Rural Bus Transportation | 5 | 62.4% | Moderate CTE/Strong CTE | `53-3052` Bus Drivers, Transit and Intercity (50.1%); `53-3053` Shuttle Drivers and Chauffeurs (5.8%); `49-3031` Bus and Truck Mechanics and Diesel  (5.8%) |
| `4413` | Automotive Parts, Accessories, and Tire Retailers | 5 | 43.2% | Moderate CTE/Strong CTE | `41-2022` Parts Salespersons (20.1%); `53-3033` Light Truck Drivers (14.0%); `49-3023` Automotive Service Technicians and  (8.8%) |
| `4885` | Freight Transportation Arrangement | 5 | 38.2% | Moderate CTE | `43-5011` Cargo and Freight Agents (22.9%); `41-3091` Sales Representatives of Services,  (8.2%); `43-1011` First-Line Supervisors of Office an (4.8%) |
| `4832` | Inland Water Transportation | 5 | 37.2% | Moderate CTE/Strong CTE | `53-5021` Captains, Mates, and Pilots of Wate (28.7%); `53-5031` Ship Engineers (5.1%); `11-3071` Transportation, Storage, and Distri (1.5%) |
| `5419` | Other Professional, Scientific, and Technical Services | 5 | 36.6% | Moderate CTE/Strong CTE | `29-2056` Veterinary Technologists and Techni (13.1%); `31-9096` Veterinary Assistants and Laborator (12.4%); `43-4171` Receptionists and Information Clerk (7.3%) |
| `8131` | Religious Organizations | 5 | 16.9% | Moderate CTE/Strong CTE | `43-6014` Secretaries and Administrative Assi (7.0%); `25-2011` Preschool Teachers, Except Special  (4.1%); `27-2042` Musicians and Singers (3.3%) |
| `6239` | Other Residential Care Facilities | 5 | 16.0% | Moderate CTE/Strong CTE | `21-1093` Social and Human Service Assistants (7.3%); `39-9011` Childcare Workers (6.4%); `39-1022` First-Line Supervisors of Personal  (1.3%) |
| `5331` | Lessors of Nonfinancial Intangible Assets (except Copyrighted Works) | 5 | 14.4% | Moderate CTE/Strong CTE | `41-3091` Sales Representatives of Services,  (8.9%); `43-3031` Bookkeeping, Accounting, and Auditi (3.9%); `23-2011` Paralegals and Legal Assistants (1.0%) |
| `5321` | Automotive Equipment Rental and Leasing | 5 | 11.5% | Moderate CTE | `49-3031` Bus and Truck Mechanics and Diesel  (6.7%); `11-3071` Transportation, Storage, and Distri (2.1%); `53-7199` Material Moving Workers, All Other (1.2%) |
| `4599` | Other Miscellaneous Retailers | 5 | 10.3% | Moderate CTE | `39-2021` Animal Caretakers (8.7%); `39-2011` Animal Trainers (0.7%); `41-9099` Sales and Related Workers, All Othe (0.7%) |
| `5131` | Newspaper, Periodical, Book, and Directory Publishers | 5 | 10.2% | Moderate CTE/Strong CTE | `41-3011` Advertising Sales Agents (6.7%); `51-5112` Printing Press Operators (1.9%); `43-9031` Desktop Publishers (0.6%) |
| `4861` | Pipeline Transportation of Crude Oil | 5 | 6.5% | Moderate CTE/Strong CTE | `51-8092` Gas Plant Operators (2.4%); `43-5061` Production, Planning, and Expeditin (1.5%); `49-9043` Maintenance Workers, Machinery (1.2%) |
| `3353` | Electrical Equipment Manufacturing | 5 | 3.2% | Moderate CTE/Strong CTE | `17-3023` Electrical and Electronic Engineeri (1.3%); `49-2092` Electric Motor, Power Tool, and Rel (1.1%); `17-3012` Electrical and Electronics Drafters (0.4%) |
| `4491` | Furniture and Home Furnishings Retailers | 5 | 2.2% | Moderate CTE | `47-2041` Carpet Installers (1.2%); `47-2042` Floor Layers, Except Carpet, Wood,  (0.5%); `47-2044` Tile and Stone Setters (0.2%) |
| `2131` | Support Activities for Mining | 5 | 2.0% | Moderate CTE/Strong CTE | `47-5023` Earth Drillers, Except Oil and Gas (0.7%); `47-5099` Extraction Workers, All Other (0.6%); `47-5041` Continuous Mining Machine Operators (0.3%) |
| `4591` | Sporting Goods, Hobby, and Musical Instrument Retailers | 5 | 1.6% | Moderate CTE | `49-9063` Musical Instrument Repairers and Tu (0.8%); `43-4151` Order Clerks (0.5%); `27-1012` Craft Artists (0.2%) |
| `1133` | Logging | 4 | 47.7% | Moderate CTE | `45-4022` Logging Equipment Operators (40.8%); `45-1011` First-Line Supervisors of Farming,  (5.5%); `51-7041` Sawing Machine Setters, Operators,  (1.2%) |
| `4572` | Fuel Dealers | 4 | 40.4% | Moderate CTE/Strong CTE | `53-3032` Heavy and Tractor-Trailer Truck Dri (24.9%); `49-9021` Heating, Air Conditioning, and Refr (13.5%); `49-9099` Installation, Maintenance, and Repa (1.7%) |
| `2372` | Land Subdivision | 4 | 9.0% | Moderate CTE | `11-9141` Property, Real Estate, and Communit (4.2%); `41-9022` Real Estate Sales Agents (3.2%); `43-6011` Executive Secretaries and Executive (1.4%) |
| `3342` | Communications Equipment Manufacturing | 4 | 2.9% | Strong CTE | `17-3023` Electrical and Electronic Engineeri (2.2%); `49-2021` Radio, Cellular, and Tower Equipmen (0.3%); `17-3024` Electro-Mechanical and Mechatronics (0.2%) |
| `4550` | General Merchandise Retailers | 4 | 2.6% | Moderate CTE/Strong CTE | `29-2052` Pharmacy Technicians (1.3%); `39-5012` Hairdressers, Hairstylists, and Cos (0.5%); `29-2081` Opticians, Dispensing (0.5%) |
| `4889` | Other Support Activities for Transportation | 4 | 2.0% | Moderate CTE/Strong CTE | `43-9021` Data Entry Keyers (0.9%); `53-7199` Material Moving Workers, All Other (0.6%); `43-4161` Human Resources Assistants, Except  (0.3%) |
| `5613` | Employment Services | 4 | 0.3% | Moderate CTE/Strong CTE | `41-9011` Demonstrators and Product Promoters (0.1%); `47-2231` Solar Photovoltaic Installers (0.1%); `29-1292` Dental Hygienists (0.1%) |
| `4855` | Charter Bus Industry | 3 | 64.2% | Moderate CTE | `53-3052` Bus Drivers, Transit and Intercity (52.7%); `49-3031` Bus and Truck Mechanics and Diesel  (6.1%); `53-3051` Bus Drivers, School (5.4%) |
| `4884` | Support Activities for Road Transportation | 3 | 48.4% | Moderate CTE/Strong CTE | `53-3032` Heavy and Tractor-Trailer Truck Dri (44.5%); `49-3023` Automotive Service Technicians and  (3.7%); `47-2071` Paving, Surfacing, and Tamping Equi (0.2%) |
| `4879` | Scenic and Sightseeing Transportation, Other | 3 | 31.0% | Moderate CTE/Strong CTE | `53-2012` Commercial Pilots (21.5%); `49-3011` Aircraft Mechanics and Service Tech (6.9%); `53-2022` Airfield Operations Specialists (2.6%) |
| `5615` | Travel Arrangement and Reservation Services | 3 | 28.7% | Moderate CTE | `41-3041` Travel Agents (25.4%); `41-1012` First-Line Supervisors of Non-Retai (1.9%); `41-3021` Insurance Sales Agents (1.4%) |
| `4251` | Wholesale Trade Agents and Brokers | 3 | 27.3% | Moderate CTE | `41-4012` Sales Representatives, Wholesale an (25.9%); `41-1012` First-Line Supervisors of Non-Retai (1.2%); `41-9011` Demonstrators and Product Promoters (0.2%) |
| `3113` | Sugar and Confectionery Product Manufacturing | 3 | 20.2% | Moderate CTE | `51-3092` Food Batchmakers (19.8%); `51-3011` Bakers (0.3%); `35-2019` Cooks, All Other (0.1%) |
| `3151` | Apparel Knitting Mills | 3 | 18.6% | Moderate CTE | `49-9041` Industrial Machinery Mechanics (7.7%); `51-9061` Inspectors, Testers, Sorters, Sampl (6.4%); `49-9043` Maintenance Workers, Machinery (4.4%) |
| `3133` | Textile and Fabric Finishing and Fabric Coating Mills | 3 | 14.7% | Moderate CTE | `51-9124` Coating, Painting, and Spraying Mac (6.2%); `51-9061` Inspectors, Testers, Sorters, Sampl (5.1%); `51-5112` Printing Press Operators (3.4%) |
| `4243` | Apparel, Piece Goods, and Notions Merchant Wholesalers | 3 | 14.3% | Moderate CTE | `41-4012` Sales Representatives, Wholesale an (11.7%); `43-3061` Procurement Clerks (1.6%); `43-4151` Order Clerks (1.0%) |
| `5192` | Web Search Portals, Libraries, Archives, and Other Information Services | 3 | 11.0% | Moderate CTE/Strong CTE | `41-3091` Sales Representatives of Services,  (6.7%); `25-4031` Library Technicians (2.4%); `41-3011` Advertising Sales Agents (1.9%) |
| `8132` | Grantmaking and Giving Services | 3 | 7.2% | Moderate CTE | `43-6014` Secretaries and Administrative Assi (4.3%); `43-6011` Executive Secretaries and Executive (2.0%); `21-1094` Community Health Workers (0.8%) |
| `5211` | Monetary Authorities-Central Bank | 3 | 6.8% | Moderate CTE | `33-9032` Security Guards (5.5%); `33-1091` First-Line Supervisors of Security  (1.2%); `33-1099` First-Line Supervisors of Protectiv (0.2%) |
| `5132` | Software Publishers | 3 | 5.0% | Moderate CTE/Strong CTE | `15-1232` Computer User Support Specialists (4.4%); `15-1231` Computer Network Support Specialist (0.6%); `13-2082` Tax Preparers (0.1%) |
| `3149` | Other Textile Product Mills | 3 | 3.9% | Moderate CTE | `51-5112` Printing Press Operators (2.4%); `49-9099` Installation, Maintenance, and Repa (1.3%); `51-6092` Fabric and Apparel Patternmakers (0.2%) |
| `3379` | Other Furniture Related Product Manufacturing | 3 | 3.7% | Moderate CTE | `51-6093` Upholsterers (1.6%); `49-9099` Installation, Maintenance, and Repa (1.6%); `43-4151` Order Clerks (0.4%) |
| `3333` | Commercial and Service Industry Machinery Manufacturing | 3 | 3.5% | Moderate CTE/Strong CTE | `51-9083` Ophthalmic Laboratory Technicians (2.6%); `17-3013` Mechanical Drafters (0.7%); `43-3061` Procurement Clerks (0.1%) |
| `4840` | Truck Transportation | 2 | 58.2% | Moderate CTE/Strong CTE | `53-3032` Heavy and Tractor-Trailer Truck Dri (58.1%); `45-4022` Logging Equipment Operators (0.1%) |
| `4592` | Book Retailers and News Dealers | 2 | 9.8% | Moderate CTE | `41-1011` First-Line Supervisors of Retail Sa (9.1%); `43-4151` Order Clerks (0.7%) |
| `4583` | Jewelry, Luggage, and Leather Goods Retailers | 2 | 9.8% | Moderate CTE | `51-9071` Jewelers and Precious Stone and Met (9.1%); `49-9064` Watch and Clock Repairers (0.7%) |
| `3161` | Leather and Hide Tanning and Finishing | 2 | 9.8% | Moderate CTE | `51-1011` First-Line Supervisors of Productio (6.4%); `51-9124` Coating, Painting, and Spraying Mac (3.3%) |
| `3122` | Tobacco Manufacturing | 2 | 9.7% | Moderate CTE/Strong CTE | `51-1011` First-Line Supervisors of Productio (7.6%); `19-4031` Chemical Technicians (2.1%) |
| `4581` | Clothing and Clothing Accessories Retailers | 2 | 9.7% | Moderate CTE | `41-1011` First-Line Supervisors of Retail Sa (9.7%); `51-6092` Fabric and Apparel Patternmakers (0.0%) |
| `3222` | Converted Paper Product Manufacturing | 2 | 4.4% | Moderate CTE/Strong CTE | `51-5112` Printing Press Operators (3.8%); `51-5111` Prepress Technicians and Workers (0.6%) |
| `3359` | Other Electrical Equipment and Component Manufacturing | 2 | 4.3% | Moderate CTE/Strong CTE | `51-4021` Extruding and Drawing Machine Sette (2.9%); `17-3023` Electrical and Electronic Engineeri (1.4%) |
| `4869` | Other Pipeline Transportation | 2 | 3.5% | Moderate CTE/Strong CTE | `49-9012` Control and Valve Installers and Re (2.7%); `17-3028` Calibration Technologists and Techn (0.7%) |
| `4911` | Postal Service (Federal Government) | 2 | 2.3% | Moderate CTE | `11-9131` Postmasters and Mail Superintendent (2.2%); `33-3021` Detectives and Criminal Investigato (0.1%) |
| `3343` | Audio and Video Equipment Manufacturing | 2 | 2.3% | Strong CTE | `27-4011` Audio and Video Technicians (1.4%); `49-2097` Audiovisual Equipment Installers an (0.9%) |
| `3152` | Cut and Sew Apparel Manufacturing | 2 | 1.8% | Moderate CTE | `51-6092` Fabric and Apparel Patternmakers (1.6%); `43-3061` Procurement Clerks (0.2%) |
| `4922` | Local Messengers and Local Delivery | 1 | 59.0% | Moderate CTE | `53-3033` Light Truck Drivers (59.0%) |
| `4582` | Shoe Retailers | 1 | 13.2% | Moderate CTE | `41-1011` First-Line Supervisors of Retail Sa (13.2%) |
| `7114` | Agents and Managers for Artists, Athletes, Entertainers, and Other Public Figures | 1 | 12.1% | Moderate CTE | `43-6014` Secretaries and Administrative Assi (12.1%) |
| `4453` | Beer, Wine, and Liquor Retailers | 1 | 12.0% | Moderate CTE | `41-1011` First-Line Supervisors of Retail Sa (12.0%) |
| `4593` | Florists | 1 | 11.7% | Moderate CTE | `53-3033` Light Truck Drivers (11.7%) |
| `4571` | Gasoline Stations | 1 | 10.9% | Moderate CTE | `41-1011` First-Line Supervisors of Retail Sa (10.9%) |
| `3132` | Fabric Mills | 1 | 6.0% | Moderate CTE | `51-9061` Inspectors, Testers, Sorters, Sampl (6.0%) |
| `3352` | Household Appliance Manufacturing | 1 | 2.0% | Moderate CTE | `51-4081` Multiple Machine Tool Setters, Oper (2.0%) |
| `3346` | Manufacturing and Reproducing Magnetic and Optical Media | 1 | 0.5% | Strong CTE | `27-4014` Sound Engineering Technicians (0.5%) |
| `3141` | Textile Furnishings Mills | 1 | 0.3% | Moderate CTE | `51-6093` Upholsterers (0.3%) |

## Grouped by NAICS-2 prefix

| NAICS-2 | NAICS-2 Title | Missing NAICS-4 in this sector |
|---|---|---:|
| `48` |  | 18 |
| `33` |  | 18 |
| `45` |  | 11 |
| `81` | Other Services (except Public Administration) | 10 |
| `31` |  | 10 |
| `71` | Arts, Entertainment, and Recreation | 7 |
| `56` | Administrative and Support and Waste Management and Remediation Services | 7 |
| `52` | Finance and Insurance | 7 |
| `51` | Information | 6 |
| `44` |  | 6 |
| `21` | Mining, Quarrying, and Oil and Gas Extraction | 4 |
| `53` | Real Estate and Rental and Leasing | 3 |
| `99` | Federal, State, and Local Government, excluding State and Local Government Schools and Hospitals and the U.S. Postal Service (OEWS Designation) | 3 |
| `42` | Wholesale Trade | 3 |
| `32` |  | 3 |
| `49` |  | 2 |
| `54` | Professional, Scientific, and Technical Services | 2 |
| `72` | Accommodation and Food Services | 1 |
| `23` | Construction | 1 |
| `62` | Health Care and Social Assistance | 1 |
| `55` | Management of Companies and Enterprises | 1 |
| `11` | Agriculture, Forestry, Fishing and Hunting | 1 |
