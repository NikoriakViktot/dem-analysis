import xdem
from pathlib import Path
from tqdm import tqdm

# === 1. Шляхи ===
base_dir = Path("/mnt/c/Users/5302/PycharmProjects/geoid/data")
geoid_tif = "/mnt/c/Users/5302/PycharmProjects/geoid/data/egg_2015.tif"

# === 2. Словник DEM-файлів і їхніх початкових вертикальних систем ===
dem_registry = {
    "alos_dem": "EGM96",
    "aster_dem": "EGM96",
    "fab_dem": "EGM08",
    "nasa_dem": "EGM96",
    "srtm_dem": "EGM96",
    "tan_dem": "Ellipsoid"
}

# === 3. Обробка кожного DEM ===
for stem, source_vcrs in tqdm(dem_registry.items(), desc="Обробка DEM"):
    # Знаходимо шлях до DEM
    dem_matches = list(base_dir.glob(f"**/{stem}.tif"))
    if not dem_matches:
        print(f"⚠️ Файл не знайдено для: {stem}")
        continue

    dem_path = dem_matches[0]
    dem = xdem.DEM(dem_path)

    # Якщо CRS відсутній, встановити WGS84
    if dem.crs is None:
        dem.set_crs("EPSG:4326")

    # === 1. Задати вихідну висотну систему ===
    try:
        dem.set_vcrs(source_vcrs)
    except Exception as e:
        print(f"❌ Помилка встановлення VCRS для {stem}: {e}")
        continue

    # === 2. Перехід до еліпсоїдних висот (якщо не Ellipsoid) ===
    try:
        dem_ellip = dem if source_vcrs == "Ellipsoid" else dem.to_vcrs("Ellipsoid")
    except Exception as e:
        print(f"❌ Помилка трансформації до Ellipsoid для {stem}: {e}")
        continue

    dem_ellip_path = dem_path.with_stem(stem + "_ellip")
    dem_ellip.save(dem_ellip_path)

    # === 3. Приведення до локального квазігеоїда ===
    try:
        dem_orth = dem_ellip.to_vcrs(geoid_tif)
        dem_orth_path = dem_path.with_stem(stem + "_orth")
        dem_orth.save(dem_orth_path)
    except Exception as e:
        print(f"❌ Помилка трансформації до локального квазігеоїда для {stem}: {e}")
        continue

    print(f"✅ {stem} успішно оброблено")
