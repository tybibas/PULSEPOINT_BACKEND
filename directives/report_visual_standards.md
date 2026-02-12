# Directive: Strategic Report Visual Standards
> Standard: DOE-03 (Visual Authority and Data Storytelling)

## Objective
To define the immutable "Gold Standard" for the visual and stylistic presentation of the Strategic Diagnostic Report. The output must bypass "marketing filters" and register immediately as an "Institute-Grade" or "Consulting-Grade" document (e.g., McKinsey, Bain, Bridgewater).

## Philosophy
**"The Medium is the Message."** 
If the report looks like a marketing brochure, the data will be treated as noise. If it looks like a Board Room Diagnostic, the data will be treated as signal. We prioritize **Density**, **Authority**, and **Precision** over decoration.

---

## 1. Visual Identity ("Sky Blue Clean")
Professional B2B aesthetic using a "Two-Column" layout and a White/Navy palette.

### Layout
-   **Structure**: 2-Column Grid.
-   **Sidebar (Left, 30%)**: Executive Synthesis, Key Takeaways.
-   **Main Content (Right, 70%)**: Deep Dive Analysis, Charts, Data tables.

### Color Palette
-   **Background**: `White (#FFFFFF)`.
-   **Primary Text**: `Dark Navy (#001F3F)`.
-   **Secondary Text**: `Slate Grey (#555555)`.
-   **Accent**: `Sky Blue (#00A4CC)` or `Clean Blue (#3498DB)`.
-   **Headers**: `Navy (#001F3F)` background with `White` text (for tables).

### Typography
-   **Headlines**: Clean Sans-Serif (Arial/Helvetica).
-   **Body**: Clean Sans-Serif.
-   **Big Numbers**: 48pt Bold (for Valuation Gaps).
-   **Styling**: Regular, Medium Grey (#555555), 11pt-12pt.

---

## 2. The "Action Title" Protocol
**Rule**: Never use generic labels. Every header must be a complete sentence that summarizes the insight.

| ❌ Generic (Forbidden) | ✅ Action Title (Required) |
| :--- | :--- |
| "Financial Overview" | "Operational efficiency has stalled despite revenue growth." |
| "Sentiment Analysis" | "Investor confidence is eroding due to untreated margin concerns." |
| "Valuation" | "The market is ignoring your $400M growth initiative." |
| "Competitor Analysis" | "Competitors are successfully framing your silence as weakness." |

---

## 3. Data Visualization Standards
We use specific chart types to communicate specific "Psychological States" of the market.

### Narrative Gaps (Diverging Bar Charts)
-   **Purpose**: To show the conflict between two viewpoints (e.g., Management vs. Market, Price vs. Value).
-   **Visual**: Center line at 0. Positive bars (Green) to the right, Negative bars (Red) to the left.
-   **Application**: "Sanitization Score" (Sell-Side vs. Glassdoor).

### Sentiment Velocity (Waterfall Charts)
-   **Purpose**: To show the *change* or *erosion* of trust over time (e.g., from Prepared Remarks to Q&A).
-   **Visual**: Starting bar (Prepared Remarks), Step-down bars (Red "uncertainty" drops), Ending bar (Q&A).
-   **Application**: "Credibility Gap" analysis.

### Color Palette ("The Signal Palette")
-   Avoid "Marketing Blue". Use "Financial Slate".
-   **Positive/Safe**: Emerald Green (#2ECC71).
-   **Negative/Risk**: Crimson Red (#E74C3C).
-   **Neutral/Context**: Slate Grey (#95A5A6).

---

## 4. Output Specification
The Execution Layer must render the final artifact to these technical specs.

-   **Format**: High-Fidelity PDF (Vector-based). **HTML-only outputs are unacceptable deliverables.**
-   **Page Size**: A4 or US Letter (Landscape or Portrait depending on module).
-   **Rendering**: generated programmatically via CSS-to-PDF engine (e.g., WeasyPrint) to ensure pixel-perfect consistency.
-   **Metadata**: Reports must be stamped with a "Generation Date" and "Data Integrity Hash" in the footer to reinforce validity.
