from llm.gemini_client import generate as gemini_generate
from llm.groq_client import generate as groq_generate


def classify_report_type(query: str) -> str:
    categories = [
        "COMPANY_COMPARISON",
        "FINANCIAL_ANALYSIS",
        "SPORTS_RIVALRY",
        "CHARACTER_ANALYSIS",
        "FICTIONAL_ARC",
        "TECHNOLOGY_RESEARCH",
        "PRODUCT_COMPARISON",
        "GENERAL_RESEARCH"
    ]
    
    classification_prompt = f"""
Classify the following research query into exactly one of these 8 registered domains:
1. COMPANY_COMPARISON: comparing two or more companies, business strategies, or corporate profiles (e.g. "OpenAI vs Anthropic", "Apple vs Google", "Microsoft vs Nvidia").
2. FINANCIAL_ANALYSIS: analysis of stocks, earnings, market trends, valuations, corporate performance, or financial data (e.g. "Tesla Stock Analysis", "NVIDIA Q3 Earnings", "Inflation rates in 2026").
3. SPORTS_RIVALRY: comparing athletes, sports teams, race drivers, sports matches, or sport rivalries (e.g. "Messi vs Ronaldo", "LeBron James vs Michael Jordan", "Lewis Hamilton vs Max Verstappen").
4. CHARACTER_ANALYSIS: analysis of fictional or non-fictional individuals, characters, biographies, traits, powers, or specific character techniques/weapons (e.g. "Optimus Prime", "Harry Potter", "Senbonzakura Bankai", "Uchiha Itachi").
5. FICTIONAL_ARC: analysis of narrative storylines, anime/manga arcs, sagas, or fictional event segments (e.g. "Marineford", "Wano Arc", "Chimera Ant Arc").
6. TECHNOLOGY_RESEARCH: analysis of technical concepts, frameworks, architectures, coding tools, scientific topics, or algorithms (e.g. "Quantum Computing current state", "Transformer Architecture", "Next.js vs Remix").
7. PRODUCT_COMPARISON: comparing consumer products, hardware devices, gadgets, software tools, models, or apps (e.g. "iPhone 16 Pro Max vs Samsung Galaxy S26 Ultra", "ChatGPT vs Claude 3.5 Sonnet").
8. GENERAL_RESEARCH: any other research topic that doesn't fit the categories above (e.g. general questions, human behavior, history, social issues, health, lifestyle, etc.).

Query: "{query}"

Return only the classification name from the list above (e.g. "SPORTS_RIVALRY" or "COMPANY_COMPARISON"). Do not include numbers, explanation, or other text.
"""
    response_clean = ""
    try:
        response = gemini_generate(classification_prompt, model="gemini-2.5-flash").strip()
        response_clean = response.replace('"', '').replace("'", "").strip()
    except Exception as e:
        import sys
        print(f"Gemini error during classification: {e}, trying Groq...", file=sys.stderr)
        try:
            response = groq_generate(classification_prompt, model="llama-3.3-70b-versatile").strip()
            response_clean = response.replace('"', '').replace("'", "").strip()
        except Exception as groq_err:
            print(f"Groq error during classification: {groq_err}", file=sys.stderr)

    if response_clean:
        for cat in categories:
            if cat.lower() in response_clean.lower():
                return cat
                
    # Rule-based fallback if LLM fails
    import re
    q_lower = query.lower()
    
    # 1. Financial Analysis
    if any(w in q_lower for w in ["stock", "financial", "earnings", "valuation", "revenue", "fiscal", "shares", "nasdaq", "nyse", "profit", "investment"]):
        return "FINANCIAL_ANALYSIS"
        
    # 2. Comparison Queries
    if re.search(r"\b(vs|versus|compare|comparison)\b", q_lower):
        # Sports rivalry comparison
        sports_keywords = ["messi", "ronaldo", "lebron", "jordan", "kobe", "federer", "nadal", "player", "athlete", "fc", "real madrid", "hamilton", "verstappen", "f1", "formula", "race", "driver", "team", "cup", "championship", "rivalry"]
        if any(w in q_lower for w in sports_keywords):
            return "SPORTS_RIVALRY"
            
        # Tech product comparison
        product_keywords = ["iphone", "galaxy", "pixel", "chatgpt", "claude", "samsung", "playstation", "xbox", "nintendo", "device", "phone", "console", "app", "model"]
        if any(w in q_lower for w in product_keywords):
            return "PRODUCT_COMPARISON"
            
        # Tech framework / programming tool comparison
        tech_keywords = ["react", "svelte", "next.js", "remix", "vue", "angular", "framework", "programming", "python", "javascript", "technology", "quantum", "computing", "network", "networks", "architecture", "transformer"]
        if any(w in q_lower for w in tech_keywords):
            return "TECHNOLOGY_RESEARCH"
            
        # Default comparison is Company Comparison
        return "COMPANY_COMPARISON"
        
    # 3. Fictional Arc
    if re.search(r"\b(arc|saga|episode|chapters|marineford|wano)\b", q_lower):
        return "FICTIONAL_ARC"
        
    # 4. Character Analysis
    character_keywords = ["bankai", "optimus", "prime", "naruto", "luffy", "goku", "character", "power", "ability", "abilities", "senbonzakura", "itachi", "sasuke", "deku", "ichigo", "itadori", "biography", "lore"]
    if any(w in q_lower for w in character_keywords):
        return "CHARACTER_ANALYSIS"
        
    # 5. Technology Research
    tech_keywords = ["computing", "architecture", "framework", "quantum", "react", "svelte", "programming", "python", "javascript", "technology", "neural network", "transformer", "ai", "ml", "llm", "blockchain", "crypto"]
    if any(w in q_lower for w in tech_keywords):
        return "TECHNOLOGY_RESEARCH"
        
    return "GENERAL_RESEARCH"


