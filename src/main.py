"""Punto de entrada de la API REST de la tienda online.

Este módulo es la capa de exposición del servicio: define los endpoints,
valida la entrada con los esquemas Pydantic, delega la lógica en
TiendaService y traduce las excepciones de dominio a códigos HTTP.

Ejecutar desde esta carpeta con:
    uvicorn main:app --reload
o directamente con el botón "Ejecutar" / ``python main.py``, que acepta
conexiones de otros equipos de la red.

La configuración del servidor (host, puerto, nivel de log, datos de ejemplo...)
se lee de variables de entorno; ver config.py.
"""

import socket
from pathlib import Path

from fastapi import Depends, FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from config import settings
from schemas import (
    PedidoCreate,
    PedidoRead,
    ProductoCreate,
    ProductoRead,
    UsuarioCreate,
    UsuarioRead,
)
from Services import (
    ConflictoError,
    NoEncontradoError,
    OperacionNoPermitidaError,
    StockInsuficienteError,
    TiendaService,
)

app = FastAPI(
    title="Tienda Online API",
    description="API REST de la tienda online (Práctica 2) construida sobre TiendaService.",
    version=settings.app_version,
)

# Permite que el frontend (abierto desde otro origen, p. ej. el fichero
# frontend/index.html o el equipo de un compañero) haga peticiones a la API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def cargar_datos_ejemplo(tienda: TiendaService) -> None:
    """Carga los usuarios y productos de prueba de la Práctica 1."""
    tienda.registrar_usuario("cliente", "Ana García", "ana@gmail.com", "Calle Mayor 1, Madrid")
    tienda.registrar_usuario("cliente", "Luis Pérez", "luis@gmail.com", "Av. Diagonal 45, Barcelona")
    tienda.registrar_usuario("cliente", "María López", "maria@gmail.com", "Calle Sol 10, Valencia")
    tienda.registrar_usuario("administrador", "Carlos Admin", "carlos@gmail.com")

    tienda.agregar_producto("electronico", "Portátil", 899.99, 10, meses_garantia=24)
    tienda.agregar_producto("electronico", "Móvil", 499.50, 15, meses_garantia=12)
    tienda.agregar_producto("ropa", "Camiseta", 19.99, 30, talla="M", color="Azul")
    tienda.agregar_producto("ropa", "Pantalón", 39.99, 20, talla="L", color="Negro")
    tienda.agregar_producto("generico", "Taza de cerámica", 7.50, 30)


# Una única instancia del servicio para toda la aplicación (datos en memoria)
tienda_service = TiendaService()
if settings.cargar_datos_ejemplo:
    cargar_datos_ejemplo(tienda_service)


def get_tienda() -> TiendaService:
    return tienda_service


# ---------------------------------------------------------------------- #
# Traducción de excepciones de dominio a respuestas HTTP
# ---------------------------------------------------------------------- #
def _error(status_code: int, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"detail": str(exc)})


@app.exception_handler(NoEncontradoError)
async def no_encontrado_handler(request: Request, exc: NoEncontradoError):
    return _error(status.HTTP_404_NOT_FOUND, exc)


@app.exception_handler(ConflictoError)
async def conflicto_handler(request: Request, exc: ConflictoError):
    return _error(status.HTTP_409_CONFLICT, exc)


@app.exception_handler(StockInsuficienteError)
async def stock_handler(request: Request, exc: StockInsuficienteError):
    return _error(status.HTTP_400_BAD_REQUEST, exc)


@app.exception_handler(OperacionNoPermitidaError)
async def operacion_no_permitida_handler(request: Request, exc: OperacionNoPermitidaError):
    return _error(status.HTTP_400_BAD_REQUEST, exc)


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return _error(status.HTTP_400_BAD_REQUEST, exc)


@app.get("/", tags=["General"])
def raiz():
    return {"mensaje": "API de la Tienda Online. Documentación en /docs, frontend en /tienda"}


@app.get("/health", tags=["General"])
def health():
    """Comprobación de salud (liveness) usada por el HEALTHCHECK de Docker."""
    return {"status": "ok", "version": settings.app_version}


# ---------------------------------------------------------------------- #
# Usuarios
# ---------------------------------------------------------------------- #
@app.post(
    "/usuarios",
    response_model=UsuarioRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Usuarios"],
    responses={409: {"description": "Ya existe un usuario con ese email"}},
)
def crear_usuario(datos: UsuarioCreate, tienda: TiendaService = Depends(get_tienda)):
    usuario = tienda.registrar_usuario(
        tipo=datos.tipo,
        nombre=datos.nombre,
        email=datos.email,
        direccion_postal=datos.direccion_postal,
    )
    return UsuarioRead.desde_dominio(usuario)


