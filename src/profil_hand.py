# -*- coding: utf-8 -*-
"""
ALL-IN-ONE (DEM + HAND → EVRS)

Функціонал:
- читає профіль (EVRS),
- визначає рівень H (EVRS),
- семплить DEM уздовж профілю (через DX),
- рахує A, P, W, Dmean, R і похибки vs. профіль,
- пише:
    cross_dem_metrics.csv
    cross_dem_verticals_2m.csv
    bed_line_xy/*.csv
    wetted_polygon_xy/*.csv
    shorelines.csv
    section_overlay.png
- HAND:
    hand_on_profile.csv
    hand_band_summary.csv
    hand_evrs_profile.csv   ← HAND переведено у EVRS (z_stream, H0/lo/hi у EVRS)
    (опц.) hand_masks/*.tif

Залежності: numpy, pandas, geopandas, rasterio, matplotlib
"""

from __future__ import annotations

import glob
import math
import unicodedata
import warnings
from pathlib import Path
from typing import Dict, Iterable, Tuple

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import rasterio


# ================== INPUTS ==================
PROFILE_GEOJSON = r"/mnt/c/Users/5302/PycharmProjects/geoid/profile_combined_evrs.geojson"

DEM_DIR = Path(r"/mnt/d/paper_data/DEM_DATA/data/DATA_UTM/dem")
DEM_PATTERNS: Dict[str, str] = {
    "alos_dem_utm32635":       "*alos*dem*32635*.tif",
    "aster_dem_utm32635":      "*aster*dem*32635*.tif",
    "copernicus_dem_utm32635": "*copernicus*dem*32635*.tif",
    "fab_dem_utm32635":        "*fab*dem*32635*.tif",
    "nasa_dem_utm32635":       "*nasa*dem*32635*.tif",
    "srtm_dem_utm32635":       "*srtm*dem*32635*.tif",
    "tan_dem_utm32635":        "*tan*dem*32635*.tif",
}
DEM_VERTICAL_OFFSETS: Dict[str, float] = {
    # приклад: "copernicus_dem_utm32635": -0.40,
}

HAND_DIR = Path(r"/mnt/d/paper_data/DEM_DATA/data/DATA_UTM/dem/HAND")
HAND_H0  = 5.6     # м над дренажем
HAND_TOL = 5.0     # ± допуск (м)
SAVE_HAND_MASKS = False

# swath (поперек профілю) — для пошуку пікселів у діапазоні HAND поруч із лінією
SWATH_HALF_WIDTH_M = 0.0   # постав 100.0, щоб увімкнути
SWATH_STEP_M       = 2.0

# Нуль поста/перехід до EVRS (коли не беремо H з GeoJSON)
NULL_POSTA_BALT  = 592.11
BALT_TO_EVRS     = 0.105
USE_H_FROM_GEOJSON = True
LEVEL_CM = 168

DX = 2.0

MAKE_PLOT = True
SOURCES_TO_PLOT = ["profile_evrs", "srtm_dem_utm32635", "copernicus_dem_utm32635", "aster_dem_utm32635"]


# ================== OUTPUTS ==================
OUT_DIR   = Path(r"/mnt/c/Users/5302/PycharmProjects/geoid/cross_dem_out_HAND")
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_SUM   = OUT_DIR / "cross_dem_metrics.csv"
OUT_VERT  = OUT_DIR / "cross_dem_verticals_2m.csv"
LINES_DIR = OUT_DIR / "plot_lines";    LINES_DIR.mkdir(exist_ok=True)
POLYS_DIR = OUT_DIR / "plot_polygons"; POLYS_DIR.mkdir(exist_ok=True)
SHORE_CSV = OUT_DIR / "shorelines.csv"
PLOT_PNG  = OUT_DIR / "section_overlay.png"

