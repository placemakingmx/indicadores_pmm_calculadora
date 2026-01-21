from pathlib import Path
import os
import re
import pandas as pd
import streamlit as st

# --------------------------------------------------------------------
# Rutas base (para logo y CSS)
# --------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
LOGO_PATH = BASE_DIR / "uploads" / "logo.png"
CSS_PATH = BASE_DIR / "uploads" / "styles.css"

# --------------------------------------------------------------------
# Configuración de la página (título, icono, layout)
# --------------------------------------------------------------------
icon_path = "uploads/carita.png"
st.set_page_config(
    page_title="Indicadores del lugar",
    page_icon=str(icon_path) if os.path.exists(icon_path) else None,
    layout="centered",
)

# --------------------------------------------------------------------
# Ocultar menú y footer de Streamlit
# --------------------------------------------------------------------
hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# --------------------------------------------------------------------
# Cargar estilos personalizados (styles.css)
# --------------------------------------------------------------------
def cargar_css_local(css_path: Path) -> None:
    if css_path.exists():
        with open(css_path, "r", encoding="utf-8") as f:
            css = f.read()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

cargar_css_local(CSS_PATH)

# --------------------------------------------------------------------
# Logo en la parte superior
# --------------------------------------------------------------------
if LOGO_PATH.exists():
    st.image(str(LOGO_PATH), width=170)

# --------------------------------------------------------------------
# Configuración general y descripción inicial
# --------------------------------------------------------------------
st.title("Indicadores de lugar")
st.markdown(
    """
Utiliza esta herramienta para obtener los valores de **Porcentaje de diversidad** y
**Puntos de accesibilidad y conexión** a partir de los datos del INEGI:
**"Espacio y datos de México"**.

**Pasos sugeridos:**
1. Haz clic en el botón para abrir el mapa de INEGI en una nueva ventana.
2. Usa el buscador o las coordenadas (si las tienes) para ubicar el lugar.
3. Elige el área a consultar (por ejemplo, una manzana, colonia o polígono de interés).
4. Haz clic en **"Consultar"** en la interfaz del mapa para obtener los datos.
"""
)

st.link_button(
    "Abrir mapa «Espacio y datos de México» del INEGI",
    "https://www.inegi.org.mx/app/mapa/espacioydatos/default.aspx",
)

st.markdown("---")
st.subheader("Tutorial:")
st.markdown("Este GIF te muestra cómo obtener la información desde la página del INEGI.")
if os.path.exists("uploads/tutorial.gif"):
    st.image("uploads/tutorial.gif", width=700)
st.markdown("---")

# --------------------------------------------------------------------
# Selector de tipo de consulta + estado
# --------------------------------------------------------------------
st.subheader("Indicadores a utilizar")

# Inicializar variables de estado (SOLO la primera vez)
if "resultado_diversidad" not in st.session_state:
    st.session_state["resultado_diversidad"] = None
    st.session_state["tabla_diversidad"] = None

if "resultado_PA" not in st.session_state:
    st.session_state["resultado_PA"] = None
    st.session_state["resultado_PC"] = None
    st.session_state["tabla_acceso"] = None

