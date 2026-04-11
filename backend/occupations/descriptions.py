"""
Generate meaningful occupation descriptions based on SOC codes and titles.

Each description is 1-2 sentences explaining what the occupation does,
written for a workforce development audience.
"""

# Hand-written descriptions for common/important occupations.
# Anything not listed falls through to SOC-group-based generation.
SPECIFIC_DESCRIPTIONS = {
    "11-1011": "Sets the overall strategic direction of an organization, coordinating operations across all departments to achieve institutional goals.",
    "11-1021": "Oversees operations and strategic planning for an organization, directing staff and managing resources to meet business objectives.",
    "11-1031": "Directs and coordinates legislative, regulatory, and policy activities for government agencies or public organizations.",
    "11-2011": "Develops and executes advertising and promotional campaigns to generate interest in products or services.",
    "11-2021": "Plans and directs marketing strategies, including market research, pricing, and brand development to drive business growth.",
    "11-2022": "Manages sales teams, sets goals and quotas, analyzes data, and develops strategies to maximize revenue.",
    "11-3010": "Oversees the administrative functions of an organization including record-keeping, facilities, and operational support.",
    "11-3012": "Manages day-to-day administrative operations, coordinating support services, facilities, and organizational procedures.",
    "11-3013": "Plans and manages building operations, maintenance, and real property to ensure safe and efficient use of facilities.",
    "11-3021": "Directs technology strategy and operations, overseeing hardware, software, and networking infrastructure for an organization.",
    "11-3031": "Oversees an organization's financial planning, reporting, and compliance, managing budgets, investments, and accounting operations.",
    "11-3051": "Plans and manages industrial production processes, ensuring manufacturing operations meet quality, cost, and schedule targets.",
    "11-3061": "Directs procurement operations, negotiating contracts and managing the acquisition of materials and services.",
    "11-3071": "Coordinates the movement of goods through supply chains, managing transportation, warehousing, and distribution logistics.",
    "11-3111": "Develops and manages employee benefit programs including health insurance, retirement plans, and leave policies.",
    "11-3121": "Oversees recruitment, employee relations, training, and compliance with labor regulations for an organization.",
    "11-3131": "Plans and coordinates organizational training and professional development programs to improve workforce skills.",
    "11-9013": "Manages agricultural operations including crop production, livestock, and farm business planning.",
    "11-9021": "Directs construction projects from planning through completion, managing budgets, schedules, and subcontractors.",
    "11-9031": "Plans and manages educational programs and services, coordinating curriculum development and instructional staff.",
    "11-9032": "Leads and manages post-secondary academic departments or programs, overseeing faculty, students, and curriculum.",
    "11-9041": "Directs engineering projects and technical teams, coordinating design, development, and manufacturing activities.",
    "11-9051": "Manages food service operations in restaurants, hotels, or institutional settings, overseeing staff, menus, and customer satisfaction.",
    "11-9071": "Plans and manages gaming operations at casinos or gaming establishments, ensuring regulatory compliance and profitability.",
    "11-9081": "Manages hotels, resorts, or lodging facilities, overseeing front office, housekeeping, and guest services.",
    "11-9111": "Plans and manages health care delivery services, coordinating clinical and administrative operations in medical facilities.",
    "11-9121": "Manages environmental quality programs, directing activities related to pollution control, waste management, and sustainability.",
    "11-9131": "Plans and manages public relations campaigns, coordinating media communications and organizational messaging.",
    "11-9141": "Manages the operation of properties including residential, commercial, or industrial real estate.",
    "11-9151": "Directs social service programs and community organizations, overseeing staff and coordinating client services.",
    "11-9161": "Directs emergency management programs, coordinating disaster preparedness, response, and recovery operations.",
    "13-1020": "Manages relationships between buyers and sellers, evaluating and recommending purchases based on quality and cost.",
    "13-1041": "Manages employee benefits, analyzes compensation data, and ensures compliance with regulations governing workplace programs.",
    "13-1051": "Estimates the financial cost of projects or products by analyzing materials, labor, and overhead requirements.",
    "13-1071": "Advises individuals and organizations on employment issues, labor relations, and human resource policies.",
    "13-1075": "Mediates disputes between parties, facilitating negotiation and resolution outside of formal legal proceedings.",
    "13-1081": "Evaluates real property to determine market value for taxation, insurance, or sale purposes.",
    "13-1082": "Assesses the condition and value of properties, developing appraisal reports for lending, investment, or tax purposes.",
    "13-1111": "Advises organizations on management practices, analyzing operations and recommending improvements to efficiency and profitability.",
    "13-1121": "Coordinates conferences, meetings, and special events, managing logistics, vendors, and participant communications.",
    "13-1131": "Assists organizations in soliciting and managing charitable donations, planning campaigns, and building donor relationships.",
    "13-1141": "Reviews insurance claims to determine coverage and settlement amounts, investigating circumstances and negotiating resolutions.",
    "13-1151": "Helps individuals develop career plans, assess skills, and identify job opportunities through counseling and coaching.",
    "13-1161": "Studies market conditions to assess potential sales of products or services, analyzing pricing and competitive dynamics.",
    "13-2011": "Prepares and examines financial records, ensuring accuracy and compliance with tax laws and accounting standards.",
    "13-2022": "Examines and assesses financial risks for insurance applications, determining coverage terms and premiums.",
    "13-2031": "Develops budgets, financial plans, and forecasts, analyzing data to guide organizational spending and investment decisions.",
    "13-2041": "Researches market data, analyzes financial statements, and recommends investment opportunities in securities and assets.",
    "13-2051": "Advises clients on financial planning, investments, retirement, and insurance to help them meet personal financial goals.",
    "13-2052": "Advises individuals and businesses on financial matters including budgeting, investments, tax planning, and estate management.",
    "13-2054": "Assesses financial risks for organizations, using mathematical models to evaluate uncertainty in insurance and investments.",
    "13-2061": "Examines financial records and organizational operations to ensure compliance with laws, regulations, and internal policies.",
    "13-2072": "Helps individuals and businesses manage debt, develop budgets, and make informed financial decisions.",
    "13-2082": "Prepares tax returns and advises clients on tax obligations, deductions, and compliance with federal and state tax laws.",
    "15-1211": "Analyzes business requirements and designs information systems solutions to improve organizational processes and efficiency.",
    "15-1212": "Protects computer networks and systems from cyber threats by implementing security measures and monitoring for breaches.",
    "15-1221": "Conducts research to discover new approaches to computing technology and develop innovative solutions to complex problems.",
    "15-1231": "Designs and manages computer networks, including local area networks, wide area networks, and internet systems.",
    "15-1232": "Administers and maintains computer network infrastructure, ensuring reliable connectivity and security.",
    "15-1241": "Manages and maintains organizational databases, optimizing performance, ensuring data integrity, and implementing backups.",
    "15-1242": "Designs and manages database systems, developing data models and architectures to support organizational needs.",
    "15-1244": "Administers and manages network infrastructure and system resources, configuring servers, storage, and security protocols.",
    "15-1251": "Designs and develops the architecture and layout of web pages and applications using programming and design tools.",
    "15-1252": "Designs, develops, and tests software applications and systems using programming languages and development frameworks.",
    "15-1253": "Develops and modifies software to meet specific system requirements, including operating systems, compilers, and network software.",
    "15-1254": "Designs web applications and services, defining technical architecture, user interfaces, and system integration approaches.",
    "15-1255": "Designs and develops front-end and back-end web applications, implementing user interfaces and server-side logic.",
    "15-1256": "Creates interactive software applications including video games, simulations, and other digital entertainment products.",
    "15-1299": "Applies specialized computing skills to roles not classified in other computer occupation categories.",
    "15-2011": "Develops mathematical models and computational methods to solve practical problems in business, engineering, and science.",
    "15-2021": "Uses statistical methods to collect, analyze, and interpret data, designing surveys and experiments to inform decision-making.",
    "15-2031": "Uses advanced analytical methods including machine learning and predictive modeling to extract insights from large datasets.",
    "15-2041": "Collects, processes, and performs statistical analyses of data, applying mathematical techniques to real-world problems.",
    "15-2098": "Applies mathematical and statistical techniques to solve problems in specialized domains not classified elsewhere.",
    "17-1011": "Designs buildings and structures, developing architectural plans that balance aesthetics, function, safety, and building codes.",
    "17-1012": "Designs outdoor spaces including parks, gardens, and public areas, integrating ecological and aesthetic considerations.",
    "17-1021": "Creates maps and analyzes geographic information using surveying data, aerial photographs, and satellite imagery.",
    "17-1022": "Determines precise locations on the earth's surface, establishing boundaries and preparing maps for construction and legal purposes.",
    "17-2011": "Designs and develops systems for flight vehicles including aircraft, satellites, and missiles.",
    "17-2021": "Designs and evaluates processes for manufacturing chemicals, fuels, pharmaceuticals, and other products.",
    "17-2031": "Designs and oversees construction of infrastructure projects including roads, bridges, buildings, and water systems.",
    "17-2041": "Designs computer hardware and systems, developing circuits, processors, and electronic components.",
    "17-2051": "Designs and develops systems for environmental protection including water treatment, waste disposal, and pollution control.",
    "17-2061": "Designs electrical systems and components for power generation, communications, and electronic devices.",
    "17-2071": "Designs and manages electrical systems for buildings, power distribution, and control systems.",
    "17-2072": "Designs electronic circuits, components, and systems for communications, navigation, and computing applications.",
    "17-2081": "Applies engineering principles to environmental and biological systems, designing agricultural and biomedical equipment.",
    "17-2111": "Designs and tests systems to protect people, property, and the environment from fire, disease, and other hazards.",
    "17-2112": "Develops safety standards and procedures for industrial workplaces, inspecting facilities and investigating accidents.",
    "17-2121": "Designs systems for efficient production processes, optimizing workflows, equipment, and resource utilization in manufacturing.",
    "17-2131": "Designs and manages systems that use the physical properties of materials to process or produce products.",
    "17-2141": "Designs and develops mechanical systems and devices, from small components to large machinery and vehicles.",
    "17-2151": "Plans and designs mining operations, ensuring safe and efficient extraction of minerals and natural resources.",
    "17-2161": "Designs and develops methods for extracting oil and gas from underground deposits.",
    "17-2199": "Applies engineering principles in specialized domains not classified under other engineering categories.",
    "17-3011": "Prepares detailed technical drawings and plans used in construction, manufacturing, and engineering projects.",
    "17-3012": "Creates electrical and electronic diagrams and schematics used in manufacturing and construction.",
    "17-3013": "Prepares technical drawings for mechanical devices, equipment, and machinery based on engineering specifications.",
    "17-3021": "Assists aerospace engineers by performing technical tasks related to aircraft design, testing, and manufacturing.",
    "17-3022": "Applies engineering principles to support construction projects, conducting inspections and testing materials.",
    "17-3023": "Performs technical tasks in electrical and electronic engineering, testing circuits and assisting with system design.",
    "17-3024": "Tests and troubleshoots electromechanical systems, maintaining equipment that combines electrical and mechanical components.",
    "17-3025": "Applies engineering principles to monitor and control environmental conditions, collecting samples and analyzing pollution data.",
    "17-3026": "Assists industrial engineers in analyzing production processes and implementing efficiency improvements.",
    "17-3027": "Supports mechanical engineers by building prototypes, testing equipment, and documenting technical specifications.",
    "17-3028": "Collects and analyzes data on work environments, recommending measures to protect worker health and safety.",
    "17-3031": "Conducts field surveys to determine precise positions, boundaries, and elevations of land features.",
    "29-1011": "Diagnoses and treats musculoskeletal disorders through spinal manipulation and other manual adjustment techniques.",
    "29-1021": "Diagnoses and treats diseases of the teeth and gums, performing examinations, restorations, and preventive care.",
    "29-1022": "Designs and applies orthodontic devices to align teeth and correct bite irregularities.",
    "29-1024": "Diagnoses and treats conditions of the mouth, jaw, and face through surgical procedures.",
    "29-1029": "Provides specialized dental care in areas such as prosthodontics, periodontics, or endodontics.",
    "29-1031": "Provides care to patients before, during, and after surgical procedures, administering anesthesia and monitoring vital signs.",
    "29-1041": "Examines eyes, diagnoses vision problems and diseases, and prescribes corrective lenses and treatments.",
    "29-1051": "Designs and fits prosthetic limbs and orthopedic braces, evaluating patients and customizing devices for mobility and function.",
    "29-1071": "Manages patient medications, advises on drug interactions, and ensures safe and effective pharmaceutical care.",
    "29-1122": "Evaluates and treats disorders of the musculoskeletal system, performing surgical procedures on bones, joints, and muscles.",
    "29-1123": "Provides medical care during pregnancy, labor, and delivery, diagnosing and treating conditions of the female reproductive system.",
    "29-1124": "Diagnoses and treats conditions affecting the skin, hair, and nails through medical and surgical procedures.",
    "29-1131": "Diagnoses and treats disorders of the eye through medical and surgical procedures.",
    "29-1141": "Assesses patient health, administers medications, coordinates care, and educates patients on managing health conditions.",
    "29-1151": "Administers anesthesia to patients during surgical and medical procedures, monitoring vital signs and adjusting dosages.",
    "29-1161": "Provides primary and specialized health care to women, including prenatal care, delivery, and reproductive health services.",
    "29-1171": "Provides advanced nursing care including diagnosing conditions, prescribing medications, and managing patient treatment plans.",
    "29-1181": "Evaluates and treats patients with hearing and balance disorders, fitting hearing aids and developing rehabilitation plans.",
    "29-1211": "Manages patient care during surgical procedures by administering anesthesia and monitoring physiological functions.",
    "29-1213": "Diagnoses and treats diseases and injuries using surgical procedures, prescribing medications and ordering diagnostic tests.",
    "29-1214": "Diagnoses and treats conditions affecting the urinary tract and male reproductive system.",
    "29-1215": "Provides comprehensive primary health care to patients across the lifespan, managing chronic and acute conditions.",
    "29-1216": "Diagnoses and provides non-surgical treatment for diseases and conditions affecting internal organs.",
    "29-1217": "Diagnoses and treats diseases and injuries of the nervous system including the brain, spinal cord, and peripheral nerves.",
    "29-1218": "Diagnoses and treats cancer and related diseases using radiation therapy, chemotherapy, and other treatment modalities.",
    "29-1221": "Diagnoses and treats mental disorders using psychotherapy, medication management, and other therapeutic approaches.",
    "29-1223": "Diagnoses conditions and treats injuries of the bones, muscles, and joints through surgical procedures.",
    "29-1224": "Interprets medical images including X-rays, CT scans, and MRIs to diagnose diseases and injuries.",
    "29-1229": "Provides specialized medical care in clinical areas not classified under other physician categories.",
    "29-1241": "Evaluates and treats patients with eye diseases and disorders through surgical and non-surgical interventions.",
    "29-1243": "Diagnoses and treats conditions of the ear, nose, and throat through medical and surgical procedures.",
    "29-1248": "Diagnoses and treats conditions of the cardiovascular system including heart disease and vascular disorders.",
    "29-1249": "Provides specialized medical care in subspecialties not classified under other physician categories.",
    "29-1292": "Cleans teeth, examines patients for oral diseases, and provides preventive dental care and patient education.",
    "29-2010": "Performs clinical laboratory tests to help diagnose and treat diseases, analyzing blood, tissue, and other specimens.",
    "29-2032": "Operates diagnostic imaging equipment to produce images of the body for medical examination and treatment.",
    "29-2034": "Operates sonographic equipment to produce images of internal body structures for diagnostic purposes.",
    "29-2035": "Performs diagnostic tests on the heart and cardiovascular system using specialized imaging and monitoring equipment.",
    "29-2036": "Performs diagnostic procedures on the heart using echocardiography and other cardiac imaging techniques.",
    "29-2042": "Provides emergency medical care and transportation, assessing patient conditions and administering pre-hospital treatment.",
    "29-2043": "Provides advanced emergency medical care in the field, performing invasive procedures and administering medications.",
    "29-2052": "Dispenses medications, manages inventory, and assists pharmacists with administrative and clinical tasks.",
    "29-2053": "Records prescriptions and dispensing information, manages patient profiles, and processes insurance claims in pharmacy settings.",
    "29-2055": "Assists surgeons during operations by organizing instruments, maintaining the sterile field, and anticipating procedural needs.",
    "29-2056": "Provides immunizations, collects blood samples, and performs basic medical procedures under clinical supervision.",
    "29-2061": "Provides care for patients with respiratory disorders, administering treatments and managing ventilator support.",
    "29-2081": "Assists optometrists by conducting preliminary eye tests, fitting eyeglasses, and managing patient records.",
    "29-9021": "Provides information about health conditions, promotes wellness, and connects communities with health care resources.",
    "29-9091": "Performs specialized health care tasks in areas not classified under other health practitioner categories.",
    "29-9092": "Assists in genetic research and testing, collecting samples and processing data for genetic analysis.",
    "31-1120": "Provides personal care and basic health services to patients in home settings, assisting with daily living activities.",
    "31-1131": "Assists nurses with patient care in hospitals and nursing facilities, performing basic clinical and comfort tasks.",
    "31-1132": "Assists with the transport and care of patients in hospital and clinical settings.",
    "31-1133": "Provides behavioral health support to patients in psychiatric facilities under the direction of clinical staff.",
    "31-2011": "Assists physical therapists with patient exercises and treatments, preparing equipment and monitoring progress.",
    "31-2012": "Assists occupational therapists in providing therapeutic activities that help patients develop or recover daily living skills.",
    "31-2021": "Assists speech-language pathologists in treating patients with communication and swallowing disorders.",
    "31-9011": "Performs diagnostic imaging procedures, positioning patients and operating radiologic equipment under supervision.",
    "31-9091": "Assists dentists during procedures, prepares treatment rooms, sterilizes instruments, and manages patient records.",
    "31-9092": "Prepares patients for medical examinations, records vital signs, and assists physicians with clinical procedures.",
    "31-9093": "Assists physicians with examinations and procedures, performing both administrative and clinical tasks in medical offices.",
    "31-9094": "Transcribes medical reports and records dictated by physicians and other health care practitioners.",
    "31-9096": "Assists veterinarians with animal examinations, treatments, and laboratory procedures in clinical settings.",
    "31-9097": "Assists audiologists with hearing tests and hearing aid fittings, maintaining equipment and patient records.",
    "47-2011": "Constructs building foundations, structures, and frameworks using concrete blocks, bricks, and stone.",
    "47-2021": "Lays brick, concrete block, and stone to construct or repair walls, foundations, and other structures.",
    "47-2031": "Builds, installs, and repairs structures made of wood and other materials, including walls, floors, and door frames.",
    "47-2041": "Installs floor coverings including carpet, hardwood, vinyl, and tile in residential and commercial buildings.",
    "47-2044": "Sets and finishes tile and marble on floors, walls, and countertops in buildings and structures.",
    "47-2051": "Pours, spreads, and finishes concrete for building foundations, sidewalks, roads, and other structures.",
    "47-2061": "Performs physical labor at construction sites, assisting skilled trades workers and operating basic equipment.",
    "47-2071": "Applies insulating materials to pipes, ducts, and structures to control temperature and sound.",
    "47-2073": "Operates heavy equipment to move and grade earth, erect structures, and pour concrete at construction sites.",
    "47-2081": "Installs and repairs drywall panels in buildings, taping joints and applying finishing compounds.",
    "47-2111": "Installs, maintains, and repairs electrical wiring, equipment, and fixtures in buildings and structures.",
    "47-2121": "Applies glass panes and panels to building windows, skylights, and structural facades.",
    "47-2131": "Installs and repairs insulation materials in buildings to improve energy efficiency and climate control.",
    "47-2141": "Applies coats of paint, stain, and varnish to buildings, equipment, and other surfaces.",
    "47-2151": "Assembles and installs pipes and fittings that carry water, steam, gas, or waste in buildings and facilities.",
    "47-2152": "Installs and repairs pipe systems for steam, hot water, and cooling in industrial and commercial buildings.",
    "47-2161": "Installs and repairs drywall, lath, and plaster surfaces in buildings.",
    "47-2171": "Erects structural steel and iron frameworks for buildings, bridges, and other construction projects.",
    "47-2181": "Installs and repairs roofing materials on buildings, ensuring waterproof and weather-resistant coverage.",
    "47-2211": "Installs and maintains metal ductwork, siding, gutters, and other sheet metal products for buildings.",
    "47-2221": "Assembles and erects metal buildings, bridges, and structural frameworks from prefabricated components.",
    "47-2231": "Installs photovoltaic systems on rooftops and other structures, connecting panels and configuring electrical components.",
    "47-3011": "Assists electricians by carrying materials, setting up equipment, and performing basic wiring tasks.",
    "47-3012": "Assists carpenters by holding materials, cleaning work areas, and performing basic carpentry tasks.",
    "47-3013": "Assists plumbers, pipefitters, and steamfitters by carrying tools, cutting pipe, and performing basic installation tasks.",
    "47-4011": "Evaluates construction projects for compliance with building codes, zoning regulations, and contract specifications.",
    "47-4051": "Operates equipment to clear land, dig trenches, and move earth and rock at construction and mining sites.",
    "47-4099": "Performs specialized construction tasks not classified under other construction occupation categories.",
    "47-5012": "Operates rotary drilling rigs to bore wells for oil, gas, water, or mineral exploration.",
    "47-5013": "Assists drilling operators by setting up equipment, monitoring gauges, and maintaining drill site operations.",
    "47-5097": "Assists in blasting operations by loading explosives and ensuring safe detonation procedures.",
    "49-1011": "Oversees teams of mechanics, installers, and repair workers, scheduling work and ensuring quality maintenance.",
    "49-2011": "Repairs and maintains computer equipment, ATMs, and other office machines, diagnosing malfunctions and replacing parts.",
    "49-2021": "Installs and repairs radio, cellular, and broadcast tower equipment, climbing structures and testing signal systems.",
    "49-2022": "Installs, maintains, and repairs telecommunications equipment and systems for voice and data transmission.",
    "49-2093": "Tests and repairs electrical power lines, transformers, and distribution equipment in utility systems.",
    "49-2094": "Installs and repairs electrical components in buildings, diagnosing problems and replacing faulty wiring and fixtures.",
    "49-2095": "Installs and repairs power lines and cables, working on utility poles and towers to maintain electrical distribution.",
    "49-2098": "Installs and maintains security systems, fire alarms, and other electronic protection equipment.",
    "49-3011": "Diagnoses and repairs mechanical and electrical problems in aircraft, performing scheduled maintenance and inspections.",
    "49-3021": "Repairs and maintains automotive heating, cooling, and air conditioning systems in vehicles.",
    "49-3022": "Repairs and replaces automotive body panels, frames, and components damaged in collisions.",
    "49-3023": "Diagnoses, repairs, and maintains mechanical and electronic systems in automobiles and light trucks.",
    "49-3031": "Diagnoses and repairs mechanical problems in diesel-powered trucks, buses, and heavy equipment.",
    "49-3041": "Maintains and repairs farm equipment and machinery including tractors, combines, and irrigation systems.",
    "49-3042": "Repairs and maintains mobile heavy equipment used in construction, logging, and mining operations.",
    "49-3043": "Maintains and repairs outboard motors, inboard engines, and other marine vessel mechanical systems.",
    "49-3051": "Services and repairs motorcycles, scooters, and similar motorized vehicles.",
    "49-3053": "Installs and repairs outdoor power equipment including lawnmowers, chainsaws, and snow blowers.",
    "49-3093": "Adjusts, aligns, and calibrates parts of bicycles using hand tools and specialized equipment.",
    "49-9011": "Inspects and repairs mechanical equipment in industrial plants, troubleshooting breakdowns and performing preventive maintenance.",
    "49-9012": "Maintains and repairs electrical and mechanical control systems used to regulate industrial processes.",
    "49-9021": "Installs, maintains, and repairs heating, ventilation, air conditioning, and refrigeration systems in buildings.",
    "49-9031": "Maintains and repairs home appliances such as washers, dryers, refrigerators, and stoves.",
    "49-9041": "Maintains and repairs industrial machinery including conveyors, packaging equipment, and production systems.",
    "49-9043": "Performs routine maintenance on industrial machines, inspecting and lubricating equipment to prevent breakdowns.",
    "49-9044": "Repairs and tunes musical instruments including pianos, organs, and stringed instruments.",
    "49-9051": "Repairs and maintains electrical power lines, cables, and related equipment for utility distribution systems.",
    "49-9052": "Installs, services, and repairs commercial and industrial electrical equipment and electronic systems.",
    "49-9071": "Maintains and services commercial building equipment and systems, performing general repair work.",
    "49-9081": "Installs and repairs locks, deadbolts, and security devices, re-keying cylinders and programming electronic access systems.",
    "49-9094": "Sets up, adjusts, and monitors precision instruments and equipment used in manufacturing and testing.",
    "49-9098": "Assists skilled maintenance workers by performing routine tasks, carrying equipment, and cleaning work areas.",
    "53-1042": "Coordinates the daily operations of transportation workers including bus drivers, delivery drivers, and logistics personnel.",
    "53-2012": "Operates commercial aircraft to transport passengers and cargo, navigating flight routes and managing in-flight systems.",
    "53-2031": "Directs the movement of aircraft on the ground and in the air, maintaining safe distances between planes.",
    "53-3032": "Operates heavy trucks to transport goods over long distances, managing cargo and complying with transportation regulations.",
    "53-3033": "Drives light delivery vehicles to transport goods locally, collecting and delivering packages and materials.",
    "53-3051": "Operates buses to transport passengers along established routes in urban and suburban areas.",
    "53-3052": "Drives buses to transport students to and from school, ensuring safe loading, transport, and unloading.",
    "53-3053": "Transports passengers by automobile, operating taxis, rideshare vehicles, or livery services.",
    "53-3054": "Operates rail vehicles to transport passengers and cargo, following signals and managing train operations.",
    "53-5011": "Commands and navigates marine vessels, managing crew and ensuring safe transport of passengers and cargo.",
    "53-5021": "Operates and maintains deck equipment and machinery on ships, performing routine vessel maintenance.",
    "53-6051": "Operates freight, baggage, or material-moving vehicles at airports, warehouses, and industrial facilities.",
    "53-7021": "Operates cranes and hoisting equipment to lift and move heavy materials at construction and industrial sites.",
    "53-7032": "Operates excavating equipment to dig foundations, trenches, and other earthwork at construction sites.",
    "53-7051": "Operates forklifts and material-handling equipment to load, unload, and move goods in warehouses and facilities.",
    "53-7062": "Loads and unloads materials by hand or with basic equipment, sorting and stacking goods in warehouses.",
    "53-7064": "Moves materials, equipment, and supplies within workplaces, warehouses, and construction sites.",
    "51-4121": "Joins metal parts using heat and filler materials through welding, cutting, soldering, and brazing techniques.",
    "27-4032": "Edits film, video, and multimedia content, assembling raw footage into polished productions for broadcast, streaming, or distribution.",
    "27-4011": "Operates broadcast equipment including cameras, audio mixers, and transmitters for television, radio, and streaming media.",
    "27-4012": "Sets up and operates camera equipment to capture images for film, television, and video productions.",
    "27-4014": "Operates audio recording equipment, mixing sound for live events, broadcasts, and studio productions.",
    "27-1011": "Directs the visual style and creative direction of publications, advertising, and media productions.",
    "27-1012": "Creates original works of art using painting, sculpture, illustration, and other visual media.",
    "27-1013": "Creates visual effects, animations, and digital imagery for film, television, games, and other media.",
    "27-1014": "Designs and creates three-dimensional objects and environments for exhibitions, film sets, and commercial displays.",
    "27-1021": "Plans and directs interior spaces for function, safety, and aesthetics in residential and commercial buildings.",
    "27-1024": "Designs visual concepts for print, digital, and multimedia communications using typography, imagery, and layout.",
    "27-1025": "Designs or arranges objects and spaces for exhibitions, trade shows, and retail environments.",
    "27-1026": "Plans and designs merchandise displays for retail stores and commercial spaces.",
    "27-1027": "Creates and develops visual concepts for costumes, sets, and theatrical productions.",
    "27-2011": "Performs in dramatic, comedic, or other productions on stage, television, film, or radio.",
    "27-2012": "Creates and performs music as a vocalist or instrumentalist in live performances and recordings.",
    "27-2022": "Plans and leads physical training programs for athletes and sports teams to improve performance.",
    "27-2023": "Calls sporting events for audiences, providing play-by-play commentary and analysis for broadcasts.",
    "27-2031": "Performs acrobatic feats, dances, or other physical acts for audiences in live or recorded productions.",
    "27-2032": "Choreographs and performs dance routines for stage, film, television, and other productions.",
    "27-2041": "Plans and coordinates music activities and performances, directing rehearsals and managing musical groups.",
    "27-2042": "Directs and leads musical ensembles and orchestras, interpreting compositions and coordinating performances.",
    "27-3011": "Researches and writes news stories for broadcast, print, or digital media outlets.",
    "27-3023": "Researches and writes informational content for news, magazines, journals, and online publications.",
    "27-3031": "Plans and coordinates public communications for organizations, managing media relations and public image.",
    "27-3041": "Reviews and edits written content for publication, ensuring accuracy, clarity, and adherence to style guidelines.",
    "27-3042": "Creates original written works including novels, screenplays, scripts, and other literary content.",
    "27-3043": "Converts written text from one language to another while preserving meaning, tone, and context.",
    "27-3044": "Facilitates communication between speakers of different languages through oral translation in real-time settings.",
    "27-4015": "Captures images using photographic equipment for commercial, artistic, scientific, or journalistic purposes.",
    "27-4021": "Maintains, adjusts, and repairs broadcast and recording studio equipment and instruments.",
    "35-1011": "Directs food preparation and cooking operations in restaurants and kitchens, planning menus and managing kitchen staff.",
    "35-2012": "Prepares and cooks a wide variety of foods in restaurants, hotels, and other food service establishments.",
    "35-2014": "Prepares meals in institutional cafeterias, hospitals, or schools following standardized recipes and dietary guidelines.",
    "35-2019": "Prepares specialized food items using specific cooking techniques not classified under other cook categories.",
    "35-2021": "Prepares baked goods including bread, cakes, pastries, and other items for commercial and retail sale.",
    "35-3011": "Mixes and serves drinks to customers at bars, restaurants, and entertainment venues.",
    "35-3023": "Takes orders and serves food and beverages to customers at fast food restaurants and counter service establishments.",
    "35-3031": "Takes orders and serves food and beverages to customers at tables in restaurants and dining establishments.",
    "39-5011": "Provides cosmetic treatments and skin care services to clients, including facials, body treatments, and makeup application.",
    "39-5012": "Cuts, styles, colors, and treats hair for clients in salons, spas, and barbershops.",
    "39-5091": "Provides cosmetic nail care services to clients, applying nail polish, artificial nails, and performing manicures and pedicures.",
    "39-5092": "Cuts and styles hair, shaves beards, and provides grooming services to clients in barbershops.",
    "39-9011": "Cares for children in daycare centers, private homes, or schools, supporting their physical and emotional development.",
    "39-9032": "Leads recreational activities for groups in parks, playgrounds, community centers, and other facilities.",
    "41-2011": "Processes customer purchases and returns, operating cash registers and handling payment transactions in retail stores.",
    "41-2021": "Sells merchandise to customers in retail stores, demonstrating products and assisting with purchasing decisions.",
    "41-2031": "Assists customers in selecting and purchasing merchandise in retail establishments, providing product information and service.",
    "41-3011": "Sells advertising space and time to businesses and organizations for print, broadcast, and digital media.",
    "41-3021": "Sells insurance policies to individuals and businesses, advising on coverage options and managing client accounts.",
    "41-3031": "Sells securities, commodities, and financial services to clients, providing investment advice and managing portfolios.",
    "41-3091": "Promotes and sells products or services by phone, email, or other communication channels without face-to-face contact.",
    "41-4012": "Sells technical products and services that require specialized scientific or technical knowledge to explain and demonstrate.",
    "41-9021": "Sells real estate properties to clients, marketing listings, conducting showings, and facilitating purchase agreements.",
    "41-9022": "Assists real estate agents with property transactions, coordinating showings, paperwork, and client communications.",
    "43-1011": "Supervises and coordinates the work of office and administrative support staff, managing workflows and schedules.",
    "43-3011": "Prepares and maintains financial records, processing invoices, receipts, and payments for organizations.",
    "43-3021": "Processes billing statements, tracks payments, and manages accounts receivable for organizations.",
    "43-3031": "Maintains financial records by recording transactions, posting debits and credits, and reconciling accounts.",
    "43-3051": "Processes payroll for employees, calculating wages, deductions, and taxes, and distributing payments.",
    "43-4051": "Assists customers with inquiries, complaints, and account issues, providing information and resolving problems.",
    "43-4171": "Answers and directs incoming telephone calls, takes messages, and provides basic information to callers.",
    "43-5061": "Schedules and coordinates the dispatch of workers, vehicles, and equipment to appropriate locations.",
    "43-6011": "Provides administrative support to executives, managing schedules, correspondence, and organizational tasks.",
    "43-6013": "Provides administrative support to medical staff, scheduling appointments, managing records, and processing insurance.",
    "43-6014": "Performs administrative tasks including answering phones, filing records, managing correspondence, and scheduling meetings.",
    "43-9061": "Verifies and maintains records and files, reviewing data for accuracy and completeness.",
}


