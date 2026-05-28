# Drone Spray Zone Analysis using Multispectral Imagery

## Overview

This project performs drone-based crop stress analysis using multispectral imagery and NDVI (Normalized Difference Vegetation Index). The workflow identifies stressed vegetation zones and converts them into geospatial spray prescription polygons for precision agriculture applications.

The project simulates a simplified post-flight agricultural drone analysis pipeline where multispectral imagery is processed to determine regions requiring intervention such as pesticide spraying or nutrient application.

## Objective

* Compute NDVI from multispectral drone imagery
* Detect stressed crop regions
* Generate spray recommendation zones
* Export geospatial polygon data
* Visualize spray zones interactively using Folium

## Technologies Used

* Python
* Rasterio
* NumPy
* GeoPandas
* Shapely
* Folium

## Dataset

Multispectral orthomosaic dataset from OpenDroneMap sample datasets.

Download link:

https://github.com/OpenDroneMap/ODMdata

Recommended dataset:

* Full-Spectrum / NDVI agricultural dataset

After downloading, place the TIFF orthomosaic inside the project directory.

## NDVI Formula

NDVI is computed using:

[
NDVI = \frac{NIR - Red}{NIR + Red}
]

Lower NDVI values indicate stressed vegetation regions which may require agricultural intervention.

## Workflow

1. Load multispectral orthomosaic TIFF
2. Extract Red and NIR bands
3. Compute NDVI values
4. Apply threshold-based stress classification
5. Generate binary spray mask
6. Convert raster mask into vector polygons
7. Export spray zones as shapefiles
8. Visualize zones using an interactive map

## Output Files

### Generated Shapefiles

* `spray_zones.shp`
* `spray_zones.dbf`
* `spray_zones.shx`
* `spray_zones.prj`

### Interactive Map

* `spray_zones_map.html`

## Project Structure

```text id="x6f1fw"
drone-spray-zone-analysis/
│
├── spray_zones.py
├── spray_zones_map.html
├── spray_zones.shp
├── spray_zones.dbf
├── spray_zones.shx
├── spray_zones.prj
├── README.md
└── .gitignore
```

## How to Run

### 1. Clone the repository

```bash id="9cgn9n"
git clone https://github.com/VihaanR/drone-spray-zone-analysis.git
cd drone-spray-zone-analysis
```

### 2. Install dependencies

```bash id="0u8g33"
pip install rasterio numpy geopandas shapely folium
```

### 3. Download the multispectral TIFF dataset

Download from:

https://github.com/OpenDroneMap/ODMdata

Place the TIFF orthomosaic inside the project directory.

Example filename:

```text id="lxbex5"
EX1_5band.tif
```

### 4. Run the analysis script

```bash id="whn22q"
python spray_zones.py
```

## Output Visualization

The generated map highlights crop stress regions requiring spraying intervention.

* Red polygons → Stressed vegetation zones
* Interactive HTML visualization generated using Folium

Open:

```text id="xyk0jv"
spray_zones_map.html
```

in a browser to explore the generated spray zones.

## Applications

* Precision agriculture
* Variable rate spraying
* Drone-assisted crop monitoring
* Crop stress detection
* Agricultural GIS workflows

## Future Improvements

* Dynamic NDVI threshold calibration
* Multi-date drone analysis
* Integration with GPS flight logs
* Automated spray recommendation engine
* Web-based GIS dashboard

## Author

Vihaan Raut
