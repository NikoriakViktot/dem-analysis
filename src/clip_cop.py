
import geopandas as gpd
import rasterio
from rasterio.mask import mask
from pathlib import Path

# --- Вхідні дані ---
dem_path = Path("/mnt/c/Users/5302/PycharmProjects/geoid/data/copernicus/copernicus_dеm_ellip.tif")  # твій DEM
mask_path = Path("/mnt/c/Users/5302/PycharmProjects/geoid/data/basin_bil_cher_buf_500.gpkg")         # твоя маска
output_path = dem_path.parent / f"{dem_path.stem}_clipped.tif"                                       # куди зберегти результат

# --- Читання маски ---
gdf = gpd.read_file(mask_path)
geometry = gdf.geometry.values

# --- Обрізка DEM ---
with rasterio.open(dem_path) as src:
    clipped_image, clipped_transform = mask(src, shapes=geometry, crop=True)
    out_meta = src.meta.copy()
    out_meta.update({
        "height": clipped_image.shape[1],
        "width": clipped_image.shape[2],
        "transform": clipped_transform
    })

    # --- Збереження обрізаного DEM ---
    with rasterio.open(output_path, "w", **out_meta) as dest:
        dest.write(clipped_image)

print(f"✅ DEM обрізано та збережено до: {output_path}")