OUT_HAND_PROF = OUT_DIR / "hand_on_profile.csv"
OUT_HAND_SUM  = OUT_DIR / "hand_band_summary.csv"
HAND_MASK_DIR = OUT_DIR / "hand_masks"
OUT_HAND_EVRS = OUT_DIR / "hand_evrs_profile.csv"


# ================== HELPERS ==================
def _normalize(s: str) -> str:
    return unicodedata.normalize("NFKC", s).lower()


def discover_files(base_dir: Path, patterns: Dict[str, str]) -> Dict[str, str]:
    """Повертає {label: path} для перших знайдених GeoTIFF за шаблонами/евристикою."""
    all_tifs = [Path(p) for p in glob.glob(str(base_dir / "*.tif"))]
    res: Dict[str, str] = {}
    for label, pat in patterns.items():
        cand = [Path(p) for p in glob.glob(str(base_dir / pat))]
        if not cand:
            want = _normalize(label).split("_")
            for p in all_tifs:
                if all(tok in _normalize(p.name) for tok in want):
                    cand.append(p)
                    break
        if cand:
            res[label] = str(cand[0])
    return res


def discover_hands(hand_dir: Path, dem_map: Dict[str, str]) -> Dict[str, str]:
    """Підбирає HAND-растр для кожного DEM-лейбла."""
    all_tifs = [Path(p) for p in glob.glob(str(hand_dir / "*.tif"))]
    res: Dict[str, str] = {}
    for label in dem_map.keys():
        pats = [f"*{label}*hand*.tif", f"*{label.replace('dem', 'dem*hand')}*.tif"]
        cand: list[Path] = []
        for pat in pats:
            cand = [Path(p) for p in glob.glob(str(hand_dir / pat))]
            if cand:
                break
        if not cand:
            want = _normalize(label).split("_") + ["hand"]
            for p in all_tifs:
                if all(tok in _normalize(p.name) for tok in want):
                    cand.append(p)
                    break
        if cand:
            res[label] = str(cand[0])
    return res


def interp_unique(x: Iterable[float], y: Iterable[float], xg: np.ndarray) -> np.ndarray:
    """Монотонізує x, прибирає дублікати, інтерполює y(x) → y(xg)."""
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    o = np.argsort(x)
    x = x[o]; y = y[o]
    m = np.concatenate(([True], np.diff(x) > 1e-9))
    return np.interp(xg, x[m], y[m])


def sample_raster_lonlat(path: str, lon: np.ndarray, lat: np.ndarray) -> np.ndarray:
    """Семплінг растра у довільних lon/lat через reprojection до CRS растру."""
    with rasterio.open(path) as src:
        pts = gpd.GeoSeries(gpd.points_from_xy(lon, lat), crs=4326).to_crs(src.crs)
        xs, ys = pts.x.to_numpy(), pts.y.to_numpy()
        vals = list(src.sample(zip(xs, ys)))
        arr = np.array([v[0] if len(v) > 0 else np.nan for v in vals], float)
        if src.nodata is not None:
            arr = np.where(np.isclose(arr, src.nodata), np.nan, arr)
        return arr


def safe_naninterp(arr: np.ndarray) -> np.ndarray:
    """Заповнення NaN лінійною інтерполяцією (в обидва боки)."""
    s = pd.Series(arr, dtype="float64")
    return s.interpolate(limit_direction="both").to_numpy()


def wetted_metrics(xg: np.ndarray, zg: np.ndarray, H: float) -> Tuple[float, float, float, float, float, np.ndarray]:
    """A, P, W, Dmean, R + вектор глибин уздовж перерізу."""
    xg = np.asarray(xg, float)
    zg = np.asarray(zg, float)
    d = np.maximum(H - zg, 0.0)
    dx = np.diff(xg)

    A = np.sum((d[:-1] + d[1:]) * 0.5 * dx)
    W = np.sum(dx * ((d[:-1] > 0) | (d[1:] > 0)))

    P = 0.0
    for i in range(len(dx)):
        z0, z1 = zg[i], zg[i + 1]
        below0 = z0 < H
        below1 = z1 < H
        if below0 and below1:
            P += math.hypot(dx[i], z1 - z0)
        elif below0 != below1:
            t = (H - z0) / (z1 - z0)
            t = float(np.clip(t, 0.0, 1.0))
            if below0:
                dz = (z0 + t * (z1 - z0)) - z0
                P += math.hypot(dx[i] * t, dz)
            else:
                dz = z1 - (z0 + t * (z1 - z0))
                P += math.hypot(dx[i] * (1 - t), dz)

    Dmean = A / W if W > 0 else 0.0
    R = A / P if P > 0 else 0.0
    return A, P, W, Dmean, R, d