def classify_research_domain(query: str) -> str:
    suggested_domains = [
        "Market Intelligence",
        "Company Analysis",
        "Industry Analysis",
        "Technology Analysis",
        "Sports Analysis",
        "Athlete Comparison",
        "Motorsport Analysis",
        "Entertainment Analysis",
        "Character Analysis",
        "Anime Analysis",
        "Fictional Universe Analysis",
        "Historical Analysis",
        "Product Analysis",
        "Scientific Analysis",
        "General Research"
    ]
    
    classification_prompt = f"""
Classify the following research query into exactly one of these 15 domains:
1. Market Intelligence: Business market comparisons, market share, corporate strategy comparisons (e.g., "OpenAI vs Anthropic").
2. Company Analysis: Specific company performance, stock analysis, earnings (e.g., "Tesla Stock Analysis", "NVIDIA Q3 Earnings").
3. Industry Analysis: Broader sector trends, industry growth, market reports.
4. Technology Analysis: Software frameworks, architectures, programming languages, algorithms (e.g., "Transformer Architecture", "React vs Svelte").
5. Sports Analysis: Sports teams, clubs, league history, rules (e.g., "F1 driver championship history").
6. Athlete Comparison: Comparisons between sports players or athletes (e.g., "Messi vs Ronaldo", "LeBron James vs Michael Jordan").
7. Motorsport Analysis: Racing, Formula 1, drivers, racing teams (e.g., "Lewis Hamilton vs Max Verstappen", "Ferrari F1").
8. Entertainment Analysis: Cinema, television, music, gaming culture (e.g., "Growth of Indian cinema in the 20s").
9. Character Analysis: Biographies, character lore, fictional individuals (e.g., "Optimus Prime", "Uchiha Itachi").
10. Anime Analysis: Anime/manga-specific concepts, techniques, weapons, or abilities (e.g., "Senbonzakura Bankai", "Goku Ultra Instinct powers").
11. Fictional Universe Analysis: Sagas, story arcs, fictional locations or events (e.g., "Marineford", "Wano Arc").
12. Historical Analysis: Historical events, figures, origin of items (e.g., "History of chocolate", "Ancient Rome").
13. Product Analysis: Consumer electronics, devices, gadget comparisons (e.g., "iPhone 16 Pro Max vs Samsung Galaxy S26 Ultra").
14. Scientific Analysis: Scientific papers, biology, physics, mathematics (e.g., "Quantum Computing current state").
15. General Research: General self-help, psychology, non-specific topics, or when classification confidence is low (e.g., "Anger management in Gen-Z", "Benefits of mindfulness").

Query: "{query}"

Return only the domain name from the list above (e.g. "Motorsport Analysis" or "Character Analysis"). Do not include numbers, explanation, or other text.
"""
    response_clean = ""
    try:
        response = gemini_generate(classification_prompt, model="gemini-2.5-flash").strip()
        response_clean = response.replace('"', '').replace("'", "").strip()
    except Exception as e:
        import sys
        print(f"Gemini error during domain classification: {e}, trying Groq...", file=sys.stderr)
        try:
            response = groq_generate(classification_prompt, model="llama-3.3-70b-versatile").strip()
            response_clean = response.replace('"', '').replace("'", "").strip()
        except Exception as groq_err:
            print(f"Groq error during domain classification: {groq_err}", file=sys.stderr)

    if response_clean:
        for dom in suggested_domains:
            if dom.lower() in response_clean.lower():
                return dom

    # Rule-based fallback if LLM fails or is rate-limited
    import re
    q_lower = query.lower()

    # 1. Motorsport Analysis
    if any(w in q_lower for w in ["hamilton", "verstappen", "f1", "formula 1", "formula one", "ferrari", "racing", "driver", "mclaren", "red bull racing", "mercedes amg"]):
        return "Motorsport Analysis"

    # 2. Athlete Comparison
    if re.search(r"\b(vs|versus|compare|comparison)\b", q_lower):
        sports_players = ["messi", "ronaldo", "lebron", "jordan", "kobe", "federer", "nadal", "djokovic", "mbappe", "haland", "neymar"]
        if any(w in q_lower for w in sports_players):
            return "Athlete Comparison"

    # 3. Sports Analysis
    if any(w in q_lower for w in ["sports", "football", "basketball", "soccer", "player", "athlete", "cup", "league", "championship"]):
        return "Sports Analysis"

    # 4. Anime Analysis
    if any(w in q_lower for w in ["bankai", "senbonzakura", "naruto", "goku", "luffy", "ichigo", "bleach", "one piece", "saiyan", "jutsu", "sharingan"]):
        return "Anime Analysis"

    # 5. Fictional Universe Analysis
    if any(w in q_lower for w in ["wano", "marineford", "arc", "saga", "fictional universe", "middle earth", "hogwarts", "gotham", "targaryen", "westeros"]):
        return "Fictional Universe Analysis"

    # 6. Character Analysis
    if any(w in q_lower for w in ["optimus", "prime", "character", "biography", "lore", "villain", "hero"]):
        return "Character Analysis"

    # 7. Company Analysis
    if any(w in q_lower for w in ["stock", "earnings", "fiscal", "revenue", "q3", "q4", "valuation", "shares", "nasdaq", "nyse", "profit"]):
        # But if it's comparison of companies:
        if re.search(r"\b(vs|versus|compare|comparison)\b", q_lower):
            return "Market Intelligence"
        return "Company Analysis"

    # 8. Product Analysis
    if any(w in q_lower for w in ["iphone", "galaxy", "pixel", "s26", "console", "device", "playstation", "xbox", "nintendo", "phone", "app"]):
        return "Product Analysis"

    # 9. Technology Analysis
    if any(w in q_lower for w in ["quantum computing", "transformer architecture", "next.js", "react", "svelte", "framework", "neural network", "algorithm", "coding", "web framework"]):
        return "Technology Analysis"

    # 10. Historical Analysis
    if any(w in q_lower for w in ["history", "ancient", "era", "century", "1920s", "origin of"]):
        return "Historical Analysis"

    # 11. Scientific Analysis
    if any(w in q_lower for w in ["paper", "academic", "research", "scientific", "physics", "biology", "cosmology"]):
        return "Scientific Analysis"

    # 12. Market Intelligence (General company comparison fallback)
    if re.search(r"\b(vs|versus|compare|comparison)\b", q_lower):
        if any(w in q_lower for w in ["openai", "anthropic", "google", "microsoft", "apple", "meta", "amazon", "company", "companies", "business", "strategies"]):
            return "Market Intelligence"

    return "General Research"


