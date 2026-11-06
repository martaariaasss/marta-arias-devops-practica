"""Pruebas de la API. Ejecutar desde la carpeta del proyecto con: python -m pytest"""

import pytest
from fastapi.testclient import TestClient

from main import app, get_tienda
from Services import TiendaService


@pytest.fixture
def client():
    # Cada prueba usa una tienda vacía e independiente
    tienda = TiendaService()
    app.dependency_overrides[get_tienda] = lambda: tienda
    yield TestClient(app)
    app.dependency_overrides.clear()


def crear_cliente(client, email="ana@example.com"):
    r = client.post("/usuarios", json={
        "nombre": "Ana", "email": email, "tipo": "cliente",
        "direccion_postal": "Calle Mayor 1, Madrid",
    })
    assert r.status_code == 201
    return r.json()


def crear_portatil(client, stock=5):
    r = client.post("/productos", json={
        "tipo": "electronico", "nombre": "Portátil", "precio": 800.0,
        "stock": stock, "meses_garantia": 24,
    })
    assert r.status_code == 201
    return r.json()


# ---------------------------- Usuarios ---------------------------- #
def test_crear_y_obtener_usuarios(client):
    cliente = crear_cliente(client)
    assert cliente == {"id": 1, "nombre": "Ana", "email": "ana@example.com", "es_admin": False}

    r = client.post("/usuarios", json={"nombre": "Luis", "email": "luis@example.com",
                                       "tipo": "administrador"})
    assert r.status_code == 201
    assert r.json()["es_admin"] is True

    assert client.get("/usuarios/1").json()["nombre"] == "Ana"
    assert len(client.get("/usuarios").json()) == 2


def test_usuario_no_encontrado(client):
    r = client.get("/usuarios/99")
    assert r.status_code == 404
    assert "no encontrado" in r.json()["detail"]


def test_email_duplicado(client):
    crear_cliente(client)
    r = client.post("/usuarios", json={"nombre": "Otra", "email": "ANA@example.com",
                                       "tipo": "cliente", "direccion_postal": "X"})
    assert r.status_code == 409


@pytest.mark.parametrize("datos", [
    {"nombre": "Ana", "email": "no-es-email", "tipo": "cliente", "direccion_postal": "X"},
    {"nombre": "Ana", "email": "a@b.com", "tipo": "invitado", "direccion_postal": "X"},
    {"nombre": "Ana", "email": "a@b.com", "tipo": "cliente"},
    {"nombre": "", "email": "a@b.com", "tipo": "administrador"},
])
def test_usuario_datos_invalidos(client, datos):
    assert client.post("/usuarios", json=datos).status_code == 422


# ---------------------------- Productos --------------------------- #
def test_crud_productos(client):
    crear_portatil(client)
    r = client.post("/productos", json={"tipo": "ropa", "nombre": "Camiseta", "precio": 15,
                                        "stock": 20, "talla": "m", "color": "Azul"})
    assert r.status_code == 201
    assert r.json()["talla"] == "M"
    r = client.post("/productos", json={"tipo": "generico", "nombre": "Taza",
                                        "precio": 5, "stock": 3})
    assert r.status_code == 201
    assert r.json()["meses_garantia"] is None

    assert len(client.get("/productos").json()) == 3
    assert client.get("/productos/1").json()["meses_garantia"] == 24

    assert client.delete("/productos/1").status_code == 204
    assert client.get("/productos/1").status_code == 404
    assert client.delete("/productos/1").status_code == 404


@pytest.mark.parametrize("datos", [
    {"tipo": "electronico", "nombre": "TV", "precio": 100, "stock": 1},
    {"tipo": "ropa", "nombre": "Pantalón", "precio": 30, "stock": 1, "talla": "L"},
    {"tipo": "generico", "nombre": "Taza", "precio": 5, "stock": 1, "color": "Rojo"},
    {"tipo": "generico", "nombre": "Taza", "precio": -5, "stock": 1},
    {"tipo": "generico", "nombre": "Taza", "precio": 5, "stock": -1},
    {"tipo": "comida", "nombre": "Pan", "precio": 1, "stock": 1},
])
def test_producto_datos_invalidos(client, datos):
    assert client.post("/productos", json=datos).status_code == 422


# ----------------------------- Pedidos ---------------------------- #
def test_crear_pedido_y_historial(client):
    cliente = crear_cliente(client)
    portatil = crear_portatil(client, stock=5)

    r = client.post("/pedidos", json={"cliente_id": cliente["id"],
                                      "items": [{"producto_id": portatil["id"], "cantidad": 2}]})
    assert r.status_code == 201
    pedido = r.json()
    assert pedido["total"] == 1600.0
    assert pedido["items"][0]["subtotal"] == 1600.0
    assert client.get(f"/productos/{portatil['id']}").json()["stock"] == 3

    historial = client.get(f"/usuarios/{cliente['id']}/pedidos").json()
    assert len(historial) == 1 and historial[0]["id"] == pedido["id"]


def test_pedido_errores(client):
    cliente = crear_cliente(client)
    portatil = crear_portatil(client, stock=1)
    admin = client.post("/usuarios", json={"nombre": "Luis", "email": "luis@example.com",
                                           "tipo": "administrador"}).json()

    def pedir(cliente_id, producto_id, cantidad):
        return client.post("/pedidos", json={"cliente_id": cliente_id, "items": [
            {"producto_id": producto_id, "cantidad": cantidad}]})

    assert pedir(99, portatil["id"], 1).status_code == 404          # cliente inexistente
    assert pedir(cliente["id"], 99, 1).status_code == 404           # producto inexistente
    assert pedir(cliente["id"], portatil["id"], 5).status_code == 400  # sin stock
    assert pedir(admin["id"], portatil["id"], 1).status_code == 400    # admin no compra
    assert pedir(cliente["id"], portatil["id"], 0).status_code == 422  # cantidad inválida
    assert client.post("/pedidos", json={"cliente_id": 1, "items": []}).status_code == 422

    # Ningún pedido fallido debe haber consumido stock
    assert client.get(f"/productos/{portatil['id']}").json()["stock"] == 1
    assert client.get("/usuarios/99/pedidos").status_code == 404


def test_historial_ordenado_por_fecha(client):
    cliente = crear_cliente(client)
    portatil = crear_portatil(client, stock=5)
    for _ in range(3):
        client.post("/pedidos", json={"cliente_id": cliente["id"],
                                      "items": [{"producto_id": portatil["id"], "cantidad": 1}]})
    fechas = [p["fecha"] for p in client.get(f"/usuarios/{cliente['id']}/pedidos").json()]
    assert fechas == sorted(fechas)


# ------------------------ Práctica 1.3 / frontend ----------------------- #
def test_actualizar_stock_compra_y_reposicion():
    tienda = TiendaService()
    taza = tienda.agregar_producto("generico", "Taza", 5, 3)
    taza.actualizar_stock(-2)
    taza.actualizar_stock(10)
    assert taza.stock == 11
    with pytest.raises(ValueError):
        taza.actualizar_stock(-20)


def test_frontend_servido_en_tienda(client):
    r = client.get("/tienda/")
    assert r.status_code == 200
    assert "Tienda Online" in r.text
