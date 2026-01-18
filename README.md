# Carnegie Higher Education Enrollment Dashboard

Interactive data visualization dashboard analyzing enrollment funnel performance for 370+ U.S. higher education institutions (2022-2024).

**Built for:** Carnegie Data Visualization Specialist Interview  
**Author:** Matheus Abrantes  
**Date:** January 2026

---

## 🎯 Project Overview

This dashboard demonstrates enrollment analytics capabilities relevant to Carnegie's work in higher education marketing and enrollment strategy. It visualizes:

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

4. **Geographic Distribution:** Interactive choropleth map showing state-level enrollment metrics ⭐ NEW
   - Toggle between Yield Rate, Total Enrollment, and Institution count
   - Aligned with Carnegie's Geospatial Analysis services

5. **Demographics:** Stacked bar chart showing enrollment diversity by race/ethnicity across years

6. **Institution Comparison:** Horizontal bar chart benchmarking top institutions by:
   - Yield Rate (default)
   - Total Enrollment
   - Admit Rate

---

## 🎨 Design Decisions

### Color Palette
Inspired by Carnegie's brand identity:
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
├── README.md                   # Project documentation
├── data/
│   └── ipeds_enrollment_data.csv   # IPEDS enrollment data
├── components/
│   ├── __init__.py
│   ├── header.py               # Header component
│   ├── filters.py              # Filter sidebar component
│   ├── funnel_chart.py         # Enrollment funnel visualization
│   ├── trends_chart.py         # Conversion trends over time
│   ├── demographics_chart.py   # Demographics breakdown
│   └── comparison_chart.py     # Institution comparison
└── utils/
    ├── __init__.py
    ├── data_loader.py          # Data loading utilities
    ├── calculations.py         # Metric calculations
    └── styling.py              # Carnegie brand colors & themes
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

## 📝 Interview Context

This project was built in a weekend (January 2026) to demonstrate:

1. **Technical Skills:** Shiny for Python, Plotly, data wrangling with Pandas
2. **Domain Knowledge:** Understanding of higher education enrollment metrics
3. **Design Acumen:** Clean, professional aesthetic aligned with Carnegie's brand
4. **Storytelling:** Clear narrative through data (funnel → trends → insights)
5. **Initiative:** Proactive research on Carnegie's business and custom dashboard creation

**Presented to:** Greg Kegeles, CPO/Head of AI at Carnegie  
**Interview Date:** January 20, 2026

---

## 📧 Contact

**Matheus Abrantes**  
Senior Data Scientist | AI Engineer  
[LinkedIn](https://linkedin.com/in/matheusabrantes) | [GitHub](https://github.com/matheusabrantes)

---

## 📄 License

This project is for portfolio and interview purposes. Data source: IPEDS (public domain).
