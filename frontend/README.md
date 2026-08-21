# Privacy Guardian

You are a senior product designer, UX architect, and frontend engineer specializing in premium browser extensions.

Build the frontend interface for a Chromium Manifest V3 browser extension called ConsentShield.

ConsentShield is a privacy-first browser extension that detects cookie banners, analyzes cookie and privacy-policy evidence, explains tracking risks, recommends a safer consent choice, and applies an approved action only after the user understands and confirms it.

This is an extension popup, not a website. Design the main experience for a compact browser popup approximately 380px wide and no more than 560px high. It must feel like a polished premium security product, not a generic dashboard.

==================================================

PRODUCT PRINCIPLE

==================================================

The core product flow is:

Detect → Analyze → Recommend → Confirm → Execute → Report

The interface must clearly distinguish:

1. What ConsentShield detected.

2. What ConsentShield recommends.

3. What action will happen.

4. Whether user confirmation is required.

5. Whether the action succeeded.

Do not hide or blur this distinction.

The default mode is Manual. ConsentShield must never silently accept cookies or execute a consent action unless automatic protection was explicitly enabled by the user.

==================================================

VISUAL DIRECTION

==================================================

Create a premium editorial-security aesthetic inspired by high-end privacy tools, financial security apps, and refined productivity software.

Do NOT use blue or purple anywhere in the interface.

Do NOT use:

- Bright blue.

- Navy blue.

- Purple.

- Violet.

- Neon gradients.

- Generic SaaS blue dashboards.

- Excessive glassmorphism.

- Heavy shadows.

- Cartoon illustrations.

- Overly rounded childish cards.

- Emoji as icons.

- Loud rainbow status colors.

Use this color system:

- Background: warm ivory, #F7F5F0.

- Primary text: charcoal, #20201E.

- Secondary text: stone gray, #77736B.

- Elevated surface: soft white, #FFFEFA.

- Border: warm gray, #E3DED4.

- Primary accent: dark forest green, #183C32.

- Secondary accent: muted sage, #A7B7A3.

- Positive status: deep green, #2F6B4F.

- Warning status: burnt amber, #B16A32.

- Critical status: dark terracotta, #9C4036.

- Neutral status: warm gray, #8C887F.

Use color sparingly. Status colors must be paired with text labels and icons, never color alone.

The overall feeling should be:

- Calm.

- Intelligent.

- Trustworthy.

- Quietly technical.

- Privacy-conscious.

- Premium.

- Precise.

- Human-controlled.

==================================================

TYPOGRAPHY

==================================================

Use a refined sans-serif interface font such as Inter, Geist, or Manrope.

Typography rules:

- Product name: bold but compact.

- Page title: 20–22px.

- Section title: 13–14px semibold.

- Body text: 13px.

- Metadata: 11–12px.

- Evidence excerpt: 12px with comfortable line height.

- Use sentence case, not all caps.

- Avoid excessive font-weight variation.

- Use tabular numerals for confidence percentages and timestamps.

Use generous line height and strong hierarchy. Avoid cramped text even inside the popup.

==================================================

LAYOUT SYSTEM

==================================================

Use a compact 8px spacing system.

Recommended popup:

- Width: 380px.

- Maximum height: 560px.

- Border radius: 18px for the main shell.

- Card radius: 12px.

- Button radius: 10px.

- Thin 1px warm-gray borders.

- Minimal shadow: soft, low-opacity, warm-tinted.

- Avoid excessive nested cards.

Use a single-column layout with clear sections:

1. Header.

2. Site context.

3. Scan or analysis state.

4. Risk overview.

5. Category findings.

6. Protection recommendation.

7. Main action.

8. Privacy and settings footer.

The popup should scroll vertically if needed, but the primary action must remain easy to find.

==================================================

BRAND HEADER

==================================================

Create a compact header:

Left:

- Minimal shield-and-cookie mark.

- ConsentShield wordmark.

- No complicated illustration.

Right:

- Small privacy mode pill.

- Settings icon.

- Optional connection/status indicator.

Brand copy:

- Name: ConsentShield.

- Descriptor: “Privacy protection for the web.”

