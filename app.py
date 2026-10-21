import dash
from dash import Dash, dcc, html, Input, Output, ALL, ctx, no_update
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import re
import os

from home import build_home

# ============================================================
# GESTIÓN DE AVISOS — DASHBOARD ANALÍTICO
# Fuente: avisos_equipos.csv (histórico de avisos + información de equipos)
# Regla: únicamente marca = normal
# ============================================================

app = Dash(
    __name__,
    title="Gestión de Avisos | ENERGY",
    suppress_callback_exceptions=True,
)

# -----------------------------
# Carga y preparación de datos
# -----------------------------
df = pd.read_csv("data/avisos_equipos.csv", low_memory=False)

for c in ["Fecha de aviso", "Fecha de cierre"]:
    if c in df.columns:
        df[c] = pd.to_datetime(df[c], errors="coerce")

for c in ["Días abierto", "Prioridad días", "Cumple prioridad periodos", "Año"]:
    if c in df.columns:
        df[c] = pd.to_numeric(df[c], errors="coerce")

text_cols = [
    "Tipo de aviso", "Sector", "Prioridad", "Estado aviso", "marca",
    "Departamento", "Municipio", "CTE", "Equipo", "Tiempo aviso",
    "Trimestre", "Linea"
]
for c in text_cols:
    if c in df.columns:
        df[c] = df[c].fillna("Sin dato").astype(str).str.strip()

# Regla analítica fija solicitada por el usuario.
df = df[df["marca"].str.lower().eq("normal")].copy()

# -----------------------------
# Paleta institucional (definida en theme.py)
# -----------------------------
from theme import (
    NAVY, BLUE, CYAN, LIGHT_BLUE, GREEN, RED, AMBER, TEXT, MUTED, GRID,
    INSTITUTIONAL_PALETTE, TYPE_COLORS, STATUS_COLORS, TIME_COLORS,
    HEATMAP_SCALE, RANK_PALETTE, CTE_COLORS, YEAR_BAND, YEAR_LINE,
)

# -----------------------------
# Helpers
# -----------------------------
def options(col):
    vals = [x for x in df[col].dropna().unique() if str(x).strip()]
    return [{"label": str(x), "value": x} for x in sorted(vals, key=str)]


def fmt_int(value):
    return f"{int(value):,}".replace(",", ".")


def hex_rgba(hex_color, alpha=1.0):
    """Convierte HEX a rgba() para resaltar una categoría y atenuar las demás."""
    h = str(hex_color).lstrip("#")
    if len(h) != 6:
        return hex_color
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def kpi(label, value, detail="", kind="info"):
    return html.Div(
        [
            html.Div(label, className="kpi-label"),
            html.Div(value, className="kpi-value"),
            html.Div(detail, className="kpi-delta"),
        ],
        className=f"kpi-card {kind}",
    )


def empty_fig(message="Sin datos para los filtros seleccionados"):
    fig = go.Figure()
    fig.add_annotation(
        text=message, x=0.5, y=0.5, xref="paper", yref="paper",
        showarrow=False, font=dict(size=13, color="#71809a")
    )
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    fig.update_layout(
        height=280, paper_bgcolor="white", plot_bgcolor="white",
        margin=dict(l=10, r=10, t=10, b=10)
    )
    return fig


def base_layout(fig, height=300, showlegend=True):
    fig.update_layout(
        height=height,
        autosize=True,
        margin=dict(l=12, r=12, t=12, b=42),
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(family="DM Sans, Arial, sans-serif", color=TEXT, size=12),
        showlegend=showlegend,
        legend=dict(
            orientation="h",
            yanchor="bottom", y=1.01,
            xanchor="left", x=0,
            font=dict(family="DM Sans, Arial, sans-serif", size=11, color=TEXT),
        ),
        hoverlabel=dict(font=dict(family="DM Sans, Arial, sans-serif", size=11)),
    )
    fig.update_xaxes(showgrid=False, zeroline=False, automargin=True, tickangle=0)
    fig.update_yaxes(gridcolor=GRID, zeroline=False, automargin=True)
    return fig


def donut(data, names, values, title_center=None, colors=None, height=280, center_value=None, pull_index=None):
    """Dona ejecutiva inspirada en los ejemplos GO.Pie del notebook.

    - Etiquetas fuera del anillo: categoría + porcentaje.
    - Separación sutil (pull) para enfatizar una categoría.
    - Centro reservado para KPI, no para repetir la leyenda.
    """
    if data.empty:
        return empty_fig()

    data = data.copy()
    data[values] = pd.to_numeric(data[values], errors="coerce").fillna(0)
    data = data[data[values] > 0].copy()
    if data.empty:
        return empty_fig()

    labels = data[names].astype(str).tolist()
    vals = data[values].tolist()
    total = float(np.sum(vals))

    # Mantener el orden analítico recibido, normalmente descendente.
    pull = [0.0] * len(data)
    if pull_index is not None and 0 <= pull_index < len(pull):
        pull[pull_index] = 0.045

    fig = go.Figure(
        go.Pie(
            labels=labels,
            values=vals,
            hole=0.58,
            sort=False,
            direction="clockwise",
            rotation=90,
            pull=pull,
            textposition="outside",
            textinfo="label+percent",
            texttemplate="%{label}<br><b>%{percent:.1%}</b>",
            insidetextorientation="horizontal",
            marker=dict(
                colors=[(colors or {}).get(label, BLUE) for label in labels],
                line=dict(color="white", width=4),
            ),
            hovertemplate=(
                "<b>%{label}</b><br>Avisos: %{value:,}"
                "<br>Participación: %{percent:.1%}<extra></extra>"
            ),
            textfont=dict(size=10, color=TEXT),
            automargin=True,
        )
    )

    display_value = center_value if center_value is not None else fmt_int(total)
    center = title_center or ""
    fig.add_annotation(
        text=(
            f"<b style='font-size:13px'>{display_value}</b>"
            f"<br><span style='font-size:9px;color:{MUTED}'>{center}</span>"
        ),
        x=0.5, y=0.5, showarrow=False, align="center",
        font=dict(family="DM Sans, Arial, sans-serif", color=NAVY),
    )

    fig = base_layout(fig, height=height, showlegend=False)
    fig.update_layout(
        margin=dict(l=36, r=36, t=12, b=12),
        uniformtext_minsize=9,
        uniformtext_mode="hide",
    )
    return fig

def _graph_key(title):
    key = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return key[:90] or "grafica"


def chart_card(title, figure, summary="", graph_height=None, class_name="chart-card"):
    """Tarjeta de gráfica con interacción hover/click y resumen ejecutivo."""
    height = graph_height or int(figure.layout.height or 300)
    figure.update_layout(clickmode="event+select", hovermode="closest")
    return html.Div(
        [
            html.Div(title, className="chart-title"),
            dcc.Graph(
                id={"type": "dashboard-graph", "index": _graph_key(title)},
                figure=figure,
                className=f"dashboard-graph {('cte-donut-graph' if _graph_key(title) == _graph_key('Participación de los avisos entre los centros registrados.') else '')}".strip(),
                style={"height": f"{height}px", "width": "100%"},
                config={"displayModeBar": False, "responsive": True},
            ),
            html.Div(
                [html.Span("Resumen · ", className="chart-summary-label"), summary],
                className="chart-summary",
            ) if summary else None,
        ],
        className=class_name,
    )


