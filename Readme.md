# 🚦 Traffic Violations Insight System
### EDA, Cleaning & Interactive Streamlit Dashboard
**Montgomery County, Maryland**

---

## 📌 Project Overview

Urban safety agencies generate millions of traffic-violation records each year, capturing details such as violation type, location, driver demographics, vehicle information, and enforcement-related metadata. This raw data is often noisy, inconsistent, duplicated, and difficult to interpret without systematic preprocessing and visualization.

This project builds a **complete data analytics system** that transforms a large, raw dataset of traffic violations (~2 million rows) from Montgomery County, Maryland into actionable insights through:
- **Data Cleaning & Preprocessing**
- **Exploratory Data Analysis (EDA)**
- **Interactive Streamlit Dashboard**
- **MariaDB Database Integration**

---

## 🛠️ Tech Stack

| Tool | Purpose |
|------|---------|
| Python 3 | Core programming language |
| Pandas | Data cleaning & manipulation |
| NumPy | Numerical operations |
| Matplotlib / Seaborn | Static visualizations (EDA) |
| Plotly | Interactive charts (Dashboard) |
| Streamlit | Interactive web dashboard |
| MariaDB | Relational database storage |
| PyMySQL | Python-MariaDB connector |
| Folium | Geographic heatmaps (optional) |
| Git LFS | Large file storage |

---

## 📁 Project Structure

```
Traffic_Violation_Project/
│
├── 01_data_cleaning.ipynb          # Data cleaning & preprocessing notebook
├── 02_eda.ipynb                    # Exploratory Data Analysis notebook
├── 03_mariadb_local.py             # MariaDB insertion script
├── 04_streamlit_app_v3.py          # Interactive Streamlit dashboard
│
├── Visualisation Charts/           # EDA charts and visualizations
│   ├── violation_types.png
│   ├── hourly_distribution.png
│   └── ...
│
├── requirements.txt                # Python dependencies
├── .gitignore                      # Git ignore rules
└── README.md                       # Project documentation
```

> **Note:** Large data files are stored on Google Drive due to GitHub's file size limits.

---

## 📊 Dataset

**Source:** Montgomery County, Maryland Open Data Portal

**Size:** ~2 million rows | 43 columns

**Large files (Google Drive):**
- 📄 [traffic_violations_cleaned.csv (1.2 GB)](https://drive.google.com/your-link-here)
- 📦 [traffic_violations_cleaned.pkl (264 MB)](https://drive.google.com/your-link-here)

**Key Columns:**
- `Date Of Stop`, `Time Of Stop` — When the violation occurred
- `Agency`, `SubAgency` — Law enforcement agency
- `Description`, `Violation Type` — Nature of the violation
- `Location`, `Latitude`, `Longitude` — Where it occurred
- `Race`, `Gender` — Driver demographics
- `Make`, `Model`, `VehicleType` — Vehicle details
- `Accident`, `Fatal`, `Personal Injury` — Safety indicators

---

## 🧹 Data Cleaning Highlights

- Removed duplicate and inconsistent records
- Standardized date/time formats
- Normalized categorical variables (Race, Gender, Vehicle Type)
- Validated and cleaned geographic coordinates (replaced 0,0 with NaN)
- Handled missing, invalid, and out-of-range values
- Engineered new features:
  - `Hour`, `DayOfWeek`, `Month`, `Time_Bucket`
  - `Vehicle_Age`, `Violation_Category`
  - `High_Risk`, `Violation_Count`

---

## 🔍 EDA Key Findings

- **Most Common Violation:** Failure to obey traffic signals
- **Peak Hour:** Evening rush hours (5 PM – 7 PM)
- **Busiest Day:** Friday
- **Most Common Vehicle:** Automobiles (02 - Automobile)
- **Top Vehicle Make:** Toyota, Honda, Ford
- **Accident Rate:** ~3% of all violations involve accidents
- **Demographics:** Male drivers account for ~67% of violations

---

## 📈 Streamlit Dashboard Features

### Sidebar Filters
- 📅 Date Range
- 🏢 Agency & Sub Agency
- 📋 Violation Category
- ⚖️ Violation Type (Citation / Warning / Esero / Sero)
- 🚗 Vehicle Type
- 👥 Race & Gender
- ⚠️ Safety Flags (Accidents Only, Alcohol-Related, High-Risk)

### Dashboard Tabs
| Tab | Content |
|-----|---------|
| 📊 Overview | Top violations, categories, safety incidents comparison |
| 🗺️ Geographic | Hotspot map, high-risk locations, district analysis |
| ⏰ Temporal | Daily trend, hourly, day of week, monthly distribution |
| 🚗 Vehicle | Makes, models, types, age groups, colors |
| 👥 Demographics | Race, gender, accident correlations |
| 📋 Summary Stats | Descriptive statistics, full breakdown table |

### KPI Metrics
- Total Violations
- Unique Stops
- Accidents & Rate
- Fatal Incidents
- Personal Injuries
- High-Risk Violations
- Property Damage
- Alcohol-Related
- No Seatbelt
- Work Zone

---

## 🗄️ Database Setup (MariaDB)

```sql
-- Create database
CREATE DATABASE traffic_violations;
USE traffic_violations;
```

```bash
# Run the insertion script
python 03_mariadb_local.py
```

**Indexes created for performance:**
- `Date Of Stop`
- `Agency`
- `Race`
- `Gender`
- `Violation_Category`
- `Accident`
- `High_Risk`
- `Arrest_Type_Desc`
- `original_seq_id`

---

## 🚀 How to Run

### 1. Clone the Repository
```bash
git clone https://github.com/GeekyVishweshNeelesh/Traffic_Violation_Project_ML.git
cd Traffic_Violation_Project_ML
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Setup MariaDB
```bash
# Start MariaDB
sudo systemctl start mariadb

# Run insertion script
python 03_mariadb_local.py
```

### 4. Run the Dashboard
```bash
streamlit run 04_streamlit_app_v3.py
```

Open your browser at `http://localhost:8501`

---

## 📦 Requirements

```
streamlit
pymysql
pandas
numpy
plotly
matplotlib
seaborn
folium
streamlit-folium
```

Install all with:
```bash
pip install streamlit pymysql pandas numpy plotly matplotlib seaborn folium streamlit-folium
```

---

## 💡 Business Use Cases

This system can help:
- 🚔 **Police Departments** — Identify high-violation zones and allocate patrol resources
- 🏙️ **Urban Planners** — Detect accident-prone intersections for infrastructure improvements
- 📋 **Policy Makers** — Inform traffic law enforcement decisions
- 🚦 **Road Safety Boards** — Monitor trends and measure intervention effectiveness

---

## 🌐 Live Deployment

The dashboard is deployed and accessible at:

👉 **[Traffic Violations Insight System](https://your-app-name.streamlit.app)**

> Deployed on [Streamlit Community Cloud](https://streamlit.io/cloud)

---

## 📸 Dashboard Screenshots

> *(Add screenshots of your dashboard here)*

---

## 👨‍💻 Author

**Vishwesh Neelesh**
- GitHub: [@GeekyVishweshNeelesh](https://github.com/GeekyVishweshNeelesh)

---

## 📄 License

---

*Built with Streamlit 🎈 | Powered by MariaDB 🗄️ | Visualized with Plotly 📊*
