# 🛡️ ConsentShield

> **Intelligent, Automated Cookie Consent Enforcement & Privacy Auditing Engine 🚀**

ConsentShield is an autonomous privacy assistant and cookie consent enforcement platform designed to eliminate "cookie banner fatigue" and dark patterns. It discovers website privacy policies, analyzes tracking mechanisms using AI models, constructs targeted protection plans, and executes deterministic browser actions through **WebCmd** to enforce user consent choices.

---

<!-- 📸 Main Dashboard / Hero Screenshot Placeholder -->
<p align="center">
  <img src="docs/screenshots/dashboard-preview.png" alt="ConsentShield Dashboard Overview" width="85%" />
</p>

---

## ✨ Features

* 🔍 **Autonomous Cookie & Tracker Detection**: Scans live pages to identify runtime cookies, third-party analytics, and advertising telemetry.
* 🤖 **AI-Powered Policy Analysis**: Ingests site privacy policies to highlight tracker risks and contrast declarations against reality.
* ⚡ **WebCmd Browser Automation Engine**: Executes deterministic browser commands to bypass dark patterns, toggle granular CMP settings, and submit consent decisions directly on the DOM.
* 📊 **Live Telemetry & Post-Scan Verification**: Verifies that non-essential scripts and cookies are suppressed after preference submission.
* ⚙️ **Granular Privacy Profiles**: Set custom acceptance rules across analytics, marketing, behavioral tracking, and essential cookies.
* 🎨 **Interactive User Interface**: Built with Vite, React, Tailwind CSS, and real-time backend event updates.

---

## 🏗️ System Architecture

```text
               +-------------------------------------------------+
               |          💻 React / Vite Frontend               |
               |  - User Preference Settings                     |
               |  - URL Scan Controller & Risk Dashboard         |
               |  - Real-Time Audit Telemetry                    |
               +-----------------------+-------------------------+
                                       |
                                       | 🌐 REST API / JSON
                                       v
               +-------------------------------------------------+
               |          ⚡ FastAPI Backend Layer               |
               |  - Routes: /scans, /preferences, /execution     |
               |  - Repositories: Supabase DB & Event Stream     |
               +-----------------------+-------------------------+
                                       |
        +------------------------------+------------------------------+
        |                                                             |
        v                                                             v
+-------------------------------+                     +-------------------------------+
|     🧠 AI & Analysis Layer    |                     |   🕹️ WebCmd Execution Engine  |
| - Policy Scraper & Parser     |                     | - Sandboxed Browser Sessions  |
| - Cookie Classifier           |                     | - Banner / CMP Navigation     |
| - LLM Protection Planner      |                     | - Deterministic DOM Actions   |
+-------------------------------+                     | - Storage & Request Audit     |
                                                      +-------------------------------+
