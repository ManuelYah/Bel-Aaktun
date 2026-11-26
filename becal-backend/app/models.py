import re
from datetime import datetime, timedelta

ESTADOS_ELEGIBLES = {
    "confirmada", "confirmado",
    "rechazada", "rechazado",
    "cancelada", "cancelado",
    "aprobada", "aprobado"
}


def generar_folio(prefijo, id_num):
    return f"{prefijo}-{str(id_num).zfill(4)}"


def extraer_id_solicitud(folio, prefijo):
    """
    Acepta: '#APT-020', 'APT-020', 'apt_20', 'APT20', o '20' (si se busca en reservas).
    """
    limpio = re.sub(r"^[#\s]+", "", (folio or "").strip().upper())
    match = re.fullmatch(rf"{prefijo}[-_]?0*(\d+)", limpio)
    if match:
        return int(match.group(1))
    if prefijo == "RES" and limpio.isdigit():
        return int(limpio)
    return None


def normalizar_folio_canonico(folio, tipo, solicitud_id):
    """Guarda siempre un folio limpio y uniforme, ej. 'APT-020' o 'RES-020'."""
    limpio = re.sub(r"^[#\s]+", "", (folio or "").strip().upper())
    if re.fullmatch(r"(RES|APT)-\d+", limpio):
        return limpio
    prefijo = "RES" if tipo == "RESERVA" else "APT"
    return f"{prefijo}-{int(solicitud_id):03d}"


def validar_elegibilidad(row):
    estado = (row.get("estado") or "").strip().lower()
    if estado in ESTADOS_ELEGIBLES:
        return True

    fecha_creacion = row.get("fecha_creacion")
    if fecha_creacion:
        if isinstance(fecha_creacion, str):
            fecha_creacion = datetime.fromisoformat(fecha_creacion.replace(" GMT", ""))
        if (datetime.now() - fecha_creacion) >= timedelta(hours=72):
            return True

    return False


def _normalizar_texto(valor):
    return (valor or "").strip().lower()


def _normalizar_contacto(valor):
    texto = (valor or "").strip().lower()
    if re.fullmatch(r"[\d\s\-\+\(\)]+", texto):
        return re.sub(r"\D", "", texto)
    return texto


def buscar_y_validar_solicitud(cursor, folio, nombre, contacto):
    """
    Busca una solicitud en `reservas` o `apartados` según el folio y valida
    elegibilidad, nombre y contacto. Devuelve un dict con `tipo`, `solicitud_id`,
    `taller_id` y `contacto_verificado`, o lanza ValueError con el motivo.
    """
    nombre_norm = _normalizar_texto(nombre)
    contacto_norm = _normalizar_contacto(contacto)

    # 1. Intentar en reservas
    res_id = extraer_id_solicitud(folio, "RES")
    if res_id is not None:
        cursor.execute(
            """
            SELECT id, taller_id, nombre_visitante, email_visitante,
                   telefono_visitante, estado, fecha_creacion
            FROM reservas
            WHERE id = %s
            """,
            (res_id,),
        )
        res = cursor.fetchone()
        if res:
            if not validar_elegibilidad(res):
                raise ValueError("La reserva aún no es elegible para comentar.")
            if _normalizar_texto(res.get("nombre_visitante")) != nombre_norm:
                raise ValueError("El nombre no coincide con la reserva.")
            coincide_contacto = (
                _normalizar_contacto(res.get("email_visitante")) == contacto_norm
                or (
                    contacto_norm.isdigit()
                    and _normalizar_contacto(res.get("telefono_visitante")) == contacto_norm
                )
            )
            if not coincide_contacto:
                raise ValueError("El contacto no coincide con la reserva.")
            return {
                "tipo": "RESERVA",
                "solicitud_id": res["id"],
                "taller_id": res["taller_id"],
                "contacto_verificado": contacto_norm,
            }

    # 2. Intentar en apartados
    apt_id = extraer_id_solicitud(folio, "APT")
    if apt_id is not None:
        cursor.execute(
            """
            SELECT id, taller_id, nombre_cliente, email_cliente,
                   telefono_cliente, estado, fecha_creacion
            FROM apartados
            WHERE id = %s
            """,
            (apt_id,),
        )
        apt = cursor.fetchone()
        if apt:
            if not validar_elegibilidad(apt):
                raise ValueError("El apartado aún no es elegible para comentar.")
            if _normalizar_texto(apt.get("nombre_cliente")) != nombre_norm:
                raise ValueError("El nombre no coincide con el apartado.")
            coincide_contacto = (
                _normalizar_contacto(apt.get("email_cliente")) == contacto_norm
                or (
                    contacto_norm.isdigit()
                    and _normalizar_contacto(apt.get("telefono_cliente")) == contacto_norm
                )
            )
            if not coincide_contacto:
                raise ValueError("El contacto no coincide con el apartado.")
            return {
                "tipo": "APARTADO",
                "solicitud_id": apt["id"],
                "taller_id": apt["taller_id"],
                "contacto_verificado": contacto_norm,
            }

    raise ValueError("No se encontró una reserva o apartado válido con ese folio.")