The logo should use forest green, charcoal, ivory, and muted sage only.

==================================================

PRIMARY SCREEN: SITE ANALYSIS

==================================================

Create the default popup state for a detected website.

Header copy:

“Privacy scan”

Site context:

- Small site favicon placeholder.

- Hostname: example.com

- Page title: Example Pricing

- Status label: “Cookie banner detected”

Primary action:

- Large button: “Scan privacy”

- Secondary text: “Read-only analysis. Nothing will be changed yet.”

Do not show an overwhelming dashboard. The user should understand the next action immediately.

==================================================

SCAN IN PROGRESS STATE

==================================================

Create a polished progress state with a restrained animated indicator.

Headline:

“Inspecting this site”

Progress steps:

- Detecting consent controls

- Finding cookie policy

- Reading privacy evidence

- Preparing recommendation

Show one active step at a time.

Add a subtle activity log:

- “Cookie banner detected”

- “Privacy Policy found”

- “Analyzing analytics practices”

Use calm motion only:

- Small pulsing indicator.

- Smooth progress transition.

- No spinning neon loaders.

- Respect prefers-reduced-motion.

The scan must feel intelligent but not theatrical.

==================================================

RESULT STATE: PRIVACY RISK RADAR

==================================================

After analysis, show a strong result header:

“Your privacy snapshot”

Under it show:

- Site hostname.

- Scan timestamp.

- Workflow status: “Verified from site evidence.”

- Small confidence indicator.

Create a compact overall risk panel:

Label:

“Privacy exposure”

Example value:

“High”

Supporting text:

“Optional tracking and third-party sharing were detected.”

Do not use a large circular gauge. Use a premium horizontal score or compact status panel instead.

Include three compact metrics:

- Tracking: Detected

- Third parties: Detected

- Unknown categories: 1

Each metric must have:

- A simple line icon.

- Label.

- Text status.

- Accessible tooltip or supporting description.

==================================================

CATEGORY FINDINGS

==================================================

Create expandable finding rows for:

1. Essential

   - Status: Allow

   - Explanation: “Required for core site functionality.”

2. Functional

   - Status: Review

   - Explanation: “May remember preferences or improve site features.”

3. Analytics

   - Status: Block

   - Explanation: “Used to measure behavior and site usage.”

4. Advertising

   - Status: Block

   - Explanation: “May support profiling, targeted advertising, or ad measurement.”

5. Unknown

   - Status: Review

   - Explanation: “The available evidence was insufficient to classify this category.”

Each finding row should display:

- Category name.

- Recommendation.

- One-line explanation.

- Small confidence value.

- Expand control.

When expanded, show:

- Evidence excerpt.

- Source type.

- Source URL.

- “Why this matters” explanation.

- “Review original policy” link.

Use realistic content. Do not use lorem ipsum.

Example evidence:

“Analytics cookies are used to understand how visitors interact with our website and improve our services.”

Add a small label:

“Evidence-backed”

Never display a finding without an evidence excerpt unless the category is explicitly marked as unknown.

==================================================

PROTECTION PLAN PANEL

==================================================

Create a visually distinct recommendation panel using dark forest green as the primary surface, with ivory text and muted sage details.

Heading:

“Recommended protection”

Recommendation:

“Reject optional cookies”

Supporting copy:

“Keep essential cookies available while blocking optional analytics, advertising, and social cookies.”

Show a compact plan summary:

- Allow: Essential, Functional

- Block: Analytics, Advertising, Social

- Review: Unknown

Add a clear safety label:

“Nothing changes until you approve it.”

Primary button:

“Review and apply”

Secondary button:

“Keep browsing”

The primary action should not say “Accept” or “Reject” without context. It should communicate exactly what will happen.

==================================================

CONFIRMATION DIALOG

==================================================

Create a confirmation modal or full popup state.

Title:

“Review protection choice”

Body:

“ConsentShield is ready to reject optional cookies on example.com.”

Show:

- Action: Reject optional cookies

- Allowed: Essential and Functional

- Blocked: Analytics, Advertising, Social

- Unknown: 1 category requires review

