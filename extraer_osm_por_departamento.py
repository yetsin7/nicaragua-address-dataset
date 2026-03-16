import os
import re
import json
import zipfile
import tempfile
import osmium
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

# -----------------------------
# RUTAS
# -----------------------------
BASE_DIR = r"C:\Dev\nicaragua-address-dataset"
PBF_FILE = os.path.join(BASE_DIR, "nicaragua-260314.osm.pbf")
ADM1_ZIP_FILE = os.path.join(BASE_DIR, "geoBoundaries-NIC-ADM1-all.zip")
OUTPUT_DIR = os.path.join(BASE_DIR, "departamentos")

# Tipos de lugares que sí interesan
TIPOS_VALIDOS = {
    "city",
    "town",
    "village",
    "hamlet",
    "suburb",
    "neighbourhood"
}

# Columnas posibles donde suele venir el nombre del departamento
CANDIDATAS_NOMBRE_DEPTO = [
    "shapeName",
    "ADM1_NAME",
    "admin1Name",
    "name",
    "NAME_1",
    "adm1_es",
    "adm1_name"
]

lugares = []


class LugarHandler(osmium.SimpleHandler):
    def node(self, n):
        try:
            if "place" not in n.tags or "name" not in n.tags:
                return

            tipo = n.tags.get("place")
            if tipo not in TIPOS_VALIDOS:
                return

            if not n.location.valid():
                return

            lugares.append({
                "osm_id": f"node/{n.id}",
                "nombre": n.tags.get("name"),
                "tipo_localidad": tipo,
                "latitud": n.location.lat,
                "longitud": n.location.lon
            })
        except Exception:
            pass


def slugify(text: str) -> str:
    text = text.strip().lower()
    reemplazos = {
        "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "ü": "u", "ñ": "n"
    }
    for k, v in reemplazos.items():
        text = text.replace(k, v)
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text


def detectar_columna_nombre(gdf: gpd.GeoDataFrame) -> str:
    cols = set(gdf.columns)
    for c in CANDIDATAS_NOMBRE_DEPTO:
        if c in cols:
            return c
    raise ValueError(
        "No encontré una columna con el nombre del departamento. "
        f"Columnas disponibles: {list(gdf.columns)}"
    )


def buscar_archivo_geografico_extraido(carpeta_extraida: str) -> str:
    candidatos = []

    for root, _, files in os.walk(carpeta_extraida):
        for file in files:
            lower = file.lower()
            if lower.endswith(".geojson") or lower.endswith(".shp"):
                candidatos.append(os.path.join(root, file))

    if not candidatos:
        raise FileNotFoundError(
            "No encontré ningún archivo .geojson o .shp dentro del ZIP ADM1."
        )

    # Priorizar geojson
    geojsons = [f for f in candidatos if f.lower().endswith(".geojson")]
    if geojsons:
        return geojsons[0]

    return candidatos[0]


def nombre_carpeta_departamento(nombre: str) -> str:
    nombre_slug = slugify(nombre)

    mapa = {
        "boaco": "boaco",
        "carazo": "carazo",
        "chinandega": "chinandega",
        "chontales": "chontales",
        "esteli": "esteli",
        "granada": "granada",
        "jinotega": "jinotega",
        "leon": "leon",
        "madriz": "madriz",
        "managua": "managua",
        "masaya": "masaya",
        "matagalpa": "matagalpa",
        "nueva-segovia": "nueva-segovia",
        "rio-san-juan": "rio-san-juan",
        "rivas": "rivas",
        "region-autonoma-de-la-costa-caribe-norte": "region-autonoma-de-la-costa-caribe-norte-RACCN",
        "region-autonoma-costa-caribe-norte": "region-autonoma-de-la-costa-caribe-norte-RACCN",
        "raccn": "region-autonoma-de-la-costa-caribe-norte-RACCN",
        "region-autonoma-de-la-costa-caribe-sur": "region-autonoma-de-la-costa-caribe-sur-RACCS",
        "region-autonoma-costa-caribe-sur": "region-autonoma-de-la-costa-caribe-sur-RACCS",
        "raccs": "region-autonoma-de-la-costa-caribe-sur-RACCS",
    }

    return mapa.get(nombre_slug, nombre_slug)