@app.get("/usuarios", response_model=list[UsuarioRead], tags=["Usuarios"])
def listar_usuarios(tienda: TiendaService = Depends(get_tienda)):
    return [UsuarioRead.desde_dominio(u) for u in tienda.listar_usuarios()]


@app.get(
    "/usuarios/{usuario_id}",
    response_model=UsuarioRead,
    tags=["Usuarios"],
    responses={404: {"description": "Usuario no encontrado"}},
)
def obtener_usuario(usuario_id: int, tienda: TiendaService = Depends(get_tienda)):
    return UsuarioRead.desde_dominio(tienda.obtener_usuario(usuario_id))


@app.get(
    "/usuarios/{cliente_id}/pedidos",
    response_model=list[PedidoRead],
    tags=["Pedidos"],
    responses={404: {"description": "Usuario no encontrado"}},
)
def pedidos_de_cliente(cliente_id: int, tienda: TiendaService = Depends(get_tienda)):
    return [PedidoRead.desde_dominio(p) for p in tienda.listar_pedidos_usuario(cliente_id)]


# ---------------------------------------------------------------------- #
# Productos
# ---------------------------------------------------------------------- #
@app.post(
    "/productos",
    response_model=ProductoRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Productos"],
)
def crear_producto(datos: ProductoCreate, tienda: TiendaService = Depends(get_tienda)):
    producto = tienda.agregar_producto(
        tipo=datos.tipo,
        nombre=datos.nombre,
        precio=datos.precio,
        stock=datos.stock,
        meses_garantia=datos.meses_garantia,
        talla=datos.talla,
        color=datos.color,
    )
    return ProductoRead.desde_dominio(producto)


@app.get("/productos", response_model=list[ProductoRead], tags=["Productos"])
def listar_productos(tienda: TiendaService = Depends(get_tienda)):
    return [ProductoRead.desde_dominio(p) for p in tienda.listar_productos()]


@app.get(
    "/productos/{producto_id}",
    response_model=ProductoRead,
    tags=["Productos"],
    responses={404: {"description": "Producto no encontrado"}},
)
def obtener_producto(producto_id: int, tienda: TiendaService = Depends(get_tienda)):
    return ProductoRead.desde_dominio(tienda.obtener_producto(producto_id))


@app.delete(
    "/productos/{producto_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Productos"],
    responses={404: {"description": "Producto no encontrado"}},
)
def eliminar_producto(producto_id: int, tienda: TiendaService = Depends(get_tienda)):
    tienda.eliminar_producto(producto_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------- #
# Pedidos
# ---------------------------------------------------------------------- #
@app.post(
    "/pedidos",
    response_model=PedidoRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Pedidos"],
    responses={
        400: {"description": "Stock insuficiente o el usuario no es un cliente"},
        404: {"description": "Cliente o producto no encontrado"},
    },
)
def crear_pedido(datos: PedidoCreate, tienda: TiendaService = Depends(get_tienda)):
    pedido = tienda.realizar_pedido(
        cliente_id=datos.cliente_id,
        items=[(item.producto_id, item.cantidad) for item in datos.items],
    )
    return PedidoRead.desde_dominio(pedido)


# El frontend sigue siendo un cliente aparte (solo usa la API con fetch);
# aquí solo se sirve el fichero para abrirlo en http://<ip>:8000/tienda/
app.mount(
    "/tienda",
    StaticFiles(directory=Path(__file__).parent / "frontend", html=True),
    name="tienda",
)


# ---------------------------------------------------------------------- #
# Arranque directo (botón "Ejecutar" / python main.py)
# ---------------------------------------------------------------------- #
def ip_local() -> str:
    """Devuelve la IP del equipo en la red local (la que usará el otro equipo)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))  # no envía nada, solo elige la interfaz de red
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


if __name__ == "__main__":
    import uvicorn

    # Por defecto HOST=0.0.0.0: acepta conexiones de otros equipos de la red
    # (y, dentro de Docker, desde fuera del contenedor), no solo de localhost
    PORT = settings.port

    print(f"API en este equipo:   http://localhost:{PORT}/docs")
    print(f"API desde otro equipo: http://{ip_local()}:{PORT}/docs")
    print(f"Frontend:              http://localhost:{PORT}/tienda/")

    uvicorn.run(app, host=settings.host, port=PORT, log_level=settings.log_level)
