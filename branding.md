# mitKI.ai — Branding Guidelines

> **Version:** 2.0  
> **Last Updated:** 2026-02-13  
> **Purpose:** Single source of truth for all visual, verbal, and strategic brand elements

---

## 0. Brand Essence

### Brand Name
**mitKI.ai**

### Positioning Statement
> **Brückenbauer zwischen Geschäftsführung & IT**  
> Pragmatismus statt Buzzwords · KI als Change-Treiber, nicht als Tool · Fokus auf Ergebnis + Umsetzung

### Core Promise
```
mitKI einfacher · mitKI schneller · gemeinsam mitKI
```

### Brand Voice
- **Klar & direkt** – keine Technik-Überheblichkeit
- **Praxisnah & storygetrieben** – echte Cases, keine Theorie
- **Humorvoll-präzise** – nie flapsig, immer respektvoll
- **B2B mit Menschlichkeit** – Business-Ton, aber warmherzig

### Target Audiences

| Persona | Pain Points | Value Prop |
|---------|-------------|------------|
| **GF 50+ (KMU)** | "Keine Ahnung, wie ich KI-Ideen dem IT-Lead erkläre" | Übersetzer + klare Prozesse |
| **IT-Leads** | "GF hat unrealistische KI-Erwartungen" | Strukturierung + Priorisierung |
| **Solopreneure** | "Zu viel Overhead, zu wenig Zeit" | Quick Wins + Automation |
| **Dev Teams** | "Wann nutzen wir KI sinnvoll?" | Best Practices + Pair Programming |

---

## 1. Visual Identity

### Color System

```css
/* Primary Palette */
--brand-orange:      #F97316;  /* Energy, Action, CTAs */
--brand-creme:       #F8E3C7;  /* Warm contrast on dark */
--brand-navy-dark:   #0A1A3A;  /* Primary background */

/* Secondary/Accent */
--brand-deep-blue:   #001434;  /* Depth layers */
--brand-amber-glow:  #FFA726;  /* Subtle highlights */
--brand-graphite:    #2C2C2E;  /* UI elements */

/* Neutrals */
--text-primary:      #FFFFFF;
--text-secondary:    #E5E7EB;
--text-muted:        #9CA3AF;
```

**Usage Rules:**
- **Orange** (`#F97316`): CTAs, Icons, Highlights (max 10% of screen)
- **Creme** (`#F8E3C7`): Text on dark backgrounds, section dividers
- **Navy** (`#0A1A3A`): Primary background (80%+ of surface)
- **Never** mix more than 3 colors in a single component

### Typography

#### Font Stack
```css
/* Primary */
font-family: 'Inter', 'Montserrat', -apple-system, sans-serif;

/* Fallback */
font-family: Arial, Helvetica, sans-serif;
```

#### Type Scale

| Element | Size | Weight | Line Height |
|---------|------|--------|-------------|
| **H1** (Hero) | 3.5rem (56px) | 800 | 1.1 |
| **H2** (Section) | 2.25rem (36px) | 700 | 1.2 |
| **H3** (Component) | 1.5rem (24px) | 600 | 1.3 |
| **Body** | 1rem (16px) | 400 | 1.6 |
| **Small** | 0.875rem (14px) | 500 | 1.5 |

**Never** use font sizes below 14px for body text.

### Logo System

**Primary Logo:**  
`mitKI_logo_horizontal.svg` (Hammer + Mobile + Circuit)

**Variants:**
- `logo_square.svg` – Social media avatars
- `logo_white.svg` – Dark backgrounds
- `logo_icon_only.svg` – Favicon, small spaces

**Clear Space:**  
Minimum 20px margin on all sides

**Minimum Size:**  
- Horizontal: 120px width
- Square: 40x40px

---

## 2. Visual Language

### Photography Style
- **Background:** Dark, matte surfaces (wood, concrete, tech setups)
- **Lighting:** Low-key with orange/warm accent lights
- **Focus:** Sharp foreground, subtle blur on background
- **Mood:** Calm, focused, professional

### Iconography
- **Style:** Line icons, 2px stroke weight
- **Color:** Orange (`#F97316`) on dark backgrounds
- **Metaphors:** Hammer (solutions), Tablet (digital), Bridge (connection)

### Video Thumbnails (YouTube)

**Template Structure:**
```
[Dark Navy Background (#0A1A3A)]
  ├─ Portrait/Cartoon (left)
  ├─ Bold Text (right, max 3 words)
  ├─ Orange Glow Effect (subtle)
  └─ Logo (bottom right corner)
```

**Text Rules:**
- **Max 3 words**, all caps or title case
- Font: Inter Black (900)
- Examples: "PROZESS → KLAR!" | "DEV IN 5 MIN"

---

## 3. Content & Messaging

### Headline Formulas

```
1. [Ergebnis] in [Zeit] – mit KI
   → "Dev-Setup in 5 Minuten – mit KI"

2. Warum [Problem] scheitern – und was du brauchst
   → "Warum KI-Projekte scheitern – und was du wirklich brauchst"

3. [Zielgruppe] vs [Zielgruppe]: Die Wahrheit über [Topic]
   → "GF vs IT: Die Wahrheit über KI-Einführung"

4. [X Schritte] zu [Ergebnis]
   → "3 Schritte zum ersten KI-Agent"
```

### Hook Principles
1. **Problem first** – dann Lösung
2. **Spezifisch** – "3 Schritte" statt "ein paar Tipps"
3. **Outcome-driven** – was hat der User am Ende?
4. **Clear CTA** – "Was du jetzt tun musst"

### CTA Lexikon

