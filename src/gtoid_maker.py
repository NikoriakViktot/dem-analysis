import rasterio
print("✅ Rasterio працює:", rasterio.__version__)

from pyproj import CRS
print("✅ pyproj CRS:", CRS.from_epsg(4326))




from quasigeoid_model import QuasigeoidModel

model = QuasigeoidModel("egg2015_evrs2007_fmt")

import matplotlib.pyplot as plt

with rasterio.open("quasigeoid_tmp.tif") as src:
    data = src.read(1)
    extent = [
        src.bounds.left,
        src.bounds.right,
        src.bounds.bottom,
        src.bounds.top
    ]
    plt.imshow(data, cmap='viridis', extent=extent, origin='upper')
    plt.title("Карта квазігеоїда")
    plt.colorbar(label="Undulation (m)")
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.show()


height = model.get_geoid_height(lon=30.52, lat=50.45)  # наприклад, Київ
print(f"📍 Геоїдна висота в Києві: {height:.3f} м")
H = model.get_orthometric_height(
    lon=30.52,
    lat=50.45,
    ellipsoidal_height=200.0
)
print(f"📍 Ортометрична висота в Києві: {H:.3f} м")