def generate_description(soc_code: str, title: str) -> str:
    """Generate a description for an occupation."""
    # Check specific descriptions first
    if soc_code in SPECIFIC_DESCRIPTIONS:
        return SPECIFIC_DESCRIPTIONS[soc_code]

    t = title.lower()
    major = soc_code.split("-")[0]

    # Handle "All Other" categories
    if "all other" in t:
        base = title.replace(", All Other", "").replace(", all other", "")
        return f"Performs specialized duties in {base.lower()} not classified under more specific occupation categories."

    # Pattern-based generation for unmatched occupations
    if "managers" in t or "manager" in t:
        field = t.replace("managers", "").replace("manager", "").strip().rstrip(",").strip()
        return f"Plans, directs, and coordinates operations in {field}, managing staff, budgets, and organizational goals."

    if "first-line supervisors" in t or "first-line supervisor" in t:
        field = t.replace("first-line supervisors of ", "").replace("first-line supervisor of ", "")
        return f"Directly supervises and coordinates the daily activities of {field}."

    if "technologists" in t or "technologist" in t:
        field = t.replace("technologists", "").replace("technologist", "").strip().rstrip(",").strip()
        return f"Applies technical expertise to perform diagnostic, analytical, or production tasks in {field}."

    if "technicians" in t or "technician" in t:
        field = t.replace("technicians", "").replace("technician", "").strip().rstrip(",").strip()
        return f"Performs technical tasks including equipment operation, testing, and maintenance in {field}."

    if "engineers" in t or "engineer" in t:
        field = t.replace("engineers", "").replace("engineer", "").strip().rstrip(",").strip()
        return f"Applies engineering principles to design, develop, and evaluate systems and processes in {field}."

    if "teachers" in t and "postsecondary" in t:
        field = t.replace("teachers, postsecondary", "").strip().rstrip(",").strip()
        return f"Teaches {field} courses at the college or university level, developing curriculum and assessing student learning."

    if "teachers" in t or "teacher" in t or "instructor" in t:
        field = t.replace("teachers", "").replace("teacher", "").replace("instructors", "").replace("instructor", "").strip().rstrip(",").strip()
        return f"Teaches and instructs students in {field}, developing lesson plans and assessing progress."

    if "clerks" in t or "clerk" in t:
        field = t.replace("clerks", "").replace("clerk", "").strip().rstrip(",").strip()
        return f"Performs clerical and administrative tasks related to {field}, organizing records and processing information."

    if "analysts" in t or "analyst" in t:
        field = t.replace("analysts", "").replace("analyst", "").strip().rstrip(",").strip()
        return f"Analyzes data and information to support decision-making in {field}."

    if "specialists" in t or "specialist" in t:
        field = t.replace("specialists", "").replace("specialist", "").strip().rstrip(",").strip()
        return f"Provides specialized knowledge and support in {field}."

    if "aides" in t or "aide" in t:
        field = t.replace("aides", "").replace("aide", "").strip().rstrip(",").strip()
        return f"Provides support and assistance in {field}, performing routine tasks under supervision."

    if "helpers" in t:
        field = t.replace("helpers--", "").replace("helpers-", "").replace("helpers", "").strip()
        return f"Assists skilled workers in {field} by performing support tasks and handling materials."

    if "assemblers" in t or "fabricators" in t:
        field = t.replace("assemblers and fabricators", "").replace("assemblers", "").replace("fabricators", "").strip().rstrip(",").strip()
        return f"Assembles and fabricates components and finished products in {field} manufacturing."

    if "operators" in t or "operator" in t:
        field = t.replace("operators", "").replace("operator", "").strip().rstrip(",").strip()
        return f"Operates and monitors equipment and machinery used in {field}."

    if "inspectors" in t or "inspector" in t or "testers" in t or "sorters" in t:
        field = t.replace("inspectors", "").replace("inspector", "").replace("testers", "").replace("sorters", "").strip().rstrip(",").strip()
        return f"Inspects and tests products, materials, or processes to ensure quality standards in {field}."

    if "installers" in t or "repairers" in t or "repairer" in t:
        field = t.replace("installers and repairers", "").replace("installers", "").replace("repairers", "").replace("repairer", "").strip().rstrip(",").strip()
        return f"Installs, maintains, and repairs equipment and systems in {field}."

    if "workers" in t or "worker" in t:
        field = t.replace("workers", "").replace("worker", "").strip().rstrip(",").strip()
        return f"Performs tasks and duties in {field}."

    if "assistants" in t or "assistant" in t:
        field = t.replace("assistants", "").replace("assistant", "").strip().rstrip(",").strip()
        return f"Supports professionals in {field} by performing administrative and technical tasks."

    # Default
    return f"Performs professional duties as a {title.lower()}."


def update_descriptions():
    """Update all occupation descriptions in occupations.json."""
    import json
    from pathlib import Path

    path = Path(__file__).parent / "occupations.json"
    with open(path) as f:
        occupations = json.load(f)

    updated = 0
    for occ in occupations:
        new_desc = generate_description(occ["soc_code"], occ["title"])
        if new_desc != occ.get("description"):
            occ["description"] = new_desc
            updated += 1

    with open(path, "w") as f:
        json.dump(occupations, f, indent=2)

    print(f"Updated {updated}/{len(occupations)} descriptions")

    # Show samples
    samples = ["15-1252", "29-1141", "49-9021", "51-4121", "47-2111", "27-4032", "31-9091"]
    for soc in samples:
        occ = next((o for o in occupations if o["soc_code"] == soc), None)
        if occ:
            print(f"\n  {occ['title']} ({soc})")
            print(f"  → {occ['description']}")


if __name__ == "__main__":
    update_descriptions()
