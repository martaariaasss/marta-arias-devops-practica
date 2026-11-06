# Tienda Online API — DevOps Práctica

**Autora:** Marta Arias
**Asignatura:** Arquitectura de Software — Universidad Intercontinental de la Empresa (UIE)

## Descripción

Aplicación Python de una **tienda online** construida con **FastAPI** y **Pydantic** sobre una
capa de dominio orientada a objetos.

- **Dominio** (`models/`): `Producto`, `ProductoElectronico`, `ProductoRopa`, `Usuario`,
  `Cliente`, `Administrador`, `Pedido` y `LineaPedido`.
- **Lógica de negocio** (`Services/`): `TiendaService` gestiona usuarios, productos y
  pedidos en memoria y lanza excepciones de dominio cuando algo falla.
- **API REST** (`main.py` + `schemas/`): expone la funcionalidad mediante endpoints HTTP,
  valida las entradas con esquemas Pydantic y traduce las excepciones a códigos HTTP.
- **Tienda web** (`frontend/`) y **cliente Python** (`cliente/`) que consumen la API.

Este repositorio se usa para practicar el ciclo DevOps: control de versiones con Git y
GitHub (ramas `feature/*`, commits descriptivos y Pull Requests) y la contenerización
de la aplicación con Docker.
