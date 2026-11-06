"""Clases de dominio para los productos de la tienda."""


class Producto:
    """Producto genérico de la tienda."""

    tipo = "generico"

    def __init__(self, id: int, nombre: str, precio: float, stock: int):
        if not nombre or not nombre.strip():
            raise ValueError("El nombre del producto no puede estar vacío")
        if precio < 0:
            raise ValueError("El precio no puede ser negativo")
        if stock < 0:
            raise ValueError("El stock no puede ser negativo")
        self.id = id
        self.nombre = nombre.strip()
        self.precio = float(precio)
        self.stock = int(stock)

    def hay_stock(self, cantidad: int) -> bool:
        """Comprueba si hay stock suficiente para la cantidad solicitada."""
        return cantidad <= self.stock

    def actualizar_stock(self, cantidad: int) -> None:
        """Actualiza el stock: positivo es una reposición, negativo una compra."""
        if self.stock + cantidad < 0:
            raise ValueError(
                f"Stock insuficiente para '{self.nombre}' "
                f"(disponible: {self.stock}, solicitado: {-cantidad})"
            )
        self.stock += cantidad

    def __str__(self) -> str:
        """Devuelve una descripción textual del producto."""
        return f"[{self.id}] {self.nombre} - {self.precio:.2f} € (stock: {self.stock})"


class ProductoElectronico(Producto):
    """Producto electrónico con garantía en meses."""

    tipo = "electronico"

    def __init__(self, id: int, nombre: str, precio: float, stock: int, meses_garantia: int):
        super().__init__(id, nombre, precio, stock)
        if meses_garantia < 0:
            raise ValueError("Los meses de garantía no pueden ser negativos")
        self.meses_garantia = int(meses_garantia)

    def __str__(self) -> str:
        return f"{super().__str__()} | Garantía: {self.meses_garantia} meses"


class ProductoRopa(Producto):
    """Prenda de ropa con talla y color."""

    tipo = "ropa"

    def __init__(self, id: int, nombre: str, precio: float, stock: int, talla: str, color: str):
        super().__init__(id, nombre, precio, stock)
        if not talla or not talla.strip():
            raise ValueError("La talla no puede estar vacía")
        if not color or not color.strip():
            raise ValueError("El color no puede estar vacío")
        self.talla = talla.strip().upper()
        self.color = color.strip()

    def __str__(self) -> str:
        return f"{super().__str__()} | Talla: {self.talla}, Color: {self.color}"
