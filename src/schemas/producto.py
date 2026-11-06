from typing import Literal

from pydantic import BaseModel, Field, model_validator

from models import Producto, ProductoElectronico, ProductoRopa

TipoProducto = Literal["generico", "electronico", "ropa"]


class ProductoCreate(BaseModel):
    tipo: TipoProducto = Field(..., examples=["electronico"])
    nombre: str = Field(..., min_length=1, max_length=100, examples=["Portátil"])
    precio: float = Field(..., ge=0, examples=[899.99])
    stock: int = Field(..., ge=0, examples=[10])
    meses_garantia: int | None = Field(default=None, ge=0, examples=[24])
    talla: str | None = Field(default=None, min_length=1, max_length=10, examples=[None])
    color: str | None = Field(default=None, min_length=1, max_length=30, examples=[None])

    @model_validator(mode="after")
    def validar_atributos_por_tipo(self):
        if self.tipo == "electronico":
            if self.meses_garantia is None:
                raise ValueError("Los productos electrónicos requieren 'meses_garantia'")
            if self.talla is not None or self.color is not None:
                raise ValueError("Los productos electrónicos no admiten 'talla' ni 'color'")
        elif self.tipo == "ropa":
            if self.talla is None or self.color is None:
                raise ValueError("Los productos de ropa requieren 'talla' y 'color'")
            if self.meses_garantia is not None:
                raise ValueError("Los productos de ropa no admiten 'meses_garantia'")
        else:
            if any(v is not None for v in (self.meses_garantia, self.talla, self.color)):
                raise ValueError(
                    "Los productos genéricos no admiten 'meses_garantia', 'talla' ni 'color'"
                )
        return self


class ProductoRead(BaseModel):
    id: int
    tipo: TipoProducto
    nombre: str
    precio: float
    stock: int
    meses_garantia: int | None = None
    talla: str | None = None
    color: str | None = None

    @classmethod
    def desde_dominio(cls, producto: Producto) -> "ProductoRead":
        datos = {
            "id": producto.id,
            "tipo": producto.tipo,
            "nombre": producto.nombre,
            "precio": producto.precio,
            "stock": producto.stock,
        }
        if isinstance(producto, ProductoElectronico):
            datos["meses_garantia"] = producto.meses_garantia
        elif isinstance(producto, ProductoRopa):
            datos["talla"] = producto.talla
            datos["color"] = producto.color
        return cls(**datos)
