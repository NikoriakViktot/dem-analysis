from pathlib import Path
import geopandas as gpd
import rasterio
import numpy as np

# 1. Дані з ICESat-2 (або будь-який набір точок)
icesat_path = Path("/mnt/c/Users/5302/OneDrive/PhD/paper_DEM_artickle/data/data_icesat2/icesat2_with_lulc.parquet")
ice_gdf = gpd.read_parquet(icesat_path)
coords = [(geom.x, geom.y) for geom in ice_gdf.geometry]

# 2. Формуємо списки файлів
attr_folder = Path("/mnt/c/Users/5302/OneDrive/PhD/paper_DEM_artickle/data/DATA_UTM/dem/terrain_attributes")
geomorphon_folder = Path("/mnt/c/Users/5302/OneDrive/PhD/paper_DEM_artickle/data/DATA_UTM/dem/geomorphons")
hand_folder = Path("/mnt/c/Users/5302/OneDrive/PhD/paper_DEM_artickle/data/DATA_UTM/dem/hand_outputs")
distance_folder = Path("/mnt/c/Users/5302/OneDrive/PhD/paper_DEM_artickle/data/DATA_UTM/dem/distance_to_stream")
twi_folder = Path("/mnt/c/Users/5302/OneDrive/PhD/paper_DEM_artickle/data/DATA_UTM/dem/flow_TWI")

attr_paths = sorted(attr_folder.glob("*.tif"))
geomorphon_paths = sorted(geomorphon_folder.glob("*_geomorphons.tif"))
hand_paths = sorted(hand_folder.glob("*_hand_2000.tif"))
dist_paths = sorted(distance_folder.glob("*_distance_to_stream.tif"))
twi_paths = sorted(twi_folder.glob("*_twi.tif"))

landform_names = {
    1: "Flat", 2: "Peak", 3: "Ridge", 4: "Shoulder", 5: "Spur",
    6: "Slope", 7: "Hollow", 8: "Footslope", 9: "Valley", 10: "Pit"
}
important_attributes = {"slope"} #"curvature", "tpi", "tri", "roughness", "aspect"

filtered_attr_paths = [p for p in attr_paths if any(attr in p.stem for attr in important_attributes)]

all_paths = filtered_attr_paths + geomorphon_paths + hand_paths + dist_paths + twi_paths

for path in all_paths:
    filename = path.stem
    with rasterio.open(path) as src:
        print("____",filename)
        # Перевірка CRS!
        assert src.crs == ice_gdf.crs, f"❌ CRS не збігається: {src.crs} vs {ice_gdf.crs}"

        # --- sample_gen застосовується до кожної точки
        sampled = list(src.sample(coords))

        if "geomorphons" in filename:
            dem_name = "_".join(filename.split("_")[:2])
            col_class = f"{dem_name}_geomorphon"
            col_name = f"{dem_name}_landform"
            geomorph_classes = [val[0] if val and val[0] > 0 else np.nan for val in sampled]
            geomorph_names = [
                landform_names.get(int(v), None) if not np.isnan(v) else None for v in geomorph_classes
            ]
            ice_gdf[col_class] = geomorph_classes
            ice_gdf[col_name] = geomorph_names
            print(f"🧭 Geomorphons: {col_class}, {col_name}")

        else:
            parts = filename.split("_")
            dem_name = "_".join(parts[:2])
            attribute = parts[-1]
            col_name = f"{dem_name}_{attribute}"
            values = [val[0] if val and val[0] != src.nodata else np.nan for val in sampled]
            ice_gdf[col_name] = values
            print(f"📌 Додано: {col_name}")

# Зберігаємо результат
final_out = "/mnt/c/Users/5302/OneDrive/PhD/paper_DEM_artickle/data/data_icesat2/icesat2_features_for_model.parquet"
ice_gdf.to_parquet(final_out)
print(f"📦 Збережено до: {final_out}")

