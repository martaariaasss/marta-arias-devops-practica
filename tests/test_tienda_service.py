"""Pruebas unitarias de TiendaService (capa de negocio, sin HTTP)."""

import pytest

from models import Cliente, ProductoElectronico, ProductoRopa
from Services import (
    ConflictoError,
    NoEncontradoError,
    OperacionNoPermitidaError,
    StockInsuficienteError,
    TiendaService,
)


@pytest.fixture
def tienda():
    return TiendaService()


@pytest.fixture
def tienda_con_datos(tienda):
    tienda.registrar_usuario("cliente", "Ana", "ana@example.com", "Calle Mayor 1")
    tienda.registrar_usuario("administrador", "Luis", "luis@example.com")
    tienda.agregar_producto("electronico", "Portátil", 800.0, 5, meses_garantia=24)
    tienda.agregar_producto("ropa", "Camiseta", 15.5, 10, talla="m", color="Azul")
    return tienda


# ----------------------------- Usuarios ----------------------------- #
def test_registrar_usuarios_asigna_ids_y_tipos(tienda_con_datos):
    ana, luis = tienda_con_datos.listar_usuarios()
    assert (ana.id, luis.id) == (1, 2)
    assert isinstance(ana, Cliente) and not ana.is_admin()
    assert luis.is_admin()


def test_email_duplicado_sin_distinguir_mayusculas(tienda_con_datos):
    with pytest.raises(ConflictoError):
        tienda_con_datos.registrar_usuario("cliente", "Otra", " ANA@example.com ", "X")


def test_tipo_de_usuario_no_valido(tienda):
    with pytest.raises(ValueError):
        tienda.registrar_usuario("invitado", "Eva", "eva@example.com")


def test_usuario_inexistente(tienda):
    with pytest.raises(NoEncontradoError):
        tienda.obtener_usuario(99)


# ----------------------------- Productos ---------------------------- #
def test_agregar_productos_de_cada_tipo(tienda_con_datos):
    portatil = tienda_con_datos.obtener_producto(1)
    camiseta = tienda_con_datos.obtener_producto(2)
    assert isinstance(portatil, ProductoElectronico) and portatil.meses_garantia == 24
    assert isinstance(camiseta, ProductoRopa) and camiseta.talla == "M"


@pytest.mark.parametrize("kwargs", [
    {"tipo": "electronico", "nombre": "TV", "precio": 100, "stock": 1},
    {"tipo": "ropa", "nombre": "Gorra", "precio": 9, "stock": 1, "talla": "L"},
    {"tipo": "comida", "nombre": "Pan", "precio": 1, "stock": 1},
    {"tipo": "generico", "nombre": "Taza", "precio": -1, "stock": 1},
])
def test_productos_invalidos(tienda, kwargs):
    with pytest.raises(ValueError):
        tienda.agregar_producto(**kwargs)


def test_eliminar_producto(tienda_con_datos):
    tienda_con_datos.eliminar_producto(1)
    with pytest.raises(NoEncontradoError):
        tienda_con_datos.obtener_producto(1)
    with pytest.raises(NoEncontradoError):
        tienda_con_datos.eliminar_producto(1)


# ------------------------------ Pedidos ----------------------------- #
def test_realizar_pedido_descuenta_stock_y_calcula_total(tienda_con_datos):
    pedido = tienda_con_datos.realizar_pedido(1, [(1, 2), (2, 2)])
    assert pedido.total == 1631.0
    assert tienda_con_datos.obtener_producto(1).stock == 3
    assert tienda_con_datos.obtener_producto(2).stock == 8
    assert tienda_con_datos.listar_pedidos_usuario(1) == [pedido]


def test_lineas_repetidas_se_agrupan(tienda_con_datos):
    pedido = tienda_con_datos.realizar_pedido(1, [(1, 1), (1, 2)])
    assert len(pedido.lineas) == 1 and pedido.lineas[0].cantidad == 3


def test_pedido_fallido_no_modifica_stock(tienda_con_datos):
    with pytest.raises(StockInsuficienteError):
        tienda_con_datos.realizar_pedido(1, [(2, 1), (1, 50)])
    assert tienda_con_datos.obtener_producto(2).stock == 10  # la primera línea no se descontó


def test_administrador_no_puede_comprar(tienda_con_datos):
    with pytest.raises(OperacionNoPermitidaError):
        tienda_con_datos.realizar_pedido(2, [(1, 1)])


def test_historial_de_pedidos_ordenado_por_fecha(tienda_con_datos):
    primero = tienda_con_datos.realizar_pedido(1, [(1, 1)])
    segundo = tienda_con_datos.realizar_pedido(1, [(2, 1)])
    assert tienda_con_datos.listar_pedidos_usuario(1) == [primero, segundo]
    with pytest.raises(NoEncontradoError):
        tienda_con_datos.listar_pedidos_usuario(99)


@pytest.mark.parametrize("cliente_id, items, error", [
    (99, [(1, 1)], NoEncontradoError),
    (1, [(99, 1)], NoEncontradoError),
    (1, [], ValueError),
    (1, [(1, 0)], ValueError),
])
def test_errores_en_pedidos(tienda_con_datos, cliente_id, items, error):
    with pytest.raises(error):
        tienda_con_datos.realizar_pedido(cliente_id, items)
