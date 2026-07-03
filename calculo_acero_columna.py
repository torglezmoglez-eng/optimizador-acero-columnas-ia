"""
Calculadora de acero mínimo para columnas de concreto reforzado.

Norma de referencia: el área mínima de acero longitudinal en una columna
debe ser 1% del área bruta de concreto (Ag), según criterios comunes de
ACI 318 


Requisitos:
    pip install google-genai

Configuración de la API key (elige una opción):
    1) Variable de entorno (recomendado):
       export GEMINI_API_KEY="tu_api_key_aqui"      (Linux/Mac)
       set GEMINI_API_KEY=tu_api_key_aqui           (Windows cmd)
    2) El programa te la pedirá si no la encuentra en el entorno.

Obtén tu API key  en: https://aistudio.google.com/app/apikey
"""

import os
import sys
import math

# --- Datos de las varillas disponibles (área en cm²) ---
# Fuente: tablas estándar de varillas corrugadas (redondeadas a 2 decimales)
VARILLAS = [
    {"diametro": "3/8 pulg (9.5 mm)", "area_cm2": 0.71},
    {"diametro": "1/2 pulg (12.7 mm)", "area_cm2": 1.29},
    {"diametro": "3/4 pulg (19.1 mm)", "area_cm2": 2.85},
]

PORCENTAJE_ACERO_MINIMO = 0.01  # 1% del área bruta
MIN_VARILLAS_COLUMNA = 4        # mínimo constructivo usual para columnas con estribos


def pedir_dato_numerico(mensaje):
    """Pide un número positivo por consola, validando la entrada."""
    while True:
        valor = input(mensaje).strip()
        try:
            numero = float(valor)
            if numero <= 0:
                print("  -> El valor debe ser mayor que cero. Intenta de nuevo.")
                continue
            return numero
        except ValueError:
            print("  -> Ingresa solo un número (ejemplo: 40 o 40.5).")


def calcular_area_bruta(largo_cm, ancho_cm):
    return largo_cm * ancho_cm


def calcular_acero_minimo(area_bruta_cm2):
    return area_bruta_cm2 * PORCENTAJE_ACERO_MINIMO


def calcular_opciones_varillas(area_acero_minimo_cm2):
    """
    Para cada diámetro de varilla, calcula cuántas varillas se necesitan
    para cubrir el área de acero mínima, respetando un mínimo constructivo.
    """
    opciones = []
    for varilla in VARILLAS:
        cantidad = math.ceil(area_acero_minimo_cm2 / varilla["area_cm2"])
        cantidad = max(cantidad, MIN_VARILLAS_COLUMNA)
        area_total = cantidad * varilla["area_cm2"]
        opciones.append({
            "diametro": varilla["diametro"],
            "area_varilla_cm2": varilla["area_cm2"],
            "cantidad_varillas": cantidad,
            "area_total_cm2": round(area_total, 2),
        })
    return opciones


def obtener_api_key():
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        return api_key
    print("\nNo se encontró la variable de entorno GEMINI_API_KEY.")
    api_key = input("Ingresa tu API key de Gemini (no se guardará): ").strip()
    if not api_key:
        print("No se proporcionó una API key. El programa continuará solo con el cálculo local.")
        return None
    return api_key


def construir_prompt(largo_cm, ancho_cm, area_bruta, area_acero_minimo, opciones):
    lineas_opciones = "\n".join(
        f"- {o['diametro']}: {o['cantidad_varillas']} varillas "
        f"(área total {o['area_total_cm2']} cm²)"
        for o in opciones
    )
    return (
        "Eres un ingeniero estructural experto en concreto reforzado. "
        f"Una columna rectangular de concreto mide {largo_cm} cm x {ancho_cm} cm "
        f"(área bruta {area_bruta:.2f} cm²). El área mínima de acero requerida "
        f"(1% de Ag) es {area_acero_minimo:.2f} cm². Estas son las opciones calculadas "
        f"para 3 diámetros de varilla disponibles:\n{lineas_opciones}\n\n"
        "Recomienda cuál diámetro y cantidad de varillas conviene usar en la práctica, "
        "considerando facilidad constructiva, espaciamiento mínimo entre varillas dentro "
        "de la sección, y economía de acero. Responde en español, de forma clara y directa, "
        "en un máximo de 150 palabras."
    )


def consultar_gemini(prompt, api_key):
    """
    Llama a la API de Gemini usando el SDK oficial google-genai.
    Si la librería no está instalada o falla la conexión, informa el error
    sin detener el programa.
    """
    try:
        from google import genai
    except ImportError:
        print("\n(!) No está instalada la librería 'google-genai'.")
        print("    Instálala con: pip install google-genai")
        return None

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )
        return response.text
    except Exception as e:
        print(f"\n(!) Error al conectar con Gemini: {e}")
        return None


def main():
    print("=" * 60)
    print(" CALCULADORA DE ACERO MÍNIMO PARA COLUMNAS")
    print("=" * 60)

    largo_cm = pedir_dato_numerico("Largo de la columna (cm): ")
    ancho_cm = pedir_dato_numerico("Ancho de la columna (cm): ")

    area_bruta = calcular_area_bruta(largo_cm, ancho_cm)
    area_acero_minimo = calcular_acero_minimo(area_bruta)
    opciones = calcular_opciones_varillas(area_acero_minimo)

    print("\n--- RESULTADOS DEL CÁLCULO ---")
    print(f"Área bruta (Ag):           {area_bruta:.2f} cm²")
    print(f"Área de acero mínima (1%): {area_acero_minimo:.2f} cm²\n")

    print(f"{'Diámetro':<22}{'Área varilla':>14}{'Cant. varillas':>16}{'Área total':>14}")
    print("-" * 66)
    for o in opciones:
        print(
            f"{o['diametro']:<22}"
            f"{o['area_varilla_cm2']:>11.2f} cm²"
            f"{o['cantidad_varillas']:>13}"
            f"{o['area_total_cm2']:>11.2f} cm²"
        )

    api_key = obtener_api_key()
    if api_key:
        print("\nConsultando a Gemini para obtener una recomendación...\n")
        prompt = construir_prompt(largo_cm, ancho_cm, area_bruta, area_acero_minimo, opciones)
        respuesta = consultar_gemini(prompt, api_key)
        if respuesta:
            print("--- RECOMENDACIÓN DE LA IA (Gemini) ---")
            print(respuesta)
        else:
            print("No se pudo obtener una recomendación de la IA. Usa la tabla de arriba como guía.")

    print("\nProceso terminado.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nPrograma interrumpido por el usuario.")
        sys.exit(0)
