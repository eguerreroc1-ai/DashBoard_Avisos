"""
theme.py — Paleta ENERGY (fuente única de colores).

Para cambiar la paleta de TODO el proyecto (gráficas + home) edite solo
los cinco colores de marca de esta sección. El CSS de /assets usa los
mismos valores (ver bloque :root en assets/style.css).
"""

# ------------------------------------------------------------
# 1) Colores de marca (paleta oficial)
# ------------------------------------------------------------
NAVY   = "#10274F"   # Azul profundo   (más oscuro)
NAVY_2 = "#183B78"   # Azul marino
BLUE   = "#1F4D9C"   # Azul corporativo (primario)
BLUE_2 = "#2863C9"   # Azul intenso
CYAN   = "#3078F2"   # Azul brillante   (acento)

BRAND = [
    ("Azul profundo", NAVY, "Fondos oscuros, texto sobre claro"),
    ("Azul marino", NAVY_2, "Variación oscura"),
    ("Azul corporativo", BLUE, "Color primario"),
    ("Azul intenso", BLUE_2, "Variación media"),
    ("Azul brillante", CYAN, "Acento y énfasis"),
]


# ------------------------------------------------------------
# 2) Utilidades para derivar tonos a partir de la marca
# ------------------------------------------------------------
def _rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def mix(c1, c2, t):
    """Mezcla c1 -> c2. t=0 devuelve c1, t=1 devuelve c2."""
    a, b = _rgb(c1), _rgb(c2)
    return "#{:02X}{:02X}{:02X}".format(*(round(x + (y - x) * t) for x, y in zip(a, b)))


def tint(c, t):
    """Aclara un color mezclándolo con blanco (t entre 0 y 1)."""
    return mix(c, "#FFFFFF", t)


# ------------------------------------------------------------
# 3) Colores derivados y semánticos
# ------------------------------------------------------------
LIGHT_BLUE = tint(CYAN, 0.50)
GREEN = "#3B6D11"    # semántico: cumplimiento
RED = "#E24B4A"      # semántico: abierto / atraso / alerta
AMBER = "#BA7517"    # semántico: acumulado / advertencia
TEXT = "#1A2540"
MUTED = "#3D4F6B"
GRID = "#E8EDF4"
NEUTRAL = "#A9B6C3"

DERIVED = [
    ("Brillante 50%", tint(CYAN, 0.50)),
    ("Brillante 75%", tint(CYAN, 0.75)),
    ("Corporativo 50%", tint(BLUE, 0.50)),
    ("Corporativo 80%", tint(BLUE, 0.80)),
    ("Corporativo 92%", tint(BLUE, 0.92)),
]

# Series categóricas (Pareto, líneas por prioridad): marca + tonos claros
# intercalados para que las series vecinas se distingan.
INSTITUTIONAL_PALETTE = [
    NAVY, CYAN, NAVY_2, tint(CYAN, 0.45), BLUE,
    tint(BLUE, 0.50), BLUE_2, tint(NAVY_2, 0.55), tint(CYAN, 0.70),
]

TYPE_COLORS = {
    "Vegetación": NAVY,
    "Construcciones": BLUE,
    "Obras": CYAN,
    "Permiso Ingreso": tint(CYAN, 0.50),
    "Invasión/Explanacion": tint(BLUE, 0.70),
}
STATUS_COLORS = {"Cerrado": BLUE, "Abierto": RED}
TIME_COLORS = {"A tiempo": BLUE, "Atrasado": RED}
CTE_COLORS = {"Centro": NAVY, "Suroccidente": CYAN, "Sin dato": NEUTRAL}

# Escala de calor: de casi blanco a azul profundo.
HEATMAP_SCALE = [
    [0.00, tint(CYAN, 0.94)],
    [0.25, tint(CYAN, 0.75)],
    [0.50, CYAN],
    [0.78, BLUE],
    [1.00, NAVY],
]

# Ranking: 10 pasos, del más claro al más oscuro.
RANK_PALETTE = [mix(tint(CYAN, 0.60), NAVY, i / 9) for i in range(10)]

# Sombreado y líneas de año en la gráfica de cumplimiento mensual.
YEAR_BAND = tint(BLUE, 0.92)
YEAR_LINE = tint(BLUE, 0.70)