def make_year_status(d):
    g = d.groupby(["Año", "Estado aviso"], observed=False).size().reset_index(name="Avisos")
    g = g.dropna(subset=["Año"]).sort_values("Año")
    if g.empty:
        return empty_fig()
    fig = px.bar(
        g, x="Año", y="Avisos", color="Estado aviso", barmode="group",
        text_auto=True, color_discrete_map=STATUS_COLORS,
        category_orders={"Estado aviso": ["Cerrado", "Abierto"]},
    )
    fig.update_traces(marker_line_width=0)
    fig.update_xaxes(dtick=1, title="Año")
    fig.update_yaxes(title="Avisos")
    return base_layout(fig, 330, True)


def make_year_trend(d):
    g = d.groupby("Año", observed=False).size().reset_index(name="Avisos")
    g = g.dropna(subset=["Año"]).sort_values("Año")
    if g.empty:
        return empty_fig()
    g["Media móvil 3 años"] = g["Avisos"].rolling(3, min_periods=1).mean()
    years = g["Año"].astype(int).tolist()
    # Mostrar años alternos para evitar saturación visual; todos siguen disponibles en hover.
    tickvals = years[::2]
    if years[-1] not in tickvals:
        tickvals.append(years[-1])
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=g["Año"], y=g["Avisos"], name="Avisos",
        marker=dict(color=BLUE, opacity=0.78),
        text=g["Avisos"], textposition="outside", cliponaxis=False,
        hovertemplate="Año: %{x}<br>Avisos: %{y:,}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=g["Año"], y=g["Media móvil 3 años"], name="Media móvil (3 años)",
        mode="lines+markers", line=dict(color=CYAN, width=3),
        hovertemplate="Año: %{x}<br>Media móvil: %{y:.1f}<extra></extra>",
    ))
    fig.update_xaxes(
        title="Año", tickmode="array", tickvals=tickvals,
        ticktext=[str(y) for y in tickvals], tickangle=0,
        showgrid=False, automargin=True,
    )
    fig.update_yaxes(
        title="Número de avisos", range=[0, float(g["Avisos"].max()) * 1.18],
        showticklabels=False,
    )
    return base_layout(fig, 285, True)

def make_heatmap_year_priority(d):
    if d.empty:
        return empty_fig()
    h = d.groupby(["Año", "Prioridad"], observed=False).size().reset_index(name="Avisos")
    h = h.dropna(subset=["Año"])
    pivot = h.pivot_table(index="Año", columns="Prioridad", values="Avisos", aggfunc="sum", fill_value=0)
    pivot = pivot.sort_index()
    if pivot.empty:
        return empty_fig()
    cols = [c for c in ["Semana", "Mes", "Trimestre", "Semestre", "Año", "Dos años", "Tres años", "Seis años", "No asignada"] if c in pivot.columns]
    pivot = pivot[[c for c in cols if c in pivot.columns]]
    fig = px.imshow(
        pivot, text_auto=True, aspect="auto",
        color_continuous_scale=HEATMAP_SCALE,
    )
    fig.update_xaxes(side="top", title="Prioridad", tickangle=0, automargin=True)
    fig.update_yaxes(title="Año", autorange="reversed", automargin=True)
    fig.update_coloraxes(colorbar_title="Avisos")
    fig.update_layout(margin=dict(l=42, r=54, t=34, b=22))
    return base_layout(fig, 285, False)

def make_heatmap_type_year(d, selected_type=None):
    if d.empty:
        return empty_fig()
    h = d.groupby(["Tipo de aviso", "Año"], observed=False).size().reset_index(name="Avisos")
    h = h.dropna(subset=["Año"])
    pivot = h.pivot_table(index="Tipo de aviso", columns="Año", values="Avisos", aggfunc="sum", fill_value=0)
    if pivot.empty:
        return empty_fig()
    order = d["Tipo de aviso"].value_counts().index.tolist()
    pivot = pivot.reindex([x for x in order if x in pivot.index])
    years = [int(x) for x in pivot.columns]
    tickvals = [str(y) for y in years[::2]]
    if str(years[-1]) not in tickvals:
        tickvals.append(str(years[-1]))
    xvals = [str(x) for x in pivot.columns]
    yvals = pivot.index.astype(str).tolist()
    if selected_type and str(selected_type) in yvals:
        # Base atenuada + fila seleccionada resaltada.
        base_z = pivot.values.astype(float).copy()
        selected_row = yvals.index(str(selected_type))
        highlight_z = np.full_like(base_z, np.nan, dtype=float)
        highlight_z[selected_row, :] = base_z[selected_row, :]
        fig = go.Figure()
        fig.add_trace(go.Heatmap(
            z=base_z, x=xvals, y=yvals, colorscale=HEATMAP_SCALE,
            opacity=0.18, showscale=False, xgap=1, ygap=1,
            hovertemplate="Tipo: %{y}<br>Año: %{x}<br>Avisos: %{z}<extra></extra>",
        ))
        fig.add_trace(go.Heatmap(
            z=highlight_z, x=xvals, y=yvals, colorscale=HEATMAP_SCALE,
            colorbar=dict(title="Avisos"), xgap=1, ygap=1,
            hovertemplate="Tipo seleccionado: %{y}<br>Año: %{x}<br>Avisos: %{z}<extra></extra>",
        ))
    else:
        fig = go.Figure(go.Heatmap(
            z=pivot.values, x=xvals, y=yvals, colorscale=HEATMAP_SCALE,
            colorbar=dict(title="Avisos"),
            hovertemplate="Tipo: %{y}<br>Año: %{x}<br>Avisos: %{z}<extra></extra>",
            xgap=1, ygap=1,
        ))
    fig.update_xaxes(
        title="Año", side="top", tickangle=0, automargin=True,
        tickmode="array", tickvals=tickvals, ticktext=tickvals,
    )
    fig.update_yaxes(title="Tipo de aviso", automargin=True)
    return base_layout(fig, 285, False)

def make_heatmap_department_year(d):
    if d.empty:
        return empty_fig()
    h = d.groupby(["Departamento", "Año"], observed=False).size().reset_index(name="Avisos")
    h = h.dropna(subset=["Año"])
    pivot = h.pivot_table(index="Departamento", columns="Año", values="Avisos", aggfunc="sum", fill_value=0)
    if pivot.empty:
        return empty_fig()
    pivot = pivot.loc[pivot.sum(axis=1).sort_values(ascending=False).index]
    fig = go.Figure(go.Heatmap(
        z=pivot.values,
        x=[str(x) for x in pivot.columns],
        y=pivot.index,
        colorscale=HEATMAP_SCALE,
        colorbar=dict(title="Avisos"),
        hovertemplate="Departamento: %{y}<br>Año: %{x}<br>Avisos: %{z}<extra></extra>",
        xgap=1, ygap=1,
    ))
    fig.update_xaxes(title="Año", side="top", tickangle=0)
    fig.update_yaxes(title="Departamento")
    return base_layout(fig, 285, False)


