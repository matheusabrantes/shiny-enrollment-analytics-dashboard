# Higher Education Enrollment Analytics Dashboard

Interactive data visualization dashboard analyzing enrollment funnel performance for 370+ U.S. higher education institutions (2022-2024).

**Author:** Matheus Abrantes  
**Date:** January 2026

**Live demo:** https://matheusabrantes-higher-ed-enrollment-funnel-analytics.share.connect.posit.cloud/

---

## 🎯 Project Overview

This dashboard demonstrates enrollment analytics capabilities for higher education marketing and enrollment strategy. It visualizes:

- **Enrollment Funnel:** Applicants → Admitted → Enrolled conversion flow
- **Trends Analysis:** Conversion rates and yield trends over time
- **Demographics:** Diversity breakdown by race/ethnicity
- **Benchmarking:** Top-performing institutions and comparative metrics

**Data Source:** IPEDS (Integrated Postsecondary Education Data System) - U.S. Department of Education public data covering 371 institutions across 2022-2024.

---

## 🛠️ Technical Stack

- **Framework:** Shiny for Python (v0.7+)
- **Visualization:** Plotly (interactive charts)
- **Data Processing:** Pandas, NumPy
- **Deployment:** Posit Cloud-ready
- **Version Control:** Git/GitHub

---

## 🚀 Quick Start

### Local Development

1. Clone repository:
```bash
git clone https://github.com/matheusabrantes/shiny-enrollment-analytics-dashboard.git
cd shiny-enrollment-analytics-dashboard
```

2. Create virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the app:
```bash
shiny run app.py
```

5. Open browser at `http://localhost:8000`

### Deployment to Posit Cloud

1. Log in to [posit.cloud](https://posit.cloud)
2. Create New Project → From Git Repository
3. Paste repository URL
4. Select `app.py` as the application file
5. Deploy

---

## 📊 Dashboard Features

### Interactive Filters
- **Year selection:** Filter by Fall 2022, 2023, or 2024
- **Institution filter:** Search and select specific institutions
- **Reset button:** Quickly restore default filter state

### Key Visualizations

1. **KPI Cards:** At-a-glance metrics
   - Total Applicants
   - Total Admissions
   - Total Enrolled
   - Average Yield Rate

2. **Enrollment Funnel:** Funnel chart showing conversion flow with stage-by-stage rates

3. **Conversion Trends:** Multi-line chart tracking admit rates, yield rates, and overall conversion over time

4. **Geographic Distribution:** Interactive choropleth map showing state-level enrollment metrics
   - Toggle between Yield Rate, Total Enrollment, and Institution count
   - Supports geospatial analysis and market opportunity insights

5. **Demographics:** Stacked bar chart showing enrollment diversity by race/ethnicity across years

6. **Institution Comparison:** Horizontal bar chart benchmarking top institutions by:
   - Yield Rate (default)
   - Total Enrollment
   - Admit Rate

---

## 🤖 AI Insights (LLM-powered analytics)

The **AI Insights** page provides natural language querying of enrollment data using OpenAI's gpt-5-mini model.

### Features
- **Natural Language Queries:** Ask questions about enrollment data in plain English
- **AI-Generated Insights:** Receive executive-style textual explanations
- **Dynamic Visualizations:** Auto-generated Plotly charts based on your query
- **Smart Filtering:** AI automatically applies relevant data filters

### Example Queries
- "Which institutions have the highest yield rates in the Northeast?"
- "Compare enrollment trends for large institutions from 2022-2024"
- "What's the relationship between admit rate and yield rate?"
- "Show me the most diverse institutions by region"

### Configuration

To enable AI features, set your OpenAI API key:

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your API key:
   ```
   OPENAI_API_KEY=your_actual_api_key_here
   ```

3. **Important:** Never commit `.env` to version control. It is already in `.gitignore`.

### Behavior Without API Key

If `OPENAI_API_KEY` is not set:
- The app will still run normally
- All other dashboard pages work as expected
- The AI Insights page displays a message: "AI features are not configured. Please set OPENAI_API_KEY."

---

## 🎨 Design Decisions

### Color Palette
Professional color scheme:
- **Primary:** Navy Blue (#002633) - trust, professionalism
- **Secondary:** Coral Orange (#FF6B35) - energy, action
- **Neutrals:** White, light gray backgrounds for readability

### UX Principles
- **Simplicity:** Single-page layout, no nested navigation
- **Focus:** Each chart tells one clear story
- **Performance:** Reactive filters, optimized data processing
- **Accessibility:** High-contrast colors, clear labels

---

## 📈 Key Insights (Example)

Based on the data:

- **Average yield rate:** ~22% of admitted students enroll (2022-2024 average)
- **Admit rate:** ~68% average across institutions
- **Diversity trend:** Hispanic student enrollment shows growth over the period
- **Top performers:** Elite institutions achieve 40%+ yield rates

---

## 🏗️ Project Structure

```
shiny-enrollment-analytics-dashboard/
├── app.py                      # Main Shiny application
├── requirements.txt            # Python dependencies
├── .gitignore                  # Git ignore file
├── .env.example                # Environment variables template
├── README.md                   # Project documentation
├── data/
│   └── ipeds_enrollment_data.csv   # IPEDS enrollment data
├── modules/
│   ├── __init__.py
│   ├── page_overview.py        # Overview page
│   ├── page_benchmarking.py    # Benchmarking page
│   ├── page_institution_profile.py  # Institution profile page
│   ├── page_simulator.py       # Enrollment simulator page
│   ├── page_ai_insights.py     # AI Insights page (LLM-powered)
│   ├── components_charts.py    # Plotly chart components
│   ├── components_kpis.py      # KPI card components
│   └── components_tables.py    # Table components
└── utils/
    ├── __init__.py
    ├── data_loader.py          # Data loading utilities
    ├── calculations.py         # Metric calculations
    ├── llm_client.py           # OpenAI API integration
    └── styling.py              # Brand colors & themes
```

---

## 🔧 Development Notes

### Data Processing
The raw IPEDS data is in wide format with columns for each year. The `data_loader.py` module transforms this to long format for easier analysis:
- Extracts demographic percentages (Hispanic, White, Black, Asian, Other)
- Extracts funnel metrics (Applicants, Admissions, Enrolled)
- Calculates derived metrics (Admit Rate, Yield Rate)

### Performance Optimizations
- Data loaded once at startup
- Filtered datasets computed reactively using `@reactive.calc`
- Plotly charts optimized with appropriate aggregation levels

### Code Quality
- Modular architecture (components separated by concern)
- Clear variable naming and docstrings
- Type hints where applicable
- Follows Shiny for Python best practices

---

## 📧 Contact

**Matheus Abrantes**  
Senior Data Scientist | AI Engineer  
[LinkedIn](https://linkedin.com/in/matheusabrantes) | [GitHub](https://github.com/matheusabrantes)

---

## 📄 License

This project is for portfolio purposes. Data source: IPEDS (public domain).