def wetted_polygon_xy(x: np.ndarray, z: np.ndarray, H: float) -> Tuple[np.ndarray, Tuple[float, float]]:
    """Повертає полігон змоченої частини (x,z) та (xL,xR) берегові межі."""
    x = np.asarray(x, float)
    z = np.asarray(z, float)
    n = len(x)
    if n < 2:
        return np.empty((0, 2)), (np.nan, np.nan)
    below = z < H
    if not below.any():
        return np.empty((0, 2)), (np.nan, np.nan)
    if below.all():
        xs = np.r_[x[0], x, x[-1], x[0]]
        zs = np.r_[H, z, H, H]
        return np.column_stack([xs, zs]), (x[0], x[-1])

    def edge_x(i0, i1):
        z0, z1 = z[i0], z[i1]
        t = float(np.clip((H - z0) / (z1 - z0), 0.0, 1.0))
        return x[i0] + t * (x[i1] - x[i0])

    if below[0]:
        xL = x[0]
    else:
        i = next(i for i in range(n - 1) if (z[i] - H) * (z[i + 1] - H) < 0)
        xL = edge_x(i, i + 1)

    if below[-1]:
        xR = x[-1]
    else:
        j = next(i for i in range(n - 2, -1, -1) if (z[i] - H) * (z[i + 1] - H) < 0)
        xR = edge_x(j, j + 1)

    idx = np.where((x >= min(xL, xR)) & (x <= max(xL, xR)))[0]
    xs = list(x[idx]); zs = list(z[idx])
    if len(xs) == 0 or xs[0] > xL + 1e-9:
        xs.insert(0, xL); zs.insert(0, H)
    if xs[-1] < xR - 1e-9:
        xs.append(xR);  zs.append(H)
    poly_x = [xL] + xs + [xR, xL]
    poly_z = [H]  + zs + [H,  H]
    return np.column_stack([poly_x, poly_z]), (xL, xR)


def count_band_pixels(hand_path: str, lo: float, hi: float) -> Tuple[int, float, float]:
    """Повертає (n_pixels, pixel_area_m2, total_area_m2) для HAND ∈ [lo,hi]."""
    with rasterio.open(hand_path) as src:
        arr = src.read(1, masked=True)
        valid = ~arr.mask
        in_band = valid & (arr >= lo) & (arr <= hi)
        n = int(in_band.sum())
        try:
            pix_w = abs(src.transform.a)
            pix_h = abs(src.transform.e)
            px_area = float(pix_w * pix_h)
            try:
                if not src.crs or not src.crs.is_projected:
                    px_area = np.nan
            except Exception:
                pass
        except Exception:
            px_area = np.nan
        tot_area = float(n * px_area) if np.isfinite(px_area) else np.nan
        return n, (px_area if np.isfinite(px_area) else np.nan), (tot_area if np.isfinite(tot_area) else np.nan)


def hand_to_m(arr: np.ndarray) -> Tuple[np.ndarray, float]:
    """Евристично приводить HAND до метрів (cm/dm → m). Повертає (масив_у_м, масштаб)."""
    a = np.asarray(arr, float)
    try:
        q95 = np.nanpercentile(a, 95)
    except Exception:
        q95 = np.nan
    if np.isfinite(q95) and q95 > 60:  # см
        return a * 0.01, 0.01
    if np.isfinite(q95) and q95 > 6:   # дм
        return a * 0.10, 0.10
    return a, 1.0