def make_box(d, selected_type=None):
    t = d[d["Días abierto"].notna()].copy()
    if t.empty:
        return empty_fig()
    fig = px.box(
        t.sort_values("Tipo de aviso"),
        x="Tipo de aviso", y="Días abierto", color="Tipo de aviso",
        points=False, notched=True, color_discrete_map=TYPE_COLORS,
    )
    for tr in fig.data:
        tr.opacity = 1 if (not selected_type or str(tr.name) == str(selected_type)) else 0.16
    fig.update_traces(boxmean=True, marker=dict(size=3))
    box_order = [str(tr.name) for tr in fig.data]
    box_labels = []
    for label in box_order:
        text = str(label)
        if text.lower().startswith("invasión") or text.lower().startswith("invasion"):
            box_labels.append("Invasión/<br>Explanación")
        elif text == "Permiso Ingreso":
            box_labels.append("Permiso<br>Ingreso")
        else:
            box_labels.append(text)
    if box_labels:
        fig.update_xaxes(
            tickangle=0, title="Tipo de aviso", automargin=True,
            tickmode="array", tickvals=box_order,
            ticktext=box_labels, tickfont=dict(size=10),
        )
    else:
        fig.update_xaxes(tickangle=0, title="Tipo de aviso", automargin=True, tickfont=dict(size=10))
    fig.update_yaxes(title="Días abierto")
    fig.update_layout(margin=dict(l=42, r=24, t=18, b=58))
    return base_layout(fig, 300, False)


def make_ranked_bar(d, col, label, n=7, colors=None, height=310):
    g = d[col].value_counts().head(n).rename_axis(label).reset_index(name="Avisos")
    if g.empty:
        return empty_fig()
    g["Porcentaje"] = g["Avisos"] / len(d) * 100
    g = g.sort_values("Avisos", ascending=True)
    fig = px.bar(
        g, x="Avisos", y=label, orientation="h", text="Porcentaje",
        category_orders={label: g[label].tolist()},
    )
    fig.update_traces(
        texttemplate="%{text:.1f}%", textposition="outside",
        marker_color=BLUE,
        marker_line_width=0, marker_cornerradius=7,
        hovertemplate="<b>%{y}</b><br>Avisos: %{x:,}<br>Participación: %{text:.1f}%<extra></extra>",
    )
    fig.update_xaxes(
        title="Número de avisos", showgrid=True, gridcolor=GRID,
        range=[0, float(g["Avisos"].max()) * 1.16],
        tickangle=0,
    )
    fig.update_yaxes(title="", automargin=True)
    return base_layout(fig, height, False)


def make_pareto(d, col, height=315, selected_type=None):
    """Pareto ejecutivo: barras de volumen + acumulado, con umbral 80%."""
    counts = d[col].value_counts().sort_values(ascending=False)
    if counts.empty:
        return empty_fig()

    g = counts.rename_axis(col).reset_index(name="Avisos")
    g["Acumulado"] = g["Avisos"].cumsum() / g["Avisos"].sum() * 100

    base_colors = INSTITUTIONAL_PALETTE[:len(g)]
    if len(g) > len(base_colors):
        base_colors += [INSTITUTIONAL_PALETTE[-1]] * (len(g) - len(base_colors))
    if selected_type:
        bar_colors = [
            color if str(cat) == str(selected_type) else hex_rgba(color, 0.18)
            for cat, color in zip(g[col], base_colors)
        ]
    else:
        bar_colors = base_colors

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=g[col], y=g["Avisos"], name="Avisos",
        text=g["Avisos"], textposition="outside", cliponaxis=False,
        textfont=dict(
            color=[TEXT if (not selected_type or str(cat) == str(selected_type)) else hex_rgba(TEXT, 0.22) for cat in g[col]],
            family="DM Sans, Arial, sans-serif", size=11,
        ),
        marker=dict(color=bar_colors, cornerradius=8),
        hovertemplate="<b>%{x}</b><br>Avisos: %{y:,}<extra></extra>",
    ))

    # Con una selección activa se atenúa la línea acumulada y se destaca
    # únicamente el punto correspondiente a la categoría seleccionada.
    line_color = hex_rgba(AMBER, 0.22) if selected_type else AMBER
    fig.add_trace(go.Scatter(
        x=g[col], y=g["Acumulado"], name="Acumulado %",
        yaxis="y2", mode="lines+markers", cliponaxis=False,
        line=dict(color=line_color, width=2.5, shape="linear"),
        marker=dict(
            size=7,
            color=[AMBER if (not selected_type or str(cat) == str(selected_type)) else hex_rgba(AMBER, 0.15) for cat in g[col]],
            line=dict(color="white", width=1.5),
        ),
        hovertemplate="<b>%{x}</b><br>Acumulado: %{y:.1f}%<extra></extra>",
    ))
    if selected_type and selected_type in set(g[col].astype(str)):
        sel = g[g[col].astype(str).eq(str(selected_type))]
        fig.add_trace(go.Scatter(
            x=sel[col], y=sel["Acumulado"], yaxis="y2",
            mode="markers", name="Selección",
            marker=dict(size=10, color=AMBER, line=dict(color="white", width=2)),
            hovertemplate="<b>%{x}</b><br>Acumulado seleccionado: %{y:.1f}%<extra></extra>",
            showlegend=False,
        ))
    # Umbral 80%: solo se muestra su etiqueta, no porcentajes sobre cada punto.
    fig.add_trace(go.Scatter(
        x=g[col], y=[80] * len(g), yaxis="y2",
        mode="lines", name="Umbral 80%",
        line=dict(color="#9AA6B2", width=1.2, dash="dot"),
        hoverinfo="skip", showlegend=False,
    ))

    pareto_ticktext = []
    for label in g[col].astype(str):
        if label.lower().startswith("invasión") or label.lower().startswith("invasion"):
            pareto_ticktext.append("Invasión/<br>Explanación")
        elif label == "Permiso Ingreso":
            pareto_ticktext.append("Permiso<br>Ingreso")
        else:
            pareto_ticktext.append(label)

    fig.update_layout(
        yaxis=dict(
            title="Avisos", gridcolor=GRID, zeroline=False,
            showticklabels=False,
            range=[0, float(g["Avisos"].max()) * 1.16],
        ),
        yaxis2=dict(
            title="Acumulado", overlaying="y", side="right",
            range=[0, 100], tickvals=[80], ticktext=["80%"],
            showgrid=False, zeroline=False,
        ),
        xaxis=dict(
            title="Tipo de aviso", tickangle=0, showgrid=False, automargin=True,
            tickmode="array", tickvals=g[col].tolist(), ticktext=pareto_ticktext,
            tickfont=dict(family="DM Sans, Arial, sans-serif", size=10),
            domain=[0, 0.93],
        ),
        legend=dict(orientation="h", y=1.04, x=0, xanchor="left"),
        margin=dict(l=42, r=56, t=42, b=58),
        bargap=0.28,
    )
    return base_layout(fig, height, True)