| Context | Primary CTA | Secondary CTA |
|---------|-------------|---------------|
| **Video** | "Jetzt lernen" | "Code kopieren" |
| **Post** | "4-Wochen-Plan holen" | "Kommentieren" |
| **Landing** | "Termin buchen" | "Playlist ansehen" |
| **Livestream** | "Jetzt dabei sein" | "Erinnerung setzen" |

---

## 4. Web Components

### Header
```css
.header-main {
  background: var(--brand-navy-dark);
  padding: 1.5rem 2rem;
  border-bottom: 2px solid var(--brand-orange);
}

.logo {
  height: 40px;
}

.nav-link {
  color: var(--text-secondary);
  font-weight: 500;
  transition: color 0.2s;
}

.nav-link:hover {
  color: var(--brand-orange);
}
```

### CTA Buttons
```css
.btn-primary {
  background: var(--brand-orange);
  color: var(--brand-navy-dark);
  font-weight: 700;
  padding: 0.875rem 2rem;
  border-radius: 8px;
  transition: transform 0.2s;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 16px rgba(249, 115, 22, 0.3);
}
```

---

## 5. Social Media System

### YouTube

**Thumbnail:**
- 1280x720px
- Dark navy background
- Portrait left, text right
- Orange glow border (optional)

**Title Format:**
```
[Hook] | [Detail] | [Series/Topic]
→ "KI ist Change, kein Tool | Prozesse vor Prompts | mitKI Basics"
```

### LinkedIn

**Post Structure:**
```
[Hook/Question]

[Problem expanded]

[Solution/Framework in 3-5 bullets]

[CTA]

---
#KI #Digitalisierung #KMU
```

**Image:**
- 1200x630px
- Same color system as brand
- Max 2 lines of text

### Shorts/Reels

**Specs:**
- 1080x1920px (9:16)
- Permanent subtitles (bottom third)
- Orange border (2-4px) for branding
- Hook in first 2 seconds

---

## 6. AI Prompt Templates

### For Web Design
```
You are building a landing page for "mitKI.ai" with these brand guidelines:

COLORS:
- Primary: #F97316 (orange)
- Background: #0A1A3A (navy-dark)
- Text: #F8E3C7 (creme)

FONTS:
- Use Inter or Montserrat
- Headlines: 700-800 weight
- Body: 400 weight

TONE:
- Pragmatic, business-oriented
- Outcome-focused, not buzzword-heavy

MESSAGING:
- "mitKI einfacher · mitKI schneller · gemeinsam mitKI"
- Focus on connection between business leaders and IT teams
- Emphasize: "Prozesse vor Prompts" | "KI ist Change, kein Tool"

Create a hero section with:
1. Bold headline (max 6 words)
2. Orange CTA button
3. Supporting visual (dark tech background)
```

### For Thumbnail Text
```
Generate a YouTube thumbnail text following mitKI.ai brand:

RULES:
- Max 3 words, all caps
- Outcome-driven (what viewer gets)
- Use action verbs or results

STYLE:
- Bold, direct, punchy
- Examples: "PROZESS → KLAR!" | "DEV IN 5 MIN"

Topic: [your video topic here]
```

### For Social Post
```
Write a LinkedIn post for mitKI.ai following these guidelines:

AUDIENCE: Business leaders (50+) or IT leads
TONE: Professional but warm, pragmatic, story-driven
LENGTH: 150-250 words

STRUCTURE:
1. Hook (question or bold statement)
2. Problem context
3. Solution framework (3-5 bullets)
4. CTA

BRAND VOICE:
- No buzzwords without substance
- Focus on outcomes and processes
- "Brückenbauer zwischen GF & IT"

Topic: [your topic here]
```

---

## 7. Do's & Don'ts

### ✅ Do
- Use high contrast for readability
- Keep headlines under 8 words
- Reserve orange for emphasis only
- Tell authentic stories with real outcomes
- Use consistent spacing (8px grid system)

### ❌ Don't
- Overcrowd thumbnails (max 3 words)
- Use multiple accent colors
- Rely on buzzwords without explanation
- Use font sizes below 14px
- Break the 60-30-10 color rule

---

## 8. File Naming Conventions

```
Components:
- btn-primary.jsx
- header-nav.jsx
- section-hero.jsx

Styles:
- brand-colors.css
- typography-scale.css
- components-buttons.css

Assets:
- mitKI_logo_horizontal.svg
- thumbnail_template_dark.psd
- icon_hammer_orange.svg
```

---

## 9. Design Tokens (JSON Export)

```json
{
  "colors": {
    "primary": {
      "orange": "#F97316",
      "creme": "#F8E3C7",
      "navy": "#0A1A3A"
    },
    "accent": {
      "amber": "#FFA726",
      "graphite": "#2C2C2E"
    }
  },
  "spacing": {
    "xs": "4px",
    "sm": "8px",
    "md": "16px",
    "lg": "24px",
    "xl": "32px",
    "2xl": "48px"
  },
  "typography": {
    "fontFamily": {
      "primary": "'Inter', sans-serif",
      "fallback": "Arial, Helvetica, sans-serif"
    },
    "fontSize": {
      "h1": "3.5rem",
      "h2": "2.25rem",
      "h3": "1.5rem",
      "body": "1rem",
      "small": "0.875rem"
    },
    "fontWeight": {
      "black": 900,
      "bold": 700,
      "semibold": 600,
      "regular": 400
    }
  }
}
```

---

## 10. Next Steps

**To implement this branding:**

1. **Web:** Use design tokens to build Tailwind config or CSS variables
2. **Video:** Create Premiere/DaVinci template with thumbnail specs
3. **Social:** Build Figma template for post graphics
4. **Code:** Import this file into AI prompts for consistent output

**Questions?** Contact: [eduard@mitki.ai]

---

**🚀 Ready to use with:** Claude Code · Codex · Midjourney · Figma · Tailwind