def generate_research_summary(
    query,
    search_results,
    route="WEB"
):

    formatted_results = ""

    for idx, result in enumerate(
        search_results,
        start=1
    ):

        content = (
            result.get("raw_content")
            or result.get("content")
            or result.get("summary")
            or ""
        )

        formatted_results += f"""
=========================
SOURCE {idx}
=========================

TITLE:
{result.get('title', 'Unknown Title')}

URL:
{result.get('url', '')}

AUTHORS:
{result.get('authors', 'Unknown Authors')}

YEAR:
{result.get('year', 'Unknown Year')}

CONTENT:
{str(content)[:25000]}
"""

    category = classify_report_type(query)
    print(f"TOPIC: {query}")
    print(f"CATEGORY: {category}")

    if route == "ARXIV":
        prompt = f"""
You are a senior academic research reviewer.

Research Topic:
{query}

Sources:

{formatted_results}

You must write a comprehensive, synthesized academic review report based on the provided papers. Do not summarize them individually.

Your report must cover the following aspects:
1. Synthesize the key findings, methodologies, and contributions across all the papers.
2. Compare the different papers, identifying where the approaches or findings agree or diverge.
3. Identify major emerging trends or future research directions in this academic area.
4. Identify explicitly any disagreements, conflicts, or debates between the papers.
5. Identify and analyze the limitations, constraints, or gaps in the current studies or methodologies.

Requirements:
- Cite the papers using inline citation markers (e.g., `[1]`, `[2]`, `[1][3]`) at the end of statements.
- Synthesize findings and compare papers rather than summarizing them individually.
- Return valid markdown only.
"""
    elif category == "COMPANY_COMPARISON":
        prompt = f"""You are a senior industry research analyst.

Research Topic:
{query}

Sources:

{formatted_results}

Do not summarize sources individually.

Instead:
- Synthesize information across all sources to compare the companies in the topic
- Compare their market positions, strategies, strengths, and weaknesses
- Include at least one side-by-side comparison table in markdown format comparing key attributes
- Explain why findings matter, identify patterns, and implications
- Draw conclusions from evidence and provide expert analysis

Every section should contain reasoning, not just facts. Focus on insight generation, not summarization.

Requirements:
- Target length: 600-800 words
- Use information from all available sources
- Mention when sources agree and disagreements when they exist
- Avoid repeating information and use concise analytical writing
- Support findings with evidence from sources using inline citation markers (e.g., `[1]`, `[2]`, `[1][3]`).
- You MUST append citation markers to every factual statement or claim. Example: "Entity A holds a 40% market share, while Entity B holds 25%.[1]"
- Do NOT fabricate citations. Only use indices matching the provided sources.
- Return valid markdown only.

Structure:

# Executive Comparison

Provide a high-level summary of the comparison and major conclusions.

## Market Position

Analyze the market standing, market share, target audience, and positioning of each company.

## Strengths & Advantages

Compare the core strengths, advantages, and unique competencies of each company.

## Weaknesses & Vulnerabilities

Identify and compare the main weaknesses, gaps, or limitations of each company.

## Financial Performance & Business Models

Detail and compare the pricing models, cost structures, revenue streams, or overall business viability.

## Strategic Risks

Compare the strategic risks, threats, regulatory challenges, and competitive vulnerabilities for each.

## Future Outlook

Provide a projection of future trends, growth prospects, and strategic trajectories for both companies.
"""
    elif category == "FINANCIAL_ANALYSIS":
        prompt = f"""You are a senior financial research analyst.

Research Topic:
{query}

Sources:

{formatted_results}

Do not summarize sources individually.

Instead:
- Synthesize information across all sources to analyze the financial performance, stock trends, or market situation
- Explain why findings matter, identify patterns, and implications
- Draw conclusions from evidence and provide expert analysis

Every section should contain reasoning, not just facts. Focus on insight generation, not summarization.

Requirements:
- Target length: 600-800 words
- Use information from all available sources
- Mention when sources agree and disagreements when they exist
- Avoid repeating information and use concise analytical writing
- Support findings with evidence from sources using inline citation markers (e.g., `[1]`, `[2]`, `[1][3]`).
- You MUST append citation markers to every factual statement or claim. Example: "Tesla stock rose by 5% following the earnings announcement.[1]"
- Do NOT fabricate citations. Only use indices matching the provided sources.
- Return valid markdown only.

Structure:

# Executive Summary

Provide a high-level overview of the financial health, stock performance, or market situation.

## Financial Performance Metrics

Analyze key financial indicators like revenue growth, profitability, EBITDA, cash flow, and debt levels.

## Market Valuation & Stock Trends

Examine stock price trends, P/E ratio, market cap, and valuation relative to industry peers.

## Growth Drivers & Opportunities

Discuss key growth catalysts, market expansions, and product innovations driving performance.

## Key Risks & Vulnerabilities

Identify macroeconomic risks, rising competition, operational challenges, or regulatory headwinds.

## Future Projections & Recommendations

Detail analyst forecast consensus, target price ranges, and financial outlook for the coming quarters.
"""
    elif category == "SPORTS_RIVALRY":
        prompt = f"""You are a senior sports research analyst.

Research Topic:
{query}

Sources:

{formatted_results}

Do not summarize sources individually.

Instead:
- Synthesize information across all sources to compare the competitors, drivers, athletes, teams, or sports concepts in the topic
- Compare their stats, playstyles, achievements, strengths, and weaknesses
- Include at least one side-by-side comparison table in markdown format comparing key stats/achievements/milestones
- Explain why findings matter, identify patterns, and implications
- Draw conclusions from evidence and provide expert analysis

Every section should contain reasoning, not just facts. Focus on insight generation, not summarization.

Requirements:
- Target length: 600-800 words
- Use information from all available sources
- Mention when sources agree and disagreements when they exist
- Avoid repeating information and use concise analytical writing
- Support findings with evidence from sources using inline citation markers (e.g., `[1]`, `[2]`, `[1][3]`).
- You MUST append citation markers to every factual statement or claim. Example: "Hamilton has won 7 world titles, while Verstappen has won 3.[1]"
- Do NOT fabricate citations. Only use indices matching the provided sources.
- Return valid markdown only.

Structure:

# Executive Summary

Summarize the context of the comparison and the legendary debate/rivalry.

## Career Achievements & Statistics

Compare key career statistics, titles, trophies, individual awards, and milestones.

## Playstyle & Tactical Analysis

Examine tactical positions, physical strengths, unique playing styles, and team dynamics.

## Key Strengths & Leadership

Identify the core athletic or leadership strengths that define each competitor.

## Weaknesses & Career Gaps

Detail any gaps, criticisms, or career limitations.

## Cultural & Commercial Impact

Examine sponsorships, global popularity, and impact outside the sport.

## Legacy & Conclusion

Conclude on their historical standing and impact on the game.
"""
    elif category == "CHARACTER_ANALYSIS":
        prompt = f"""You are a senior narrative research analyst.

Research Topic:
{query}

Sources:

{formatted_results}

Do not summarize sources individually.

Instead:
- Synthesize information across all sources to analyze the character/individual/abilities/factions in the topic
- Detail their background, lore, personality, abilities, role, and cultural impact
- Explain why findings matter, identify patterns, and implications
- Draw conclusions from evidence and provide expert analysis

Every section should contain reasoning, not just facts. Focus on insight generation, not summarization.

Requirements:
- Target length: 600-800 words
- Use information from all available sources
- Mention when sources agree and disagreements when they exist
- Avoid repeating information and use concise analytical writing
- Support findings with evidence from sources using inline citation markers (e.g., `[1]`, `[2]`, `[1][3]`).
- You MUST append citation markers to every factual statement or claim. Example: "Optimus Prime is the leader of the Autobots.[1]"
- Do NOT fabricate citations. Only use indices matching the provided sources.
- Return valid markdown only.

Structure:

# Executive Character Summary

Overview of the character's origins, identity, and narrative role.

## Biography & Lore

Examine their background, origin story, key narrative events, and relationship networks.

## Personality & Psychology

Analyze their personality traits, motivations, beliefs, flaws, and character arc.

## Powers & Key Abilities

Detail their unique abilities, skills, equipment, weapons, or special techniques.

## Narrative Significance & Themes

Analyze how the character represents key themes, struggles, or motifs in their story.

## Cultural Impact & Legacy

Discuss their popularity, critical reception, and legacy in media and pop culture.
"""
    elif category == "FICTIONAL_ARC":
        prompt = f"""You are a senior literary and narrative research analyst.

Research Topic:
{query}

Sources:

{formatted_results}

Do not summarize sources individually.

Instead:
- Synthesize information across all sources to analyze the story arc, saga, or fictional events in the topic
- Detail its plot points, themes, character development, consequences, and reception
- Explain why findings matter, identify patterns, and implications
- Draw conclusions from evidence and provide expert analysis

Every section should contain reasoning, not just facts. Focus on insight generation, not summarization.

Requirements:
- Target length: 600-800 words
- Use information from all available sources
- Mention when sources agree and disagreements when they exist
- Avoid repeating information and use concise analytical writing
- Support findings with evidence from sources using inline citation markers (e.g., `[1]`, `[2]`, `[1][3]`).
- You MUST append citation markers to every factual statement or claim. Example: "The Marineford Arc concludes with the death of Portgas D. Ace.[1]"
- Do NOT fabricate citations. Only use indices matching the provided sources.
- Return valid markdown only.

Structure:

# Executive Summary

Introduce the fictional arc, its place in the overall story, and its general significance.

## Plot Summary & Key Events

Provide a summary of major battles, turning points, plot twists, and key event sequences.

## Themes & Motifs

Examine the central themes, moral questions, and symbolisms explored in the arc.

## Character Development

Detail the emotional, physical, or status changes undergone by key characters.

## Narrative Consequences & Fallout

Analyze how this arc changes the balance of power and sets up future storylines.

## Reception & Cultural Impact

Discuss fan ratings, critical reception, animation quality (if applicable), and cultural footprint.
"""
    elif category == "TECHNOLOGY_RESEARCH":
        prompt = f"""You are a senior technology analyst.

Research Topic:
{query}

Sources:

{formatted_results}

Do not summarize sources individually.

Instead:
- Synthesize information across all sources to analyze the technology, framework, architecture, or algorithm in the topic
- Detail its architecture, use cases, advantages, limitations, and future trends
- Explain why findings matter, identify patterns, and implications
- Draw conclusions from evidence and provide expert analysis

Every section should contain reasoning, not just facts. Focus on insight generation, not summarization.

Requirements:
- Target length: 600-800 words
- Use information from all available sources
- Mention when sources agree and disagreements when they exist
- Avoid repeating information and use concise analytical writing
- Support findings with evidence from sources using inline citation markers (e.g., `[1]`, `[2]`, `[1][3]`).
- You MUST append citation markers to every factual statement or claim. Example: "Quantum computers utilize qubits to perform complex calculations.[1]"
- Do NOT fabricate citations. Only use indices matching the provided sources.
- Return valid markdown only.

Structure:

# Executive Summary

High-level summary of the technology, its primary purpose, and its significance.

## Core Concepts & Architecture

Detail the underlying technical architecture, protocols, standards, or structural design.

## Main Use Cases & Applications

Explore where and how the technology is deployed in real-world scenarios.

## Technical Advantages & Strengths

Analyze performance, efficiency, scalability, and other strengths.

## Technical Limitations & Gaps

Examine bottlenecks, security risks, complexity, or areas needing improvement.

## Future Trends & Development

Outline the roadmap, future research directions, or emerging standards.
"""
    elif category == "PRODUCT_COMPARISON":
        prompt = f"""You are a senior product research analyst.

Research Topic:
{query}

Sources:

{formatted_results}

Do not summarize sources individually.

Instead:
- Synthesize information across all sources to compare the consumer products, gadgets, hardware, apps, or models in the topic
- Compare their features, specifications, usability, strengths, and weaknesses
- Include at least one side-by-side comparison table in markdown format comparing key features
- Explain why findings matter, identify patterns, and implications
- Draw conclusions from evidence and provide expert analysis

Every section should contain reasoning, not just facts. Focus on insight generation, not summarization.

Requirements:
- Target length: 600-800 words
- Use information from all available sources
- Mention when sources agree and disagreements when they exist
- Avoid repeating information and use concise analytical writing
- Support findings with evidence from sources using inline citation markers (e.g., `[1]`, `[2]`, `[1][3]`).
- You MUST append citation markers to every factual statement or claim. Example: "Product A has a battery life of 15 hours, while Product B lasts 12 hours.[1]"
- Do NOT fabricate citations. Only use indices matching the provided sources.
- Return valid markdown only.

Structure:

# Executive Comparison

Provide a high-level comparison summary, target audiences, and key use cases.

## Feature & Specification Analysis

Detailed comparison of technical specifications, capabilities, and features.

## Pricing & Value Proposition

Analyze cost plans, licensing, tiered pricing, and overall value return.

## Pros & Cons

Clear bulleted pros and cons lists for each compared product.

## Technology & Usability

Compare technical architecture, performance, and user interface/experience.

## Verdict & Recommendation

Final summary evaluation recommending which product suits which user segment.
"""
    else:
        prompt = f"""You are a senior general research analyst.

Research Topic:
{query}

Sources:

{formatted_results}

Do not summarize sources individually.

Instead:
- Synthesize information across all sources
- Explain why findings matter, identify patterns, and implications
- Draw conclusions from evidence and provide expert analysis

Every section should contain reasoning, not just facts. Focus on insight generation, not summarization.

IMPORTANT PRIORITY INSTRUCTION:
The sources provided above are ordered by authority and priority (Priority 1 sources like Academic/Government appear first, Priority 5 sources like Community forums appear last). You MUST give higher priority sources significantly more weight and influence when synthesizing findings and drawing conclusions.

Requirements:
- Target length: 600-800 words
- Use information from all available sources
- Mention when sources agree and disagreements when they exist
- Avoid repeating information and use concise analytical writing
- Support findings with evidence from sources using inline citation markers (e.g., `[1]`, `[2]`, `[1][3]`).
- You MUST append citation markers to every factual statement or claim. Example: "ARPANET adopted TCP/IP in 1983.[1]"
- Do NOT fabricate citations. Only use indices matching the provided sources.
- Return valid markdown only.

Structure:

# Executive Summary

Brief overview of the topic and major conclusions.

## Key Findings

Summarize the most important findings from the sources.

## Emerging Trends

Identify patterns, innovations, and future developments.

## Conflicting Opinions

Mention disagreements or write "No significant conflicts found."

## Key Takeaways

Suggest next steps, practical implications, or areas for further research based on the topic.

## Conclusion

Provide a closing summary.
"""

    import time
    import sys

    providers = [
        ("Gemini", gemini_generate, "gemini-2.5-flash"),
        ("Groq", groq_generate, "llama-3.3-70b-versatile"),
        ("Gemini", gemini_generate, "gemini-1.5-pro"),
        ("Groq", groq_generate, "llama-3.1-8b-instant")
    ]
    
    backoff = [2, 5, 10]
    
    for i, (provider_name, func, model) in enumerate(providers):
        for attempt in range(4): # 1 initial + 3 retries
            start_time = time.time()
            try:
                print(f"DIAGNOSTIC: Provider selected: {provider_name}")
                if attempt > 0:
                    print(f"DIAGNOSTIC: Retry count: {attempt}")
                result = func(prompt, model=model)
                duration = time.time() - start_time
                print(f"Provider {provider_name} ({model}) succeeded on attempt {attempt+1}. Duration: {duration:.2f}s")
                return result
            except Exception as e:
                duration = time.time() - start_time
                error_msg = str(e).lower()
                is_transient = any(x in error_msg for x in ["429", "500", "503", "timeout", "unavailable", "rate limit", "temporarily", "server error"])
                
                print(f"FAILED: Provider={provider_name}, Model={model}, Reason={e}, Status=Error, RetryCount={attempt}, Duration={duration:.2f}s", file=sys.stderr)
                
                if is_transient and attempt < 3:
                    sleep_time = backoff[attempt]
                    print(f"Retrying {provider_name} ({model}) in {sleep_time}s...", file=sys.stderr)
                    time.sleep(sleep_time)
                else:
                    if i < len(providers) - 1:
                        next_provider = providers[i+1]
                        print(f"DIAGNOSTIC: Fallback provider selected: {next_provider[0]}")
                        print(f"Selected fallback provider: {next_provider[0]} ({next_provider[2]})", file=sys.stderr)
                    else:
                        print("CRITICAL: All research providers failed.", file=sys.stderr)
                        return """# Research Report

Research generation could not be completed at this time.

Please try again shortly."""
                    break # Break inner retry loop to move to next provider