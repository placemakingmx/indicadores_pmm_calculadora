from pathlib import Path
import streamlit as st
import pandas as pd
import re


# --------------------------------------------------------------------
# Rutas base (para logo y CSS)
# --------------------------------------------------------------------
BASE_DIR = Path(__file__).parent
LOGO_PATH = BASE_DIR / "uploads" / "logo.png"
CSS_PATH = BASE_DIR / "uploads" / "styles.css"


# --------------------------------------------------------------------
# Configuración de la página (título, icono, layout)
# --------------------------------------------------------------------
st.set_page_config(
    page_title="Indicadores de lugar",
    page_icon=str(LOGO_PATH) if LOGO_PATH.exists() else None,
    layout="left",
)

# --------------------------------------------------------------------
# Cargar estilos personalizados (styles.css)
# --------------------------------------------------------------------
def cargar_css_local(css_path: Path) -> None:
    if css_path.exists():
        with open(css_path, "r", encoding="utf-8") as f:
            css = f.read()
        # .stApp es el contenedor principal de la app
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


cargar_css_local(CSS_PATH)


# --------------------------------------------------------------------
# Logo en la parte superior
# --------------------------------------------------------------------
if LOGO_PATH.exists():
    st.image(str(LOGO_PATH), width=170)  # ajusta el ancho si quieres


# --------------------------------------------------------------------
# Configuración general y descripción inicial
# --------------------------------------------------------------------
st.title("Indicadores de lugar")

st.markdown(
    """
Utiliza esta herramienta para obtener los valores de **Porcentaje de diversidad** y **Puntos de accesibilidad y conexión**
a partir de los datos del INEGI: **“Espacio y datos de México”**.

**Pasos sugeridos:**

1. Haz clic en el botón para abrir el mapa de INEGI en una nueva ventana.
2. Usa el buscador o las coordenadas (si las tienes) para ubicar el lugar.
3. Elige el área a consultar (por ejemplo, una manzana, colonia o polígono de interés).
4. Haz clic en **“Consultar”** en la interfaz del mapa para obtener los datos.
"""
)

# Botón que abre el mapa de INEGI en otra pestaña
st.link_button(
    "Abrir mapa «Espacio y datos de México» del INEGI",
    "https://www.inegi.org.mx/app/mapa/espacioydatos/default.aspx",
)

st.markdown("---")
st.subheader("Referencia visual")
st.markdown(
    "_Aquí se mostrará un GIF de referencia sobre cómo usar el mapa de INEGI (placeholder)._"
)
# Cuando tengas el GIF, podrás reemplazar la línea anterior por algo como:
# st.image("ruta/al/gif_referencia.gif", caption="Cómo consultar el área en el mapa de INEGI", use_column_width=True)

st.markdown("---")


# --------------------------------------------------------------------
# Selector de tipo de consulta
# --------------------------------------------------------------------
opcion = st.radio(
    "¿Qué quieres consultar?",
    ("Porcentaje de diversidad", "Puntos de accesibilidad y conexión"),
)


# --------------------------------------------------------------------
# Definición de etiquetas y funciones comunes (Sección diversidad)
# --------------------------------------------------------------------
ETIQUETAS = [
    ("Población total", "PT"),
    ("Población femenina", "PF"),
    ("Población masculina", "PM"),
    ("Población de 0 a 14 años", "NNA"),
    ("Población de 15 a 29 años", "PJ"),
    ("Población de 30 a 59 años", "PA"),
    ("Población de 60 años y más", "PAM"),
    ("Población con discapacidad", "PD"),
]


def extraer_valores(texto: str):
    """
    Busca en el texto cada etiqueta y extrae el entero
    (permitiendo separadores de miles con comas).
    Devuelve un dict con claves = códigos (PT, PF...) y valores = int.
    """
    valores = {}
    for etiqueta, codigo in ETIQUETAS:
        # Busca: 'Etiqueta' seguido de espacios y un número que puede tener comas (ej. 6,822)
        patron = rf"{re.escape(etiqueta)}\s+([\d,]+)\b"
        coincidencia = re.search(patron, texto)
        if coincidencia:
            num_str = coincidencia.group(1).replace(",", "")  # quitar comas
            try:
                valores[codigo] = int(num_str)
            except ValueError:
                # Si por alguna razón no es entero, se considera no encontrado
                pass
    return valores


