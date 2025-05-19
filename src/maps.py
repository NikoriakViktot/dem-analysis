
import os
from pathlib import Path
import rasterio
import matplotlib.pyplot as plt
from rasterio.plot import show
from tqdm import tqdm

# --- Шляхи ---
clipped_dir = Path("data_clipped")  # ← папка з обрізаними DEM
output_fig_dir = Path("maps")       # ← куди зберігати PNG
output_fig_dir.mkdir(exist_ok=True)

# --- Пошук .tif ---
tif_paths = list(clipped_dir.rglob("*.tif"))

# --- Обхід та візуалізація ---
for tif_path in tqdm(tif_paths, desc="Генерація мап"):
    try:
        with rasterio.open(tif_path) as src:
            fig, ax = plt.subplots(figsize=(8, 6))
            show(src, ax=ax, cmap='terrain')
            ax.set_title(tif_path.stem)
            ax.axis('off')

            # Збереження
            out_fig_path = output_fig_dir / f"{tif_path.stem}.png"
            plt.savefig(out_fig_path, bbox_inches='tight')
            plt.close()

    except Exception as e:
        print(f"❌ Помилка при обробці {tif_path.name}: {e}")

print("✅ Готово! Усі карти збережено в папку 'maps'")
