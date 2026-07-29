PROJECTS = {
    "tracksense": {
        "slug": "tracksense",
        "name": "TrackSense",
        "role": "Founder and Sole Developer",
        "status": "Completed",
        "github": "https://github.com/anantmehta20100-ant/tracksense",
        "description": (
            "TrackSense is a computer vision system that traces how possible "
            "allergen cross-contact risk spreads through a kitchen in real time, "
            "flagging elevated-risk objects before exposure may occur."
        ),
        "technologies": [
            "Python",
            "Flask",
            "YOLO through Ultralytics",
            "OpenCV",
            "scikit-learn",
            "Random Forest",
            "Roboflow",
            "GitHub",
        ],
        "test_count": 92,
        "risk_chain": ["Nut butter jar", "Cutlery", "Bread", "Plate"],
        # The eight classes locked before data preparation, so detection,
        # contact logic, and dashboard could rely on stable class IDs.
        "class_schema": [
            (0, "nut_butter_jar", "Primary allergen source"),
            (1, "whole_nuts", "Secondary allergen source"),
            (2, "hand", "Mobile carrier between objects"),
            (3, "cutlery", "Transfer vector (jar to bread)"),
            (4, "chopping_board", "Shared surface / transfer point"),
            (5, "plate", "Downstream receiving object"),
            (6, "bowl", "Downstream receiving object"),
            (7, "bread", "Final consumed item"),
        ],
        # Reliability observed in on-camera testing, not a numerical metric.
        "detection_reliability": [
            ("nut_butter_jar", "Strong", "Safe to build a demo around"),
            ("bread", "Strong", "Reliable in the scene"),
            ("cutlery (metal)", "Good", "Detects dependably"),
            ("cutlery (plastic)", "Borderline", "Much weaker than metal"),
            ("chopping_board", "Conditional", "False positives on wood grain"),
            ("whole_nuts", "Weak", "Near zero at low confidence"),
            ("bowl", "Weak", "Near zero at low confidence"),
        ],
        "risk_dataset": {
            "scenarios": "5,000",
            "events": "24,570",
            "split": "70 / 15 / 15",
        },
        "limitations": [
            "No biochemical measurement",
            "Relative-risk estimates only",
            "Camera occlusion",
            "Difficulty detecting small objects",
            "Lighting and viewpoint dependence",
            "Domain-specific training data",
            "Physical verification remains necessary",
        ],
    },
    "forebid": {
        "slug": "forebid",
        "name": "ForeBid",
        "role": "Core Developer and Co-Creator",
        "team": "Four-person team",
        "status": "Live demo and backend prototype",
        "live_demo": "https://nanda-payments.replit.app/",
        "description": (
            "ForeBid is a trust-aware market-intelligence layer that gives AI "
            "agents a fair-price snapshot before they make an offer in the "
            "NandaTown agent marketplace."
        ),
        "technologies": [
            "React",
            "Vite",
            "Express API",
            "Recharts",
            "NANDA AgentFacts schema",
            "Trust-weighted aggregation",
            "Byzantine outlier detection",
        ],
        "shipped": [
            "Live deployed frontend",
            "Snapshot endpoint",
            "AgentFacts endpoint",
            "Deterministic computeSnapshot() formula",
            "Backend prototype",
            "Market-signal visualization",
        ],
        "planned": [
            "Register ForeBid in the NANDA Index",
            "Replace deterministic data with MongoDB transaction queries",
            "Integrate the Agents collection",
            "Add an optional x402-NP payment header",
            "Connect ForeBid to a buying agent’s decision loop",
        ],
    },
    "engram-pipeline": {
        "slug": "engram-pipeline",
        "name": "Finance Expert Discovery Pipeline",
        "role": "Intern project at Engram",
        "status": "Operational internal workflow",
        "description": (
            "Built an automated, re-runnable research pipeline that identifies "
            "senior finance professionals from public company sources and "
            "converts the results into a clean, source-linked dataset for expert sourcing."
        ),
        "technologies": [
            "Python",
            "requests",
            "BeautifulSoup",
            "lxml",
            "curl_cffi",
            "Playwright",
            "Git",
            "GitHub",
            "Claude Code",
            "Codex",
        ],
        "contribution": (
            "Built using AI coding agents under my direction. I made the "
            "architectural decisions, designed the seniority-filtering logic, "
            "tested the system, diagnosed output errors, and reviewed the data "
            "before it was accepted."
        ),
        "impact": (
            "Replaced a manual, one-at-a-time research process with an automated, "
            "reviewable, and re-runnable workflow."
        ),
    },
}
