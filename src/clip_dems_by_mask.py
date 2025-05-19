from pathlib import Path
import geopandas as gpd
import rasterio
from rasterio.mask import mask
from tqdm import tqdm

# --- Вхідні шляхи ---
base_dir = Path("data")
output_dir = Path("data_clipped")
mask_path = "/mnt/c/Users/5302/PycharmProjects/geoid/data/basin_bil_cher_buf_500.gpkg"  # твоя буферна маска

# --- Читання маски ---
gdf = gpd.read_file(mask_path)
geometry = gdf.geometry.values

# --- Прохід по всіх DEM, крім raw_data ---
for dem_path in tqdm(base_dir.rglob("*.tif")):
    if "raw_data" and "icesat" in dem_path.parts:
        continue  # пропускаємо raw_data

    rel_path = dem_path.relative_to(base_dir)
    out_path = output_dir / rel_path
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with rasterio.open(dem_path) as src:
        try:
            clipped_image, clipped_transform = mask(src, shapes=geometry, crop=True)
        except ValueError:
            print(f"❌ Проблема з {dem_path}")
            continue

        out_meta = src.meta.copy()
        out_meta.update({
            "height": clipped_image.shape[1],
            "width": clipped_image.shape[2],
            "transform": clipped_transform
        })

        with rasterio.open(out_path, "w", **out_meta) as dest:
            dest.write(clipped_image)

print("✅ Успішно обрізано всі DEM (окрім raw_data)")
