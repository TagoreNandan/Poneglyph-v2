---
name: Poneglyph Warm Journal
colors:
  surface: '#fcf9f4'
  surface-dim: '#dcdad5'
  surface-bright: '#fcf9f4'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f6f3ee'
  surface-container: '#f0ede9'
  surface-container-high: '#ebe8e3'
  surface-container-highest: '#e5e2dd'
  on-surface: '#1c1c19'
  on-surface-variant: '#4a4455'
  inverse-surface: '#31302d'
  inverse-on-surface: '#f3f0eb'
  outline: '#7b7487'
  outline-variant: '#ccc3d8'
  surface-tint: '#732ee4'
  primary: '#630ed4'
  on-primary: '#ffffff'
  primary-container: '#7c3aed'
  on-primary-container: '#ede0ff'
  inverse-primary: '#d2bbff'
  secondary: '#5e5e5e'
  on-secondary: '#ffffff'
  secondary-container: '#e2e2e2'
  on-secondary-container: '#646464'
  tertiary: '#7d3d00'
  on-tertiary: '#ffffff'
  tertiary-container: '#a15100'
  on-tertiary-container: '#ffe0cd'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#eaddff'
  primary-fixed-dim: '#d2bbff'
  on-primary-fixed: '#25005a'
  on-primary-fixed-variant: '#5a00c6'
  secondary-fixed: '#e2e2e2'
  secondary-fixed-dim: '#c6c6c6'
  on-secondary-fixed: '#1b1b1b'
  on-secondary-fixed-variant: '#474747'
  tertiary-fixed: '#ffdcc6'
  tertiary-fixed-dim: '#ffb784'
  on-tertiary-fixed: '#301400'
  on-tertiary-fixed-variant: '#713700'
  background: '#fcf9f4'
  on-background: '#1c1c19'
  surface-variant: '#e5e2dd'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 64px
    fontWeight: '800'
    lineHeight: '1.1'
    letterSpacing: -0.04em
  display-lg-mobile:
    fontFamily: Inter
    fontSize: 40px
    fontWeight: '800'
    lineHeight: '1.1'
    letterSpacing: -0.03em
  headline-xl:
    fontFamily: Inter
    fontSize: 36px
    fontWeight: '700'
    lineHeight: '1.2'
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Inter
    fontSize: 28px
    fontWeight: '700'
    lineHeight: '1.3'
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: '1.7'
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.6'
  label-caps:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '700'
    lineHeight: '1.5'
    letterSpacing: 0.1em
  citation:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '500'
    lineHeight: '1.5'
spacing:
  unit: 4px
  container-max: 1120px
  gutter: 32px
  margin-desktop: 64px
  margin-mobile: 20px
  stack-sm: 12px
  stack-md: 24px
  stack-lg: 48px
  stack-xl: 80px
---

## Brand & Style
The design system embodies the authority of a premium research journal mixed with a contemporary, high-contrast editorial aesthetic. It is designed for deep focus, long-form reading, and intellectual rigor. The personality is confident and serious, avoiding the sterile "sameness" of modern SaaS in favor of a bold, intentional presence.

The style is a hybrid of **Minimalism** and **High-Contrast Editorial**. It leverages vast amounts of whitespace and a limited, high-impact color palette to direct attention. It prioritizes clarity of information and the hierarchy of thought over decorative elements. The emotional response should be one of "Warm Intellectualism"—approachable due to its tonal palette, but imposing through its precise, aggressive typography.

## Colors
The color strategy is binary and intentional. The foundation is a warm, parchment-like off-white (`#FAF7F2`), which reduces eye strain during long reading sessions compared to pure white. 

- **Primary (Electric Violet):** Reserved exclusively for active states, citations, highlights, and primary calls to action. It serves as the "ink of record" for interactive elements.
- **Secondary/Neutral (Black):** Used for all structural text and iconography to ensure maximum legibility and an authoritative, printed-page feel.
- **Background (Warm Paper):** Provides a premium, tactile quality that softens the aggressive black typography.

## Typography
This design system utilizes **Inter** across all roles, but differentiates through extreme variations in scale and weight. 

- **Headlines:** Set with tight tracking and heavy weights (Bold/ExtraBold) to create "blocks" of text that feel architectural.
- **Body:** Set with generous line heights (1.6 - 1.7) to ensure a comfortable reading rhythm reminiscent of high-end physical journals.
- **Labels:** Use uppercase and increased letter-spacing to provide a clear distinction from narrative content.
- **Citations:** Specifically styled to be distinct, utilizing the Primary Electric Violet and italics to signal secondary but essential information.

## Layout & Spacing
The layout follows a **Fixed Grid** philosophy for desktop to maintain the narrow measure ideal for readability, while transitioning to a fluid model for mobile.

- **Desktop:** 12-column grid with a maximum content width of 1120px. Centered.
- **Vertical Rhythm:** A strict 4px baseline grid is used. Spacing between sections is aggressive (`stack-xl`) to allow the content to breathe.
- **Asymmetry:** Occasional use of "outdent" elements (like pull-quotes or citations) that sit in the margins to break the vertical flow and add editorial flair.
- **Mobile:** Content reflows to a single column with 20px margins, maintaining the bold typographic scale for headlines but reducing `display-lg` sizes for accessibility.

## Elevation & Depth
Depth is created through **Tonal Layers** and **Low-Contrast Outlines** rather than traditional shadows. This keeps the interface feeling flat, like paper.

- **Surfaces:** Use subtle shifts in background color (e.g., a slightly darker cream) to define sidebars or metadata panels.
- **Outlines:** Use thin (1px) solid black or very dark grey borders to define input areas or card boundaries.
- **Active State:** Depth is signaled by a solid fill of the Primary color rather than a shadow, reinforcing the bold, graphic nature of the design.

## Shapes
The shape language is **Sharp (0)**. Everything from buttons to cards to input fields uses 90-degree angles. This reinforces the "Journal" aesthetic, echoing the sharp corners of a printed page or a hardcover book. It conveys precision, discipline, and a lack of ornamental fluff.

## Components
- **Buttons:** Solid black fill with white text for primary actions. Outlined (1px black) for secondary. No rounded corners. High-impact hover state uses the Electric Violet fill.
- **Input Fields:** Bottom-border only (2px black) or full rectangular outline (1px black). Sharp corners. Labels are always `label-caps`.
- **Chips/Tags:** Small, sharp-edged rectangles. Neutral tags use a light grey stroke; active/selected tags use a solid Electric Violet fill with white text.
- **Cards:** No shadows. Defined by a 1px solid black border or a subtle tonal shift in background. Headlines within cards should be `headline-lg`.
- **Lists:** Clean, bulletless lists for table of contents or references. Use thin horizontal rules (1px) to separate high-density data.
- **Citations:** Inline links or block-quotes highlighted with an Electric Violet left-border (4px width).
- **Progress Markers:** For long-form reading, a thin Electric Violet line at the top of the viewport indicates scroll progress.