def nombre_archivo_departamento(carpeta_depto: str) -> str:
    return f"{carpeta_depto}-nicaragua.json"


def main():
    print("Verificando archivos...")

    if not os.path.exists(PBF_FILE):
        raise FileNotFoundError(f"No existe el PBF: {PBF_FILE}")

    if not os.path.exists(ADM1_ZIP_FILE):
        raise FileNotFoundError(f"No existe el ZIP ADM1: {ADM1_ZIP_FILE}")

    if not os.path.exists(OUTPUT_DIR):
        raise FileNotFoundError(f"No existe la carpeta de salida: {OUTPUT_DIR}")

    print("Extrayendo lugares del .pbf...")
    handler = LugarHandler()
    handler.apply_file(PBF_FILE)

    if not lugares:
        print("No se extrajeron lugares.")
        return

    print(f"Lugares extraídos: {len(lugares)}")

    print("Creando GeoDataFrame de puntos...")
    df = pd.DataFrame(lugares)
    gdf_points = gpd.GeoDataFrame(
        df,
        geometry=[Point(xy) for xy in zip(df["longitud"], df["latitud"])],
        crs="EPSG:4326"
    )

    print("Extrayendo y leyendo límites ADM1 desde ZIP...")
    with tempfile.TemporaryDirectory() as temp_dir:
        with zipfile.ZipFile(ADM1_ZIP_FILE, "r") as zip_ref:
            zip_ref.extractall(temp_dir)

        adm1_file = buscar_archivo_geografico_extraido(temp_dir)
        print(f"Archivo geográfico encontrado: {adm1_file}")

        gdf_adm1 = gpd.read_file(adm1_file)

    # Asegurar mismo CRS
    if gdf_adm1.crs is None:
        gdf_adm1 = gdf_adm1.set_crs("EPSG:4326")
    elif gdf_adm1.crs != gdf_points.crs:
        gdf_adm1 = gdf_adm1.to_crs(gdf_points.crs)

    col_depto = detectar_columna_nombre(gdf_adm1)
    print(f"Columna detectada para nombre de departamento: {col_depto}")

    # Dejar solo nombre + geometría
    gdf_adm1 = gdf_adm1[[col_depto, "geometry"]].copy()
    gdf_adm1 = gdf_adm1.rename(columns={col_depto: "departamento"})

    print("Haciendo cruce espacial...")
    unidos = gpd.sjoin(gdf_points, gdf_adm1, how="left", predicate="within")

    cols_finales = [
        "osm_id", "nombre", "tipo_localidad",
        "latitud", "longitud", "departamento"
    ]
    unidos = unidos[cols_finales].copy()
    unidos["departamento"] = unidos["departamento"].fillna("SIN_DEPARTAMENTO")

    print("Guardando archivos por departamento dentro de /departamentos...")
    total_archivos = 0

    for depto, grupo in unidos.groupby("departamento"):
        if depto == "SIN_DEPARTAMENTO":
            print("Saltando registros sin departamento.")
            continue

        carpeta_depto = nombre_carpeta_departamento(depto)
        ruta_carpeta_depto = os.path.join(OUTPUT_DIR, carpeta_depto)
        os.makedirs(ruta_carpeta_depto, exist_ok=True)

        registros = grupo.to_dict(orient="records")

        salida = {
            "departamento": depto,
            "total_registros": len(registros),
            "lugares": registros
        }

        nombre_archivo = nombre_archivo_departamento(carpeta_depto)
        output_path = os.path.join(ruta_carpeta_depto, nombre_archivo)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(salida, f, ensure_ascii=False, indent=2)

        print(f"Generado: {output_path} ({len(registros)} registros)")
        total_archivos += 1

    print(f"\nProceso completado. Archivos generados: {total_archivos}")
    print(f"Carpeta de salida: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()