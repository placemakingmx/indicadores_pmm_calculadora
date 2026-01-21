from pathlib import Path
import os
import re
import pandas as pd
import streamlit as st

# --------------------------------------------------------------------
# Rutas base (logo y CSS)
# --------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
LOGO_PATH = BASE_DIR / "uploads" / "logo.png"
CSS_PATH = BASE_DIR / "uploads" / "styles.css"

# --------------------------------------------------------------------
# Configuración de la página
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
# Cargar CSS personalizado
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
# Descripción general
# --------------------------------------------------------------------
st.title("Indicadores de lugar")
st.markdown(
    """
Utiliza esta herramienta para obtener los valores de **Porcentaje de diversidad** y
**Puntos de accesibilidad y conexión** a partir de los datos del INEGI.

**Pasos sugeridos**  
 Abrir el mapa del INEGI.  
 Buscar o introducir coordenadas.  
 Seleccionar el área (manzana, colonia, etc.).  
 Pulsar **Consultar** y copiar los datos.
"""
)

st.link_button(
    "Abrir mapa «Espacio y datos de México» del INEGI",
    "https://www.inegi.org.mx/app/mapa/espacioydatos/default.aspx",
)

st.markdown("---")
st.subheader("Tutorial")
st.markdown("Este GIF muestra cómo obtener la información desde la página del INEGI.")
if os.path.exists("uploads/tutorial.gif"):
    st.image("uploads/tutorial.gif", width=700)
st.markdown("---")

# --------------------------------------------------------------------
# Selector de indicador
# --------------------------------------------------------------------
st.subheader("Indicadores a utilizar")

# Inicializar variables de estado (solo la primera vez)
if "resultado_diversidad" not in st.session_state:
    st.session_state["resultado_diversidad"] = None
    st.session_state["tabla_diversidad"] = None

if "resultado_PA" not in st.session_state:
    st.session_state["resultado_PA"] = None
    st.session_state["resultado_PC"] = None
    st.session_state["tabla_acceso"] = None

# Radio (el valor queda guardado en session_state["opcion_radio"])
opcion = st.radio(
    "Selecciona qué quieres calcular:",
    ("Porcentaje de diversidad", "Puntos de accesibilidad y conexión"),
    key="opcion_radio",
)

# --------------------------------------------------------------------
# ---------------------- SECCIÓN DIVERSIDAD -------------------------
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

def extraer_valores(texto: str) -> dict:
    """Devuelve un dict {código: entero} a partir del texto pegado."""
    valores = {}
    for etiqueta, codigo in ETIQUETAS:
        patron = rf"{re.escape(etiqueta)}\s+([\d,]+)\b"
        coincidencia = re.search(patron, texto)
        if coincidencia:
            num = coincidencia.group(1).replace(",", "")
            try:
                valores[codigo] = int(num)
            except ValueError:
                pass
    return valores


