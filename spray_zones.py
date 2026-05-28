"""Generate NDVI-based spray prescription zones from a 5-band orthomosaic."""

import sys
from pathlib import Path

import folium
import geopandas as gpd
import numpy as np
import rasterio
from rasterio.features import shapes
from shapely.geometry import shape


INPUT_FILE = Path("EX1_5Band.tif")
SPRAY_THRESHOLD = 0.3
AREA_CRS = "EPSG:32644"
MAP_CRS = "EPSG:4326"
SHAPEFILE_OUTPUT = Path("spray_zones.shp")
MAP_OUTPUT = Path("spray_zones_map.html")


def combined_geometry(geometries):
    """Return one combined shapely geometry across GeoPandas/Shapely versions."""
    if hasattr(geometries, "union_all"):
        return geometries.union_all()
    return geometries.unary_union


def main():
    # Multispectral orthomosaics store each wavelength as a separate raster band;
    # NDVI only needs the red band and near-infrared band.
    with rasterio.open(INPUT_FILE) as src:
        red = src.read(3).astype("float32")
j        transform = src.transform
        crs = src.crs
        nodata = src.nodata

        print(f"Number of bands: {src.count}")
        print(f"CRS: {crs}")
        print(f"Nodata value: {nodata}")
        print(f"Pixel dimensions: {src.width} columns x {src.height} rows")

    # Nodata pixels are not real crop measurements, so they must be excluded
    # before calculating vegetation health indices.
    if nodata is not None:
        if np.isnan(nodata):
            red[np.isnan(red)] = np.nan
            nir[np.isnan(nir)] = np.nan
        else:
            red[red == nodata] = np.nan
            nir[nir == nodata] = np.nan

    # NDVI compares near-infrared reflectance with red reflectance; healthy
    # vegetation usually reflects more NIR and absorbs more red light.
    with np.errstate(divide="ignore", invalid="ignore"):
        ndvi = (nir - red) / (nir + red)
    ndvi[np.isinf(ndvi)] = np.nan

    valid_ndvi = ndvi[~np.isnan(ndvi)]
    if valid_ndvi.size == 0:
        print("Error: No valid NDVI pixels were found after nodata masking.")
        sys.exit(0)

    ndvi_min = float(np.nanmin(valid_ndvi))
    ndvi_max = float(np.nanmax(valid_ndvi))
    ndvi_mean = float(np.nanmean(valid_ndvi))
    percentiles = np.nanpercentile(valid_ndvi, [10, 25, 50, 75, 90])

    print(f"NDVI min: {ndvi_min:.4f}")
    print(f"NDVI max: {ndvi_max:.4f}")
    print(f"NDVI mean: {ndvi_mean:.4f}")
    print("NDVI percentile distribution:")
    print(f"  10th: {percentiles[0]:.4f}")
    print(f"  25th: {percentiles[1]:.4f}")
    print(f"  50th: {percentiles[2]:.4f}")
    print(f"  75th: {percentiles[3]:.4f}")
    print(f"  90th: {percentiles[4]:.4f}")

    # The spray mask turns continuous NDVI values into a simple prescription:
    # 1 means stressed vegetation below the threshold, 0 means no spray needed.
    valid_mask = ~np.isnan(ndvi)
    spray_mask = np.where(valid_mask & (ndvi < SPRAY_THRESHOLD), 1, 0).astype(
        "uint8"
    )

    valid_pixel_count = int(valid_mask.sum())
    spray_pixel_count = int(spray_mask.sum())
    spray_percentage = (spray_pixel_count / valid_pixel_count) * 100

    print(f"Valid pixels flagged for spraying: {spray_percentage:.2f}%")
    if spray_percentage == 0 or spray_percentage == 100:
        print(
            "Warning: 0% or 100% of valid pixels were flagged for spraying. "
            "Thresholds may need adjustment; check the Step 3 percentile "
            "distribution."
        )

    # Raster masks are grid-based, but drone mission software usually consumes
    # vector polygons, so the spray pixels are converted to geographic shapes.
    geometries = []
    for geometry, value in shapes(
        spray_mask, mask=spray_mask == 1, transform=transform
    ):
        if value == 1:
            geometries.append(shape(geometry))

    if not geometries:
        print("Error: No spray-required polygons were created from the mask.")
        sys.exit(0)

    # A GeoDataFrame attaches coordinate reference information and attributes
    # to the spray polygons so they can be analyzed and exported as GIS data.
    spray_gdf = gpd.GeoDataFrame(geometry=geometries, crs=crs)
    spray_gdf["zone"] = "spray_required"

    # Dissolving merges touching spray pixels into larger operational zones;
    # projecting to UTM lets area be measured in metres instead of degrees.
    dissolved_gdf = spray_gdf.dissolve(by="zone").reset_index()
    dissolved_gdf = dissolved_gdf.explode(index_parts=False).reset_index(drop=True)

    if dissolved_gdf.crs is None:
        print("Error: Source raster has no CRS, so spray zone area cannot be trusted.")
        sys.exit(0)

    area_gdf = dissolved_gdf
    if area_gdf.crs.is_geographic:
        area_gdf = area_gdf.to_crs(AREA_CRS)

    area_ha = area_gdf.geometry.area / 10000
    dissolved_gdf["area_ha"] = area_ha.round(2).to_numpy()

    total_zones = len(dissolved_gdf)
    total_area_ha = float(area_ha.sum())
    print(f"Total number of spray zones: {total_zones}")
    print(f"Total spray area: {total_area_ha:.2f} hectares")

    # WGS84 is a web-map-friendly CRS, so the polygons are reprojected before
    # exporting and displaying them in Folium.
    map_gdf = dissolved_gdf.to_crs(MAP_CRS)
    map_gdf.to_file(SHAPEFILE_OUTPUT)
    print(f"Shapefile saved: {SHAPEFILE_OUTPUT}")

    # The map centers on the combined spray-zone geometry and overlays the
    # prescription zones on satellite imagery for visual field inspection.
    spray_union = combined_geometry(map_gdf.geometry)
    centroid = spray_union.centroid

    spray_map = folium.Map(
        location=[centroid.y, centroid.x],
        zoom_start=17,
        tiles=None,
    )
    folium.TileLayer(
        tiles=(
            "https://server.arcgisonline.com/ArcGIS/rest/services/"
            "World_Imagery/MapServer/tile/{z}/{y}/{x}"
        ),
        attr="Esri",
        name="Satellite",
    ).add_to(spray_map)
    folium.GeoJson(
        map_gdf,
        name="Spray Zones",
        style_function=lambda _feature: {
            "fillColor": "#d73027",
            "fillOpacity": 0.4,
            "color": "#d73027",
            "weight": 1,
        },
        tooltip=folium.GeoJsonTooltip(
            fields=["area_ha"],
            aliases=["Spray Area (ha):"],
        ),
    ).add_to(spray_map)
    folium.LayerControl().add_to(spray_map)

    # This floating title box explains the map symbology directly on the web
    # map so a drone operator can interpret the prescription layer quickly.
    title_html = """
<div style="position: fixed; top: 10px; right: 10px; z-index: 1000;
background-color: white; padding: 10px 14px; border-radius: 8px;
border: 1px solid #ccc; font-family: Arial; font-size: 13px;
box-shadow: 2px 2px 6px rgba(0,0,0,0.2);">
<b>Drone Spray Zone Analysis</b><br>
Dataset: Agricultural Field Trial (ODM)<br>
NDVI Threshold: &lt; 0.3 = Spray Required<br>
<span style="color:#d73027;">&#9632;</span> Spray Required Zone
</div>
"""
    spray_map.get_root().html.add_child(folium.Element(title_html))
    spray_map.save(MAP_OUTPUT)
    print(f"Map saved: {MAP_OUTPUT}")

    # A final summary collects the core processing choices and output files so
    # the prescription run is easy to review after the script finishes.
    print("\nSummary")
    print("-------")
    print("Input file: EX1_5Band.tif")
    print(f"NDVI threshold used: {SPRAY_THRESHOLD}")
    print(f"Total spray zones identified: {total_zones}")
    print(f"Total area requiring spraying: {total_area_ha:.2f} hectares")
    print(f"Outputs: {SHAPEFILE_OUTPUT}, {MAP_OUTPUT}")


if __name__ == "__main__":
    main()