- Source: Cookie Policy and consent banner

Show a warning if unknown categories exist:

“Unknown categories will not be automatically accepted.”

Buttons:

- Primary: “Apply protection”

- Secondary: “Cancel”

If automatic protection is disabled, show:

“Manual approval is enabled.”

If automatic protection is enabled, show:

“Automatic protection is enabled for your selected privacy mode.”

Never make the destructive or privacy-sensitive action visually ambiguous.

==================================================

EXECUTION STATE

==================================================

Create an execution state after the user confirms.

Headline:

“Applying your choice”

Steps:

- Verifying current page

- Confirming site identity

- Locating consent control

- Applying approved preference

Show:

- Current hostname.

- Short-lived plan status.

- “This action is limited to the current page.”

Do not show technical secrets, raw selectors, or browser internals to the user.

==================================================

SUCCESS STATE

==================================================

Create a calm success state.

Headline:

“Protection applied”

Supporting copy:

“Optional cookies were rejected on example.com.”

Show a summary:

- Essential: Allowed

- Analytics: Blocked

- Advertising: Blocked

- Social: Blocked

Add:

“ConsentShield did not change anything outside this page.”

Actions:

- “View scan details”

- “Close”

Use a restrained forest-green success treatment, not bright green.

==================================================

PARTIAL AND ERROR STATES

==================================================

Create polished states for:

### Partial result

Headline:

“Some privacy details could not be verified”

Copy:

“We found useful evidence, but this site did not clearly identify every cookie category.”

Show:

- Verified findings.

- Unknown findings.

- Source links.

- Recommendation disabled or marked “Review manually.”

CTA:

“View evidence”

### Unsupported page

Headline:

“This page cannot be scanned”

Copy:

“Browser settings and extension pages cannot be inspected by ConsentShield.”

CTA:

“Close”

### Backend unavailable

Headline:

“Privacy scan unavailable”

Copy:

“ConsentShield could not reach its analysis service. Nothing was changed.”

CTA:

“Try again”

### Stale protection plan

Headline:

“Page changed”

Copy:

“The page changed after the scan, so the protection plan was cancelled for safety.”

CTA:

“Scan again”

### No banner detected

Headline:

“No consent banner found”

Copy:

“We could not find a visible cookie control on this page. You can still review the available privacy policy.”

CTA:

“Review policy”

Never present a false success state.

==================================================

SETTINGS SCREEN

==================================================

Create a settings view reachable through the header settings icon.

Sections:

### Privacy mode

Use a segmented or stacked selector:

- Manual

- Strict

- Balanced

- Functional

- Custom

Default:

Manual

### Category preferences

Use accessible toggles:

- Essential — Always allowed and locked.

- Functional.

- Analytics.

- Advertising.

- Social.

- Unknown — Never automatically allowed.

### Protection behavior

Toggle:

“Allow automatic protection”

Supporting copy:

“When enabled, ConsentShield may apply your selected privacy preferences after verifying the current page.”

This toggle must be off by default.

Additional toggle:

“Require confirmation for unknown categories”

Default: On.

### Data controls

Actions:

- “Delete saved scan history”

- “Clear local preferences”

- “View privacy policy”

Use destructive styling only for destructive actions.

==================================================

COMPONENT SYSTEM

==================================================

Create reusable components:

- `ExtensionShell`

- `BrandHeader`

- `SiteContext`

- `PrivacyModePill`

- `ScanButton`

- `ScanProgress`

- `RiskOverview`

- `MetricTile`

- `CategoryFinding`

- `EvidenceDrawer`

- `ProtectionPlan`

- `ConfirmationDialog`

- `ExecutionProgress`

- `SuccessState`

- `PartialResultState`

- `ErrorState`

- `SettingsView`

- `ToggleRow`

- `SourceLink`

- `ConfidenceBadge`

- `EmptyState`

Use consistent props, states, spacing, and typography across components.

==================================================

INTERACTION DETAILS

==================================================

- Use subtle hover, focus, and pressed states.

- Use keyboard-accessible buttons and toggles.

- Provide visible focus rings in dark forest green.