# --------------------------------------------------------------------
# Sección 1: Porcentaje de diversidad (MNNAPAM)
# --------------------------------------------------------------------
def seccion_diversidad():
    st.header("Porcentaje de diversidad (MNNAPAM)")

    st.markdown(
        """
Pega el bloque de texto que contenga, con estas etiquetas **exactas**
(puede haber líneas extra, pero se deben mantener estas líneas y nombres):

- Población total
- Población femenina
- Población masculina
- Población de 0 a 14 años
- Población de 15 a 29 años
- Población de 30 a 59 años
- Población de 60 años y más
- Población con discapacidad

Los valores pueden venir con separadores de miles con coma (por ejemplo, 6,822),
y se convertirán automáticamente a enteros sin comas.
"""
    )

    texto = st.text_area(
        "Pega aquí el texto con los datos de población:",
        height=220,
        placeholder=(
            "Población total 6,822\n"
            "Población femenina 3,597\n"
            "Población masculina 3,224\n"
            "Población de 0 a 14 años 1,302\n"
            "Población de 15 a 29 años 1,723\n"
            "Población de 30 a 59 años 2,781\n"
            "Población de 60 años y más 1,009\n"
            "Población con discapacidad 264"
        ),
    )

    if st.button("Calcular indicadores de diversidad"):
        texto_limpio = (texto or "").strip()
        if not texto_limpio:
            st.error(
                "Por favor, copia y pega el bloque de texto con los datos de población."
            )
            return

        valores = extraer_valores(texto_limpio)

        # Validar que se encontraron las 8 variables
        if len(valores) != len(ETIQUETAS):
            faltantes = [cod for _, cod in ETIQUETAS if cod not in valores]
            st.error(
                "No se detectaron correctamente los 8 valores requeridos. "
                "Por favor, copia y pega nuevamente el bloque completo desde "
                "'Población total' hasta 'Población con discapacidad'."
            )
            if faltantes:
                st.info(
                    "Variables faltantes o mal detectadas: "
                    + ", ".join(faltantes)
                )
            return

        PT = valores["PT"]
        PF = valores["PF"]
        PM = valores["PM"]
        NNA = valores["NNA"]
        PJ = valores["PJ"]
        PA = valores["PA"]
        PAM = valores["PAM"]
        PD = valores["PD"]

        if PT == 0:
            st.error("La Población total (PT) no puede ser 0. Verifica los datos.")
            return

        # Cálculo de la proporción MNNAPAM
        # Fórmula: (PF + NNA*(PM/PT) + PAM*(PM/PT)) / PT
        mnn_pam = (PF + NNA * (PM / PT) + PAM * (PM / PT)) / PT

        # Texto explicativo
        st.markdown(
            f"""
La proporción de mujeres, niñas, niños y adolescentes, y personas adultas mayores
respecto al total de la población es de **{mnn_pam:.2f}**.

Copia y pega el siguiente valor en el cuestionario.
"""
        )

        # Métrica (fácil de copiar y pegar)
        st.metric(label="Proporción MNNAPAM", value=f"{mnn_pam:.2f}")

        # Construcción de la tabla
        filas = []
        for etiqueta, codigo in ETIQUETAS:
            valor_abs = valores[codigo]
            if codigo == "PT":
                porcentaje = 100.0
            else:
                porcentaje = (valor_abs / PT) * 100.0
            filas.append(
                {
                    "Código": codigo,
                    "Variable": etiqueta,
                    "Valor absoluto": valor_abs,
                    "Porcentaje sobre PT": f"{porcentaje:.2f} %",
                }
            )

        df = pd.DataFrame(filas)
        st.subheader("Distribución porcentual respecto a la población total")
        st.dataframe(df, use_container_width=True)


