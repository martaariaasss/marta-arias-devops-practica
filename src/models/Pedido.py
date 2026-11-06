"""Clases de dominio para los pedidos de la tienda."""

from datetime import datetime

from .Producto import Producto
from .Usuario import Cliente


class LineaPedido:
    """Línea de un pedido: producto, cantidad y precio en el momento de la compra."""

    def __init__(self, producto: Producto, cantidad: int):
        if cantidad <= 0:
            raise ValueError("La cantidad debe ser mayor que 0")
        self.producto = producto
        self.cantidad = cantidad
        self.precio_unitario = producto.precio

    @property
    def subtotal(self) -> float:
        return round(self.precio_unitario * self.cantidad, 2)


class Pedido:
    """Pedido realizado por un cliente."""

    def __init__(self, id: int, cliente: Cliente, lineas: list[LineaPedido]):
        if not lineas:
            raise ValueError("El pedido debe contener al menos un producto")
        self.id = id
        self.cliente = cliente
        self.lineas = lineas
        self.fecha = datetime.now()

    def calcular_total(self) -> float:
        return round(sum(linea.subtotal for linea in self.lineas), 2)

    @property
    def total(self) -> float:
        return self.calcular_total()

    def __str__(self) -> str:
        return (
            f"Pedido {self.id} - {self.cliente.nombre} - "
            f"{self.fecha:%d/%m/%Y %H:%M} - Total: {self.total:.2f} €"
        )
