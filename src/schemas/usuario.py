from typing import Literal

from pydantic import BaseModel, Field, model_validator

from models import Usuario

EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class UsuarioCreate(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=100, examples=["Ana García"])
    email: str = Field(..., pattern=EMAIL_PATTERN, examples=["ana@example.com"])
    tipo: Literal["cliente", "administrador"] = Field(..., examples=["cliente"])
    direccion_postal: str | None = Field(
        default=None, max_length=200, examples=["Calle Mayor 1, 28013 Madrid"]
    )

    @model_validator(mode="after")
    def cliente_requiere_direccion(self):
        if self.tipo == "cliente" and not (self.direccion_postal and self.direccion_postal.strip()):
            raise ValueError("Los clientes deben indicar una dirección postal")
        return self


class UsuarioRead(BaseModel):
    id: int
    nombre: str
    email: str
    es_admin: bool

    @classmethod
    def desde_dominio(cls, usuario: Usuario) -> "UsuarioRead":
        return cls(
            id=usuario.id,
            nombre=usuario.nombre,
            email=usuario.email,
            es_admin=usuario.is_admin(),
        )