def make_grouped_type_status(d, height=315, selected_type=None):
    """Barras agrupadas ejecutivas con etiquetas legibles y mayor ancho visual."""
    g = (
        d.groupby(["Tipo de aviso", "Estado aviso"], observed=False)
        .size().reset_index(name="Avisos")
    )
    if g.empty:
        return empty_fig()

    totals = g.groupby("Tipo de aviso")["Avisos"].sum().sort_values(ascending=False)
    order = totals.index.tolist()
    g["Estado aviso"] = pd.Categorical(
        g["Estado aviso"], categories=["Cerrado", "Abierto"], ordered=True
    )
    g = g.sort_values(["Tipo de aviso", "Estado aviso"])

    fig = px.bar(
        g, x="Tipo de aviso", y="Avisos", color="Estado aviso",
        barmode="group", text="Avisos",
        category_orders={"Tipo de aviso": order, "Estado aviso": ["Cerrado", "Abierto"]},
        color_discrete_map=STATUS_COLORS,
    )

    # Etiquetas largas en dos líneas para evitar cruces en el eje X.
    ticktext = []
    for label in order:
        label = str(label)
        if label.lower().startswith("invasión") or label.lower().startswith("invasion"):
            ticktext.append("Invasión/<br>Explanación")
        elif label == "Permiso Ingreso":
            ticktext.append("Permiso<br>Ingreso")
        else:
            ticktext.append(label)

    # IMPORTANTE: cada traza puede tener su propio orden de categorías.
    # Usamos tr.x como fuente de verdad para colores y customdata, evitando
    # desalineaciones entre la barra pulsada y la categoría seleccionada.
    for tr in fig.data:
        state = str(tr.name)
        original = STATUS_COLORS.get(state, BLUE)
        categories = [str(x) for x in (list(tr.x) if tr.x is not None else [])]
        tr.customdata = categories
        if selected_type:
            tr.marker.color = [
                original if cat == str(selected_type) else hex_rgba(original, 0.18)
                for cat in categories
            ]
        else:
            tr.marker.color = original
        tr.texttemplate = "%{y:,}"
        tr.textposition = "outside"
        tr.cliponaxis = False
        tr.textfont = dict(
            family="DM Sans, Arial, sans-serif", size=11,
            color=[TEXT if (not selected_type or cat == str(selected_type)) else hex_rgba(TEXT, 0.22) for cat in categories],
        )
        tr.marker.cornerradius = 7
        tr.marker.line.width = 0
        tr.hovertemplate = "<b>%{x}</b><br>%{fullData.name}: %{y:,}<extra></extra>"
    fig.update_layout(
        barmode="group", bargap=0.16, bargroupgap=0.035,
        uniformtext_minsize=9, uniformtext_mode="hide",
        legend=dict(orientation="h", y=1.06, x=0, xanchor="left"),
        margin=dict(l=46, r=20, t=40, b=68),
    )
    fig.update_xaxes(
        title="Tipo de aviso", tickangle=0, showgrid=False, automargin=True,
        tickmode="array", tickvals=order, ticktext=ticktext,
        tickfont=dict(family="DM Sans, Arial, sans-serif", size=10),
    )
    fig.update_yaxes(
        title="Número de avisos", gridcolor=GRID, zeroline=False,
        range=[0, float(g["Avisos"].max()) * 1.28],
        showticklabels=False,
        tickfont=dict(family="DM Sans, Arial, sans-serif", size=10),
    )
    return base_layout(fig, height, True)

def make_executive_rank_bar(d, col, n=10, height=340, title_axis="Avisos"):
    """Ranking horizontal tipo 'executive bar': ranking, volumen y participación."""
    counts = d[col].value_counts().head(n).sort_values(ascending=True)
    if counts.empty:
        return empty_fig()

    total = len(d)
    labels = counts.index.astype(str).tolist()
    values = counts.values.tolist()
    shares = [v / total * 100 for v in values]
    ranks = list(range(len(labels), 0, -1))
    ylabels = [f"{r:02d}  {lab}" for r, lab in zip(ranks, labels)]
    # Más oscuro para los primeros puestos visuales (última barra en orden ascendente).
    colors = RANK_PALETTE[-len(values):] if len(values) <= len(RANK_PALETTE) else [BLUE] * len(values)

    fig = go.Figure(go.Bar(
        x=values, y=ylabels, orientation="h",
        text=[f"{v:,}  ·  {s:.1f}%" for v, s in zip(values, shares)],
        textposition="outside",
        marker=dict(color=colors, cornerradius=8),
        customdata=labels,
        hovertemplate="<b>%{y}</b><br>Avisos: %{x:,}<extra></extra>",
        cliponaxis=False,
    ))
    fig.update_xaxes(
        title="", showticklabels=False, showgrid=False, zeroline=False,
        range=[0, float(max(values)) * 1.18],
    )
    fig.update_yaxes(title="", showgrid=False, automargin=True, categoryorder="array", categoryarray=ylabels)
    fig.update_layout(bargap=0.30)
    fig = base_layout(fig, height, False)
    # El margen se define después de base_layout, que si no lo sobrescribe.
    fig.update_layout(margin=dict(l=8, r=24, t=8, b=8))
    return fig

def make_compliance_behavior(d):
    t = d[
        (d["Estado aviso"].str.lower() == "cerrado")
        & d["Fecha de aviso"].notna()
        & d["Cumple prioridad días"].notna()
    ].copy()
    if t.empty:
        return empty_fig("No hay avisos cerrados con fecha y cumplimiento disponibles")
    t["Mes"] = t["Fecha de aviso"].dt.to_period("M").dt.to_timestamp()
    g = (
        t.groupby(["Mes", "Prioridad"], observed=False)["Cumple prioridad días"]
        .mean()
        .reset_index()
    )
    g["Cumplimiento (días)"] = g["Cumple prioridad días"]
    prioridad_map = {"Año": "Un año"}
    g["Prioridad visual"] = g["Prioridad"].replace(prioridad_map)
    orden = ["Seis años", "Tres años", "Dos años", "Un año", "Semestre", "Trimestre", "Mes"]
    orden = [x for x in orden if x in g["Prioridad visual"].unique()]
    g["Prioridad visual"] = pd.Categorical(g["Prioridad visual"], categories=orden, ordered=True)
    fig = px.line(
        g, x="Mes", y="Cumplimiento (días)", color="Prioridad visual",
        markers=True, category_orders={"Prioridad visual": orden},
        color_discrete_sequence=INSTITUTIONAL_PALETTE,
        hover_data={
            "Mes": "|%b %Y",
            "Cumplimiento (días)": ":.1f",
            "Prioridad visual": True,
        },
    )
    visibles = {"Un año", "Mes"}
    for tr in fig.data:
        tr.visible = True if tr.name in visibles else "legendonly"
    # Sombreado temporal suave para separar visualmente cada año.
    # Se mantiene deliberadamente tenue para no competir con las series.
    min_month = g["Mes"].min().normalize()
    max_month = g["Mes"].max().normalize()
    years = range(min_month.year, max_month.year + 1)
    for year in years:
        start = pd.Timestamp(year=year, month=1, day=1)
        end = pd.Timestamp(year=year + 1, month=1, day=1)
        if end < min_month or start > max_month:
            continue
        if year % 2 == 0:
            fig.add_vrect(
                x0=max(start, min_month),
                x1=min(end, max_month + pd.Timedelta(days=31)),
                fillcolor=YEAR_BAND,
                opacity=0.42,
                line_width=0,
                layer="below",
            )
        if start >= min_month and start <= max_month:
            fig.add_vline(
                x=start,
                line_width=1,
                line_dash="dot",
                line_color=YEAR_LINE,
                opacity=0.75,
            )

    fig.add_hline(
        y=0, line_dash="dash", line_color=RED, line_width=1.5,
        annotation_text="Límite de cumplimiento",
        annotation_position="top left",
    )
    fig.update_traces(line=dict(width=2), marker=dict(size=5))
    fig.update_xaxes(title="Mes de aviso", showgrid=False)
    fig.update_yaxes(title="Cumplimiento (días)", gridcolor=GRID, zeroline=False)
    return base_layout(fig, 330, True)

