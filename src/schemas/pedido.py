from datetime import datetime

from pydantic import BaseModel, Field

from models import LineaPedido, Pedido


class PedidoItemCreate(BaseModel):
    producto_id: int = Field(..., ge=1, examples=[1])
    cantidad: int = Field(..., gt=0, examples=[2])


class PedidoCreate(BaseModel):
    cliente_id: int = Field(..., ge=1, examples=[1])
    items: list[PedidoItemCreate] = Field(..., min_length=1)


class PedidoItemRead(BaseModel):
    producto_id: int
    nombre_producto: str
    cantidad: int
    precio_unitario: float
    subtotal: float

    @classmethod
    def desde_dominio(cls, linea: LineaPedido) -> "PedidoItemRead":
        return cls(
            producto_id=linea.producto.id,
            nombre_producto=linea.producto.nombre,
            cantidad=linea.cantidad,
            precio_unitario=linea.precio_unitario,
            subtotal=linea.subtotal,
        )


class PedidoRead(BaseModel):
    id: int
    fecha: datetime
    cliente_id: int
    nombre_cliente: str
    total: float
    items: list[PedidoItemRead]

    @classmethod
    def desde_dominio(cls, pedido: Pedido) -> "PedidoRead":
        return cls(
            id=pedido.id,
            fecha=pedido.fecha,
            cliente_id=pedido.cliente.id,
            nombre_cliente=pedido.cliente.nombre,
            total=pedido.total,
            items=[PedidoItemRead.desde_dominio(linea) for linea in pedido.lineas],
        )
