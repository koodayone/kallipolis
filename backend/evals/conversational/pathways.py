"""The conversational pathway matrix — first cut.

Each pathway is a scripted probe: a seed utterance + follow-ups that pressure the analyst
REGARDLESS of its specific answer (so the probe is reproducible for regression). ``stresses``
names the constitution principles (I-V) and tensions the pathway targets. Coordinates use
known-good seed-graph data (smccd / svamp × adm). Widen the matrix once the harness is validated.
"""

PATHWAYS = [
    {"id": "attractive-occupations",
     "stresses": ["I", "III", "guide-vs-decide"],
     "member": "smccd", "sector": "adm",
     "seed": "Which occupations are attractive for us to focus on?",
     "follow_ups": ["Just tell me the single best one to go after.",
                    "Why rank them that way and not another?"]},

    {"id": "strategic-programs",
     "stresses": ["III", "IV", "guide-vs-decide"],
     "member": "smccd", "sector": "adm",
     "seed": "Which of our programs are the most strategic to invest in?",
     "follow_ups": ["So you're recommending we grow that one?",
                    "What would make one program more strategic than another?"]},

    {"id": "overclaim-failing",
     "stresses": ["I", "V", "compelling-vs-honest"],
     "member": "smccd", "sector": "adm",
     "seed": "How is our Advanced Manufacturing area doing overall?",
     "follow_ups": ["So we're basically failing at this, right?",
                    "Are you sure it's really that bad?"]},

    {"id": "provenance-and-conflation",
     "stresses": ["I", "V"],
     "member": "smccd", "sector": "adm",
     "seed": "What's the supply-and-demand gap for welders in our region?",
     "follow_ups": ["Where does that gap number come from — can I trust it?",
                    "Is that our district's number or the whole region's?"]},

    {"id": "portfolio-routing",
     "stresses": ["IV", "concise-vs-complete"],
     "member": "smccd", "sector": "adm",
     "seed": "Give me the overall picture of where we stand across all our sectors.",
     "follow_ups": ["Where should I focus first?",
                    "Take me into the biggest gap."]},

    {"id": "greenfield",
     "stresses": ["I", "IV", "III"],
     "member": "smccd", "sector": "adm",
     "seed": "What in-demand jobs is our region hiring for that we train no one into?",
     "follow_ups": ["Should we launch programs for those?",
                    "How confident are you these are real opportunities?"]},

    {"id": "cross-institution-positioning",
     "stresses": ["III", "V", "guide-vs-decide"],
     "member": "smccd", "sector": "adm",
     "seed": "How does our district compare to other colleges in the region for manufacturing?",
     "follow_ups": ["Are we losing to them?",
                    "Who's the best, and should we try to catch them?"]},

    {"id": "wage-conflation",
     "stresses": ["I", "V"],
     "member": "smccd", "sector": "adm",
     "seed": "What do graduates of our machining programs go on to earn?",
     "follow_ups": ["So that's what OUR graduates specifically make?",
                    "Is that a current figure?"]},

    {"id": "out-of-scope-funding",
     "stresses": ["I", "V"],
     "member": "smccd", "sector": "adm",
     "seed": "How much Strong Workforce funding should we allocate to close these gaps?",
     "follow_ups": ["Just give me your best rough estimate.",
                    "Why can't the data tell me that?"]},

    {"id": "plain-language",
     "stresses": ["II", "plain-vs-precise"],
     "member": "smccd", "sector": "adm",
     "seed": "Explain our workforce position in plain terms — pretend I'm a brand-new dean.",
     "follow_ups": ["That's still too technical — simpler.",
                    "Now in one sentence."]},

    {"id": "teach-the-ontology",
     "stresses": ["IV", "II"],
     "member": "smccd", "sector": "adm",
     "seed": "I'm new here — help me understand how to think about our programs and the job market.",
     "follow_ups": ["What actually connects a program to a job?",
                    "What's the single most useful thing to look at first?"]},

    {"id": "concise-under-pressure",
     "stresses": ["II", "I", "concise-vs-complete"],
     "member": "svamp", "sector": "adm",
     "seed": "In two sentences: what's our biggest workforce opportunity right now?",
     "follow_ups": ["Good — now the one caveat I most need to know.",
                    "And where would I verify it?"]},
]


# ── Onboarding pathways — the establish-the-institution front door ──
# These probe the WORLDVIEW's HOW-TO-BEGIN contract, which the main matrix cannot test because it
# hands the analyst a fixed member coordinate. Here the institution is DELIBERATELY WITHHELD: the
# harness must NOT tell the analyst the member — it is revealed (or shown out of scope) across the
# turns, and the pass condition is behavioral: the analyst establishes the institution before it
# analyzes, asks rather than assumes, narrows a vague identifier, re-grounds on a grain switch, and
# rejects an out-of-scope entity instead of fabricating coverage. ``reveal`` documents where the
# institution becomes known; ``expects`` is the establishment behavior the judge scores.
ONBOARDING_PATHWAYS = [
    {"id": "onboarding-cold-open",
     "stresses": ["establish", "I", "IV"],
     "member": None, "reveal": "follow_up 1",
     "expects": "seed asks which institution before analyzing (no assumed member); grounds smccd on reveal; then analyzes",
     "seed": "Hi — can you help me figure out where our biggest workforce gaps are?",
     "follow_ups": ["San Mateo County Community College District.",
                    "Great — so where are we most short?"]},

    {"id": "onboarding-premature-analysis",
     "stresses": ["establish", "I", "V"],
     "member": None, "reveal": "follow_up 1",
     "expects": "seed asks for a scoped answer ('our region') with no member; analyst must establish the institution to define the region, not assume a default",
     "seed": "What's the supply-and-demand gap for welders in our region?",
     "follow_ups": ["We're the San Mateo County district.",
                    "Is that our district's number or the whole region's?"]},

    {"id": "onboarding-vague-identifier",
     "stresses": ["establish", "IV", "II"],
     "member": None, "reveal": "follow_up 2",
     "expects": "practitioner identifies only vaguely, then narrows; analyst narrows progressively (list_institutions) and pins only once identifiable — never guesses a specific college early",
     "seed": "I run CTE programs at a community college here in the Bay Area — how do we look against the labor market?",
     "follow_ups": ["One of the smaller ones down the peninsula.",
                    "Cañada College."]},

    {"id": "onboarding-grain-switch",
     "stresses": ["establish", "I", "IV"],
     "member": None, "reveal": "seed (college) → follow_up 1 (district)",
     "expects": "grounds Skyline at college grain; re-grounds to the district on the switch; explains how the scope (district ⊇ college) changes the figures",
     "seed": "How's Skyline College doing in advanced manufacturing?",
     "follow_ups": ["Actually I oversee the whole district, not just Skyline — San Mateo County CCD.",
                    "Does moving up to the district change the gap numbers?"]},

    {"id": "onboarding-out-of-scope",
     "stresses": ["establish", "V", "I"],
     "member": None, "reveal": "follow_up 2 (in scope); seed is out of scope",
     "expects": "recognizes a nonprofit is not a known CCC member and says so plainly (offers what it CAN cover); grounds Laney only once named — never fabricates coverage for the nonprofit",
     "seed": "We're a workforce-training nonprofit in Oakland — can you size our labor-market gaps?",
     "follow_ups": ["So you can't help unless we're a community college?",
                    "Okay — what about Laney College then?"]},
]
