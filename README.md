# DEM Analysis and Validation in the Ukrainian Carpathians

This repository presents a scientific study and practical workflow for evaluating global Digital Elevation Models (DEMs) in mountainous regions of Ukraine, with a focus on hydrological and hydraulic applications.

## 🌍 Project Overview

Digital Elevation Models (DEMs) are the geometric backbone of hydrological modeling, enabling watershed delineation, river profiling, and floodplain simulation. However, DEMs are more than just height grids — they represent a discretized form of the gravitational field that governs how water flows.

In this study, we systematically assess the quality of four publicly available global DEMs:

- **SRTM**  
- **ALOS AW3D30**  
- **Copernicus GLO-30**  
- **FABDEM**

Each model is aligned to the **EGG2015** vertical reference system and validated using high-precision **ICESat-2 ATL08** LiDAR ground returns over the **Bilyi Cheremosh River basin** — a representative mountainous watershed in the Ukrainian Carpathians.

## 🎯 Objectives

- Align all DEMs to a **unified vertical datum** (EGG2015 / EVRS)
- Validate DEMs against **ICESat-2 ATL08** ground elevations
- Compute **pointwise accuracy metrics**: ME, RMSE, MAE
- Extract and analyze:
  - **longitudinal profiles**
  - **cross-sectional profiles**
  - **terrain derivatives** (slope, curvature, ruggedness)
- Assess **DEM suitability for hydrological and hydraulic modeling**

## 🧠 Knowledge Gap Addressed

While global DEM evaluations with ICESat-2 exist, few studies focus on:
- the **Ukrainian Carpathians**
- the **hydrological relevance** (e.g., valley shape, slope realism)
- the **need for vertical datum harmonization**

## 🧪 Scientific Contribution

By integrating DEMs with geoid models and validating against ICESat-2 reference surfaces, this project provides:
- a **new framework** for DEM trust evaluation
- reproducible, geodetically accurate methods
- high-resolution insights for mountain hydrology and terrain modeling

## 📁 Repository Structure

```
project/
├── src/                   # Main application logic
│   ├── config/            # .env and settings
│   ├── adapter/           # File access, readers, path resolvers
│   ├── domain/            # DEM-specific logic (e.g., read_dem)
│   └── myio/              # Clean interface (read_parquet, read_dem)
├── notebooks/             # Jupyter Notebooks for analysis
├── data/ (not tracked)    # Local or linked DEM/ATL08 data
├── .env.example           # Example path to data directory
├── requirements.txt       # Dependencies
└── README.md              # Project documentation
```

## ⚙️ Getting Started

### 1. Clone the repository

```bash
git clone git@github.com:NikoriakViktot/dem-analysis.git
cd dem-analysis
```

### 2. Set up the environment

```bash
cp .env.example .env
conda env create -f environment.yml
conda activate dem-env
```

### 3. Explore the notebooks

```bash
jupyter lab
```

## 📚 References

- ICESat-2 ATL08 Product: https://nsidc.org/data/ATL08
- EGG2015 Geoid Model: https://www.bkg.bund.de/EGG2015
- FABDEM: Forest and Buildings Removed Copernicus DEM: https://fabdem.github.io

## 📜 License

MIT License © Viktor Nikoriak, Ukrainian Hydrometeorological Institute

## 🤝 Acknowledgements

This work contributes to ongoing research in the **Ukrainian Hydrometeorological Institute**