def sample_hand_swath_xy(
    hand_path: str,
    dem_path: str,
    xs_prof: np.ndarray,
    ys_prof: np.ndarray,
    offsets: np.ndarray,
    lo: float,
    hi: float,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Для кожного вузла профілю бере точки на нормалі на відстанях offsets (у CRS растру),
    семплить HAND і DEM, повертає:
      in_band_nearby, dist_first_m, z_stream_band_median
    """
    with rasterio.open(hand_path) as sh, rasterio.open(dem_path) as sd:
        def normals(x, y):
            dx = np.gradient(x); dy = np.gradient(y)
            L = np.hypot(dx, dy); L[L == 0] = 1.0
            nx, ny = -dy / L, dx / L
            return nx, ny

        nx, ny = normals(xs_prof, ys_prof)
        n = len(xs_prof)
        in_band_nearby = np.zeros(n, bool)
        dist_first = np.full(n, np.nan)
        z_stream_med = np.full(n, np.nan)

        for i in range(n):
            xs = xs_prof[i] + nx[i] * offsets
            ys = ys_prof[i] + ny[i] * offsets
            hvals = np.array([v[0] for v in sh.sample(zip(xs, ys))], float)
            dvals = np.array([v[0] for v in sd.sample(zip(xs, ys))], float)
            hvals[hvals == sh.nodata] = np.nan
            dvals[dvals == sd.nodata] = np.nan
            hvals, _ = hand_to_m(hvals)
            ok = np.isfinite(hvals) & np.isfinite(dvals)
            if not ok.any():
                continue
            sel = ok & (hvals >= lo) & (hvals <= hi)
            if sel.any():
                in_band_nearby[i] = True
                dist_first[i] = float(np.min(np.abs(offsets[sel])))
                z_stream = dvals[sel] - hvals[sel]
                z_stream_med[i] = float(np.nanmedian(z_stream))
        return in_band_nearby, dist_first, z_stream_med


# ================== PIPELINE ==================
def main() -> None:
    warnings.filterwarnings("ignore", category=UserWarning, module="rasterio")

    # 1) Профіль
    g = gpd.read_file(PROFILE_GEOJSON)
    kind = g.get("kind").fillna("profile_point")
    pts = g[kind == "profile_point"].copy()
    if "distance_m" not in pts.columns:
        raise ValueError("GeoJSON не має поля 'distance_m'.")
    pts = pts.sort_values("distance_m").reset_index(drop=True)

    x = pts["distance_m"].to_numpy(float)
    lon = pts.geometry.x.to_numpy(float)
    lat = pts.geometry.y.to_numpy(float)

    if "elevation_evrs_m" in pts.columns:
        z_prof = pts["elevation_evrs_m"].to_numpy(float)
    elif "elevation_m" in pts.columns:
        z_prof = pts["elevation_m"].to_numpy(float) + BALT_TO_EVRS
    else:
        raise ValueError("Немає elevation_evrs_m / elevation_m у профілі.")

    if USE_H_FROM_GEOJSON and "H_max_evrs_m" in pts.columns and pts["H_max_evrs_m"].notna().any():
        H = float(pts["H_max_evrs_m"].dropna().iloc[0])
    else:
        H = (NULL_POSTA_BALT + BALT_TO_EVRS) + LEVEL_CM / 100.0
    print(f"[INFO] H = {H:.3f} m EVRS")

    # 2) Вертикалі через DX
    xg = np.arange(x.min(), x.max() + DX, DX)
    lon_g = interp_unique(x, lon, xg)
    lat_g = interp_unique(x, lat, xg)
    zpg = interp_unique(x, z_prof, xg)

    # 3) Еталонні метрики (профіль)
    A0, P0, W0, D0, R0, d_prof = wetted_metrics(xg, zpg, H)
    rows = [{
        "source": "profile_evrs", "A_m2": A0, "P_m": P0, "W_m": W0, "D_mean_m": D0, "R_m": R0,
        "dA_vs_profile_m2": 0.0, "dP_vs_profile_m": 0.0, "rel_dA_%": 0.0, "rel_dP_%": 0.0
    }]
    verts_rec = [{"source": "profile_evrs", "x_m": xi, "bed_elev_evrs_m": zi, "depth_m": di}
                 for xi, zi, di in zip(xg, zpg, d_prof)]

    # 4) DEM-и
    dem_paths = discover_files(DEM_DIR, DEM_PATTERNS)
    print(f"[INFO] Found DEMs: {list(dem_paths.keys())}")

    for name, path in dem_paths.items():
        z_dem = sample_raster_lonlat(path, lon_g, lat_g)
        if np.all(~np.isfinite(z_dem)):
            print(f"[WARN] All NaN for DEM: {name} — skip.")
            continue
        z_dem = safe_naninterp(z_dem) + float(DEM_VERTICAL_OFFSETS.get(name, 0.0))

        A, P, W, Dm, R, d = wetted_metrics(xg, z_dem, H)
        rows.append({
            "source": name, "A_m2": A, "P_m": P, "W_m": W, "D_mean_m": Dm, "R_m": R,
            "dA_vs_profile_m2": A - A0, "dP_vs_profile_m": P - P0,
            "rel_dA_%": ((A - A0) / A0 * 100.0) if A0 > 0 else np.nan,
            "rel_dP_%": ((P - P0) / P0 * 100.0) if P0 > 0 else np.nan
        })
        verts_rec += [{"source": name, "x_m": xi, "bed_elev_evrs_m": zi, "depth_m": di}
                      for xi, zi, di in zip(xg, z_dem, d)]

    # 5) Збереження DEM-таблиць
    df_sum = pd.DataFrame(rows).sort_values("source")
    df_vert = pd.DataFrame(verts_rec)
    df_sum.to_csv(OUT_SUM, index=False)
    df_vert.to_csv(OUT_VERT, index=False)
    print("[OK] metrics   ->", OUT_SUM)
    print("[OK] verticals ->", OUT_VERT)

    # 6) Координати для графіків + береги
    shore_rows = []
    for src, d in df_vert.groupby("source"):
        d = d.sort_values("x_m")
        xx = d["x_m"].to_numpy(float)
        zz = d["bed_elev_evrs_m"].to_numpy(float)

        pd.DataFrame({"x_m": xx, "z_evrs_m": zz}).to_csv(LINES_DIR / f"{src}_bed_line_xy.csv", index=False)

        poly, (xL, xR) = wetted_polygon_xy(xx, zz, H)
        if poly.size > 0:
            pd.DataFrame({"x_m": poly[:, 0], "z_evrs_m": poly[:, 1]}) \
                .to_csv(POLYS_DIR / f"{src}_wetted_polygon_xy.csv", index=False)
        shore_rows.append({"source": src, "x_left_m": xL, "x_right_m": xR, "width_W_m": (xR - xL)})
    pd.DataFrame(shore_rows).to_csv(SHORE_CSV, index=False)
    print("[OK] lines     ->", LINES_DIR)
    print("[OK] polygons  ->", POLYS_DIR)
    print("[OK] shores    ->", SHORE_CSV)

    # 7) Оглядовий графік
    if MAKE_PLOT:
        plt.figure(figsize=(11, 5))
        for src in SOURCES_TO_PLOT:
            d = df_vert[df_vert["source"] == src].sort_values("x_m")
            if d.empty:
                continue
            plt.plot(d["x_m"], d["bed_elev_evrs_m"], label=src, linewidth=1.8)
        plt.axhline(H, ls="--", lw=1.4, label=f"H = {H:.3f} m EVRS")
        d0 = df_vert[df_vert["source"] == "profile_evrs"].sort_values("x_m")
        if not d0.empty:
            x0 = d0["x_m"].to_numpy(float)
            z0 = d0["bed_elev_evrs_m"].to_numpy(float)
            plt.fill_between(x0, z0, H, where=(z0 < H), alpha=0.30, label="water (profile)")
        plt.grid(alpha=0.25)
        plt.xlabel("Відстань вздовж профілю, м")
        plt.ylabel("Висота (EVRS), м")
        plt.title("Поперечний переріз: еталон і DEM")
        plt.legend()
        plt.tight_layout()
        plt.savefig(PLOT_PNG, dpi=160)
        print("[OK] plot     ->", PLOT_PNG)

    # 8) HAND: профіль + EVRS-прив’язка
    dem_paths = discover_files(DEM_DIR, DEM_PATTERNS)
    hand_paths = discover_hands(HAND_DIR, dem_paths)
    print(f"[INFO] Found HANDs: {list(hand_paths.keys())}")

    lo = max(0.0, HAND_H0 - HAND_TOL)
    hi = HAND_H0 + HAND_TOL
    print(f"[HAND] band: HAND ∈ [{lo:.2f}, {hi:.2f}] м (h0={HAND_H0}, tol=±{HAND_TOL})")

    hand_prof_records = []
    hand_summ_rows = []
    hand_evrs_rows = []

    if SAVE_HAND_MASKS:
        HAND_MASK_DIR.mkdir(exist_ok=True)

    for label, hand_path in hand_paths.items():
        n_pix, px_area, area_m2 = count_band_pixels(hand_path, lo, hi)

        hand_vals_raw = sample_raster_lonlat(hand_path, lon_g, lat_g)
        hand_vals, scale_used = hand_to_m(hand_vals_raw)

        dem_path = dem_paths.get(label, None)
        if dem_path is None:
            print(f"[WARN] DEM not found for HAND {label} — skip EVRS mapping")
            z_dem_line = np.full_like(hand_vals, np.nan, dtype=float)
        else:
            z_dem_line = sample_raster_lonlat(dem_path, lon_g, lat_g)
            z_dem_line = safe_naninterp(z_dem_line) + float(DEM_VERTICAL_OFFSETS.get(label, 0.0))

        z_stream = z_dem_line - hand_vals              # дренаж у EVRS
        h_at_H   = H - z_stream                        # HAND-поріг, еквівалентний H
        depth_H  = np.maximum(0.0, h_at_H - hand_vals) # «глибина за HAND» при рівні H

        in_band_prof = np.isfinite(hand_vals) & (hand_vals >= lo) & (hand_vals <= hi)
        n_prof = int(in_band_prof.sum())
        frac_prof = n_prof / float(len(hand_vals)) if len(hand_vals) > 0 else np.nan

        for xi, lo_i, la_i, hv, flag, zd, zs, hh, dH in zip(
            xg, lon_g, lat_g, hand_vals, in_band_prof, z_dem_line, z_stream, h_at_H, depth_H
        ):
            hand_prof_records.append({
                "source": label, "x_m": float(xi),
                "lon": float(lo_i), "lat": float(la_i),
                "HAND_m": float(hv) if np.isfinite(hv) else np.nan,
                "in_band": bool(flag), "band_lo_m": lo, "band_hi_m": hi
            })
            hand_evrs_rows.append({
                "source": label, "x_m": float(xi),
                "z_dem_evrs_m": float(zd) if np.isfinite(zd) else np.nan,
                "z_stream_evrs_m": float(zs) if np.isfinite(zs) else np.nan,
                "H_evrs_m": float(H),
                "H0_evrs_m": float(zs + HAND_H0) if np.isfinite(zs) else np.nan,
                "H_lo_evrs_m": float(zs + lo) if np.isfinite(zs) else np.nan,
                "H_hi_evrs_m": float(zs + hi) if np.isfinite(zs) else np.nan,
                "h_at_H_evrs_m": float(hh) if np.isfinite(hh) else np.nan,
                "depth_hand_at_H_m": float(dH) if np.isfinite(dH) else np.nan
            })

        if SAVE_HAND_MASKS:
            with rasterio.open(hand_path) as src:
                prof = src.profile
                prof.update(dtype=rasterio.uint8, nodata=0, count=1, compress="lzw")
                arr = src.read(1, masked=True)
                arr_m, _ = hand_to_m(arr.filled(np.nan))
                sel = (~np.isnan(arr_m)) & (arr_m >= lo) & (arr_m <= hi)
                mask_u8 = np.zeros(arr.shape, dtype=np.uint8)
                mask_u8[sel] = 1
                out_mask = HAND_MASK_DIR / f"{label}_hand_band_{lo:.2f}_{hi:.2f}.tif"
                with rasterio.open(out_mask, "w", **prof) as dst:
                    dst.write(mask_u8, 1)

        hand_summ_rows.append({
            "source": label, "hand_path": hand_path,
            "h0_m": HAND_H0, "tol_m": HAND_TOL,
            "band_lo_m": lo, "band_hi_m": hi,
            "n_pixels_band": n_pix, "pixel_area_m2": px_area, "area_band_m2": area_m2,
            "n_profile_pts": int(len(hand_vals)), "n_profile_in_band": n_prof,
            "profile_in_band_frac": frac_prof, "hand_scale_to_m": scale_used
        })

    # 8.3 swath (опційно)
    if SWATH_HALF_WIDTH_M > 0 and len(hand_paths) > 0:
        first_hand = next(iter(hand_paths.values()))
        with rasterio.open(first_hand) as src:
            pts_proj = gpd.GeoSeries(gpd.points_from_xy(lon_g, lat_g), crs=4326).to_crs(src.crs)
            xs_proj, ys_proj = pts_proj.x.to_numpy(), pts_proj.y.to_numpy()
            offsets = np.arange(-SWATH_HALF_WIDTH_M, SWATH_HALF_WIDTH_M + SWATH_STEP_M, SWATH_STEP_M)

        for label, hand_path in hand_paths.items():
            dem_path = dem_paths.get(label)
            if dem_path is None:
                continue
            inb, dmin, zmed = sample_hand_swath_xy(hand_path, dem_path, xs_proj, ys_proj, offsets, lo, hi)
            for xi, zs_med, hit, dd in zip(xg, zmed, inb, dmin):
                hand_evrs_rows.append({
                    "source": f"{label}__swath",
                    "x_m": float(xi),
                    "z_dem_evrs_m": np.nan,
                    "z_stream_evrs_m": float(zs_med) if np.isfinite(zs_med) else np.nan,
                    "H_evrs_m": float(H),
                    "H0_evrs_m": float(zs_med + HAND_H0) if np.isfinite(zs_med) else np.nan,
                    "H_lo_evrs_m": float(zs_med + lo) if np.isfinite(zs_med) else np.nan,
                    "H_hi_evrs_m": float(zs_med + hi) if np.isfinite(zs_med) else np.nan,
                    "h_at_H_evrs_m": float(H - zs_med) if np.isfinite(zs_med) else np.nan,
                    "depth_hand_at_H_m": np.nan,
                    "swath_hit": bool(hit),
                    "swath_nearest_dist_m": float(dd) if np.isfinite(dd) else np.nan
                })

    # 8.4 вивід HAND-результатів
    pd.DataFrame(hand_prof_records).to_csv(OUT_HAND_PROF, index=False)
    pd.DataFrame(hand_summ_rows).to_csv(OUT_HAND_SUM, index=False)
    pd.DataFrame(hand_evrs_rows).to_csv(OUT_HAND_EVRS, index=False)
    print("[OK] HAND profile  ->", OUT_HAND_PROF)
    print("[OK] HAND summary  ->", OUT_HAND_SUM)
    print("[OK] HAND (EVRS)   ->", OUT_HAND_EVRS)

    print("\n[DONE]")


if __name__ == "__main__":
    main()