# --------------------------------------------------------------------
# Definición de indicadores de accesibilidad / conexión
# --------------------------------------------------------------------
INDICADORES_ACCESO = [
    ("Recubrimiento de la calle", "RDC"),
    ("Rampa para silla de ruedas", "RSR"),
    ("Paso peatonal", "PP"),
    ("Banqueta", "BQ"),
    ("Guarnición", "GN"),
    ("Ciclovía", "CV"),
    ("Ciclocarril", "CC"),
    ("Alumbrado público", "AP"),
    ("Letrero con nombre de la calle", "LNC"),
    ("Teléfono público", "TP"),
    ("Árboles y palmeras", "ARB"),
    ("Semáforo para peatón", "SP"),
    ("Semáforo auditivo", "SA"),
    ("Parada de transporte colectivo", "PTP"),
    ("Estación para bicicleta", "EBC"),
    ("Alcantarilla de drenaje pluvial", "ADP"),
    ("Transporte colectivo", "TC"),
    ("Sin restricción del paso a peatones", "SRPP"),
    ("Sin restricción del paso a automóviles", "SRPA"),
    ("Puesto semifijo", "PS"),
    ("Puesto ambulante", "PA"),
]


def parsear_tabla_accesibilidad(texto: str):
    """
    Busca en el texto cada indicador de accesibilidad/conexión
    y extrae los 5 enteros (En todas, En alguna, En ninguna,
    No especificado, No aplica), permitiendo separadores de miles
    con comas.

    Devuelve un dict:
    {
      "RDC": {
        "codigo": "RDC",
        "nombre": "...",
        "en_todas": int,
        "en_alguna": int,
        "en_ninguna": int,
        "no_especificado": int,
        "no_aplica": int,
      },
      ...
    }
    """
    valores = {}

    for nombre, codigo in INDICADORES_ACCESO:
        # Patrón: Nombre + 5 números (con o sin comas) separados por espacios
        # Ejemplo:
        # "Recubrimiento de la calle 29 18 0 0 0"
        # o "Recubrimiento de la calle 1,029 18 0 0 0"
        patron = rf"^{re.escape(nombre)}\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)\s*$"
        encontrado = False

        for linea in texto.splitlines():
            linea = linea.strip()
            if not linea:
                continue

            m = re.match(patron, linea)
            if m:
                # Quitar comas de cada número antes de convertir
                en_todas = int(m.group(1).replace(",", ""))
                en_alguna = int(m.group(2).replace(",", ""))
                en_ninguna = int(m.group(3).replace(",", ""))
                no_especificado = int(m.group(4).replace(",", ""))
                no_aplica = int(m.group(5).replace(",", ""))

                valores[codigo] = {
                    "codigo": codigo,
                    "nombre": nombre,
                    "en_todas": en_todas,
                    "en_alguna": en_alguna,
                    "en_ninguna": en_ninguna,
                    "no_especificado": no_especificado,
                    "no_aplica": no_aplica,
                }
                encontrado = True
                break

        # Si no se encontró la línea correspondiente a este indicador,
        # no se añade al dict; se reportará después.
        if not encontrado:
            continue

    return valores


def calcular_TM(valores_indicadores: dict) -> int:
    """
    Calcula TM a partir de RDC y TC y verifica que sean iguales.
    """
    # Recubrimiento de la calle (RDC)
    info_rdc = valores_indicadores["RDC"]
    TM_rdc = (
        info_rdc["en_todas"]
        + info_rdc["en_alguna"]
        + info_rdc["en_ninguna"]
        + info_rdc["no_especificado"]
        + info_rdc["no_aplica"]
    )

    # Transporte colectivo (TC)
    info_tc = valores_indicadores["TC"]
    TM_tc = (
        info_tc["en_todas"]
        + info_tc["en_alguna"]
        + info_tc["en_ninguna"]
        + info_tc["no_especificado"]
        + info_tc["no_aplica"]
    )

    if TM_rdc == 0 or TM_tc == 0:
        raise ValueError("El total de manzanas (TM) no puede ser 0. Verifica la tabla.")

    if TM_rdc != TM_tc:
        raise ValueError(
            f"El total de manzanas calculado en 'Recubrimiento de la calle' (TM={TM_rdc}) "
            f"no coincide con el de 'Transporte colectivo' (TM={TM_tc})."
        )

    return TM_rdc


