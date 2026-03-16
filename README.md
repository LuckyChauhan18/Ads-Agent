# Spectra AI: Multi-Agent Ad Generation System

Spectra AI is a cutting-edge platform designed to automate the creation of high-impact video advertisements. By leveraging a multi-agent orchestrated workflow, it transforms raw product ideas into cinematic video ads.

## 🚀 Current Project Status

-   **✅ Rendering (Production Agent):** **Working Good.** The video rendering pipeline, including avatar generation, voiceover synchronization, and cinematic effects, is stable and produces high-quality results.
-   **⚠️ Scripting (Creative Agent):** **In Progress.** We are currently refactoring the script generation logic to improve narrative flow and psychological impact. It may produce inconsistent results during this phase.

---

## 🛠️ Setup Instructions

### Prerequisites
- **Python 3.10+**
- **Node.js 18+**
- **MongoDB** (Local or Atlas)
- **Redis**

### 1. Project Initialization
```bash
# Clone the repository
git clone <repository-url>
cd langgraph_add

# Switch to the test branch
git checkout lucky/test

# Install Python dependencies
pip install -r requirements.txt

# Install Frontend dependencies
cd react-wizard
npm install
cd ..
```

### 2. Environment Configuration
Create a `.env` file in the root directory and add the following:
```env
OPENROUTER_API_KEY=your_key
HEYGEN_API_KEY=your_key
GEMINI_API_KEY=your_key
MONGODB_URL=your_mongodb_url
LTM_MONGODB_URL=your_ltm_mongodb_url
TAVILY_API_KEY=your_tavily_key
SARVAM_API_KEY=your_sarvam_key
ELEVENLABS_API_KEY=your_elevenlabs_key
REDIS_URL=your_redis_url
# ... other Cloudflare R2 and JWT configs
```

### 3. Running the System
```bash
# Start the Backend API (from root)
python run_api.py

# Start the Frontend (from react-wizard)
cd react-wizard
npm run dev
```

---

## 🧠 System Architecture & Workflow

The system operates as a linear pipeline of specialized agents coordinated via LangGraph.

### Phase 1: Research Agent
-   **Input:** Raw product information and target keywords.
-   **Process:** Deep web search (via Tavily), competitor ad scraping, and brand DNA extraction.
-   **Output:** `product_understanding` (AI-enriched analysis) and `competitor_results` (scraped ad DNA).

### Phase 2: Strategy Agent
-   **Input:** Research results and founder intent (funnel stage, emotions, objections).
-   **Process:** Generates a campaign psychology framework and selects the optimal ad pattern (e.g., Founder Story, Problem-Solution).
-   **Output:** `campaign_psychology` (detailed emotional strategy) and `pattern_blueprint` (structural ad plan).

### Phase 3: Creative Agent (Scripting)
-   **Input:** Strategy blueprint and brand voice preferences.
-   **Process:** Creates a scene-by-scene script including voiceover copy, visual descriptions, and avatar configurations.
-   **Output:** `script_output` (VO scripts) and `storyboard_output` (visual shot list).

### Phase 4: Production Agent (Rendering)
-   **Input:** Creative storyboard and script.
-   **Process:** AI avatar generation, TTS synthesis, video assembly, and cinematic layering.
-   **Output:** `variants_output` (ad variants) and final video files ready for preview.

---

## 🤝 Contribution
We are actively working on the **Creative Agent**. Contributions to the scripting engine and prompt engineering are welcome.
