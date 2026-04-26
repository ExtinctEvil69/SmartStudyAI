"""Curated catalog of training-data sources for SmartStudy fine-tuning.

Add new entries here. Each recipe specifies:
  - source_module: which fine_tuning/sources/*.py to use
  - spec:          arguments passed to source.fetch()
  - subject:       used for exam-style mapping
  - exam_styles:   which exam formats to ALSO generate from this source
  - max_chunks:    cap on per-document chunk count

Run:  python3 fine_tuning/build_master_dataset.py
       python3 fine_tuning/build_master_dataset.py --recipes mit_801 stanford_cs229
"""

# ── YOUTUBE LECTURE RECIPES ─────────────────────────────────────────────────
# When yt-dlp is installed, you can swap explicit videos= for playlist_url=.
# I included explicit IDs for proven public lectures so the pipeline works
# without any extra installs.

RECIPES = {

    # MIT 8.01 Classical Mechanics — Walter Lewin (the flagship)
    "mit_801_physics": {
        "source_module": "youtube_lecture",
        "subject": "Physics",
        "exam_styles": ["jee_advanced", "putnam"],
        "max_chunks": 2,
        "spec": {
            "subject": "Physics",
            "videos": [
                ("GtOGurrUPmQ", "MIT 8.01 — L1: Powers of Ten, Units, Dimensions"),
                ("9JmQ8YNeoBs", "MIT 8.01 — L2: 1D Kinematics"),
                ("0BIFFCwgwxs", "MIT 8.01 — L3: Vectors, Dot/Cross Products"),
                ("dnRwoVsBV1k", "MIT 8.01 — L4: 3D Kinematics, Free Falling Frames"),
                ("g8KZRA2flyo", "MIT 8.01 — L5: Circular Motion"),
            ],
        },
    },

    # MIT 18.06 Linear Algebra — Gilbert Strang
    "mit_1806_linear_algebra": {
        "source_module": "youtube_lecture",
        "subject": "Mathematics",
        "exam_styles": ["putnam", "imo", "gate_cs"],
        "max_chunks": 2,
        "spec": {
            "subject": "Linear Algebra",
            "videos": [
                ("ZK3O402wf1c", "MIT 18.06 — L1: Geometry of Linear Equations"),
                ("QVKj3LADCnA", "MIT 18.06 — L2: Elimination with Matrices"),
                ("FX4C-JpTFgY", "MIT 18.06 — L3: Multiplication and Inverse Matrices"),
            ],
        },
    },

    # MIT 6.006 Introduction to Algorithms
    "mit_6006_algorithms": {
        "source_module": "youtube_lecture",
        "subject": "Computer Science",
        "exam_styles": ["gate_cs"],
        "max_chunks": 2,
        "spec": {
            "subject": "Algorithms",
            "videos": [
                ("HtSuA80QTyo", "MIT 6.006 — L1: Algorithmic Thinking, Peak Finding"),
                ("Zc54gFhdpLA", "MIT 6.006 — L2: Models of Computation, Document Distance"),
            ],
        },
    },

    # Stanford CS229 Machine Learning — Andrew Ng
    "stanford_cs229_ml": {
        "source_module": "youtube_lecture",
        "subject": "Machine Learning",
        "exam_styles": ["gate_cs"],
        "max_chunks": 2,
        "spec": {
            "subject": "Machine Learning",
            "videos": [
                ("jGwO_UgTS7I", "Stanford CS229 — L1: Introduction"),
                ("4b4MUYve_U8", "Stanford CS229 — L2: Linear Regression and Gradient Descent"),
            ],
        },
    },

    # Harvard CS50 — David Malan
    "harvard_cs50": {
        "source_module": "youtube_lecture",
        "subject": "Computer Science",
        "exam_styles": ["gate_cs"],
        "max_chunks": 2,
        "spec": {
            "subject": "Programming",
            "videos": [
                ("3LPJfIKxwWc", "Harvard CS50 — L0: Scratch"),
                ("cwtpLIWylAw", "Harvard CS50 — L1: C"),
            ],
        },
    },

    # 3Blue1Brown — Essence of Calculus
    "3b1b_calculus": {
        "source_module": "youtube_lecture",
        "subject": "Mathematics",
        "exam_styles": ["jee_advanced", "putnam"],
        "max_chunks": 1,
        "spec": {
            "subject": "Calculus",
            "videos": [
                ("WUvTyaaNkzM", "3B1B — Essence of Calculus, Ch.1"),
                ("9vKqVkMQHKk", "3B1B — Paradox of the derivative, Ch.2"),
                ("S0_qX4VJhMQ", "3B1B — Derivative formulas through geometry, Ch.3"),
            ],
        },
    },

    # 3Blue1Brown — Essence of Linear Algebra
    "3b1b_linear_algebra": {
        "source_module": "youtube_lecture",
        "subject": "Mathematics",
        "exam_styles": ["putnam", "gate_cs"],
        "max_chunks": 1,
        "spec": {
            "subject": "Linear Algebra",
            "videos": [
                ("fNk_zzaMoSs", "3B1B — Essence of Linear Algebra, Ch.1: Vectors"),
                ("k7RM-ot2NWY", "3B1B — Linear combinations, span, basis"),
                ("kYB8IZa5AuE", "3B1B — Linear transformations and matrices"),
            ],
        },
    },

    # 3Blue1Brown — Neural Networks (proven IDs, top-tier ML content)
    "3b1b_neural_networks": {
        "source_module": "youtube_lecture",
        "subject": "Machine Learning",
        "exam_styles": ["gate_cs"],
        "max_chunks": 2,
        "spec": {
            "subject": "Neural Networks",
            "videos": [
                ("aircAruvnKk", "3B1B — But what is a Neural Network?"),
                ("IHZwWFHWa-w", "3B1B — Gradient descent, how neural networks learn"),
                ("Ilg3gGewQ5U", "3B1B — What is backpropagation really doing?"),
                ("tIeHLnjs5U8", "3B1B — Backpropagation calculus"),
            ],
        },
    },

    # MIT 18.01 Single Variable Calculus (David Jerison)
    "mit_1801_calculus": {
        "source_module": "youtube_lecture",
        "subject": "Mathematics",
        "exam_styles": ["jee_advanced", "putnam"],
        "max_chunks": 2,
        "spec": {
            "subject": "Single Variable Calculus",
            "videos": [
                ("7K1sB05pE0A", "MIT 18.01 — L1: Derivatives, slope, velocity, rate of change"),
                ("ohXaUf8mEMA", "MIT 18.01 — L2: Limits, continuity"),
            ],
        },
    },

    # ── GITHUB LECTURE NOTES ────────────────────────────────────────────────

    "stanford_cs229_cheatsheets": {
        "source_module": "github_notes",
        "subject": "Machine Learning",
        "exam_styles": ["gate_cs"],
        "max_chunks": 1,
        "spec": {
            "repo": "afshinea/stanford-cs-229-machine-learning",
            "subject": "Machine Learning",
        },
    },

    "karpathy_nn_zero_to_hero": {
        "source_module": "github_notes",
        "subject": "Deep Learning",
        "exam_styles": ["gate_cs"],
        "max_chunks": 1,
        "spec": {
            "repo": "karpathy/nn-zero-to-hero",
            "subject": "Neural Networks",
        },
    },

    # ════════════════════════════════════════════════════════════════════════
    # V4 ADDITIONS — bigger STEM coverage (queued to run after v3 finishes)
    # YouTube channels use playlist_url + yt-dlp; GitHub repos use github_notes
    # ════════════════════════════════════════════════════════════════════════

    # YouTube channel pulls (yt-dlp extracts up to max_videos most-recent)
    "veritasium_physics": {
        "source_module": "youtube_lecture",
        "subject": "Physics",
        "exam_styles": ["jee_advanced", "putnam"],
        "max_chunks": 2,
        "spec": {
            "subject": "Physics",
            "playlist_url": "https://www.youtube.com/@veritasium/videos",
            "max_videos": 6,
        },
    },

    "numberphile_math": {
        "source_module": "youtube_lecture",
        "subject": "Mathematics",
        "exam_styles": ["putnam", "imo"],
        "max_chunks": 2,
        "spec": {
            "subject": "Mathematics",
            "playlist_url": "https://www.youtube.com/@numberphile/videos",
            "max_videos": 6,
        },
    },

    "computerphile_cs": {
        "source_module": "youtube_lecture",
        "subject": "Computer Science",
        "exam_styles": ["gate_cs"],
        "max_chunks": 2,
        "spec": {
            "subject": "Computer Science",
            "playlist_url": "https://www.youtube.com/@Computerphile/videos",
            "max_videos": 6,
        },
    },

    "fireship_dev": {
        "source_module": "youtube_lecture",
        "subject": "Computer Science",
        "exam_styles": ["gate_cs"],
        "max_chunks": 2,
        "spec": {
            "subject": "Software Engineering",
            "playlist_url": "https://www.youtube.com/@Fireship/videos",
            "max_videos": 6,
        },
    },

    "neetcode_leetcode": {
        "source_module": "youtube_lecture",
        "subject": "Computer Science",
        "exam_styles": ["gate_cs"],
        "max_chunks": 2,
        "spec": {
            "subject": "DSA / LeetCode",
            "playlist_url": "https://www.youtube.com/@NeetCodeIO/videos",
            "max_videos": 8,
        },
    },

    "statquest_stats": {
        "source_module": "youtube_lecture",
        "subject": "Statistics",
        "exam_styles": ["gate_cs"],
        "max_chunks": 2,
        "spec": {
            "subject": "Statistics & ML",
            "playlist_url": "https://www.youtube.com/@statquest/videos",
            "max_videos": 6,
        },
    },

    # GitHub repos — these are very high-yield (lots of .md files)
    "the_algorithms_python": {
        "source_module": "github_notes",
        "subject": "Computer Science",
        "exam_styles": ["gate_cs"],
        "max_chunks": 1,
        "spec": {
            "repo": "TheAlgorithms/Python",
            "subject": "Algorithms",
        },
    },

    "neetcode_solutions_repo": {
        "source_module": "github_notes",
        "subject": "Computer Science",
        "exam_styles": ["gate_cs"],
        "max_chunks": 1,
        "spec": {
            "repo": "neetcode-gh/leetcode",
            "subject": "DSA / LeetCode",
            "max_files": 40,   # repo has ~925 .md files; cap for sanity
        },
    },

    "langchain_docs": {
        "source_module": "github_notes",
        "subject": "Machine Learning",
        "exam_styles": ["gate_cs"],
        "max_chunks": 1,
        "spec": {
            "repo": "langchain-ai/langchain",
            "subject": "LLM Frameworks",
            "subdir": "docs",
            "max_files": 40,
        },
    },

    "d2l_deep_learning": {
        "source_module": "github_notes",
        "subject": "Deep Learning",
        "exam_styles": ["gate_cs"],
        "max_chunks": 1,
        "spec": {
            "repo": "d2l-ai/d2l-en",
            "subject": "Deep Learning",
            "max_files": 50,
        },
    },

    # OpenMythos — recurrent-transformer reference (skips silently if repo not public).
    # If the user has the actual URL, edit repo: "owner/name" below.
    "openmythos_reference": {
        "source_module": "github_notes",
        "subject": "Machine Learning",
        "exam_styles": ["gate_cs"],
        "max_chunks": 1,
        "spec": {
            "repo": "OpenMythos/OpenMythos",
            "subject": "Recurrent Transformer Architectures",
        },
    },

    # ════════════════════════════════════════════════════════════════════════
    # V5 — SUNDAY ADDITIONS (subject balance + reliable high-yield repos)
    # ════════════════════════════════════════════════════════════════════════

    "handson_ml3": {
        "source_module": "github_notes",
        "subject": "Machine Learning",
        "exam_styles": ["gate_cs"],
        "max_chunks": 1,
        "spec": {
            "repo": "ageron/handson-ml3",
            "subject": "Machine Learning (Géron book)",
            "max_files": 40,
        },
    },

    "ml_for_beginners": {
        "source_module": "github_notes",
        "subject": "Machine Learning",
        "exam_styles": ["gate_cs"],
        "max_chunks": 1,
        "spec": {
            "repo": "microsoft/ML-For-Beginners",
            "subject": "ML fundamentals (Microsoft curriculum)",
            "max_files": 40,
        },
    },

    "ossu_computer_science": {
        "source_module": "github_notes",
        "subject": "Computer Science",
        "exam_styles": ["gate_cs"],
        "max_chunks": 1,
        "spec": {
            "repo": "ossu/computer-science",
            "subject": "Open-Source CS Curriculum",
            "max_files": 25,
        },
    },

    "stanford_cs230_dl_cheatsheets": {
        "source_module": "github_notes",
        "subject": "Deep Learning",
        "exam_styles": ["gate_cs"],
        "max_chunks": 1,
        "spec": {
            "repo": "afshinea/stanford-cs-230-deep-learning",
            "subject": "Deep Learning (Stanford CS230)",
            "max_files": 30,
        },
    },

    "ted_ed_humanities": {
        "source_module": "youtube_lecture",
        "subject": "Humanities",
        "exam_styles": [],
        "max_chunks": 2,
        "spec": {
            "subject": "Humanities & Science",
            "playlist_url": "https://www.youtube.com/@TED-Ed/videos",
            "max_videos": 6,
        },
    },

    "crashcourse_general": {
        "source_module": "youtube_lecture",
        "subject": "Science",
        "exam_styles": ["sat_math"],
        "max_chunks": 2,
        "spec": {
            "subject": "Crash Course (mixed)",
            "playlist_url": "https://www.youtube.com/@crashcourse/videos",
            "max_videos": 6,
        },
    },
}


# ── EXAM-PREP-ONLY RECIPES ──────────────────────────────────────────────────
# These don't fetch external content — they reuse the MERGED transcripts/notes
# from other recipes and produce additional exam-style problems.
# Listed here so the master runner can iterate them.

EXAM_BOOST_TARGETS = {
    "olympiad_math": ["putnam", "imo", "usamo"],
    "indian_engineering": ["jee_advanced", "gate_cs"],
    "us_college": ["sat_math"],
}


# ── Convenience: list all recipe IDs ────────────────────────────────────────

def all_recipe_ids() -> list[str]:
    return list(RECIPES.keys())