def mostrar_diversidad():
    """UI, cálculo y visualización del indicador de diversidad."""
    st.header("Porcentaje de diversidad (MNNAPAM)")
    st.markdown(
        """
Pega el bloque de texto que contenga **exactamente** las siguientes etiquetas:

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
        txt = (texto or "").strip()
        if not txt:
            st.error("Debes pegar el bloque de texto con los datos de población.")
            return

        valores = extraer_valores(txt)
        if len(valores) != len(ETIQUETAS):
            faltantes = [cod for _, cod in ETIQUETAS if cod not in valores]
            st.error("Faltan valores o el formato es incorrecto.")
            st.info("Variables faltantes: " + ", ".join(faltantes))
            return

        PT = valores["PT"]
        if PT == 0:
            st.error("La población total (PT) no puede ser 0.")
            return

        PF, PM, NNA, PAM = (
            valores["PF"],
            valores["PM"],
            valores["NNA"],
            valores["PAM"],
        )
        mnn_pam = ((PF + NNA * (PM / PT) + PAM * (PM / PT)) / PT) * 10

        # Tabla de desglose
        filas = [
            {
                "Código": cod,
                "Variable": eti,
                "Valor absoluto": valores[cod],
                "Porcentaje sobre PT": f"{(valores[cod] / PT) * 100:.2f} %",
            }
            for eti, cod in ETIQUETAS
        ]
        df = pd.DataFrame(filas)

        # Guardar en session_state
        st.session_state["resultado_diversidad"] = mnn_pam
        st.session_state["tabla_diversidad"] = df

    # ---------- Mostrar resultados ----------
    # Sólo si hay resultados *y* el radio activo es este indicador
    if (
        st.session_state.get("resultado_diversidad") is not None
        and st.session_state.get("opcion_radio") == "Porcentaje de diversidad"
    ):
        st.markdown("---")
        mnn = st.session_state["resultado_diversidad"]
        df = st.session_state["tabla_diversidad"]
        st.markdown(
            f"""
La proporción de mujeres, niñas, niños y adultos mayores respecto al total de la población es **{mnn:.2f}**.
"""
        )
        st.metric(label="Proporción MNNAPAM", value=f"{mnn:.2f}")

        st.markdown(
            """
### ¿Qué evalúa este indicador?  
Estimación de la proporción de grupos que pueden necesitar mayor atención (mujeres, niños, adultos mayores).  
"""
        )
        st.latex(
            r"""
\text{MNNAPAM} = \frac{ PF + NNA \cdot \frac{PM}{PT} + PAM \cdot \frac{PM}{PT} }{PT} \times 10
"""
        )
        st.subheader("Distribución porcentual")
        st.markdown(
            f'<div class="stTable tabla-scroll">{df.to_html(index=False)}</div>',
            unsafe_allow_html=True,
        )


# --------------------------------------------------------------------
# ------------------- SECCIÓN ACCESIBILIDAD -------------------------
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

def parsear_tabla_accesibilidad(texto: str) -> dict:
    """Devuelve dict {código: {en_todas,...}} a partir del texto."""
    valores = {}
    for nombre, codigo in INDICADORES_ACCESO:
        patron = rf"^{re.escape(nombre)}\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)\s*$"
        for linea in texto.splitlines():
            m = re.match(patron, linea.strip())
            if m:
                valores[codigo] = {
                    "en_todas": int(m.group(1).replace(",", "")),
                    "en_alguna": int(m.group(2).replace(",", "")),
                    "en_ninguna": int(m.group(3).replace(",", "")),
                    "no_especificado": int(m.group(4).replace(",", "")),
                    "no_aplica": int(m.group(5).replace(",", "")),
                }
                break
    return valores


def calcular_TM(valores: dict) -> int:
    """Total de manzanas (TM) usando RDC (debe coincidir con TC)."""
    rdc = valores["RDC"]
    TM = (
        rdc["en_todas"]
        + rdc["en_alguna"]
        + rdc["en_ninguna"]
        + rdc["no_especificado"]
        + rdc["no_aplica"]
    )
    if TM == 0:
        raise ValueError("El total de manzanas (TM) no puede ser 0.")
    return TM


def calcular_puntajes(valores: dict):
    """Devuelve (puntajes, TM)."""
    TM = calcular_TM(valores)

    def base(info):
        return info["en_todas"] + 0.8 * info["en_alguna"]

    puntajes = {c: base(i) / TM for c, i in valores.items()}
    return puntajes, TM


def mostrar_accesibilidad():
    """UI, cálculo y visualización del indicador de accesibilidad/conexión."""
    st.header("Puntos de accesibilidad y conexión")
    st.markdown(
        """
Pega la tabla de indicadores de accesibilidad y conexión con los siguientes encabezados (en este orden):

`Nombre del indicador En todas En alguna En ninguna No especificado No aplica`
"""
    )
    texto = st.text_area(
        "Pega aquí la tabla:",
        height=350,
        placeholder=(
            "Nombre del indicador En todas En alguna En ninguna No especificado No aplica\n"
            "Recubrimiento de la calle 29 18 0 0 0\n"
            "Rampa para silla de ruedas 3 14 30 0 0\n..."
        ),
        key="texto_acceso",
    )

    if st.button(
        "Calcular puntos de accesibilidad y conexión", key="btn_acceso"
    ):
        txt = (texto or "").strip()
        if not txt:
            st.error("Debes pegar la tabla completa.")
            return

        valores = parsear_tabla_accesibilidad(txt)

        if len(valores) != len(INDICADORES_ACCESO):
            faltantes = [
                cod
                for _, cod in INDICADORES_ACCESO
                if cod not in valores
            ]
            st.error("Faltan indicadores o el formato es incorrecto.")
            st.info("Indicadores faltantes: " + ", ".join(faltantes))
            return

        try:
            puntajes, TM = calcular_puntajes(valores)
        except ValueError as e:
            st.error(str(e))
            return

        # Cálculo de PA y PC según la fórmula original
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

        # Tabla de puntajes por indicador
        filas = [
            {
                "Código": cod,
                "Indicador": nom,
                "Puntaje": f"{puntajes.get(cod,0):.4f}",
            }
            for nom, cod in INDICADORES_ACCESO
        ]
        df_puntajes = pd.DataFrame(filas)

        # Guardar en session_state
        st.session_state["resultado_PA"] = pa
        st.session_state["resultado_PC"] = pc
        st.session_state["tabla_acceso"] = df_puntajes

    # ---------- Mostrar resultados ----------
    # Sólo si hay resultados *y* el radio activo corresponde a esta sección
    if (
        st.session_state.get("resultado_PA") is not None
        and st.session_state.get("resultado_PC") is not None
        and st.session_state.get("opcion_radio")
        == "Puntos de accesibilidad y conexión"
    ):
        st.markdown("---")
        pa = st.session_state["resultado_PA"]
        pc = st.session_state["resultado_PC"]
        df = st.session_state["tabla_acceso"]

        st.subheader("Puntajes agregados")
        col1, col2 = st.columns(2)
        col1.metric("Puntaje Accesibilidad (PA)", f"{pa:.2f}")
        col2.metric("Puntaje Conexiones (PC)", f"{pc:.2f}")

        st.markdown(
            """
### ¿Qué evalúan PA y PC?  
- **PA (Accesibilidad):** Elementos que facilitan el desplazamiento peatonal.  
- **PC (Conexiones):** Grado de conectividad del área con el resto de la ciudad.
"""
        )
        st.latex(
            r"""
\small
PA = 0.5\cdot RDC + 2.0\cdot RSR + 2.0\cdot PP + 1.0\cdot BQ
    + 0.5\cdot GN + 1.0\cdot SA + 1.0\cdot PTP + 2.0\cdot SRPP
"""
        )
        st.latex(
            r"""
\small
PC = 1.0\cdot RDC + 1.0\cdot BQ + 1.0\cdot GN + 1.5\cdot CV
    + 0.5\cdot CC + 1.0\cdot LNC + 1.0\cdot SP
    + 1.0\cdot PTP + 1.0\cdot EBC + 1.0\cdot TC
"""
        )
        st.subheader("Puntaje por indicador")
        st.markdown(
            f'<div class="stTable tabla-scroll">{df.to_html(index=False)}</div>',
            unsafe_allow_html=True,
        )

# --------------------------------------------------------------------
# Llamada a la sección correspondiente según el radio
# --------------------------------------------------------------------
if opcion == "Porcentaje de diversidad":
    mostrar_diversidad()
else:
    mostrar_accesibilidad()
