"""Lógica de negocio de la tienda online.

TiendaService guarda los datos en memoria y no sabe nada de HTTP:
cuando algo falla lanza excepciones de dominio, y main.py las traduce
a códigos de estado HTTP.
"""

from models import (
    Administrador,
    Cliente,
    LineaPedido,
    Pedido,
    Producto,
    ProductoElectronico,
    ProductoRopa,
    Usuario,
)


class TiendaError(Exception):
    """Error base de la tienda."""


class NoEncontradoError(TiendaError):
    """El recurso solicitado no existe."""


class ConflictoError(TiendaError):
    """La operación entra en conflicto con el estado actual (p. ej. email repetido)."""


class StockInsuficienteError(TiendaError):
    """No hay stock suficiente para atender el pedido."""


class OperacionNoPermitidaError(TiendaError):
    """La operación no está permitida para ese usuario o recurso."""


class TiendaService:
    def __init__(self):
        self._usuarios: dict[int, Usuario] = {}
        self._productos: dict[int, Producto] = {}
        self._pedidos: dict[int, Pedido] = {}
        self._siguiente_usuario_id = 1
        self._siguiente_producto_id = 1
        self._siguiente_pedido_id = 1

    # ------------------------------------------------------------------ #
    # Usuarios
    # ------------------------------------------------------------------ #
    def registrar_usuario(
        self, tipo: str, nombre: str, email: str, direccion_postal: str | None = None
    ) -> Usuario:
        """Registra un usuario de tipo "cliente" o "administrador"."""
        email_normalizado = email.strip().lower()
        if any(u.email == email_normalizado for u in self._usuarios.values()):
            raise ConflictoError(f"Ya existe un usuario con el email '{email_normalizado}'")

        nuevo_id = self._siguiente_usuario_id
        if tipo == "cliente":
            usuario = Cliente(nuevo_id, nombre, email, direccion_postal)
        elif tipo == "administrador":
            usuario = Administrador(nuevo_id, nombre, email, direccion_postal)
        else:
            raise ValueError(f"Tipo de usuario no válido: '{tipo}'")

        self._usuarios[nuevo_id] = usuario
        self._siguiente_usuario_id += 1
        return usuario

    def obtener_usuario(self, usuario_id: int) -> Usuario:
        """Devuelve un usuario por su id o lanza NoEncontradoError."""
        usuario = self._usuarios.get(usuario_id)
        if usuario is None:
            raise NoEncontradoError(f"Usuario con id {usuario_id} no encontrado")
        return usuario

    def listar_usuarios(self) -> list[Usuario]:
        """Devuelve todos los usuarios registrados."""
        return list(self._usuarios.values())

    # ------------------------------------------------------------------ #
    # Productos
    # ------------------------------------------------------------------ #
    def agregar_producto(
        self,
        tipo: str,
        nombre: str,
        precio: float,
        stock: int,
        meses_garantia: int | None = None,
        talla: str | None = None,
        color: str | None = None,
    ) -> Producto:
        """Añade al inventario un producto "generico", "electronico" o "ropa"."""
        nuevo_id = self._siguiente_producto_id
        if tipo == "generico":
            producto = Producto(nuevo_id, nombre, precio, stock)
        elif tipo == "electronico":
            if meses_garantia is None:
                raise ValueError("Los productos electrónicos requieren 'meses_garantia'")
            producto = ProductoElectronico(nuevo_id, nombre, precio, stock, meses_garantia)
        elif tipo == "ropa":
            if talla is None or color is None:
                raise ValueError("Los productos de ropa requieren 'talla' y 'color'")
            producto = ProductoRopa(nuevo_id, nombre, precio, stock, talla, color)
        else:
            raise ValueError(f"Tipo de producto no válido: '{tipo}'")

        self._productos[nuevo_id] = producto
        self._siguiente_producto_id += 1
        return producto

    def obtener_producto(self, producto_id: int) -> Producto:
        """Devuelve un producto por su id o lanza NoEncontradoError."""
        producto = self._productos.get(producto_id)
        if producto is None:
            raise NoEncontradoError(f"Producto con id {producto_id} no encontrado")
        return producto

    def listar_productos(self) -> list[Producto]:
        """Devuelve todos los productos del inventario."""
        return list(self._productos.values())

    def eliminar_producto(self, producto_id: int) -> None:
        """Elimina un producto del inventario a partir de su id."""
        self.obtener_producto(producto_id)
        del self._productos[producto_id]

    # ------------------------------------------------------------------ #
    # Pedidos
    # ------------------------------------------------------------------ #
    def realizar_pedido(self, cliente_id: int, items: list[tuple[int, int]]) -> Pedido:
        """Crea un pedido a partir de una lista de (producto_id, cantidad).

        Se comprueba todo antes de tocar el stock, de modo que si una línea
        falla no se descuenta nada del resto.
        """
        usuario = self.obtener_usuario(cliente_id)
        if not isinstance(usuario, Cliente):
            raise OperacionNoPermitidaError(
                f"El usuario {cliente_id} no es un cliente y no puede realizar pedidos"
            )
        if not items:
            raise ValueError("El pedido debe contener al menos un producto")

        # Agrupar cantidades por producto por si se repite en varias líneas
        cantidades: dict[int, int] = {}
        for producto_id, cantidad in items:
            if cantidad <= 0:
                raise ValueError("La cantidad de cada línea debe ser mayor que 0")
            cantidades[producto_id] = cantidades.get(producto_id, 0) + cantidad

        # Validar existencia y stock de todos los productos
        for producto_id, cantidad in cantidades.items():
            producto = self.obtener_producto(producto_id)
            if not producto.hay_stock(cantidad):
                raise StockInsuficienteError(
                    f"Stock insuficiente para '{producto.nombre}' "
                    f"(disponible: {producto.stock}, solicitado: {cantidad})"
                )

        # Todo correcto: crear líneas y descontar stock
        lineas = []
        for producto_id, cantidad in cantidades.items():
            producto = self._productos[producto_id]
            lineas.append(LineaPedido(producto, cantidad))
            producto.actualizar_stock(-cantidad)

        pedido = Pedido(self._siguiente_pedido_id, usuario, lineas)
        self._pedidos[pedido.id] = pedido
        self._siguiente_pedido_id += 1
        return pedido

    def listar_pedidos_usuario(self, cliente_id: int) -> list[Pedido]:
        """Devuelve los pedidos de un usuario ordenados por fecha."""
        self.obtener_usuario(cliente_id)
        pedidos = [p for p in self._pedidos.values() if p.cliente.id == cliente_id]
        return sorted(pedidos, key=lambda p: p.fecha)
