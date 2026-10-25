"""
scripts/seed_admin.py
Script utilitario para crear/actualizar el usuario administrador inicial.

Uso:
    cd itq_backend
    python -m scripts.seed_admin
"""
import asyncio
import sys
import os

# Asegurar que el módulo app sea encontrable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.core import Rol, Usuario, UsuarioRol


async def seed_admin():
    async with AsyncSessionLocal() as db:
        # Verificar si ya existe el admin
        result = await db.execute(
            select(Usuario).where(Usuario.nombre_usuario == "admin")
        )
        admin = result.scalar_one_or_none()

        if admin:
            print("⚠️  El usuario 'admin' ya existe. Actualizando contraseña...")
            admin.contrasena_hash = hash_password("Admin@ITQ2026")
            db.add(admin)
        else:
            print("✅  Creando usuario administrador inicial...")
            admin = Usuario(
                nombre_usuario="admin",
                correo_institucional="admin@itq.edu.ec",
                contrasena_hash=hash_password("Admin@ITQ2026"),
                estado="activo",
            )
            db.add(admin)
            await db.flush()

            # Asignar rol de administrador
            rol_result = await db.execute(
                select(Rol).where(Rol.nombre == "administrador")
            )
            rol = rol_result.scalar_one_or_none()

            if rol:
                usuario_rol = UsuarioRol(
                    id_usuario=admin.id_usuario,
                    id_rol=rol.id_rol,
                    estado="activo",
                )
                db.add(usuario_rol)
                print(f"✅  Rol 'administrador' asignado.")
            else:
                print("⚠️  Rol 'administrador' no encontrado. Crea los roles primero.")

        await db.commit()
        print(f"✅  Usuario admin listo. Contraseña: Admin@ITQ2026")
        print(f"    ⚠️  Cambia la contraseña inmediatamente en producción.")


if __name__ == "__main__":
    asyncio.run(seed_admin())
