# 🚀 Agentic B2B Outbound Sales Automation System

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Framework-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19-61DAFB?logo=react)](https://react.dev/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Orchestration-orange)](https://github.com/langchain-ai/langgraph)

An autonomous, multi-agent system designed to transform high-level sales missions into precision-targeted outreach campaigns. Powered by **GPT-4o-mini** and **LangGraph**, it handles everything from deep company research to personalized email coordination.

---

## ✨ Key Features

- **🧠 Deep Intelligence Agents**: Autonomous web-scanners that research your own company and target prospects to find the perfect value match.
- **🎯 Precision Lead Finder**: Targeted search for relevant companies and specific decision-makers.
- **✍️ Personalized Narrative Engine**: Dynamic drafting of outreach emails that reflect the synthesized context of both sender and recipient.
- **📬 Autonomous Inbox Monitoring**: Built-in IMAP listeners that detect prospect replies and categorize intent in real-time.
- **⚖️ Human-in-the-Loop**: A premium React dashboard to review, edit, and approve drafts before they go live.
- **📅 Discovery Bridge**: Integrated workflow to transition high-intent leads into booked discovery calls via Calendly.

## 🛠️ Technology Stack

- **Backend**: FastAPI (Python)
- **Orchestration**: LangGraph (Multi-Agent State Machine)
- **LLM**: OpenAI GPT-4o-mini
- **Database**: Neon (Serverless Postgres)
- **Frontend**: React 19 + Framer Motion (Premium UI)
- **Research**: Trafilatura, Playwright, Tavily Search API
- **Deployment**: Render-Ready (Blueprint included)

---

## 🚦 Getting Started

### Prerequisites

- Python 3.10+
- React 19+
- API Keys: OpenAI, Tavily Search, Neon DB

### Installation

1. **Clone the project:**

   ```bash
   git clone https://github.com/vinaykumarreddy9/company-outreach-agent.git
   cd company-outreach-agent
   ```

2. **Set up the Backend:**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Set up the Frontend:**

   ```bash
   cd frontend
   npm install
   ```

4. **Configuration:**
   Create a `.env` file in the root directory with the following:
   ```env
   OPENAI_API_KEY=your_key
   NEON_DB_URL=your_postgres_url
   TAVILY_API_KEY=your_key
   EMAIL_USER=your_smtp_email
   EMAIL_PASSWORD=your_smtp_password
   ```

### Running Locally

Use the provided master bootstrapper (Windows only):

```bash
./run.bat
```

_Choose **[1] Unified Engine** to run the Full Stack inside a single window (ideal for testing Render-like behavior)._

---

## 🎨 Design Philosophy

The UI is built with a focus on **Visual Excellence**:

- **Glassmorphism**: Sleek, modern card layouts.
- **Micro-animations**: Smooth transitions powered by Framer Motion.
- **Action-Oriented**: Clear "Review → Approve → Send" workflow.

## ☁️ Deployment

This repository is **Render-Ready**.

1. Push your code to GitHub.
2. Link your repo to Render as a **Blueprint**.
3. Render will automatically deploy the Backend (Web Service) and Frontend (Static Site).

---

## 🤝 Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements.

## 📜 License

This project is licensed under the MIT License.

---

_Built with ❤️ by the Digiotai Solutions Team_
