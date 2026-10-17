# CITYSENSE – Multi-City Urban Risk Intelligence

### Multi-Source Urban Monitoring, Risk Analysis & Early Warning

CITYSENSE is a multi-city data analytics project that integrates weather forecasts, air-quality information, and traffic incident data to monitor urban conditions and identify potential disruptions across six major Indian cities.

The project combines Python-based data processing, SQL/SQLite data storage, risk assessment, short-term forecasting, and interactive Power BI dashboards to transform raw data into actionable urban intelligence.

![Project Status](https://img.shields.io/badge/status-active-success)
![Python](https://img.shields.io/badge/Python-Analytics-blue)
![Power BI](https://img.shields.io/badge/Power%20BI-Dashboard-yellow)
![SQL](https://img.shields.io/badge/SQL-Data%20Management-orange)
![Power Automate](https://img.shields.io/badge/Power%20Automate-Workflow-0066FF)

---

## 🎯 Project Overview

CITYSENSE provides a unified view of urban conditions by combining information from multiple data sources. It helps users compare city-level conditions, examine risk patterns, and monitor potential disruptions using data-driven analysis.

### Key Features

- **Multi-City Monitoring:** Covers Chennai, Bengaluru, Hyderabad, Mumbai, Delhi, and Kolkata.
- **Weather Intelligence:** Analyzes temperature, humidity, precipitation, wind speed, and hourly forecasts.
- **Air-Quality Analysis:** Examines available air-quality indicators and variations across cities.
- **Traffic Incident Intelligence:** Analyzes traffic incident data to identify disruption patterns.
- **Risk Assessment:** Uses risk indicators and scoring workflows to highlight potentially concerning conditions.
- **Short-Term Forecasting:** Uses available forecast data and analytical outputs to support forward-looking monitoring.
- **Interactive Power BI Dashboard:** Presents city comparisons, trends, risk indicators, and forecast information.
- **Manual Refresh Workflow:** Allows users to initiate data updates when required.
- **Power Automate Integration:** Coordinates the configured refresh workflow and reporting actions.
- **Decision Support:** Helps users interpret changing urban conditions through a consolidated analytical view.

---

## 🌆 Cities Covered

| City | Monitoring Focus |
|---|---|
| Chennai | Weather, air quality, and traffic incidents |
| Bengaluru | Weather, air quality, and traffic incidents |
| Hyderabad | Weather, air quality, and traffic incidents |
| Mumbai | Weather, air quality, and traffic incidents |
| Delhi | Weather, air quality, and traffic incidents |
| Kolkata | Weather, air quality, and traffic incidents |

The availability and freshness of each metric depend on its configured data source.

---

## 🛠️ Technologies Used

### Programming and Data Processing
- Python
- Pandas
- NumPy
- Scikit-learn, where applicable

### Data Storage
- SQL
- SQLite
- CSV datasets

### Visualization and Reporting
- Microsoft Power BI Desktop

### Data Integration and Workflow
- REST APIs
- Microsoft Power Automate

### Analytical Techniques
- Data cleaning and validation
- Exploratory data analysis
- Time-series and trend analysis
- Risk scoring
- Forecast interpretation
- Incident pattern analysis

---

## 🔄 Data Collection and Refresh Workflow

CITYSENSE uses an on-demand refresh approach supported by Microsoft Power Automate.

### Workflow

1. **Trigger:** Initiate the configured manual refresh workflow.
2. **Data Collection:** Retrieve the latest available information from configured APIs and data sources.
3. **Data Processing:** Clean, transform, and validate collected data using Python.
4. **Data Storage:** Update the relevant datasets and storage tables.
5. **Risk Analysis:** Generate or update configured risk indicators and forecast outputs.
6. **Power BI Refresh:** Execute the configured reporting refresh action through the workflow.
7. **Review:** Explore updated city conditions, trends, and risk indicators in Power BI.

### Power Automate Integration

Microsoft Power Automate coordinates the configured refresh workflow and reporting actions. This reduces repetitive manual steps and supports on-demand updates without requiring continuous background data collection.

---

## 📊 Power BI Dashboard

The Power BI dashboard provides an interactive view of urban conditions across the six cities.

### Dashboard Analysis
- City-level comparisons of available weather indicators.
- Temperature, humidity, precipitation, and wind-speed trends.
- Hourly weather forecasts and short-term outlooks.
- Air-quality indicators from configured sources.
- Traffic incident patterns and disruption indicators.
- City-level risk assessments and early-warning information.
- Interactive filtering and comparison for data exploration.

**Power BI report:** [`powerbi/CITYSENSE_AI.pbix`](powerbi/CITYSENSE_AI.pbix)

Open the report using Microsoft Power BI Desktop.

---

## 📁 Project Structure

```text
CITYSENSE_AI/
├── 01_weather_intelligence/
├── 02_traffic_intelligence/
├── 04_incident_intelligence/
├── 05_air_quality_intelligence/
├── 06_forecasting_early_warnings/
├── database/
├── models/
├── notebooks/
├── powerbi/
│   └── CITYSENSE_AI.pbix
├── reports/
├── scripts/
├── .gitignore
└── README.md
```

*This is a summary of the project structure. Refer to the repository for the actual files and folders.*

---

## ▶️ Getting Started

### Prerequisites
- Python
- Microsoft Power BI Desktop
- Required API access for configured data sources
- Microsoft Power Automate access for the refresh workflow
- Git, if cloning the repository

### Step 1: Clone the Repository

```bash
git clone https://github.com/jana304/CITYSENSE-Multi-City-Urban-Risk-Intelligence.git
cd CITYSENSE-Multi-City-Urban-Risk-Intelligence
```

### Step 2: Set Up Python

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it in Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies from the appropriate requirements file, if available:

```bash
pip install -r requirements.txt
```

If there is no root-level `requirements.txt`, install the dependencies specified for the individual scripts.

### Step 3: Configure Data Sources

Configure required API credentials locally using environment variables. Never commit API keys, passwords, or other secrets to GitHub.

### Step 4: Run the Data Workflow

Run the required data-collection and processing scripts in the appropriate order. Verify that the datasets have been updated before refreshing the dashboard.

### Step 5: Open Power BI

Open `powerbi/CITYSENSE_AI.pbix` in Power BI Desktop. Verify the data-source paths and connections, then refresh the report through the configured workflow.

---

## 📈 Project Objectives

The main objectives of CITYSENSE are to:

- Combine multiple sources of urban data in one analytical project.
- Compare conditions and potential risks across cities.
- Identify trends and potentially concerning changes.
- Present forecasts and risk indicators through interactive visualizations.
- Reduce repetitive refresh tasks through Power Automate.
- Demonstrate practical skills in data analytics, data integration, visualization, and workflow design.

---

## 🔐 Data and Security

- Store API credentials securely outside the repository.
- Exclude local databases and generated datasets from GitHub when appropriate.
- Validate data quality and source availability before interpreting results.
- Treat forecasts and risk scores as estimates rather than guaranteed predictions.

---

## 🚀 Future Enhancements

Potential improvements include:

- Expanding road-level traffic analysis where reliable free data is available.
- Evaluating relationships between weather conditions and traffic incidents.
- Improving risk-scoring methods through model validation.
- Adding historical performance tracking for forecasts and warnings.
- Integrating additional verified data sources.

---

## 👨‍💻 Project Information

- **Project Name:** CITYSENSE – Multi-City Urban Risk Intelligence
- **Domain:** Urban Data Analytics and Decision Intelligence
- **Programming:** Python
- **Database:** SQL / SQLite
- **Visualization:** Microsoft Power BI
- **Workflow Automation:** Microsoft Power Automate
- **Cities Covered:** Chennai, Bengaluru, Hyderabad, Mumbai, Delhi, and Kolkata
- **Author:** Jana M.
- **Year:** 2026

---

## ⚠️ Disclaimer

CITYSENSE is an analytical project intended for educational and decision-support purposes. Data freshness depends on configured sources and the refresh workflow. Forecasts and risk indicators represent estimates and do not guarantee future urban conditions.

---

**Built with Python, SQL, Power BI, and Power Automate.**
