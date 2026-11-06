"""Clases de dominio para los usuarios de la tienda."""


class Usuario:
    """Usuario base de la tienda."""

    tipo = "usuario"

    def __init__(self, id: int, nombre: str, email: str):
        if not nombre or not nombre.strip():
            raise ValueError("El nombre del usuario no puede estar vacío")
        if not email or "@" not in email:
            raise ValueError("El email no es válido")
        self.id = id
        self.nombre = nombre.strip()
        self.email = email.strip().lower()

    def is_admin(self) -> bool:
        """Indica si el usuario tiene privilegios de administrador."""
        return False

    def __str__(self) -> str:
        return f"[{self.id}] {self.nombre} <{self.email}>"


class Cliente(Usuario):
    """Cliente que puede realizar pedidos."""

    tipo = "cliente"

    def __init__(self, id: int, nombre: str, email: str, direccion_postal: str):
        super().__init__(id, nombre, email)
        if not direccion_postal or not direccion_postal.strip():
            raise ValueError("El cliente debe tener una dirección postal")
        self.direccion_postal = direccion_postal.strip()

    def __str__(self) -> str:
        return f"Cliente {super().__str__()} - {self.direccion_postal}"


class Administrador(Usuario):
    """Administrador de la tienda."""

    tipo = "administrador"

    def __init__(self, id: int, nombre: str, email: str, direccion_postal: str | None = None):
        super().__init__(id, nombre, email)
        self.direccion_postal = direccion_postal.strip() if direccion_postal else None

    def is_admin(self) -> bool:
        """Los administradores siempre tienen privilegios de administrador."""
        return True

    def __str__(self) -> str:
        return f"Administrador {super().__str__()}"
