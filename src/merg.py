# import duckdb
#
# # Твої списки:
# needed_geomorph = [
#     'alos_dem_geomorphon', 'alos_dem_landform',
#     'aster_dem_geomorphon', 'aster_dem_landform',
#     'copernicus_dеm_geomorphon', 'copernicus_dеm_landform',
#     'fab_dem_geomorphon', 'fab_dem_landform',
#     'nasa_dem_geomorphon', 'nasa_dem_landform',
#     'srtm_dem_geomorphon', 'srtm_dem_landform',
#     'tan_dem_geomorphon', 'tan_dem_landform'
# ]
#
# needed_hand = [
#     'hand_alos_dem', 'hand_aster_dem', 'hand_copernicus_dеm',
#     'hand_fab_dem', 'hand_nasa_dem', 'hand_srtm_dem', 'hand_tan_dem'
# ]
#
# con = duckdb.connect(database=':memory:')
#
# # 1. SELECT all columns from terrain (a.*), потрібні з b і c:
# geom_cols = ', '.join([f"b.{c}" for c in needed_geomorph])
# hand_cols = ', '.join([f"c.{c}" for c in needed_hand])
#
# # 2. Формуємо запит:
# con.execute(f"""
#     CREATE TABLE merged AS
#     SELECT
#         a.*,
#         {geom_cols},
#         {hand_cols}
#     FROM
#         parquet_scan('/mnt/c/Users/5302/OneDrive/PhD/paper_DEM_artickle/data/data_icesat2/icesat2_with_terrain_attributes.parquet') a
#     LEFT JOIN parquet_scan('/mnt/c/Users/5302/OneDrive/PhD/paper_DEM_artickle/data/data_icesat2/icesat2_with_geomorphons.parquet') b
#         USING (time)
#     LEFT JOIN parquet_scan('/mnt/c/Users/5302/OneDrive/PhD/paper_DEM_artickle/data/data_icesat2/icesat2_with_HAND.parquet') c
#         USING (time)
# """)
#
# con.execute("""
#     COPY merged TO '/mnt/d/merged_icesat2_needed_only.parquet' (FORMAT 'parquet')
# """)
# import duckdb
#
# con = duckdb.connect()
#
# con.execute("""
#     CREATE TABLE merged_hand AS
#     SELECT
#         a.*,
#         c.hand_alos_dem, c.hand_aster_dem, c.hand_copernicus_dеm,
#         c.hand_fab_dem, c.hand_nasa_dem, c.hand_srtm_dem, c.hand_tan_dem
#     FROM
#         parquet_scan('/mnt/c/Users/5302/OneDrive/PhD/paper_DEM_artickle/data/data_icesat2/icesat2_with_terrain_attributes.parquet') a
#     LEFT JOIN parquet_scan('/mnt/c/Users/5302/OneDrive/PhD/paper_DEM_artickle/data/data_icesat2/icesat2_with_HAND.parquet') c
#         USING (time)
# """)
#
# con.execute("""
#     COPY merged_hand TO '/mnt/d/merged_terrain_hand.parquet' (FORMAT 'parquet')
# """)
# con.execute("DROP TABLE merged_hand")
import pandas as pd
#
# needed_hand = [
#     'time',  # не забувай про ключ!
#     'hand_alos_dem', 'hand_aster_dem', 'hand_copernicus_dеm',
#     'hand_fab_dem', 'hand_nasa_dem', 'hand_srtm_dem', 'hand_tan_dem'
# ]
#
# hand_small = pd.read_parquet(
#     '/mnt/c/Users/5302/OneDrive/PhD/paper_DEM_artickle/data/data_icesat2/icesat2_with_HAND.parquet',
#     columns=needed_hand
# )
# hand_small.to_parquet('/mnt/c/Users/5302/OneDrive/PhD/paper_DEM_artickle/data/data_icesat2/HAND_only_needed.parquet')


# needed_geomorph = [
#     'time',
#     'alos_dem_geomorphon', 'alos_dem_landform',
#     'aster_dem_geomorphon', 'aster_dem_landform',
#     'copernicus_dеm_geomorphon', 'copernicus_dеm_landform',
#     'fab_dem_geomorphon', 'fab_dem_landform',
#     'nasa_dem_geomorphon', 'nasa_dem_landform',
#     'srtm_dem_geomorphon', 'srtm_dem_landform',
#     'tan_dem_geomorphon', 'tan_dem_landform'
# ]
#
# geomorph_small = pd.read_parquet(
#     '/mnt/c/Users/5302/OneDrive/PhD/paper_DEM_artickle/data/data_icesat2/icesat2_with_geomorphons.parquet',
#     columns=needed_geomorph
# )
# geomorph_small.to_parquet('/mnt/c/Users/5302/OneDrive/PhD/paper_DEM_artickle/data/data_icesat2/geomorphons_only_needed.parquet')
#

terrain = pd.read_parquet('/mnt/c/Users/5302/OneDrive/PhD/paper_DEM_artickle/data/data_icesat2/icesat2_with_terrain_attributes.parquet')

hand = pd.read_parquet('/mnt/c/Users/5302/OneDrive/PhD/paper_DEM_artickle/data/data_icesat2/HAND_only_needed.parquet')
geomorph = pd.read_parquet('/mnt/c/Users/5302/OneDrive/PhD/paper_DEM_artickle/data/data_icesat2/geomorphons_only_needed.parquet')

# Join по time (додаємо унікальні колонки)
result = terrain.set_index('time')
result = result.join(hand.set_index('time'), how='left')
result = result.join(geomorph.set_index('time'), how='left')


result.to_parquet('/mnt/c/Users/5302/OneDrive/PhD/paper_DEM_artickle/data/data_icesat2/merged_only_needed.parquet')
