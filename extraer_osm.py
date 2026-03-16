import os
import json
import osmium

# Ruta completa del archivo .pbf
PBF_FILE = r"C:\Dev\nicaragua-address-dataset\nicaragua-260314.osm.pbf"
OUTPUT_FILE = r"C:\Dev\nicaragua-address-dataset\lugares_nicaragua.json"

lugares = []


class LugarHandler(osmium.SimpleHandler):
    def node(self, n):
        try:
            if 'place' in n.tags and 'name' in n.tags:
                if n.location.valid():
                    lugares.append({
                        "nombre": n.tags.get("name"),
                        "tipo": n.tags.get("place"),
                        "latitud": n.location.lat,
                        "longitud": n.location.lon
                    })
        except Exception:
            pass


def main():
    print(f"Buscando archivo: {PBF_FILE}")

    if not os.path.exists(PBF_FILE):
        print("ERROR: No se encontró el archivo .pbf")
        print("Verifica que exista exactamente aquí:")
        print(PBF_FILE)
        return

    print("Archivo encontrado. Iniciando extracción...")

    handler = LugarHandler()
    handler.apply_file(PBF_FILE)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(lugares, f, indent=2, ensure_ascii=False)

    print(f"Listo. Archivo generado: {OUTPUT_FILE}")
    print(f"Total de lugares extraídos: {len(lugares)}")


if __name__ == "__main__":
    main()