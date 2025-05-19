import numpy as np
import rasterio
from rasterio.transform import from_origin
from pyproj import Transformer


class QuasigeoidModel:
    def __init__(self, ascii_path, temp_tif="quasigeoid_tmp.tif"):
        """
        Ініціалізація моделі: з ASCII-файлу створюється тимчасовий GeoTIFF
        """
        self.ascii_path = ascii_path
        self.tif_path = temp_tif
        self.dataset = None

        self._ascii_to_geotiff()
        self._load_geotiff()

    def _ascii_to_geotiff(self):
        with open(self.ascii_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

        # 🧭 Правильна інтерпретація:
        lat_min, lat_max = map(float, lines[0].strip().split())  # широта (Y)
        lon_min, lon_max = map(float, lines[1].strip().split())  # довгота (X)
        lat_step, lon_step = map(float, lines[2].strip().split())

        # Розміри сітки
        n_rows = int(round((lat_max - lat_min) / lat_step)) + 1
        n_cols = int(round((lon_max - lon_min) / lon_step)) + 1

        print(f"📐 Розмір сітки (рядки x стовпці): {n_rows} x {n_cols}")

        # Зчитування значень
        raw_values = " ".join(lines[3:]).split()
        cleaned_values = []
        for v in raw_values:
            try:
                cleaned_values.append(float(v))
            except ValueError:
                print(f"⚠️ Пропущено некоректне значення: {repr(v)}")
                continue

        flat_array = np.array(cleaned_values)

        if len(flat_array) != n_rows * n_cols:
            raise ValueError(f"❌ Очікувано {n_rows * n_cols} значень, а отримано {len(flat_array)}")

        array = flat_array.reshape((n_rows, n_cols))  # Без перевороту!

        # 🌍 Географічна трансформація (верхня ліва точка — північний захід)
        transform = from_origin(
            west=lon_min,
            north=lat_max,
            xsize=lon_step,
            ysize=lat_step  # бо пікселі "йдуть вниз"
        )

        with rasterio.open(
                self.tif_path, 'w',
                driver='GTiff',
                height=n_rows,
                width=n_cols,
                count=1,
                dtype=array.dtype,
                crs='EPSG:4326',
                transform=transform
        ) as dst:
            dst.write(array, 1)

    def _load_geotiff(self):
        self.dataset = rasterio.open(self.tif_path)

    def get_geoid_height(self, lon, lat, input_crs="EPSG:4326"):
        if input_crs != "EPSG:4326":
            transformer = Transformer.from_crs(input_crs, "EPSG:4326", always_xy=True)
            lon, lat = transformer.transform(lon, lat)
        value = list(self.dataset.sample([(lon, lat)]))[0][0]
        return float(value)

    def get_orthometric_height(self, lon, lat, ellipsoidal_height, input_crs="EPSG:4326"):
        geoid_height = self.get_geoid_height(lon, lat, input_crs=input_crs)
        return ellipsoidal_height - geoid_height