# Dash 4 permite personalizar el texto "selected" de los multi-select.
# Se deja compatible con versiones anteriores para evitar romper instalaciones existentes.
DROPDOWN_LABELS = (
    {"selected_count": "{num_selected}"} if int(dash.__version__.split(".")[0]) >= 4 else {}
)

# -----------------------------
# Sidebar
# -----------------------------
sidebar = html.Aside(
    [
        html.Div(
            [
                html.Img(src="/assets/logo_energy.png", className="sidebar-logo"),
                html.Div("GESTIÓN DE AVISOS", className="sidebar-brand-caption"),
                html.Div("GRID INTELLIGENCE", className="brand-tag"),
            ],
            className="sidebar-brand",
        ),
        html.Div("NAVEGACIÓN", className="section-label"),
        dcc.Link([html.Span(className="nav-dot"), "Inicio"], href="/inicio", id="nav-inicio", className="nav-link"),
        dcc.Link([html.Span(className="nav-dot"), "Resumen"], href="/resumen", id="nav-resumen", className="nav-link"),
        dcc.Link([html.Span(className="nav-dot"), "Avisos"], href="/avisos", id="nav-avisos", className="nav-link"),
        dcc.Link([html.Span(className="nav-dot"), "Equipos"], href="/equipos", id="nav-equipos", className="nav-link"),
        html.Div("FILTROS", className="section-label"),
        html.Div(
            [
                html.Button("↺  RESTABLECER FILTROS", id="reset-filters", n_clicks=0, className="reset-filters-btn"),
                html.Div("BASE ACTIVA · MARCA = NORMAL", className="normal-badge"),
                html.Div("Seleccione uno o varios valores; el tablero se actualiza automáticamente.", className="filter-hint"),
                html.Label("AÑO", className="filter-label"),
                dcc.Dropdown(id="f-year", options=options("Año"), value=[], multi=True, clearable=True, searchable=True, placeholder="Todos los años", labels=DROPDOWN_LABELS, debounce=True, closeOnSelect=False),
                html.Label("TIPO DE AVISO", className="filter-label"),
                dcc.Dropdown(id="f-type", options=options("Tipo de aviso"), value=[], multi=True, clearable=True, searchable=True, placeholder="Todos los tipos", labels=DROPDOWN_LABELS, debounce=True, closeOnSelect=False),
                html.Label("DEPARTAMENTO", className="filter-label"),
                dcc.Dropdown(id="f-dept", options=options("Departamento"), value=[], multi=True, clearable=True, searchable=True, placeholder="Todos los departamentos", labels=DROPDOWN_LABELS, debounce=True, closeOnSelect=False),
            ],
            className="sidebar-filters",
        ),
        html.Div(
            [
                html.Div("AUTORES", className="authors-title"),
                html.Div(
                    [
                        html.Div("MG", className="author-avatar"),
                        html.Div("Mauricio Guerrero", className="author-name"),
                    ],
                    className="author-row",
                ),
                html.Div(
                    [
                        html.Div("DR", className="author-avatar"),
                        html.Div("Daniel Rodriguez", className="author-name"),
                    ],
                    className="author-row",
                ),
            ],
            className="authors-panel",
        ),
    ],
    id="sidebar",
    className="sidebar",
)


def page_header(title, subtitle):
    return html.Div([html.Div(title, className="page-title"), html.Div(subtitle, className="page-subtitle")], className="page-header")


def common_kpis(d):
    total = len(d)
    closed = int(d["Estado aviso"].str.lower().eq("cerrado").sum())
    open_ = int(d["Estado aviso"].str.lower().eq("abierto").sum())
    on_time = int(d["Tiempo aviso"].str.lower().eq("a tiempo").sum())
    late = int(d["Tiempo aviso"].str.lower().eq("atrasado").sum())
    avg_days = d["Días abierto"].mean() if total else 0
    compliance = (on_time / (on_time + late) * 100) if (on_time + late) else 0
    unique_equip = d["Equipo"].nunique()
    return [
        kpi("AVISOS", fmt_int(total), "Registros marca normal", "info"),
        kpi("CERRADOS", fmt_int(closed), f"{closed / total * 100:.1f}% del total" if total else "0%", "ok"),
        kpi("ABIERTOS", fmt_int(open_), "Pendientes", "warning"),
        kpi("CUMPLIMIENTO", f"{compliance:.1f}%", f"{fmt_int(on_time)} a tiempo", "ok" if compliance >= 80 else "warning"),
        kpi("EQUIPOS", fmt_int(unique_equip), f"Promedio {avg_days:.1f} días abiertos" if total else "Sin datos", "info"),
    ]


def apply_filters(years, types, depts):
    d = df.copy()
    if years:
        d = d[d["Año"].isin(years)]
    if types:
        d = d[d["Tipo de aviso"].isin(types)]
    if depts:
        d = d[d["Departamento"].isin(depts)]
    return d

