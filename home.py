"""
home.py — Página de inicio del dashboard "Gestión de Avisos | ENERGY".
Los colores se leen de theme.py, así que el home siempre refleja la paleta vigente.
"""
from dash import html

import theme as T

# ------------------------------------------------------------
# Identidad corporativa (inventada)
# ------------------------------------------------------------
RAZON_SOCIAL = "ENERGY Transmisión y Servicios S.A.S."
NOMBRE_COMERCIAL = "ENERGY"
SLOGAN = "Grid Intelligence: conocer la red para cuidarla."
DESCRIPCION = (
    "Empresa dedicada a la gestión integral de la infraestructura de transmisión "
    "de energía: inspección de líneas, control de vegetación, seguimiento de "
    "construcciones e invasiones en franja de servidumbre, y analítica operativa "
    "de avisos para priorizar la atención en campo."
)
DATOS_LEGALES = [
    ("Razón social", RAZON_SOCIAL),
    ("Nombre comercial", NOMBRE_COMERCIAL),
    ("Tipo de sociedad", "Sociedad por Acciones Simplificada (S.A.S.)"),
    ("Objeto social", "Gestión, mantenimiento y analítica de infraestructura eléctrica"),
    ("Áreas operativas", "Centro · Suroccidente"),
]

# ------------------------------------------------------------
# Paletas mostradas (todas derivadas de theme.py)
# ------------------------------------------------------------
PALETAS = [
    {
        "titulo": "Marca",
        "uso": "Paleta oficial: identidad, series principales y elementos base.",
        "colores": list(T.BRAND),
    },
    {
        "titulo": "Tonos derivados",
        "uso": "Versiones claras de la marca para fondos, series secundarias y heatmaps.",
        "colores": [(n, c, "") for n, c in T.DERIVED],
    },
    {
        "titulo": "Semántica",
        "uso": "Reservada para estados y alertas; no forma parte de la marca.",
        "colores": [
            ("Verde", T.GREEN, "Cumplimiento"),
            ("Rojo", T.RED, "Abierto / atraso"),
            ("Ámbar", T.AMBER, "Acumulado / advertencia"),
        ],
    },
    {
        "titulo": "Texto y estructura",
        "uso": "Tipografía, cuadrículas y categorías neutras.",
        "colores": [
            ("Texto", T.TEXT, "Principal"),
            ("Texto secundario", T.MUTED, "Etiquetas"),
            ("Grid", T.GRID, "Cuadrícula"),
            ("Sin dato", T.NEUTRAL, "Categoría neutra"),
        ],
    },
    {
        "titulo": "Escala de calor (heatmaps)",
        "uso": "De menor a mayor concentración de avisos.",
        "colores": [
            (f"{int(p * 100)}%", c, "") for p, c in T.HEATMAP_SCALE
        ],
    },
    {
        "titulo": "Ranking",
        "uso": "Barras ordenadas: más oscuro = mayor posición.",
        "colores": [(str(i + 1), c, "") for i, c in enumerate(T.RANK_PALETTE)],
    },
    {
        "titulo": "Series categóricas",
        "uso": "Pareto y líneas por prioridad.",
        "colores": [(str(i + 1), c, "") for i, c in enumerate(T.INSTITUTIONAL_PALETTE)],
    },
]


def _text_color(hex_color):
    """Blanco u oscuro según la luminosidad del fondo."""
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return "#FFFFFF" if (0.299 * r + 0.587 * g + 0.114 * b) < 150 else T.TEXT


def _swatch(nombre, hex_color, rol):
    return html.Div(
        [
            html.Div(
                hex_color.upper(),
                style={
                    "backgroundColor": hex_color,
                    "color": _text_color(hex_color),
                    "height": "72px",
                    "display": "flex",
                    "alignItems": "flex-end",
                    "padding": "8px 10px",
                    "fontSize": "12px",
                    "fontWeight": "600",
                    "letterSpacing": "0.04em",
                    "border": f"1px solid {T.GRID}",
                    "borderRadius": "10px 10px 0 0",
                },
            ),
            html.Div(
                [
                    html.Div(nombre, style={"fontWeight": "600", "fontSize": "12px", "color": T.TEXT}),
                    html.Div(rol, style={"fontSize": "11px", "color": T.MUTED}) if rol else None,
                ],
                style={
                    "padding": "8px 10px",
                    "background": "white",
                    "border": f"1px solid {T.GRID}",
                    "borderTop": "none",
                    "borderRadius": "0 0 10px 10px",
                    "minHeight": "44px",
                },
            ),
        ],
        className="palette-swatch",
    )


def _palette_block(p):
    return html.Div(
        [
            html.Div(p["titulo"], className="chart-title"),
            html.Div(p["uso"], className="chart-subtitle", style={"marginBottom": "12px"}),
            html.Div(
                [_swatch(*c) for c in p["colores"]],
                className="palette-swatches",
            ),
        ],
        className="chart-card palette-block",
    )


def _legal_card():
    rows = [
        html.Div(
            [
                html.Div(k, style={"fontSize": "11px", "color": T.MUTED, "letterSpacing": "0.06em", "textTransform": "uppercase"}),
                html.Div(v, style={"fontSize": "14px", "fontWeight": "600", "color": T.TEXT}),
            ],
            style={"padding": "8px 0", "borderBottom": f"1px solid {T.GRID}"},
        )
        for k, v in DATOS_LEGALES
    ]
    mid = (len(rows) + 1) // 2
    left = rows[:mid]
    right = rows[mid:]
    return html.Div(
        [
            html.Div("Ficha corporativa", className="chart-title"),
            html.Div([html.Div(left), html.Div(right)], className="home-corporate-grid"),
        ],
        className="chart-card home-corporate-card",
    )


def _hero():
    return html.Div(
        [
            html.Div("BIENVENIDO", style={"fontSize": "11px", "letterSpacing": "0.18em", "color": T.tint(T.CYAN, 0.6)}),
            html.Div(RAZON_SOCIAL, style={"fontSize": "30px", "fontWeight": "700", "margin": "6px 0", "color": "white"}),
            html.Div(SLOGAN, style={"fontSize": "15px", "color": T.tint(T.CYAN, 0.45), "marginBottom": "12px"}),
            html.Div(DESCRIPCION, style={"fontSize": "13px", "lineHeight": "1.6", "color": T.tint(T.CYAN, 0.88), "maxWidth": "760px"}),
        ],
        style={
            "background": f"linear-gradient(135deg, {T.NAVY} 0%, {T.BLUE} 100%)",
            "borderRadius": "14px",
            "padding": "28px 32px",
            "marginBottom": "16px",
        },
    )


def build_home():
    return html.Div(
        [
            _hero(),
            html.Div([_legal_card()], className="home-corporate-wrap"),
            html.Div("Paletas de colores", className="page-title", style={"margin": "18px 0 4px"}),
            html.Div(
                "Colores utilizados en las visualizaciones del tablero.",
                className="page-subtitle",
                style={"marginBottom": "12px"},
            ),
            html.Div([_palette_block(p) for p in PALETAS], className="home-palette-grid"),
        ]
    )