def calcular_puntajes_acceso(valores_indicadores: dict):
    """
    Calcula TM y los puntajes por indicador, de acuerdo con las fórmulas especificadas.

    Devuelve (puntajes, TM), donde:
      - puntajes: dict {codigo: valor_float}
      - TM: entero con el total de manzanas
    """
    TM = calcular_TM(valores_indicadores)

    def base(info):
        return info["en_todas"] + 0.8 * info["en_alguna"]

    puntajes = {}

    # Indicadores con división directa sobre TM
    codigos_TM_directo = [
        "RDC",
        "RSR",
        "PP",
        "BQ",
        "GN",
        "CV",
        "CC",
        "AP",
        "LNC",
        "TP",
        "ARB",
        "SP",
        "SA",
        "ADP",
        "PS",
        "PA",
    ]

    for codigo in codigos_TM_directo:
        info = valores_indicadores[codigo]
        puntajes[codigo] = base(info) / TM

    # PTP: divide entre (TM / 3)
    info_ptp = valores_indicadores["PTP"]
    puntajes["PTP"] = base(info_ptp) / (TM / 3.0)

    # EBC: divide entre (TM / 4)
    info_ebc = valores_indicadores["EBC"]
    puntajes["EBC"] = base(info_ebc) / (TM / 4.0)

    # TC: divide entre (TM / 3)
    info_tc = valores_indicadores["TC"]
    puntajes["TC"] = base(info_tc) / (TM / 3.0)

    # SRPP y SRPA: (TM - base) / TM
    info_srpp = valores_indicadores["SRPP"]
    puntajes["SRPP"] = (TM - base(info_srpp)) / TM

    info_srpa = valores_indicadores["SRPA"]
    puntajes["SRPA"] = (TM - base(info_srpa)) / TM

    return puntajes, TM