- Never rely on color alone to communicate status.

- Add tooltips for confidence and evidence terminology.

- Use optimistic UI only for local preference changes.

- Do not show a fake progress percentage unless it reflects backend progress.

- Disable primary actions while a request is in progress.

- Prevent duplicate scans.

- Preserve the user’s current popup state during service-worker message updates.

- Handle popup reopening by hydrating state from extension storage or backend status.

- Respect `prefers-reduced-motion`.

- Use aria labels for icons.

- Ensure text remains readable at browser zoom levels.

==================================================

REAL CONTENT

==================================================

Use this sample data in the preview:

Site:

- Hostname: example.com

- Page title: Example Pricing

- Status: Cookie banner detected

Overall:

- Privacy exposure: High

- Tracking: Detected

- Third-party sharing: Detected

- Unknown categories: 1

- Confidence: 88%

Findings:

- Essential: Allow

- Functional: Allow

- Analytics: Block

- Advertising: Block

- Social: Block

- Unknown: Review

Evidence:

“Analytics cookies help us understand how visitors use our website and improve our services.”

Recommendation:

“Reject optional cookies”

Do not use generic placeholders such as “Lorem ipsum,” “Click here,” or “Sample text.”

==================================================

TECHNICAL BOUNDARIES

==================================================

Build only the extension frontend interface and its local interaction states.

Do not:

- Build a marketing website.

- Build a landing page.

- Build a desktop dashboard.

- Expose API keys.

- Put Supabase service-role keys in frontend code.

- Implement arbitrary browser automation.

- Auto-click consent controls without an explicit settings-based permission.

- Invent backend endpoints not present in the API contract.

- Replace the existing API contract.

- Store full HTML or raw cookies.

Use mock service data for the visual prototype if backend endpoints are not connected yet. Keep API calls behind a single `api.js` or equivalent service layer so the backend can be connected later without rewriting components.

==================================================

RESPONSIVE AND POPUP CONSTRAINTS

==================================================

The primary target is a browser popup:

- Width: 380px.

- Minimum height: 120px.

- Maximum height: 560px.

- No horizontal scrolling.

- Vertical scrolling only when necessary.

- Main CTA visible without excessive scrolling in the result state.

Also make the component layout responsive enough for:

- 320px width.

- 380px width.

- 480px width.

Do not create desktop-only layouts.

==================================================

IMPLEMENTATION ORDER

==================================================

1. Establish the design system and theme tokens.

2. Build the shell and header.

3. Build the initial scan state.

4. Build scan progress state.

5. Build risk result state.

6. Build finding expansion and evidence drawer.

7. Build protection-plan panel.

8. Build confirmation state.

9. Build execution and success states.

10. Build partial, error, and unsupported states.

11. Build settings.

12. Add responsive behavior and accessibility.

13. Add realistic mock data.

14. Verify all states visually before adding backend wiring.

Before making major structural changes, show a short implementation plan. Build reusable components instead of duplicating markup.

==================================================

QUALITY BAR

==================================================

The final result must feel:

- Premium.

- Calm.

- Privacy-first.

- Designed, not generated.

- Dense but not cramped.

- Clear within five seconds.

- Credible enough for a security product demo.

The primary interaction should be obvious:

1. Scan the current site.

2. Understand the evidence.

3. Review the recommendation.

4. Approve or decline protection.

Do not use blue or purple anywhere. Do not produce a generic SaaS dashboard. Do not add decorative elements that compete with the evidence and action flow.

This project was built with [Lovable](https://lovable.dev).

## Build with Lovable

Continue developing this project in the [Lovable editor](https://lovable.dev/projects/4ed7b7ee-50f9-4754-93c6-5d2643c4ece1).

- **Ship faster**: describe what you want to build and Lovable handles the code.
- **Stay in sync**: every change made in Lovable is committed straight to this repository.
- **Full ownership**: this code is yours. Push to `main` on GitHub and your changes sync back into Lovable, ready for your next prompt.

## Development

Prefer working locally? You need Node.js and npm — [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating).

```sh
git clone <this-repository-url>
cd <repository-name>
npm i
npm run dev
```