# ============================================================
# RESUMEN
# ============================================================
def build_resumen(d, selected_type=None):
    status_source = d[d["Tipo de aviso"].eq(selected_type)] if selected_type else d
    status = status_source["Estado aviso"].value_counts().rename_axis("Estado").reset_index(name="Avisos")
    prioridad = d["Prioridad"].value_counts().rename_axis("Prioridad").reset_index(name="Avisos")
    return html.Div([
        page_header("Centro de control operativo", "Resumen general de avisos, estado, prioridades y comportamiento temporal."),
        html.Div(common_kpis(d), className="kpi-row"),
        html.Div([
            chart_card(
                "Distribución de registros cerrados y abiertos.",
                donut(
                    status, "Estado", "Avisos", "Estado",
                    {"Cerrado": NAVY, "Abierto": RED},
                    245, center_value=fmt_int(len(status_source)), pull_index=0,
                ),
                summary="Muestra qué proporción de los avisos se encuentra cerrada y cuál permanece abierta.",
            ),
            chart_card(
                "Pareto para identificar los tipos que concentran la mayor parte de los avisos.",
                make_pareto(d, "Tipo de aviso", 280, selected_type),
                summary="Permite identificar los tipos de aviso que concentran la mayor parte del volumen total y dónde se alcanza el 80% acumulado.",
            ),
        ], className="charts-2col"),
        html.Div([
            chart_card(
                "Distribución de registros según la prioridad definida.",
                make_ranked_bar(d, "Prioridad", "Prioridad", n=9, height=270),
                summary="Compara el volumen de avisos asociado a cada prioridad para identificar cuáles concentran la mayor carga operativa.",
            ),
            chart_card(
                "Volumen anual y media móvil de tres años para identificar tendencia.",
                make_year_trend(d),
                summary="Muestra la evolución anual de los avisos y su media móvil para reconocer cambios sostenidos en el volumen registrado.",
            ),
        ], className="charts-2col"),
        html.Div([
            chart_card(
                "Mapa de calor para identificar concentraciones temporales de prioridad.",
                make_heatmap_year_priority(d),
                summary="Relaciona cada año con las prioridades registradas para detectar concentraciones temporales y cambios en la composición de los avisos.",
            ),
            html.Div(
                [
                    html.Div("Análisis y conclusiones", className="chart-title"),
                    html.Div(
                        [
                            html.P(
                                f"La prioridad con mayor volumen es {d['Prioridad'].value_counts().idxmax()} ({fmt_int(d['Prioridad'].value_counts().max())} avisos).",
                                className="analysis-item",
                            ) if not d.empty else html.P("Sin datos para analizar.", className="analysis-item"),
                            html.P(
                                "El mapa permite comparar simultáneamente la intensidad de los avisos por año y prioridad; los tonos más oscuros señalan las mayores concentraciones.",
                                className="analysis-item",
                            ),
                            html.P(
                                "La lectura debe orientarse a identificar años y prioridades que requieran seguimiento operativo o revisión de capacidad de atención.",
                                className="analysis-item",
                            ),
                            html.P(
                                f"El año con mayor volumen registra {fmt_int(d.groupby('Año').size().max())} avisos; este pico permite focalizar la revisión de capacidad y demanda operativa.",
                                className="analysis-item",
                            ) if not d.empty else html.P("Sin datos anuales para analizar.", className="analysis-item"),
                            html.P(
                                f"Los dos tipos con mayor volumen concentran {((d['Tipo de aviso'].value_counts().head(2).sum() / len(d)) * 100):.1f}% del total analizado, señalando dónde se concentra la mayor carga operativa.",
                                className="analysis-item",
                            ) if not d.empty else html.P("Sin datos de tipo de aviso para analizar.", className="analysis-item"),
                        ]
                    ),
                ],
                className="chart-card analysis-card",
            ),
        ], className="heatmap-analysis-grid"),
        html.Div([
            html.Div("Base analizada", className="chart-title"),
            html.Div(
                f"Se analizan {fmt_int(len(d))} registros con marca = normal. "
                "Los registros extremo y escaso no participan en los cálculos.",
                className="chart-subtitle",
            ),
        ], className="chart-card info-card"),
    ])

# ============================================================
# AVISOS
# ============================================================
def build_avisos(d, selected_type=None):
    comp_source = d[d["Tipo de aviso"].eq(selected_type)] if selected_type else d
    comp = comp_source["Tiempo aviso"].value_counts().rename_axis("Resultado").reset_index(name="Avisos")
    return html.Div([
        page_header("Gestión de avisos", "Análisis de cumplimiento, tiempos de atención y comportamiento por tipo de aviso."),
        html.Div(common_kpis(d), className="kpi-row"),
        html.Div([
            chart_card(
                "Avisos clasificados como A tiempo o Atrasado.",
                donut(
                    comp, "Resultado", "Avisos", "Cumplimiento", TIME_COLORS,
                    245, center_value=f"{(comp.loc[comp['Resultado'].eq('A tiempo'), 'Avisos'].sum() / comp['Avisos'].sum() * 100):.1f}%" if comp['Avisos'].sum() else "0.0%",
                    pull_index=(comp["Resultado"].tolist().index("Atrasado") if "Atrasado" in comp["Resultado"].tolist() else 0),
                ),
                summary="Resume la distribución de avisos a tiempo y atrasados para dimensionar el nivel de cumplimiento registrado.",
            ),
            chart_card(
                "Comparación del volumen de avisos cerrados y abiertos por tipo.",
                make_grouped_type_status(d, 315, selected_type),
                summary="Compara directamente los avisos cerrados y abiertos dentro de cada tipo para identificar dónde se concentra el pendiente.",
            ),
        ], className="charts-2col"),
        html.Div([
            chart_card(
                "Variabilidad del tiempo de atención por tipo; se muestra mediana, media y dispersión.",
                make_box(d, selected_type),
                summary="Compara la mediana, media y dispersión de los días abiertos para identificar tipos con tiempos de atención más variables.",
            ),
            chart_card(
                "Mapa de calor: volumen de cada tipo a través de los años.",
                make_heatmap_type_year(d, selected_type),
                summary="Permite observar en qué años y tipos de aviso se concentran los mayores volúmenes registrados.",
            ),
        ], className="charts-2col"),
        chart_card(
            "Promedio mensual del cumplimiento de avisos cerrados, segmentado por prioridad. Valores positivos indican cumplimiento y negativos atraso.",
            make_compliance_behavior(d),
            class_name="chart-card chart-wide",
            summary="Muestra la evolución mensual del cumplimiento por prioridad; valores sobre cero representan cumplimiento y bajo cero atraso.",
        ),
    ])

# ============================================================
# EQUIPOS
# ============================================================
def build_equipos(d, selected_equipment=None):
    # La selección cruzada de Equipos filtra todas las visualizaciones de esta página.
    # La selección no modifica los filtros globales de la barra lateral.
    view = d.copy()
    selected_value = None
    selected_dimension = None
    if isinstance(selected_equipment, dict):
        selected_dimension = selected_equipment.get("dimension")
        selected_value = selected_equipment.get("value")
        if selected_dimension in {"CTE", "Departamento", "Linea", "Municipio"} and selected_value is not None:
            view = view[view[selected_dimension].astype(str).eq(str(selected_value))].copy()

    cte = view["CTE"].value_counts().rename_axis("CTE").reset_index(name="Avisos")
    unique_equipment = view["Equipo"].nunique()
    unique_lineas = view["Linea"].nunique()
    unique_municipios = view["Municipio"].nunique()
    return html.Div([
        page_header("Equipos y ubicación", "Distribución de equipos asociados a los avisos y concentración geográfica."),
        html.Div([
            kpi("EQUIPOS ÚNICOS", fmt_int(unique_equipment), "En registros marca normal", "info"),
            kpi("LÍNEAS", fmt_int(unique_lineas), "Líneas con avisos", "info"),
            kpi("MUNICIPIOS", fmt_int(unique_municipios), "Municipios con avisos", "ok"),
            kpi("CTE", fmt_int(view["CTE"].nunique()), "Centros registrados", "warning"),
            kpi("DEPARTAMENTOS", fmt_int(view["Departamento"].nunique()), "Con registros", "info"),
        ], className="kpi-row"),
        html.Div([
            chart_card(
                "Participación de los avisos entre los centros registrados.",
                donut(
                    cte, "CTE", "Avisos", "CTE",
                    CTE_COLORS,
                    245, center_value=fmt_int(len(view)), pull_index=0,
                ),
                summary="Muestra cómo se distribuyen los avisos entre los centros de trabajo registrados. Haga clic para filtrar la página por CTE.",
            ),
            chart_card(
                "Ranking de departamentos por volumen de avisos y participación sobre el total.",
                make_executive_rank_bar(view, "Departamento", n=10, height=285),
                summary="Identifica los departamentos con mayor volumen de avisos y permite filtrar el resto de la página por departamento.",
            ),
        ], className="charts-2col"),
        html.Div([
            chart_card(
                "Top 10 líneas por volumen de avisos; se muestra cantidad y participación.",
                make_executive_rank_bar(view, "Linea", n=10, height=285),
                summary="Ordena las líneas con más avisos y permite analizar el resto del tablero para una línea seleccionada.",
            ),
            chart_card(
                "Top 10 municipios por volumen de avisos; se muestra cantidad y participación.",
                make_executive_rank_bar(view, "Municipio", n=10, height=285),
                summary="Identifica los municipios con mayor concentración de avisos y permite filtrar la página por municipio.",
            ),
        ], className="charts-2col"),
        chart_card(
            "Mapa de calor construido a partir de la información de equipos asociada al histórico.",
            make_heatmap_department_year(view),
            class_name="chart-card chart-wide",
            summary="Relaciona departamentos y años para visualizar la concentración geográfica de los avisos a través del tiempo. Haga clic en un departamento para filtrar la página.",
        ),
    ])