# --------------------------------------------------------------------
# Sección 2: Puntos de accesibilidad y conexión
# --------------------------------------------------------------------
def seccion_accesibilidad_conexion():
    st.header("Puntos de accesibilidad y conexión")

    st.markdown(
        """
Pega la tabla de indicadores de accesibilidad y conexión, con los siguientes encabezados
de columna (en este orden):

Nombre del indicador: En todas - En alguna - En ninguna - No especificado - No aplica

Los valores pueden tener separadores de miles con coma (por ejemplo, 1,029),
y se convertirán automáticamente a enteros sin comas.

Ejemplo de filas (los números son solo ilustrativos, pero el texto del nombre debe ser exacto):

Recubrimiento de la calle 29 18 0 0 0  
Rampa para silla de ruedas 3 14 30 0 0  

Se ignorará cualquier otra línea, como la cabecera o la fecha de actualización.
"""
    )

    texto_tabla = st.text_area(
        "Pega aquí la tabla de accesibilidad y conexión:",
        height=350,
        placeholder=(
            "Nombre del indicador En todas En alguna En ninguna No especificado No aplica\n"
            "Recubrimiento de la calle 29 18 0 0 0\n"
            "Rampa para silla de ruedas 3 14 30 0 0\n"
            "Paso peatonal 2 28 17 0 0\n"
            "Banqueta 14 31 2 0 0\n"
            "Guarnición 12 34 1 0 0\n"
            "Ciclovía 0 0 47 0 0\n"
            "Ciclocarril 0 0 47 0 0\n"
            "Alumbrado público 3 42 2 0 0\n"
            "Letrero con nombre de la calle 7 36 4 0 0\n"
            "Teléfono público 0 9 38 0 0\n"
            "Árboles y palmeras 1 38 8 0 0\n"
            "Semáforo para peatón 1 3 43 0 0\n"
            "Semáforo auditivo 0 0 47 0 0\n"
            "Parada de transporte colectivo 0 6 41 0 0\n"
            "Estación para bicicleta 0 1 46 0 0\n"
            "Alcantarilla de drenaje pluvial 1 12 34 0 0\n"
            "Transporte colectivo 5 30 12 0 0\n"
            "Sin restricción del paso a peatones 0 4 43 0 0\n"
            "Sin restricción del paso a automóviles 0 4 43 0 0\n"
            "Puesto semifijo 0 8 39 0 0\n"
            "Puesto ambulante 0 12 35 0 0\n"
            "Fecha de actualización: 2020"
        ),
    )

    if st.button("Calcular puntos de accesibilidad y conexión"):
        texto_limpio = (texto_tabla or "").strip()
        if not texto_limpio:
            st.error(
                "Por favor, copia y pega la tabla completa de accesibilidad y conexión."
            )
            return

        # 1) Parsear tabla
        valores_indicadores = parsear_tabla_accesibilidad(texto_limpio)

        # 2) Validar que se encontraron los 21 indicadores
        codigos_esperados = [cod for _, cod in INDICADORES_ACCESO]
        codigos_encontrados = list(valores_indicadores.keys())

        if len(valores_indicadores) != len(INDICADORES_ACCESO):
            faltantes = [c for c in codigos_esperados if c not in codigos_encontrados]
            st.error(
                "No se detectaron correctamente todos los indicadores requeridos.\n\n"
                "Por favor, copia y pega nuevamente la tabla completa desde "
                "'Recubrimiento de la calle' hasta 'Puesto ambulante', "
                "incluyendo los encabezados de columna."
            )
            if faltantes:
                st.info(
                    "Indicadores faltantes o mal detectados (por código): "
                    + ", ".join(faltantes)
                )
            return

        # 3) Mostrar tabla de control de los valores leídos
        filas_valores = []
        for nombre, codigo in INDICADORES_ACCESO:
            info = valores_indicadores[codigo]
            filas_valores.append(
                {
                    "Código": codigo,
                    "Indicador": nombre,
                    "En todas": info["en_todas"],
                    "En alguna": info["en_alguna"],
                    "En ninguna": info["en_ninguna"],
                    "No especificado": info["no_especificado"],
                    "No aplica": info["no_aplica"],
                }
            )
        df_valores = pd.DataFrame(filas_valores)
        st.subheader("Valores detectados en la tabla")
        st.dataframe(df_valores, use_container_width=True)

        # 4) Calcular TM y puntajes individuales
        try:
            puntajes, TM = calcular_puntajes_acceso(valores_indicadores)
        except ValueError as e:
            st.error(str(e))
            return

        st.success(f"Total de manzanas (TM) calculado correctamente: TM = {TM}")

        # 5) Calcular Puntaje Accesibilidad y Puntaje Conexiones
        puntaje_accesibilidad = (
            puntajes["RDC"] * 0.5
            + puntajes["RSR"] * 2.0
            + puntajes["PP"] * 2.0
            + puntajes["BQ"] * 1.0
            + puntajes["GN"] * 0.5
            + puntajes["SA"] * 1.0
            + puntajes["PTP"] * 1.0
            + puntajes["SRPP"] * 2.0
        )

        puntaje_conexiones = (
            puntajes["RDC"] * 1.0
            + puntajes["BQ"] * 1.0
            + puntajes["GN"] * 1.0
            + puntajes["CV"] * 1.5
            + puntajes["CC"] * 0.5
            + puntajes["LNC"] * 1.0
            + puntajes["SP"] * 1.0
            + puntajes["PTP"] * 1.0
            + puntajes["EBC"] * 1.0
            + puntajes["TC"] * 1.0
        )

        # 6) Mostrar métricas para copiar y pegar
        st.subheader("Puntajes agregados")
        col1, col2 = st.columns(2)
        with col1:
            st.metric(
                label="Puntaje Accesibilidad",
                value=f"{puntaje_accesibilidad:.2f}",
            )
        with col2:
            st.metric(
                label="Puntaje Conexiones",
                value=f"{puntaje_conexiones:.2f}",
            )

        # 7) Tabla con el valor (puntaje) de cada variable
        filas_puntajes = []
        for nombre, codigo in INDICADORES_ACCESO:
            filas_puntajes.append(
                {
                    "Código": codigo,
                    "Indicador": nombre,
                    "Puntaje": round(puntajes[codigo], 4),
                    "Puntaje (2 decimales)": f"{puntajes[codigo]:.2f}",
                }
            )
        df_puntajes = pd.DataFrame(filas_puntajes)
        st.subheader("Puntaje por indicador")
        st.dataframe(df_puntajes, use_container_width=True)


# --------------------------------------------------------------------
# Mostrar la sección según la opción elegida
# --------------------------------------------------------------------
if opcion == "Porcentaje de diversidad":
    seccion_diversidad()
else:
    seccion_accesibilidad_conexion()
