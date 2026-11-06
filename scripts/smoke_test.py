"""Smoke test de la API contra un contenedor (o servidor) en ejecución.

Uso:
    python scripts/smoke_test.py                       # http://localhost:8000
    python scripts/smoke_test.py http://localhost:8080
    BASE_URL=http://localhost:8080 python scripts/smoke_test.py

Solo usa la librería estándar, así que no hace falta instalar nada.
Devuelve código de salida 0 si todo va bien y 1 si alguna comprobación falla,
por lo que sirve tanto en local como en la CI.

Nota: crea datos (usuarios, productos, pedidos). Lánzalo contra un contenedor
recién arrancado, ya que los datos se guardan en memoria.
"""

import json
import os
import sys
import time
import urllib.error
import urllib.request

BASE_URL = (sys.argv[1] if len(sys.argv) > 1 else os.getenv("BASE_URL", "http://localhost:8000")).rstrip("/")
fallos = 0


def _leer_cuerpo(resp) -> object:
    texto = resp.read().decode()
    if texto and "json" in resp.headers.get("Content-Type", ""):
        return json.loads(texto)
    return texto or None  # p. ej. /docs devuelve HTML


def peticion(metodo: str, ruta: str, cuerpo: dict | None = None) -> tuple[int, object]:
    datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
    req = urllib.request.Request(
        BASE_URL + ruta, data=datos, method=metodo, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status, _leer_cuerpo(resp)
    except urllib.error.HTTPError as err:
        return err.code, _leer_cuerpo(err)


def comprobar(descripcion: str, condicion: bool) -> None:
    global fallos
    print(f"  [{'OK' if condicion else 'FALLO'}] {descripcion}")
    if not condicion:
        fallos += 1


def esperar_a_que_arranque(intentos: int = 30) -> None:
    for _ in range(intentos):
        try:
            if peticion("GET", "/health")[0] == 200:
                return
        except (urllib.error.URLError, ConnectionError, OSError):
            pass
        time.sleep(1)
    print(f"La API no responde en {BASE_URL}/health tras {intentos} s")
    sys.exit(1)


def main() -> None:
    print(f"Smoke test contra {BASE_URL}")
    esperar_a_que_arranque()

    estado, cuerpo = peticion("GET", "/health")
    comprobar("GET /health -> 200 y status ok", estado == 200 and cuerpo["status"] == "ok")

    estado, _ = peticion("GET", "/docs")
    comprobar("GET /docs (Swagger UI) -> 200", estado == 200)

    estado, html = peticion("GET", "/tienda/")
    comprobar("GET /tienda/ (frontend de la tienda) -> 200", estado == 200 and "Tienda Online" in (html or ""))

    estado, cliente = peticion("POST", "/usuarios", {
        "nombre": "Ana García", "email": "ana.smoke@example.com", "tipo": "cliente",
        "direccion_postal": "Calle Mayor 1, 28013 Madrid",
    })
    comprobar("POST /usuarios (cliente) -> 201", estado == 201)

    estado, _ = peticion("POST", "/usuarios", {
        "nombre": "Otra", "email": "ANA.SMOKE@example.com", "tipo": "cliente", "direccion_postal": "X",
    })
    comprobar("POST /usuarios con email repetido -> 409", estado == 409)

    estado, producto = peticion("POST", "/productos", {
        "tipo": "electronico", "nombre": "Portátil", "precio": 899.99, "stock": 10, "meses_garantia": 24,
    })
    comprobar("POST /productos (electrónico) -> 201", estado == 201)

    estado, _ = peticion("POST", "/productos", {
        "tipo": "electronico", "nombre": "TV", "precio": 1, "stock": 1,
    })
    comprobar("POST /productos sin meses_garantia -> 422", estado == 422)

    estado, pedido = peticion("POST", "/pedidos", {
        "cliente_id": cliente["id"], "items": [{"producto_id": producto["id"], "cantidad": 2}],
    })
    comprobar("POST /pedidos -> 201 con total 1799.98", estado == 201 and pedido["total"] == 1799.98)

    estado, prod = peticion("GET", f"/productos/{producto['id']}")
    comprobar("El stock baja de 10 a 8", estado == 200 and prod["stock"] == 8)

    estado, historial = peticion("GET", f"/usuarios/{cliente['id']}/pedidos")
    comprobar("GET /usuarios/{id}/pedidos -> 1 pedido", estado == 200 and len(historial) == 1)

    estado, _ = peticion("GET", "/productos/9999")
    comprobar("GET /productos/9999 -> 404", estado == 404)

    print("RESULTADO:", "TODO CORRECTO" if fallos == 0 else f"{fallos} COMPROBACIÓN(ES) FALLIDA(S)")
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()