# ============================================================
# LAYOUT / CALLBACKS
# ============================================================
app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    dcc.Store(id="type-selection", data=None),
    dcc.Store(id="equipment-selection", data=None),
    dcc.Store(id="graph-reset-signal", data=0),
    sidebar,
    html.Main(
        [
            html.Button("☰  Filtros", id="mobile-sidebar-toggle", n_clicks=0, className="mobile-sidebar-toggle"),
            html.Button(id="graph-reset-button", n_clicks=0, style={"display": "none"}),
            html.Div("Pase el cursor sobre una gráfica para ver el detalle. Haga clic sobre un elemento para fijar su información.", id="interaction-feedback", className="interaction-feedback"),
            html.Div(id="page-content"),
        ],
        className="main-content",
    ),
], className="app-wrapper")


@app.callback(
    Output("f-year", "value"),
    Output("f-type", "value"),
    Output("f-dept", "value"),
    Input("reset-filters", "n_clicks"),
    prevent_initial_call=True,
)
def reset_filters(_):
    return ([], [], [])


@app.callback(
    Output("type-selection", "data"),
    Input("url", "pathname"),
    Input("reset-filters", "n_clicks"),
    Input("f-year", "value"),
    Input("f-type", "value"),
    Input("f-dept", "value"),
    Input("graph-reset-button", "n_clicks"),
    Input("graph-reset-signal", "data"),
    Input({"type": "dashboard-graph", "index": ALL}, "clickData"),
    Input({"type": "dashboard-graph", "index": ALL}, "relayoutData"),
)
def update_type_selection(pathname, reset_clicks, years, types, depts, graph_reset_clicks, graph_reset_signal, click_datas, relayout_datas):
    """Captura exclusivamente el evento de la gráfica que originó el clic.

    Importante: con un Input pattern-matching ALL, ctx.triggered[0]['value']
    puede contener la lista completa de eventos y no necesariamente el evento
    de la gráfica que el usuario pulsó. Por eso aquí usamos triggered_prop_ids
    + inputs_list para recuperar el clickData del gráfico exacto.
    """
    triggered_props = ctx.triggered_prop_ids or {}
    trigger = ctx.triggered_id

    # 1) Doble clic de Plotly: restaurar selección.
    if isinstance(trigger, dict) and trigger.get("type") == "dashboard-graph":
        relayout_prop = next((k for k in triggered_props if k.endswith(".relayoutData")), None)
        if relayout_prop:
            graph_id = triggered_props[relayout_prop]
            for group in ctx.inputs_list:
                items = group if isinstance(group, list) else [group]
                for item in items:
                    if item.get("id") == graph_id and item.get("property") == "relayoutData":
                        event = item.get("value")
                        if isinstance(event, dict) and any(
                            str(k).endswith(".autorange") and bool(v) for k, v in event.items()
                        ):
                            return None

    # 2) Navegación o filtros globales: limpiar selección cruzada.
    if isinstance(trigger, str) and trigger in {"reset-filters", "url", "f-year", "f-type", "f-dept", "graph-reset-button", "graph-reset-signal"}:
        return None

    # 3) Solo procesamos un clickData que realmente haya disparado el callback.
    click_prop = next((k for k in triggered_props if k.endswith(".clickData")), None)
    if not click_prop or not isinstance(trigger, dict):
        return no_update

    graph_id = triggered_props[click_prop]
    event = None
    for group in ctx.inputs_list:
        items = group if isinstance(group, list) else [group]
        for item in items:
            if item.get("id") == graph_id and item.get("property") == "clickData":
                event = item.get("value")
                break
        if event is not None:
            break

    if not isinstance(event, dict) or not event.get("points"):
        return no_update

    type_graphs = {
        _graph_key("Pareto para identificar los tipos que concentran la mayor parte de los avisos."),
        _graph_key("Comparación del volumen de avisos cerrados y abiertos por tipo."),
        _graph_key("Variabilidad del tiempo de atención por tipo; se muestra mediana, media y dispersión."),
        _graph_key("Mapa de calor: volumen de cada tipo a través de los años."),
    }
    graph_index = graph_id.get("index") if isinstance(graph_id, dict) else None
    if graph_index not in type_graphs:
        return no_update

    point = event["points"][0]
    valid_types = set(df["Tipo de aviso"].astype(str).unique())

    # Cada una de las cuatro gráficas usa un campo categórico distinto.
    # Buscamos primero la dimensión natural de cada visualización y luego
    # usamos label/y/x como respaldo.
    # customdata es la fuente primaria para las gráficas de tipo.
    # En particular, la gráfica agrupada Cerrado/Abierto puede tener dos
    # trazas y su orden interno no debe inferirse desde el índice de la traza.
    candidates = []
    custom = point.get("customdata")
    if custom is not None:
        if isinstance(custom, (list, tuple)):
            candidates.extend(custom)
        else:
            candidates.append(custom)

    if graph_index == _graph_key("Mapa de calor: volumen de cada tipo a través de los años."):
        candidates.extend([point.get("y"), point.get("label")])
    elif graph_index == _graph_key("Variabilidad del tiempo de atención por tipo; se muestra mediana, media y dispersión."):
        candidates.extend([point.get("x"), point.get("label")])
    else:
        candidates.extend([point.get("x"), point.get("label"), point.get("y")])

    for candidate in candidates:
        if candidate is not None and str(candidate) in valid_types:
            return {"value": str(candidate), "source": graph_index}

    return no_update


