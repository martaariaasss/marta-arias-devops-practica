"""Cliente Python de la API REST de la tienda online (Práctica 2, parte 2).

Script independiente del servidor: no importa TiendaService, los modelos ni
nada de main.py. Toda la comunicación se hace mediante peticiones HTTP con
la librería requests.

Uso (con la API ya arrancada):
    python cliente.py

Para probar contra la API de otro equipo de la red, cambia BASE_URL por la
IP de ese equipo, p. ej. "http://192.168.1.34:8000".
"""

import time

import requests

# Dirección base de la API: cámbiala aquí para probar en local o entre equipos
BASE_URL = "http://localhost:8000"


def comprobar(respuesta: requests.Response, esperado: int, accion: str):
    """Comprueba el código de estado HTTP y devuelve el JSON de la respuesta."""
    print(f"\n[{respuesta.request.method} {respuesta.request.path_url}] {accion}")
    print(f"  Código recibido: {respuesta.status_code} (esperado {esperado})")
    datos = respuesta.json()
    if respuesta.status_code != esperado:
        print(f"  ERROR: {datos.get('detail', datos)}")
        raise SystemExit(1)
    return datos


def crear_usuario(nombre: str, email: str, direccion: str) -> dict:
    cuerpo = {"nombre": nombre, "email": email, "tipo": "cliente", "direccion_postal": direccion}
    r = requests.post(f"{BASE_URL}/usuarios", json=cuerpo)
    usuario = comprobar(r, 201, "Crear usuario")
    print(f"  Usuario creado: id={usuario['id']}, {usuario['nombre']} <{usuario['email']}>")
    return usuario


def listar_usuarios() -> list[dict]:
    r = requests.get(f"{BASE_URL}/usuarios")
    usuarios = comprobar(r, 200, "Listar usuarios")
    for u in usuarios:
        rol = "administrador" if u["es_admin"] else "cliente"
        print(f"  - id={u['id']}: {u['nombre']} <{u['email']}> ({rol})")
    return usuarios


def crear_producto(**datos) -> dict:
    r = requests.post(f"{BASE_URL}/productos", json=datos)
    producto = comprobar(r, 201, f"Crear producto '{datos['nombre']}'")
    print(f"  Producto creado: id={producto['id']}, {producto['nombre']} ({producto['tipo']})")
    return producto


def listar_productos() -> list[dict]:
    r = requests.get(f"{BASE_URL}/productos")
    productos = comprobar(r, 200, "Listar productos")
    for p in productos:
        print(f"  - id={p['id']}: {p['nombre']} ({p['tipo']}) {p['precio']} € - stock {p['stock']}")
    return productos


def crear_pedido(cliente_id: int, items: list[tuple[int, int]]) -> dict:
    cuerpo = {
        "cliente_id": cliente_id,
        "items": [{"producto_id": pid, "cantidad": cant} for pid, cant in items],
    }
    r = requests.post(f"{BASE_URL}/pedidos", json=cuerpo)
    pedido = comprobar(r, 201, "Crear pedido")
    print(f"  Pedido creado: id={pedido['id']}, total={pedido['total']} €")
    return pedido


def pedidos_de_usuario(cliente_id: int) -> list[dict]:
    r = requests.get(f"{BASE_URL}/usuarios/{cliente_id}/pedidos")
    pedidos = comprobar(r, 200, f"Pedidos del usuario {cliente_id}")
    for p in pedidos:
        print(f"  - Pedido {p['id']} ({p['fecha']}) de {p['nombre_cliente']}: {p['total']} €")
        for item in p["items"]:
            print(f"      {item['cantidad']} x {item['nombre_producto']} = {item['subtotal']} €")
    return pedidos


def main():
    print(f"Usando la API en {BASE_URL}")

    # Email único en cada ejecución para no chocar con el 409 de email repetido
    email = f"ana{int(time.time())}@example.com"
    usuario = crear_usuario("Ana García", email, "Calle Mayor 1, 28013 Madrid")
    listar_usuarios()

    portatil = crear_producto(
        tipo="electronico", nombre="Portátil", precio=899.99, stock=10, meses_garantia=24
    )
    camiseta = crear_producto(
        tipo="ropa", nombre="Camiseta", precio=15.5, stock=50, talla="M", color="Azul"
    )
    listar_productos()

    crear_pedido(usuario["id"], [(portatil["id"], 1), (camiseta["id"], 3)])
    pedidos_de_usuario(usuario["id"])

    print("\nFlujo completado correctamente.")


if __name__ == "__main__":
    try:
        main()
    except requests.ConnectionError:
        print(f"\nNo se pudo conectar con {BASE_URL}. ¿Está arrancada la API (python main.py)?")