# Radio con key (guardamos en session_state["opcion_radio"])
opcion = st.radio(
    "Selecciona qué quieres calcular:",
    ("Porcentaje de diversidad", "Puntos de accesibilidad y conexión"),
    key="opcion_radio",
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
    """Busca en el texto cada etiqueta y extrae el entero."""
    valores = {}
    for etiqueta, codigo in ETIQUETAS:
        patron = rf"{re.escape(etiqueta)}\s+([\d,]+)\b"
        coincidencia = re.search(patron, texto)
        if coincidencia:
            num_str = coincidencia.group(1).replace(",", "")
            try:
                valores[codigo] = int(num_str)
            except ValueError:
                pass
    return valores

# --------------------------------------------------------------------
# Sección 1: Porcentaje de diversidad (MNNAPAM)
# --------------------------------------------------------------------
def seccion_diversidad():
    st.header("Porcentaje de diversidad (MNNAPAM)")
    st.markdown(
        """
Pega el bloque de texto que contenga, con estas etiquetas **exactas**:

- Población total  
- Población femenina  
- Población masculina  
- Población de 0 a 14 años  
- Población de 15 a 29 años  
- Población de 30 a 59 años  
- Población de 60 años y más  
- Población con discapacidad
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
        key="texto_diversidad",
    )

    if st.button("Calcular indicadores de diversidad", key="btn_diversidad"):
        texto_limpio = (texto or "").strip()
        if not texto_limpio:
            st.error("Por favor, copia y pega el bloque de texto con los datos de población.")
        else:
            valores = extraer_valores(texto_limpio)

            if len(valores) != len(ETIQUETAS):
                faltantes = [cod for _, cod in ETIQUETAS if cod not in valores]
                st.error(
                    "No se detectaron correctamente los 8 valores requeridos. "
                    "Copia y pega nuevamente el bloque completo."
                )
                if faltantes:
                    st.info("Variables faltantes o mal detectadas: " + ", ".join(faltantes))
            else:
                PT = valores.get("PT", 0)
                if PT == 0:
                    st.error("La Población total (PT) no puede ser 0.")
                else:
                    PF = valores.get("PF", 0)
                    PM = valores.get("PM", 0)
                    NNA = valores.get("NNA", 0)
                    PAM = valores.get("PAM", 0)

                    mnn_pam = ((PF + NNA * (PM / PT) + PAM * (PM / PT)) / PT) * 10

                    filas = []
                    for etiqueta, codigo in ETIQUETAS:
                        valor_abs = valores.get(codigo, 0)
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

                    st.session_state["resultado_diversidad"] = mnn_pam
                    st.session_state["tabla_diversidad"] = df

    # --------------------------------------------------------------
    # MOSTRAR RESULTADOS SOLO SI:
    # - hay algo calculado Y
    # - el radio actual es "Porcentaje de diversidad"
    # --------------------------------------------------------------
    if (
        st.session_state.get("resultado_diversidad") is not None
        and st.session_state.get("opcion_radio") == "Porcentaje de diversidad"
    ):
        st.markdown("---")
        mnn_pam = st.session_state["resultado_diversidad"]
        df = st.session_state["tabla_diversidad"]

        st.markdown(
            f"""
La proporción de mujeres, niñas, niños y adolescentes, y personas adultas mayores
respecto al total de la población es de **{mnn_pam:.2f}**.
"""
        )
        st.metric(label="Proporción MNNAPAM", value=f"{mnn_pam:.2f}")

        st.markdown("### ¿Qué evalúa este indicador?")
        st.markdown(
            """
Este indicador estima la proporción de grupos que pueden tener mayores necesidades
de cuidado y accesibilidad en el área.
"""
        )

        st.latex(
            r"""
\text{MNNAPAM} = \frac{ PF + NNA \cdot \frac{PM}{PT} + PAM \cdot \frac{PM}{PT} }{PT} \times 10
"""
        )

        st.subheader("Distribución porcentual respecto a la población total")
        html_table = st.session_state["tabla_diversidad"].to_html(index=False)
        st.markdown(
            f'<div class="stTable tabla-scroll">{html_table}</div>',
            unsafe_allow_html=True,
        )

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
    valores = {}
    for nombre, codigo in INDICADORES_ACCESO:
        patron = rf"^{re.escape(nombre)}\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)\s*$"
        encontrado = False
        for linea in texto.splitlines():
            linea = linea.strip()
            if not linea:
                continue
            m = re.match(patron, linea)
            if m:
                valores[codigo] = {
                    "en_todas": int(m.group(1).replace(",", "")),
                    "en_alguna": int(m.group(2).replace(",", "")),
                    "en_ninguna": int(m.group(3).replace(",", "")),
                    "no_especificado": int(m.group(4).replace(",", "")),
                    "no_aplica": int(m.group(5).replace(",", "")),
                }
                encontrado = True
                break
        if not encontrado:
            continue
    return valores

def calcular_TM(valores_indicadores: dict) -> int:
    info_rdc = valores_indicadores["RDC"]
    TM = (
        info_rdc["en_todas"]
        + info_rdc["en_alguna"]
        + info_rdc["en_ninguna"]
        + info_rdc["no_especificado"]
        + info_rdc["no_aplica"]
    )
    if TM == 0:
        raise ValueError("El total de manzanas (TM) no puede ser 0. Verifica la tabla.")
    return TM

def calcular_puntajes_acceso(valores_indicadores: dict):
    TM = calcular_TM(valores_indicadores)

    def base(info):
        return info["en_todas"] + 0.8 * info["en_alguna"]

    puntajes = {}
    for codigo, info in valores_indicadores.items():
        puntajes[codigo] = base(info) / TM

    return puntajes, TM

# --------------------------------------------------------------------
# Sección 2: Puntos de accesibilidad y conexión
# --------------------------------------------------------------------
def seccion_accesibilidad_conexion():
    st.header("Puntos de accesibilidad y conexión")
    st.markdown(
        """
Pega la tabla de indicadores de accesibilidad y conexión, con los encabezados:

`Nombre del indicador En todas En alguna En ninguna No especificado No aplica`
"""
    )

    texto_tabla = st.text_area(
        "Pega aquí la tabla de accesibilidad y conexión:",
        height=350,
        placeholder=(
            "Nombre del indicador En todas En alguna En ninguna No especificado No aplica\n"
            "Recubrimiento de la calle 29 18 0 0 0\n"
            "Rampa para silla de ruedas 3 14 30 0 0\n"
            "..."
        ),
        key="texto_acceso",
    )

    if st.button("Calcular puntos de accesibilidad y conexión", key="btn_acceso"):
        texto_limpio = (texto_tabla or "").strip()
        if not texto_limpio:
            st.error("Por favor, copia y pega la tabla completa de accesibilidad y conexión.")
        else:
            valores_indicadores = parsear_tabla_accesibilidad(texto_limpio)
            if len(valores_indicadores) != len(INDICADORES_ACCESO):
                faltantes = [
                    cod for _, cod in INDICADORES_ACCESO
                    if cod not in valores_indicadores
                ]
                st.error(
                    "No se detectaron correctamente todos los indicadores requeridos.\n"
                    "Revisa que los nombres y el formato de la tabla coincidan."
                )
                if faltantes:
                    st.info(
                        "Indicadores faltantes o mal detectados (por código): "
                        + ", ".join(faltantes)
                    )
            else:
                try:
                    puntajes, TM = calcular_puntajes_acceso(valores_indicadores)
                except ValueError as e:
                    st.error(str(e))
                else:
                    st.success(f"Total de manzanas (TM) calculado correctamente: TM = {TM}")

                    pa = (
                        puntajes["RDC"] * 0.5
                        + puntajes["RSR"] * 2.0
                        + puntajes["PP"] * 2.0
                        + puntajes["BQ"] * 1.0
                        + puntajes["GN"] * 0.5
                        + puntajes["SA"] * 1.0
                        + puntajes["PTP"] * 1.0
                        + puntajes["SRPP"] * 2.0
                    )

                    pc = (
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

                    filas_puntajes = []
                    for nombre, codigo in INDICADORES_ACCESO:
                        filas_puntajes.append(
                            {
                                "Código": codigo,
                                "Indicador": nombre,
                                "Puntaje": f"{puntajes.get(codigo, 0):.4f}",
                            }
                        )
                    df_puntajes = pd.DataFrame(filas_puntajes)

                    st.session_state["resultado_PA"] = pa
                    st.session_state["resultado_PC"] = pc
                    st.session_state["tabla_acceso"] = df_puntajes

    # --------------------------------------------------------------
    # MOSTRAR RESULTADOS SOLO SI:
    # - hay algo calculado (PA y PC) Y
    # - el radio actual es "Puntos de accesibilidad y conexión"
    # --------------------------------------------------------------
    if (
        st.session_state.get("resultado_PA") is not None
        and st.session_state.get("resultado_PC") is not None
        and st.session_state.get("opcion_radio") == "Puntos de accesibilidad y conexión"
    ):
        st.markdown("---")
        pa = st.session_state["resultado_PA"]
        pc = st.session_state["resultado_PC"]
        df_puntajes = st.session_state["tabla_acceso"]

        st.subheader("Puntajes agregados")
        col1, col2 = st.columns(2)
        col1.metric("Puntaje Accesibilidad (PA)", f"{pa:.2f}")
        col2.metric("Puntaje Conexiones (PC)", f"{pc:.2f}")

        st.markdown(
            """
### ¿Qué evalúan PA y PC?
- **PA (Puntaje de Accesibilidad):** elementos que facilitan caminar y moverse con seguridad.
- **PC (Puntaje de Conexiones):** qué tan bien conectado está el área con el resto de la ciudad.
"""
        )

        st.subheader("Puntaje por indicador")
        html_puntajes = df_puntajes.to_html(index=False)
        st.markdown(
            f'<div class="stTable tabla-scroll">{html_puntajes}</div>',
            unsafe_allow_html=True,
        )

# --------------------------------------------------------------------
# Mostrar la sección según la opción elegida
# --------------------------------------------------------------------
if opcion == "Porcentaje de diversidad":
    seccion_diversidad()
else:
    seccion_accesibilidad_conexion()