@app.callback(
    Output("equipment-selection", "data"),
    Input("url", "pathname"),
    Input("reset-filters", "n_clicks"),
    Input("f-year", "value"),
    Input("f-type", "value"),
    Input("f-dept", "value"),
    Input("graph-reset-button", "n_clicks"),
    Input("graph-reset-signal", "data"),
    Input({"type": "dashboard-graph", "index": ALL}, "clickData"),
    Input({"type": "dashboard-graph", "index": ALL}, "relayoutData"),
)
def update_equipment_selection(pathname, reset_clicks, years, types, depts, graph_reset_clicks, graph_reset_signal, click_datas, relayout_datas):
    """Selección cruzada exclusiva de la página Equipos.

    Cada visualización identifica su propia dimensión (CTE, Departamento,
    Linea o Municipio). El valor se obtiene del punto realmente pulsado,
    priorizando customdata cuando está disponible.
    """
    trigger = ctx.triggered_id
    triggered_props = ctx.triggered_prop_ids or {}

    if isinstance(trigger, str) and trigger in {"reset-filters", "url", "f-year", "f-type", "f-dept", "graph-reset-button", "graph-reset-signal"}:
        return None

    if isinstance(trigger, dict) and trigger.get("type") == "dashboard-graph":
        relayout_prop = next((k for k in triggered_props if k.endswith(".relayoutData")), None)
        if relayout_prop:
            graph_id = triggered_props[relayout_prop]
            for group in ctx.inputs_list:
                items = group if isinstance(group, list) else [group]
                for item in items:
                    if item.get("id") == graph_id and item.get("property") == "relayoutData":
                        event = item.get("value")
                        if isinstance(event, dict) and any(
                            str(k).endswith(".autorange") and bool(v) for k, v in event.items()
                        ):
                            return None

    click_prop = next((k for k in triggered_props if k.endswith(".clickData")), None)
    if not click_prop or not isinstance(trigger, dict):
        return no_update

    graph_id = triggered_props[click_prop]
    equipment_graphs = {
        _graph_key("Participación de los avisos entre los centros registrados."),
        _graph_key("Ranking de departamentos por volumen de avisos y participación sobre el total."),
        _graph_key("Top 10 líneas por volumen de avisos; se muestra cantidad y participación."),
        _graph_key("Top 10 municipios por volumen de avisos; se muestra cantidad y participación."),
        _graph_key("Mapa de calor construido a partir de la información de equipos asociada al histórico."),
    }
    graph_index = graph_id.get("index") if isinstance(graph_id, dict) else None
    if graph_index not in equipment_graphs:
        return no_update

    event = None
    for group in ctx.inputs_list:
        items = group if isinstance(group, list) else [group]
        for item in items:
            if item.get("id") == graph_id and item.get("property") == "clickData":
                event = item.get("value")
                break
        if event is not None:
            break
    if not isinstance(event, dict) or not event.get("points"):
        return no_update

    point = event["points"][0]
    dimension_by_graph = {
        _graph_key("Participación de los avisos entre los centros registrados."): "CTE",
        _graph_key("Ranking de departamentos por volumen de avisos y participación sobre el total."): "Departamento",
        _graph_key("Top 10 líneas por volumen de avisos; se muestra cantidad y participación."): "Linea",
        _graph_key("Top 10 municipios por volumen de avisos; se muestra cantidad y participación."): "Municipio",
        _graph_key("Mapa de calor construido a partir de la información de equipos asociada al histórico."): "Departamento",
    }
    dimension = dimension_by_graph[graph_index]
    valid_values = set(df[dimension].astype(str).unique())

    candidates = []
    custom = point.get("customdata")
    if custom is not None:
        if isinstance(custom, (list, tuple)):
            candidates.extend(custom)
        else:
            candidates.append(custom)
    if dimension == "Departamento" and graph_index == _graph_key("Mapa de calor construido a partir de la información de equipos asociada al histórico."):
        candidates.extend([point.get("y"), point.get("label")])
    elif dimension in {"Departamento", "Linea", "Municipio"}:
        candidates.extend([point.get("y"), point.get("x"), point.get("label")])
        # Los rankings muestran un prefijo 01, 02, etc.; customdata evita tener que parsearlo.
    else:
        candidates.extend([point.get("label"), point.get("x"), point.get("y")])

    for candidate in candidates:
        if candidate is not None and str(candidate) in valid_values:
            return {"dimension": dimension, "value": str(candidate), "source": graph_index}

    return no_update


@app.callback(
    Output("page-content", "children"),
    Input("url", "pathname"),
    Input("f-year", "value"),
    Input("f-type", "value"),
    Input("f-dept", "value"),
    Input("type-selection", "data"),
    Input("equipment-selection", "data"),
)
def render_page(pathname, years, types, depts, selected_type, selected_equipment):
    if pathname in (None, "/", "/inicio"):
        return build_home()
    d = apply_filters(years, types, depts)

    # El Store puede contener metadatos de la selección.
    selected_value = None
    if isinstance(selected_type, dict):
        selected_value = selected_type.get("value")
    elif isinstance(selected_type, str):
        selected_value = selected_type

    # El clic solo actúa como filtro cruzado dentro de la página actual.
    # No altera los filtros persistentes de la barra lateral.
    if selected_value and selected_value not in set(d["Tipo de aviso"].astype(str).unique()):
        selected_value = None
    if pathname == "/avisos":
        return build_avisos(d, selected_value)
    if pathname == "/equipos":
        return build_equipos(d, selected_equipment)
    return build_resumen(d, selected_value)


@app.callback(
    Output("interaction-feedback", "children"),
    Input({"type": "dashboard-graph", "index": ALL}, "clickData"),
    Input({"type": "dashboard-graph", "index": ALL}, "relayoutData"),
    prevent_initial_call=True,
)
def graph_interaction(click_datas, relayout_datas):
    trigger = ctx.triggered_id
    if not isinstance(trigger, dict):
        return ""
    event = ctx.triggered[0].get("value") if ctx.triggered else None
    if isinstance(event, dict) and any(
        str(k).endswith(".autorange") and bool(v) for k, v in event.items()
    ):
        return ""
    if not event or not event.get("points"):
        return ""
    point = event["points"][0]
    label = point.get("x") if point.get("x") is not None else point.get("y")
    value = point.get("y") if point.get("y") is not None else point.get("z")
    trace = point.get("fullData", {}).get("name", "Elemento seleccionado")
    if isinstance(value, (int, float)):
        value_text = f" · Valor: {value:,.1f}".replace(",", ".")
    else:
        value_text = ""
    return html.Span([
        html.B("Interacción · "),
        f"Selección: {trace} · Categoría: {label}{value_text} · Doble clic para restaurar",
    ])


@app.callback(
    Output("sidebar", "className"),
    Input("mobile-sidebar-toggle", "n_clicks"),
)
def toggle_mobile_sidebar(n_clicks):
    return "sidebar mobile-open" if (n_clicks or 0) % 2 else "sidebar"


@app.callback(
    Output("nav-inicio", "className"),
    Output("nav-resumen", "className"),
    Output("nav-avisos", "className"),
    Output("nav-equipos", "className"),
    Input("url", "pathname"),
)
def set_active_nav(pathname):
    pathname = pathname or "/inicio"
    return (
        "nav-link active" if pathname in ("/", "/inicio") else "nav-link",
        "nav-link active" if pathname == "/resumen" else "nav-link",
        "nav-link active" if pathname == "/avisos" else "nav-link",
        "nav-link active" if pathname == "/equipos" else "nav-link",
    )


server = app.server

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8050)))
