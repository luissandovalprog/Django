import re

def validar_rut_chileno(rut):
    if not rut or not isinstance(rut, str):
        return False

    rut_limpio = re.sub(r'[.-]', '', rut).lower()

    if len(rut_limpio) < 8:
        return False

    cuerpo = rut_limpio[:-1]
    dv = rut_limpio[-1]

    if not cuerpo.isdigit():
        return False

    try:
        suma = 0
        multiplo = 2
        for i in reversed(cuerpo):
            suma += int(i) * multiplo
            multiplo = 7 if multiplo == 7 else multiplo + 1

        dv_esperado = 11 - (suma % 11)
        dv_final = str(dv_esperado) if dv_esperado < 10 else ('k' if dv_esperado == 10 else '0')

        return dv == dv_final
    except Exception:
        return False

def validar_rango(valor, min_val, max_val):
    try:
        num = float(valor)
        return min_val <= num <= max_val
    except (ValueError, TypeError):
        return False

def validar_peso_rn(peso):
    return validar_rango(peso, 500, 6000)

def validar_talla_rn(talla):
    return validar_rango(talla, 30, 70)

def validar_apgar(apgar):
    try:
        num = int(apgar)
        return 0 <= num <= 10
    except (ValueError, TypeError):
        return False