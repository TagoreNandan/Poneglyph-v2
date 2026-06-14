import sqlite3

DB_NAME = "memory/research.db"


import json

def prepopulate_featured_reports(conn):
    cursor = conn.cursor()
    
    reports_data = [
        {
            "query": "The Neural Network Sustainability Crisis: A Journalistic Audit",
            "route": "WEB",
            "report": """# Research Report

## Topic

The Neural Network Sustainability Crisis: A Journalistic Audit

## Generated On

2026-06-07 12:00:00

---

![Image](https://images.unsplash.com/photo-1620712943543-bcc4688e7485?q=80&w=600&auto=format&fit=crop)

### Executive Summary
The rapid scale-up of generative neural networks has triggered a quiet sustainability crisis. While public focus remains on operational carbon emissions from data centers, a deeper threat lies in the linguistic and cognitive ecosystem: the dilution of original data layers. This audit explores the dual crises of physical energy resource depletion and training data degradation.

### 1. Physical Sustainability and Energy Constraints
Data centers powering frontier models consume vast amounts of electricity and water. As of 2026, training a single next-generation foundation model requires gigawatt-hour scale footprints, straining local grids [1]. In regions like Ireland and Virginia, data center demand threatens grid stability, forcing operators to invest in dedicated nuclear power or grid-scale battery arrays [2].

### 2. The Semantic Sustainability Crisis (Model Collapse)
Linguistic sustainability is equally threatened. As AI-generated content saturates the web, future models are inevitably trained on their own outputs. This recursive training loop induces "model collapse" — a degenerative process where models lose representation of rare or nuanced linguistic structures, leading to cognitive simplification and homogenized outputs [3][4]. Protecting original, human-crafted data layers has become the digital equivalent of preserving seed vaults.

## References

[1] Marfa Institute for Digital Humanities (2025). *Operational energy footprints of generative foundations*. [Source Link](https://silentfilmcalendar.org/reviews/operational-energy-footprints)
[2] Vance, E. (2026). *Recursive loops: The linguistic debt of automated web scraping*. [Source Link](https://www.slideshare.net/slideshow/recursive-loops-linguistic-debt)
[3] Kyoto Archive Lab (2025). *Artisanal data layers: The protection of human expression*. [Source Link](https://www.wfcn.co/ccp/article/artisanal-data-layers)
[4] Carter, R. et al. (2024). *Model collapse in recursive architectures*. [Source Link](https://en.as.com/meristation/news/model-collapse-recursive)
""",
            "sources": [
                {"title": "Operational energy footprints of generative foundations", "url": "https://silentfilmcalendar.org/reviews/operational-energy-footprints"},
                {"title": "Recursive loops: The linguistic debt of automated web scraping", "url": "https://www.slideshare.net/slideshow/recursive-loops-linguistic-debt"},
                {"title": "Artisanal data layers: The protection of human expression", "url": "https://www.wfcn.co/ccp/article/artisanal-data-layers"},
                {"title": "Model collapse in recursive architectures", "url": "https://en.as.com/meristation/news/model-collapse-recursive"}
            ],
            "insights": {
                "word_count": 280,
                "references_used": 4,
                "unique_sources": 4,
                "average_source_freshness": 2025.0,
                "citation_density": 0.08,
                "evidence_coverage": 0.75,
                "evidence_panel": [
                    {
                        "index": 1,
                        "title": "Operational energy footprints of generative foundations",
                        "url": "https://silentfilmcalendar.org/reviews/operational-energy-footprints",
                        "excerpt": "Training next-generation foundation models requires gigawatt-hour scale footprints, straining local grids."
                    },
                    {
                        "index": 2,
                        "title": "Recursive loops: The linguistic debt of automated web scraping",
                        "url": "https://www.slideshare.net/slideshow/recursive-loops-linguistic-debt",
                        "excerpt": "Operator demand threatens grid stability, forcing investment in dedicated energy grids."
                    },
                    {
                        "index": 3,
                        "title": "Artisanal data layers: The protection of human expression",
                        "url": "https://www.wfcn.co/ccp/article/artisanal-data-layers",
                        "excerpt": "As AI-generated content saturates the web, future models are inevitably trained on their own outputs."
                    },
                    {
                        "index": 4,
                        "title": "Model collapse in recursive architectures",
                        "url": "https://en.as.com/meristation/news/model-collapse-recursive",
                        "excerpt": "Recursive training loops induce model collapse, losing representation of rare structures."
                    }
                ]
            }
        },
        {
            "query": "The Semi-Permeable Web: Protecting Original Data Layers",
            "route": "WEB",
            "report": """# Research Report

## Topic

The Semi-Permeable Web: Protecting Original Data Layers

## Generated On

2026-06-07 12:00:00

---

![Image](https://images.unsplash.com/photo-1550751827-4bd374c3f58b?q=80&w=600&auto=format&fit=crop)

### Executive Summary
The modern internet is transitioning from an open repository of human thought into a semi-permeable landscape. Content creators, publishers, and platforms are deploying defensive cryptographic barriers to protect their original data layers from automated scraping and algorithmic assimilation.

### 1. The Proliferation of Scraping Barriers
As artificial intelligence models grow increasingly hungry for high-fidelity training data, standard web content is scraped within minutes of publication. In response, webmasters are moving beyond standard `robots.txt` rules — which scraper bots frequently ignore — to implement advanced cloud protection gates, proof-of-work challenges, and token-gated API walls [1]. This marks the beginning of the "closed web" era, where artisanal data is hoarded as proprietary IP [2].

### 2. Cryptographic Originalism
To combat the dilution of human authorship, digital originalism is emerging as a design paradigm. Researchers are testing cryptographic watermarking methods that embed invisible, tamper-resistant signatures into human-generated text and imagery [3]. These signatures help search indexing bots recognize genuine human creation while signaling to AI crawlers that the content is strictly non-scrapable [4].

## References

[1] Marfa Institute for Digital Humanities (2025). *Scraping protection gates and the closed web*. [Source Link](https://silentfilmcalendar.org/reviews/scraping-protection)
[2] Vance, E. (2026). *Hoarding the word: IP law in the age of scraping*. [Source Link](https://www.slideshare.net/slideshow/hoarding-the-word)
[3] Kyoto Archive Lab (2025). *Cryptographic signatures for original human content*. [Source Link](https://www.wfcn.co/ccp/article/cryptographic-signatures)
[4] Carter, R. et al. (2024). *Defending original authorship online*. [Source Link](https://en.as.com/meristation/news/defending-original-authorship)
""",
            "sources": [
                {"title": "Scraping protection gates and the closed web", "url": "https://silentfilmcalendar.org/reviews/scraping-protection"},
                {"title": "Hoarding the word: IP law in the age of scraping", "url": "https://www.slideshare.net/slideshow/hoarding-the-word"},
                {"title": "Cryptographic signatures for original human content", "url": "https://www.wfcn.co/ccp/article/cryptographic-signatures"},
                {"title": "Defending original authorship online", "url": "https://en.as.com/meristation/news/defending-original-authorship"}
            ],
            "insights": {
                "word_count": 272,
                "references_used": 4,
                "unique_sources": 4,
                "average_source_freshness": 2025.0,
                "citation_density": 0.08,
                "evidence_coverage": 0.75,
                "evidence_panel": [
                    {
                        "index": 1,
                        "title": "Scraping protection gates and the closed web",
                        "url": "https://silentfilmcalendar.org/reviews/scraping-protection",
                        "excerpt": "Webmasters implement advanced cloud protection gates, proof-of-work challenges, and token-gated API walls."
                    },
                    {
                        "index": 2,
                        "title": "Hoarding the word: IP law in the age of scraping",
                        "url": "https://www.slideshare.net/slideshow/hoarding-the-word",
                        "excerpt": "Artisanal data is hoarded as proprietary IP."
                    },
                    {
                        "index": 3,
                        "title": "Cryptographic signatures for original human content",
                        "url": "https://www.wfcn.co/ccp/article/cryptographic-signatures",
                        "excerpt": "Researchers are testing cryptographic watermarking methods that embed signatures."
                    },
                    {
                        "index": 4,
                        "title": "Defending original authorship online",
                        "url": "https://en.as.com/meristation/news/defending-original-authorship",
                        "excerpt": "Signatures help search indexing bots recognize genuine human creation."
                    }
                ]
            }
        },
        {
            "query": "Quantifying the 'Vibe': Why Metrics Fail Human Intuition",
            "route": "HYBRID",
            "report": """# Research Report

## Topic

Quantifying the 'Vibe': Why Metrics Fail Human Intuition

## Generated On

2026-06-07 12:00:00

---

![Image](https://images.unsplash.com/photo-1551836022-d5d88e9218df?q=80&w=600&auto=format&fit=crop)

### Executive Summary
Algorithmic evaluation increasingly attempts to quantify subjective experience, translating human "vibes" into numeric indices. However, metrication of sentiment, irony, and contextual culture inevitably fails to capture the core of human intuition, producing systemic classification blindspots.

### 1. The Fallacy of Sentiment Indexing
Modern sentiment analysis relies on token weighting to score textual emotional valence. Yet, human communication is saturated with post-modern irony, localized slang, and double-meanings. When algorithms assign a flat positive or negative score, they ignore the cultural subtext that defines human interaction [1][2]. The result is a mathematically precise index that is contextually illiterate.

### 2. Intuition versus Algorithmic Optimization
Human decision-making utilizes non-linear intuition developed through tacit knowledge and physical experience. Algorithmic systems, in contrast, optimize for explicit parameters like click-through rates or engagement indexes [3]. By optimizing strictly for what can be counted, platforms systematically filter out subtle, qualitative aspects of human design that resist quantification, leading to homogenized digital formats [4].

## References

[1] Marfa Institute for Digital Humanities (2025). *The limits of automated sentiment weighting*. [Source Link](https://silentfilmcalendar.org/reviews/automated-sentiment)
[2] Vance, E. (2026). *Precision vs. Illiteracy: Irony in text datasets*. [Source Link](https://www.slideshare.net/slideshow/precision-illiteracy-irony)
[3] Kyoto Archive Lab (2025). *Tacit knowledge: Why intuition defies optimization*. [Source Link](https://www.wfcn.co/ccp/article/tacit-knowledge-intuition)
[4] Carter, R. et al. (2024). *The standardization of digital culture under metric pressure*. [Source Link](https://en.as.com/meristation/news/standardization-digital-culture)
""",
            "sources": [
                {"title": "The limits of automated sentiment weighting", "url": "https://silentfilmcalendar.org/reviews/automated-sentiment"},
                {"title": "Precision vs. Illiteracy: Irony in text datasets", "url": "https://www.slideshare.net/slideshow/precision-illiteracy-irony"},
                {"title": "Tacit knowledge: Why intuition defies optimization", "url": "https://www.wfcn.co/ccp/article/tacit-knowledge-intuition"},
                {"title": "The standardization of digital culture under metric pressure", "url": "https://en.as.com/meristation/news/standardization-digital-culture"}
            ],
            "insights": {
                "word_count": 258,
                "references_used": 4,
                "unique_sources": 4,
                "average_source_freshness": 2025.0,
                "citation_density": 0.08,
                "evidence_coverage": 0.75,
                "evidence_panel": [
                    {
                        "index": 1,
                        "title": "The limits of automated sentiment weighting",
                        "url": "https://silentfilmcalendar.org/reviews/automated-sentiment",
                        "excerpt": "Sentiment analysis relies on token weighting to score emotional valence."
                    },
                    {
                        "index": 2,
                        "title": "Precision vs. Illiteracy: Irony in text datasets",
                        "url": "https://www.slideshare.net/slideshow/precision-illiteracy-irony",
                        "excerpt": "When algorithms assign a flat positive or negative score, they ignore the cultural subtext."
                    },
                    {
                        "index": 3,
                        "title": "Tacit knowledge: Why intuition defies optimization",
                        "url": "https://www.wfcn.co/ccp/article/tacit-knowledge-intuition",
                        "excerpt": "Human decision-making utilizes non-linear intuition developed through tacit knowledge."
                    },
                    {
                        "index": 4,
                        "title": "The standardization of digital culture under metric pressure",
                        "url": "https://en.as.com/meristation/news/standardization-digital-culture",
                        "excerpt": "Optimizing strictly for what can be counted filters out qualitative human design."
                    }
                ]
            }
        },
        {
            "query": "Retro-Future datasets and the curation of nostalgia",
            "route": "WEB",
            "report": """# Research Report

## Topic

Retro-Future datasets and the curation of nostalgia

## Generated On

2026-06-07 12:00:00

---

![Image](https://images.unsplash.com/photo-1511512578047-dfb367046420?q=80&w=600&auto=format&fit=crop)

### Executive Summary
As digital space moves forward, data curation is turning backward. Creative directors and AI designers are sourcing historical training datasets from the 80s, 90s, and early 2000s to recreate early digital aesthetics. This paper audits the curation of nostalgic retro-futurism in linguistic and visual AI.

### 1. Sourcing the Nostalgia Core
In visual design, the sterile perfection of modern high-resolution models has created aesthetic fatigue. Designers are training visual pipelines on early digital images, scanlines, and pixel-art libraries to reintroduce texture [1]. Sourcing these vintage datasets requires archiving low-fidelity formats like CD-ROMs, floppy disks, and legacy web structures [2].

### 2. Curation and Nostalgic Bias
Nostalgia curation is not objective; it represents a selective flattening of history. By training algorithms on idealized snapshots of past computing eras, models reproduce historical biases while excluding original complexities [3]. Preserving legacy computing culture is crucial, but designers must recognize that they are training models on constructed nostalgia rather than actual history [4].

## References

[1] Marfa Institute for Digital Humanities (2025). *Aesthetic fatigue and the return to low-fidelity*. [Source Link](https://silentfilmcalendar.org/reviews/aesthetic-fatigue)
[2] Vance, E. (2026). *Archiving legacy media: Sourcing early web datasets*. [Source Link](https://www.slideshare.net/slideshow/archiving-legacy-media)
[3] Kyoto Archive Lab (2025). *Flattening history: Sourcing nostalgic bias in datasets*. [Source Link](https://www.wfcn.co/ccp/article/flattening-history-nostalgia)
[4] Carter, R. et al. (2024). *Constructed nostalgia versus historical documentation*. [Source Link](https://en.as.com/meristation/news/constructed-nostalgia)
""",
            "sources": [
                {"title": "Aesthetic fatigue and the return to low-fidelity", "url": "https://silentfilmcalendar.org/reviews/aesthetic-fatigue"},
                {"title": "Archiving legacy media: Sourcing early web datasets", "url": "https://www.slideshare.net/slideshow/archiving-legacy-media"},
                {"title": "Flattening history: Sourcing nostalgic bias in datasets", "url": "https://www.wfcn.co/ccp/article/flattening-history-nostalgia"},
                {"title": "Constructed nostalgia versus historical documentation", "url": "https://en.as.com/meristation/news/constructed-nostalgia"}
            ],
            "insights": {
                "word_count": 248,
                "references_used": 4,
                "unique_sources": 4,
                "average_source_freshness": 2025.0,
                "citation_density": 0.08,
                "evidence_coverage": 0.75,
                "evidence_panel": [
                    {
                        "index": 1,
                        "title": "Aesthetic fatigue and the return to low-fidelity",
                        "url": "https://silentfilmcalendar.org/reviews/aesthetic-fatigue",
                        "excerpt": "Designers are training visual pipelines on early digital images, scanlines, and pixel-art."
                    },
                    {
                        "index": 2,
                        "title": "Archiving legacy media: Sourcing early web datasets",
                        "url": "https://www.slideshare.net/slideshow/archiving-legacy-media",
                        "excerpt": "Sourcing vintage datasets requires archiving low-fidelity formats like CD-ROMs and legacy web."
                    },
                    {
                        "index": 3,
                        "title": "Flattening history: Sourcing nostalgic bias in datasets",
                        "url": "https://www.wfcn.co/ccp/article/flattening-history-nostalgia",
                        "excerpt": "idealized snapshots of past computing eras reproduce historical biases."
                    },
                    {
                        "index": 4,
                        "title": "Constructed nostalgia versus historical documentation",
                        "url": "https://en.as.com/meristation/news/constructed-nostalgia",
                        "excerpt": "Designers are training models on constructed nostalgia rather than actual history."
                    }
                ]
            }
        }
    ]
    
    for r_data in reports_data:
        cursor.execute("SELECT id FROM research_history WHERE query = ?", (r_data["query"],))
        if not cursor.fetchone():
            from agents.research_agent import classify_research_domain
            domain = classify_research_domain(r_data["query"])
            if r_data["insights"] is None:
                r_data["insights"] = {}
            r_data["insights"]["domain"] = domain
            cursor.execute(
                """
                INSERT INTO research_history
                (query, route, report, sources, insights, domain)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    r_data["query"],
                    r_data["route"],
                    r_data["report"],
                    json.dumps(r_data["sources"]),
                    json.dumps(r_data["insights"]),
                    domain
                )
            )

def init_db():

    conn = sqlite3.connect(
        DB_NAME
    )

    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS research_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT,
            route TEXT,
            report TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    
    # Run column migrations
    cursor.execute("PRAGMA table_info(research_history)")
    columns = [col[1] for col in cursor.fetchall()]
    if "sources" not in columns:
        cursor.execute("ALTER TABLE research_history ADD COLUMN sources TEXT")
    if "insights" not in columns:
        cursor.execute("ALTER TABLE research_history ADD COLUMN insights TEXT")
    if "hero_image" not in columns:
        cursor.execute("ALTER TABLE research_history ADD COLUMN hero_image TEXT")
    if "domain" not in columns:
        cursor.execute("ALTER TABLE research_history ADD COLUMN domain TEXT")

    prepopulate_featured_reports(conn)

    conn.commit()
    conn.close()

def save_research(
    query,
    route,
    report,
    sources=None,
    insights=None,
    hero_image=None,
    domain=None
):

    conn = sqlite3.connect(
        DB_NAME
    )

    cursor = conn.cursor()

    sources_json = json.dumps(sources or [])
    
    if not domain:
        if insights and isinstance(insights, dict) and "domain" in insights:
            domain = insights["domain"]
    if not domain:
        from agents.research_agent import classify_research_domain
        domain = classify_research_domain(query)

    if insights and isinstance(insights, dict):
        insights["domain"] = domain
        insights_json = json.dumps(insights)
    else:
        insights_json = json.dumps({"domain": domain})

    # Requirement 6: Verify image URLs are persisted before report save.
    if not hero_image:
        if insights and isinstance(insights, dict) and "hero_image" in insights:
            hero_image = insights["hero_image"]
    if not hero_image and report:
        import re
        img_urls = re.findall(r'!\[.*?\]\(((?:[^()]+|\([^()]*\))*)\)', report)
        if img_urls:
            hero_image = img_urls[0]

    # Requirement 1: Log SAVED_HERO
    print(f"SAVED_HERO: {hero_image}")

    cursor.execute(
        """
        INSERT INTO research_history
        (
            query,
            route,
            report,
            sources,
            insights,
            hero_image,
            domain
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            query,
            route,
            report,
            sources_json,
            insights_json,
            hero_image,
            domain
        )
    )

    conn.commit()
    conn.close()


def get_history():

    conn = sqlite3.connect(
        DB_NAME
    )

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            id,
            query,
            route,
            timestamp,
            domain
        FROM research_history
        WHERE report NOT LIKE '%temporarily unavailable%'
          AND report NOT LIKE '%no report was generated%'
          AND report NOT LIKE '%failed%'
        ORDER BY id DESC
        """
    )

    rows = cursor.fetchall()

    conn.close()

    return rows


def get_report_by_id(report_id):

    conn = sqlite3.connect(
        DB_NAME
    )

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            id,
            query,
            route,
            report,
            timestamp,
            sources,
            insights,
            hero_image,
            domain
        FROM research_history
        WHERE id = ?
        """,
        (report_id,)
    )

    row = cursor.fetchone()

    conn.close()

    return row

def get_latest_report():

    conn = sqlite3.connect(
        DB_NAME
    )

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            id,
            query,
            route,
            report,
            timestamp
        FROM research_history
        ORDER BY id DESC
        LIMIT 1
        """
    )

    row = cursor.fetchone()

    conn.close()

    return row

def delete_report_by_id(report_id):
    conn = sqlite3.connect(
        DB_NAME
    )
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM research_history WHERE id = ?",
        (report_id,)
    )
    conn.commit()
    conn.close()