# from rasterio.transform import rowcol
# from pathlib import Path
# import geopandas as gpd
# import rasterio
# import numpy as np
#
# def sample_dem_ram(dem_array, transform, nodata, coords):
#     # Векторизовано отримуємо індекси пікселів
#     xs, ys = zip(*coords)
#     rows, cols = rowcol(transform, xs, ys)
#     rows = np.array(rows)
#     cols = np.array(cols)
#
#     mask = (
#         (rows >= 0) & (rows < dem_array.shape[0]) &
#         (cols >= 0) & (cols < dem_array.shape[1])
#     )
#     vals = np.full(len(rows), np.nan)
#     vals[mask] = dem_array[rows[mask], cols[mask]]
#     if nodata is not None:
#         vals[vals == nodata] = np.nan
#     return vals
#
#
# # 1. Дані з ICESat-2 (або будь-який набір точок)
# icesat_path = Path("/mnt/c/Users/5302/OneDrive/PhD/paper_DEM_artickle/data/data_icesat2/icesat2_with_lulc.parquet")
# ice_gdf = gpd.read_parquet(icesat_path)
# coords = [(geom.x, geom.y) for geom in ice_gdf.geometry]
#
# # 2. Формуємо списки файлів
# attr_folder = Path("/mnt/c/Users/5302/OneDrive/PhD/paper_DEM_artickle/data/DATA_UTM/dem/terrain_attributes")
# geomorphon_folder = Path("/mnt/c/Users/5302/OneDrive/PhD/paper_DEM_artickle/data/DATA_UTM/dem/geomorphons")
# hand_folder = Path("/mnt/c/Users/5302/OneDrive/PhD/paper_DEM_artickle/data/DATA_UTM/dem/hand_outputs")
# distance_folder = Path("/mnt/c/Users/5302/OneDrive/PhD/paper_DEM_artickle/data/DATA_UTM/dem/distance_to_stream")
# twi_folder = Path("/mnt/c/Users/5302/OneDrive/PhD/paper_DEM_artickle/data/DATA_UTM/dem/flow_TWI")
#
# attr_paths = sorted(attr_folder.glob("*.tif"))
# geomorphon_paths = sorted(geomorphon_folder.glob("*_geomorphons.tif"))
# hand_paths = sorted(hand_folder.glob("*_hand_2000.tif"))
# dist_paths = sorted(distance_folder.glob("*_distance_to_stream.tif"))
# twi_paths = sorted(twi_folder.glob("*_twi.tif"))
#
# landform_names = {
#     1: "Flat", 2: "Peak", 3: "Ridge", 4: "Shoulder", 5: "Spur",
#     6: "Slope", 7: "Hollow", 8: "Footslope", 9: "Valley", 10: "Pit"
# }
# important_attributes = {"slope", "curvature", "tpi", "tri", "roughness", "aspect"}
# filtered_attr_paths = [p for p in attr_paths if any(attr in p.stem for attr in important_attributes)]
#
# all_paths = filtered_attr_paths + geomorphon_paths + hand_paths + dist_paths + twi_paths
#
# from rasterio.transform import rowcol
#
# for path in all_paths:
#     filename = path.stem
#     with rasterio.open(path) as src:
#         dem_array = src.read(1)  # Завантажуємо ВСІ дані у RAM
#         transform = src.transform
#         nodata = src.nodata
#
#         if "geomorphons" in filename:
#             dem_name = "_".join(filename.split("_")[:2])
#             col_class = f"{dem_name}_geomorphon"
#             col_name = f"{dem_name}_landform"
#             vals = sample_dem_ram(dem_array, transform, nodata, coords)
#             geomorph_classes = [v if (not np.isnan(v) and v > 0) else np.nan for v in vals]
#             geomorph_names = [
#                 landform_names.get(int(v), None) if not np.isnan(v) else None for v in geomorph_classes
#             ]
#             ice_gdf[col_class] = geomorph_classes
#             ice_gdf[col_name] = geomorph_names
#             print(f"🧭 Geomorphons: {col_class}, {col_name}")
#
#         else:
#             parts = filename.split("_")
#             dem_name = "_".join(parts[:2])
#             attribute = parts[-1]
#             col_name = f"{dem_name}_{attribute}"
#
#             vals = sample_dem_ram(dem_array, transform, nodata, coords)
#             ice_gdf[col_name] = vals
#             print(f"📌 Додано: {col_name}")
#
# # Зберігаємо результат
# final_out = "/mnt/c/Users/5302/OneDrive/PhD/paper_DEM_artickle/data/data_icesat2/icesat2_features_for_model.parquet"
# ice_gdf.to_parquet(final_out)
# print(f"📦 Збережено до: {final_out}")
