# ============================================================
#  VISOR NO2 - DMQ  |  Streamlit App
#  Lee la cache generada por el pipeline (Seccion 12).
#  Ejecutar: streamlit run app.py
# ============================================================

import os, json, io, base64, warnings
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
warnings.filterwarnings('ignore')

# ── Configuracion de pagina ───────────────────────────────────
st.set_page_config(
    page_title="Visor NO2 – DMQ",
    page_icon="🌫️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════
#  CONSTANTES Y ESTILOS
# ══════════════════════════════════════════════════════════════

CACHE_PATHS = ['no2_cache_dmq', 'no2_cache', '/content/no2_cache',
               '/content/drive/MyDrive/no2_cache_dmq']
ARCHIVOS_OK = ['meta.json', 'tile_urls.json', 'variables_meta.json',
               'df_calib.csv', 'resultado_df.csv', 'resumen_vias.csv', 'checksum.json']

_BG   = '#0a1628'
_BG2  = '#060f1e'
_BD   = '#1a2e45'
_T1   = '#e2f0ff'
_T2   = '#7aa3cc'
_T3   = '#334155'
ESC_COL = {'Base': '#3b82f6', 'E1': '#f59e0b', 'E2': '#ef4444', f'Proy.': '#a78bfa'}

CSS = """
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
  html, body, [class*="css"] { font-family: 'Inter', 'Segoe UI', system-ui, sans-serif; }
  .main { background: #0a1628 !important; }
  .block-container { background: #0a1628 !important; padding-top: 1rem !important; }
  section[data-testid="stSidebar"] { background: #060f1e !important; border-right: 1px solid #1a2e45; }
  section[data-testid="stSidebar"] * { color: #94a3b8 !important; }
  h1, h2, h3, h4 { color: #e2f0ff !important; }
  .stTabs [data-baseweb="tab-list"] { background: #060f1e; border-bottom: 1px solid #1a2e45; gap: 0; }
  .stTabs [data-baseweb="tab"] {
    background: transparent; color: #7aa3cc; border: none;
    border-bottom: 2px solid transparent; padding: 10px 18px;
    font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: .6px;
  }
  .stTabs [aria-selected="true"] {
    background: transparent !important; color: #34d399 !important;
    border-bottom: 2px solid #34d399 !important;
  }
  .stTabs [data-baseweb="tab-panel"] { background: #0a1628; padding: 0; }
  .stSelectbox > div > div { background: #0d1f38 !important; color: #e2f0ff !important; border: 1px solid #1a2e45 !important; }
  .stButton > button {
    background: #0d1f38 !important; color: #60a5fa !important;
    border: 1px solid #1e3a5f !important; border-radius: 6px;
    font-size: 11px; font-weight: 700;
  }
  .stButton > button:hover { background: #1e3a5f !important; }
  .stNumberInput > div > div > input, .stTextInput > div > div > input {
    background: #0d1f38 !important; color: #e2f0ff !important; border: 1px solid #1a2e45 !important;
  }
  hr { border-color: #1a2e45; }
  .kpi-card {
    background: #0d1f38; border: 1px solid #1e3a5f; border-radius: 10px;
    padding: 16px 18px; position: relative; overflow: hidden;
  }
  .kpi-bar { height: 3px; border-radius: 2px; margin-bottom: 12px; }
  .kpi-label { font-size: 9px; color: #4a7fa5; font-weight: 700;
    text-transform: uppercase; letter-spacing: .8px; margin-bottom: 6px; }
  .kpi-val { font-size: 26px; font-weight: 700; line-height: 1; margin-bottom: 4px; }
  .kpi-unit { font-size: 9px; color: #334155; }
  .kpi-sub { font-size: 9px; margin-top: 6px; }
  .section-label {
    font-size: 9px; font-weight: 700; color: #2d5a8e;
    text-transform: uppercase; letter-spacing: 1.2px;
    margin: 18px 0 8px; padding-bottom: 4px;
    border-bottom: 1px solid #1a2e45;
  }
  .badge {
    display: inline-block; background: #052e16; color: #34d399;
    border: 1px solid #166534; font-size: 9px; font-weight: 700;
    padding: 3px 9px; border-radius: 20px; letter-spacing: .5px; margin-left: 6px;
  }
  .via-card {
    background: #0d1f38; border: 1px solid #1e3a5f; border-radius: 8px;
    padding: 14px 16px;
  }
  .meto-section {
    background: #0d1f38; border: 1px solid #1e3a5f; border-radius: 8px;
    padding: 16px 20px; margin-bottom: 14px;
  }
  .meto-title { font-size: 13px; font-weight: 700; color: #60a5fa; margin-bottom: 8px; }
  .meto-body { font-size: 11px; color: #94a3b8; line-height: 1.8; }
  .meto-formula {
    background: #060f1e; border-left: 3px solid #3b82f6; border-radius: 4px;
    padding: 10px 14px; margin: 10px 0; font-family: monospace;
    font-size: 11px; color: #f59e0b;
  }
  .calc-result {
    background: #052e16; border: 1px solid #166534; border-radius: 8px;
    padding: 16px 20px; margin-top: 12px;
  }
  .stDataFrame { background: #0d1f38 !important; }
  .stDataFrame td, .stDataFrame th { color: #cbd5e1 !important; background: #0d1f38 !important; }
  p, li, span { color: #94a3b8; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
#  CACHE
# ══════════════════════════════════════════════════════════════

def _cache_valida(d):
    return os.path.isdir(d) and all(
        os.path.isfile(os.path.join(d, f)) for f in ARCHIVOS_OK)

@st.cache_resource(show_spinner="Cargando datos del cache...")
def cargar_cache():
    ruta = next((p for p in CACHE_PATHS if _cache_valida(p)), None)
    if not ruta:
        return None, None
    with open(os.path.join(ruta, 'meta.json'))           as f: meta     = json.load(f)
    with open(os.path.join(ruta, 'tile_urls.json'))      as f: t_raw    = json.load(f)
    with open(os.path.join(ruta, 'variables_meta.json')) as f: var_meta = json.load(f)
    with open(os.path.join(ruta, 'checksum.json'))       as f: chk      = json.load(f)
    tile_cache   = {tuple(k.split('||')): v for k, v in t_raw.items()}
    df_calib     = pd.read_csv(os.path.join(ruta, 'df_calib.csv'))
    resultado_df = pd.read_csv(os.path.join(ruta, 'resultado_df.csv'))
    resumen_vias = pd.read_csv(os.path.join(ruta, 'resumen_vias.csv'))
    insitu_path  = os.path.join(ruta, 'no2_insitu.csv')
    df_insitu    = pd.read_csv(insitu_path) if os.path.isfile(insitu_path) else pd.DataFrame()
    return dict(meta=meta, tile_cache=tile_cache, var_meta=var_meta,
                chk=chk, df_calib=df_calib, resultado_df=resultado_df,
                resumen_vias=resumen_vias, df_insitu=df_insitu), ruta

# ══════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════

def _b64fig(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=130, bbox_inches='tight',
                facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()

def _ax_style(ax):
    ax.set_facecolor(_BG)
    for sp in ax.spines.values(): sp.set_edgecolor(_BD)
    ax.tick_params(colors=_T3, labelsize=8)
    ax.grid(axis='both', color=_BD, lw=0.7, alpha=0.6)

def kpi(label, value, unit, sub='', color='#3b82f6', sub_color='#94a3b8'):
    st.markdown(f"""
    <div class="kpi-card">
      <div class="kpi-bar" style="background:{color};"></div>
      <div class="kpi-label">{label}</div>
      <div class="kpi-val" style="color:{color};">{value}</div>
      <div class="kpi-unit">{unit}</div>
      {"" if not sub else f'<div class="kpi-sub" style="color:{sub_color};">{sub}</div>'}
    </div>""", unsafe_allow_html=True)

def section_label(txt):
    st.markdown(f'<div class="section-label">{txt}</div>', unsafe_allow_html=True)

def _df_to_download(df, fname):
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label=f"⬇ Descargar {fname}",
        data=csv, file_name=fname, mime='text/csv',
        use_container_width=True,
    )

# ══════════════════════════════════════════════════════════════
#  GRAFICOS (cacheados)
# ══════════════════════════════════════════════════════════════

@st.cache_data(show_spinner=False)
def _graf_emisiones_curvas(resumen_vias_json):
    rv = pd.read_json(resumen_vias_json, orient='records')
    FACT = {
        'Autopista': {'g_km': 0.62, 'vel': 90,  'flujo': 4500, 'color': '#3b82f6'},
        'Avenida'  : {'g_km': 0.85, 'vel': 40,  'flujo': 1800, 'color': '#f59e0b'},
        'Calle'    : {'g_km': 1.10, 'vel': 30,  'flujo': 800,  'color': '#22c55e'},
        'Puente'   : {'g_km': 0.85, 'vel': 40,  'flujo': 600,  'color': '#a78bfa'},
    }
    HORAS    = 20
    km_range = np.linspace(0, 50, 200)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), facecolor=_BG2)
    ax = axes[0]; _ax_style(ax)
    for tipo, p in FACT.items():
        y = p['flujo'] * km_range * p['g_km'] * HORAS / 1000
        ax.plot(km_range, y, lw=2.5, color=p['color'], label=tipo)
    ax.set_xlabel('Longitud de vía (km)', color=_T2, fontsize=9)
    ax.set_ylabel('Emisión NO₂ (kg/día)', color=_T2, fontsize=9)
    ax.legend(fontsize=9, facecolor='#0d1f38', edgecolor=_BD, labelcolor='#cbd5e1')
    ax.set_title('Curvas de emisión por tipo de vía', color=_T1, fontsize=10, pad=8, fontweight='600')
    ax2 = axes[1]; _ax_style(ax2)
    if 'emision_kg_dia' not in rv.columns and 'ton_anio' in rv.columns:
        rv['emision_kg_dia'] = rv['ton_anio'] * 1000 / 365
    total_k = rv['emision_kg_dia'].sum()
    rv['pct'] = rv['emision_kg_dia'] / total_k * 100
    rv = rv.sort_values('pct', ascending=False).reset_index(drop=True)
    cum = 0
    for _, row in rv.iterrows():
        clr = FACT.get(row['Tipo'], {}).get('color', '#94a3b8')
        ax2.barh(0, row['pct'], left=cum, color=clr, height=0.6, edgecolor=_BG2, lw=1.5)
        if row['pct'] > 3:
            txt_clr = '#1a0a00' if row['pct'] > 15 else '#e2f0ff'
            ax2.text(cum + row['pct'] / 2, 0,
                     f"{row['Tipo']}\n{row['pct']:.1f}%",
                     ha='center', va='center', fontsize=9, fontweight='700', color=txt_clr)
        cum += row['pct']
    ax2.set_xlim(0, 100)
    ax2.set_xlabel('Contribución (%)', color=_T2, fontsize=9)
    ax2.set_yticks([])
    ax2.set_title('Distribución de emisiones', color=_T1, fontsize=10, pad=8, fontweight='600')
    handles = [mpatches.Patch(facecolor=FACT.get(r['Tipo'], {}).get('color', '#94a3b8'),
                               label=f"{r['Tipo']} ({r['pct']:.1f}%)")
               for _, r in rv.iterrows()]
    ax2.legend(handles=handles, fontsize=8.5, facecolor='#0d1f38', edgecolor=_BD,
               labelcolor='#cbd5e1', loc='lower right')
    fig.tight_layout()
    return _b64fig(fig)

@st.cache_data(show_spinner=False)
def _graf_ranking(df_json, col_proy, CNM, n=15):
    df = pd.read_json(df_json, orient='records').head(n)
    fig, ax = plt.subplots(figsize=(10, max(4, n * 0.42)), facecolor=_BG2)
    _ax_style(ax)
    y   = np.arange(len(df))
    act = pd.to_numeric(df['NO2_actual'], errors='coerce').values
    e1  = pd.to_numeric(df['NO2_E1'],    errors='coerce').values
    e2  = pd.to_numeric(df['NO2_E2'],    errors='coerce').values
    pr  = pd.to_numeric(df[col_proy],    errors='coerce').values
    h   = 0.18
    ax.barh(y + 3*h/2, act, h, color='#3b82f6', label='Actual')
    ax.barh(y + h/2,   e1,  h, color='#f59e0b', label='E1')
    ax.barh(y - h/2,   e2,  h, color='#ef4444', label='E2')
    ax.barh(y - 3*h/2, pr,  h, color='#a78bfa', label=f'Proy.')
    ax.set_yticks(y)
    ax.set_yticklabels(df[CNM].values, fontsize=8, color=_T2)
    ax.invert_yaxis()
    ax.set_xlabel('NO₂ (µmol/m²)', color=_T2, fontsize=9)
    ax.set_title(f'Top {n} parroquias — comparación de escenarios',
                 color=_T1, fontsize=10, pad=8, fontweight='600')
    ax.legend(fontsize=9, facecolor='#0d1f38', edgecolor=_BD, labelcolor='#cbd5e1',
              loc='lower right')
    fig.tight_layout()
    return _b64fig(fig)

# ══════════════════════════════════════════════════════════════
#  TABS
# ══════════════════════════════════════════════════════════════

def tab_resumen(D, meta_vals):
    no2_prom, no2_proy, no2_e1_prom, no2_e2_prom, proy_prom, \
    no2_max_v, no2_min_v, parr_max, parr_min, \
    n_parr, delta_27, AFP, col_proy, CNM, df_sorted, \
    A0, A1, E1T, E2T = meta_vals

    st.markdown(f"""
    <div style="background:#0f2744;border:1px solid #1e3a5f;border-radius:10px;
      padding:18px 22px;margin-bottom:20px;">
      <div style="font-size:20px;font-weight:700;color:#e2f0ff;">
        <span style="color:#34d399;">NO2 DMQ</span>
        <span style="color:#7aa3cc;font-size:12px;font-weight:400;margin-left:10px;">
          Monitor de Dióxido de Nitrógeno — Distrito Metropolitano de Quito</span>
        <span class="badge">Sentinel-5P</span>
        <span class="badge">ERA5</span>
        <span class="badge">Landsat</span>
      </div>
      <div style="font-size:9px;color:#334155;margin-top:4px;">
        Periodo analizado: {A0}–{A1} | {n_parr} parroquias | Proyección al {AFP}
      </div>
    </div>""", unsafe_allow_html=True)

    delta_lbl  = f'+{delta_27:.1f}%' if delta_27 >= 0 else f'{delta_27:.1f}%'
    delta_clr  = '#ef4444' if delta_27 >= 0 else '#34d399'

    c1, c2, c3, c4 = st.columns(4)
    with c1: kpi('NO₂ Promedio DMQ', f'{no2_prom:.4f}', 'µmol/m²',
                 f'{delta_lbl} vs proyección {AFP}', '#60a5fa', delta_clr)
    with c2: kpi('Concentración Máxima', f'{no2_max_v:.4f}', f'µmol/m² — {parr_max}',
                 'Parroquia más contaminada', '#ef4444', '#ef4444')
    with c3: kpi('Concentración Mínima', f'{no2_min_v:.4f}', f'µmol/m² — {parr_min}',
                 'Parroquia más limpia', '#34d399', '#34d399')
    with c4: kpi(f'Proyección {AFP}', f'{no2_proy:.4f}', 'µmol/m²',
                 f'{n_parr} parroquias analizadas', '#a78bfa', '#7aa3cc')

    st.markdown('<div style="margin:20px 0;"></div>', unsafe_allow_html=True)
    section_label('Escenarios')
    cs = st.columns(4)
    pairs = [
        ('Actual', no2_prom,    '#3b82f6', f'{A0}–{A1}'),
        ('E1',     no2_e1_prom, '#f59e0b', f'+{round((E1T-1)*100)}% tráfico'),
        ('E2',     no2_e2_prom, '#ef4444', f'+{round((E2T-1)*100)}% tráfico'),
        (f'Proy. {AFP}', proy_prom, '#a78bfa', f'Proyección'),
    ]
    for col, (lbl, val, clr, sub) in zip(cs, pairs):
        with col: kpi(lbl, f'{val:.4f}', 'µmol/m²', sub, clr, '#94a3b8')

    section_label('Ranking Top 15 Parroquias DMQ')
    b64 = _graf_ranking(df_sorted.to_json(orient='records'), col_proy, CNM, n=15)
    st.markdown(f'<img src="data:image/png;base64,{b64}" style="width:100%;border-radius:8px;">',
                unsafe_allow_html=True)

    section_label('Tabla completa')
    top_df = df_sorted[[CNM, 'NO2_actual', 'NO2_E1', 'NO2_E2', col_proy]].copy()
    top_df.columns = ['Parroquia', 'Actual', 'E1', 'E2', f'Proy.{AFP}']
    top_df = top_df.reset_index(drop=True)
    top_df.index += 1
    st.dataframe(top_df.style
        .format({c: '{:.4f}' for c in top_df.columns if c != 'Parroquia'})
        .background_gradient(subset=['Actual'], cmap='Reds'),
        use_container_width=True, height=420)


def tab_mapa(D, meta_vals):
    *_, AFP, col_proy, CNM, df_sorted, A0, A1, E1T, E2T = meta_vals
    TC  = D['tile_cache']
    VM  = D['var_meta']

    st.markdown('<div style="color:#7aa3cc;font-size:11px;margin-bottom:12px;">'
                'Selecciona escenario y variable para visualizar en el mapa interactivo.</div>',
                unsafe_allow_html=True)

    col_ctrl, col_map = st.columns([1, 3])
    with col_ctrl:
        section_label('Escenario')
        esc = st.radio('', ['Base', 'E1', 'E2', f'Proy.{AFP}'],
                       label_visibility='collapsed')
        section_label('Variable')
        var_opts = [(f"{vm.get('icono','')} {vm.get('nombre',v)}", v)
                    for v, vm in VM.items()]
        var_lbl = st.selectbox('', [o[0] for o in var_opts], label_visibility='collapsed')
        var_id  = next((v for l, v in var_opts if l == var_lbl), list(VM.keys())[0])
        mv      = VM.get(var_id, {})
        esc_key = esc if esc != f'Proy.{AFP}' else 'Proyec.'
        url     = TC.get((esc_key, var_id), '')

    with col_map:
        try:
            import folium
            from streamlit_folium import st_folium
            m = folium.Map(location=[-0.2299, -78.5249], zoom_start=10,
                           tiles='CartoDB dark_matter')
            if url:
                folium.TileLayer(
                    tiles=url, name=var_lbl, attr='Google Earth Engine',
                    overlay=True, control=True, opacity=0.85,
                ).add_to(m)
                folium.LayerControl().add_to(m)
            st_folium(m, width=None, height=520, returned_objects=[])
            if url:
                mn = mv.get('min', 0); mx = mv.get('max', 1)
                grad = ', '.join(mv.get('paleta', ['#fff','#f00']))
                st.markdown(
                    f'<div style="background:#0d1f38;border:1px solid #1a2e45;'
                    f'border-radius:6px;padding:8px 14px;margin-top:6px;display:inline-block;">'
                    f'<b style="font-size:10px;color:#c7e0f4;">'
                    f'{mv.get("icono","")} {mv.get("nombre",var_id)}</b>'
                    f'<span style="font-size:9px;color:#4a7fa5;"> — {esc}</span>'
                    f'<div style="height:7px;border-radius:3px;margin:4px 0;'
                    f'background:linear-gradient(to right,{grad});width:200px;"></div>'
                    f'<div style="display:flex;justify-content:space-between;'
                    f'font-size:9px;color:#334155;width:200px;">'
                    f'<span>{mn}</span><span>{round((mn+mx)/2,3)}</span><span>{mx}</span></div>'
                    f'<div style="font-size:9px;color:#334155;text-align:right;">'
                    f'{mv.get("unidad","")}</div></div>',
                    unsafe_allow_html=True)
            else:
                st.info('No hay tile disponible para esta combinación escenario/variable.')
        except ImportError:
            st.warning('Instala `folium` y `streamlit-folium` para ver el mapa interactivo.')
            st.code('pip install folium streamlit-folium')


def tab_parroquia(D, meta_vals):
    no2_prom, no2_proy, no2_e1_prom, no2_e2_prom, proy_prom, \
    no2_max_v, no2_min_v, parr_max, parr_min, \
    n_parr, delta_27, AFP, col_proy, CNM, df_sorted, \
    A0, A1, E1T, E2T = meta_vals

    parr_sel = st.selectbox('Selecciona una parroquia', df_sorted[CNM].values,
                            label_visibility='visible')
    matches  = df_sorted[df_sorted[CNM] == parr_sel]
    if len(matches) == 0:
        st.warning('Parroquia no encontrada.')
        return

    row   = matches.iloc[0]
    rank  = int(matches.index[0]) + 1
    v_act = pd.to_numeric(row['NO2_actual'], errors='coerce')
    v_e1  = pd.to_numeric(row['NO2_E1'],    errors='coerce')
    v_e2  = pd.to_numeric(row['NO2_E2'],    errors='coerce')
    v_p   = pd.to_numeric(row[col_proy],    errors='coerce')
    pct_rank = round((n_parr - rank) / n_parr * 100) if n_parr else 0
    d27      = (v_p - v_act) / v_act * 100 if v_act else 0

    st.markdown(f"""
    <div style="background:#0f2744;border:1px solid #1e3a5f;border-radius:8px;
      padding:16px 20px;margin-bottom:16px;">
      <div style="font-size:18px;font-weight:700;color:#34d399;margin-bottom:10px;">
        {parr_sel}</div>
    </div>""", unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    rk_clr = '#f59e0b' if rank <= 3 else '#e2f0ff'
    with c1: kpi('Ranking DMQ', f'#{rank}', f'de {n_parr} parroquias', '', rk_clr)
    with c2: kpi('Percentil',  f'{pct_rank}%', '', '', '#60a5fa')
    with c3: kpi('NO₂ Actual', f'{v_act:.4f}', 'µmol/m²', '', '#3b82f6')
    with c4: kpi(f'Proyección {AFP}', f'{v_p:.4f}', 'µmol/m²',
                 f'+{d27:.1f}% vs actual', '#a78bfa', '#ef4444')

    section_label('Comparación de Escenarios')
    max_bar = no2_max_v * 1.3 if no2_max_v else 1
    for val, lbl, clr in [
        (v_act, 'Actual',                      '#3b82f6'),
        (v_e1,  f'E1 +{round((E1T-1)*100)}%', '#f59e0b'),
        (v_e2,  f'E2 +{round((E2T-1)*100)}%', '#ef4444'),
        (v_p,   f'Proyección {AFP}',           '#a78bfa'),
    ]:
        pct_w = int(val / max_bar * 100) if max_bar else 0
        st.markdown(
            f'<div style="margin-bottom:10px;">'
            f'<div style="display:flex;justify-content:space-between;margin-bottom:3px;">'
            f'<span style="font-size:10px;color:#94a3b8;">{lbl}</span>'
            f'<span style="font-size:10px;font-weight:700;color:{clr};">{val:.4f} µmol/m²</span>'
            f'</div>'
            f'<div style="background:#0a1628;border-radius:3px;height:8px;overflow:hidden;">'
            f'<div style="width:{pct_w}%;height:8px;border-radius:3px;background:{clr};"></div>'
            f'</div></div>',
            unsafe_allow_html=True)

    section_label('Contexto DMQ')
    st.markdown(
        f'<div style="background:#0d1f38;border:1px solid #1e3a5f;border-radius:8px;padding:12px 14px;">'
        f'<div style="display:flex;justify-content:space-between;padding:6px 0;'
        f'border-bottom:1px solid #0a1628;font-size:10.5px;">'
        f'<span style="color:#7aa3cc;">NO₂ máximo DMQ</span>'
        f'<span style="color:#e2f0ff;font-weight:600;">{no2_max_v:.4f} µmol/m²</span></div>'
        f'<div style="display:flex;justify-content:space-between;padding:6px 0;'
        f'border-bottom:1px solid #0a1628;font-size:10.5px;">'
        f'<span style="color:#7aa3cc;">NO₂ promedio DMQ</span>'
        f'<span style="color:#e2f0ff;font-weight:600;">{no2_prom:.4f} µmol/m²</span></div>'
        f'<div style="display:flex;justify-content:space-between;padding:6px 0;'
        f'border-bottom:1px solid #0a1628;font-size:10.5px;">'
        f'<span style="color:#7aa3cc;">Esta parroquia</span>'
        f'<span style="color:#34d399;font-weight:700;">{v_act:.4f} µmol/m²</span></div>'
        f'<div style="display:flex;justify-content:space-between;padding:6px 0;font-size:10.5px;">'
        f'<span style="color:#7aa3cc;">NO₂ mínimo DMQ</span>'
        f'<span style="color:#e2f0ff;font-weight:600;">{no2_min_v:.4f} µmol/m²</span></div>'
        f'</div>',
        unsafe_allow_html=True)


def tab_via(D, meta_vals):
    *_, AFP, col_proy, CNM, df_sorted, A0, A1, E1T, E2T = meta_vals
    res_vias = D['resumen_vias'].copy()
    if 'emision_ton_anio' in res_vias.columns and 'ton_anio' not in res_vias.columns:
        res_vias = res_vias.rename(columns={'emision_ton_anio': 'ton_anio'})
    elif 'ton_anio' not in res_vias.columns:
        res_vias['ton_anio'] = res_vias['emision_kg_dia'] * 365 / 1000

    vc = {'Autopista': '#3b82f6', 'Avenida': '#f59e0b',
          'Calle': '#22c55e', 'Puente': '#a78bfa'}
    total_kg  = float(res_vias['emision_kg_dia'].sum())
    total_ton = float(res_vias['ton_anio'].sum())
    n_vias_t  = int(res_vias['n_vias'].sum())

    c1, c2, c3 = st.columns(3)
    with c1: kpi('Emisión Total DMQ',  f'{total_kg:,.0f}', 'kg NO₂/día', '', '#3b82f6')
    with c2: kpi('Emisión Anual',      f'{total_ton:,.0f}', 'toneladas NO₂/año', '', '#34d399')
    with c3: kpi('Segmentos',          f'{n_vias_t:,}', 'vías en el DMQ', '', '#f59e0b')

    section_label('Distribución por categoría vial')
    b64 = _graf_emisiones_curvas(res_vias.to_json(orient='records'))
    st.markdown(f'<img src="data:image/png;base64,{b64}" style="width:100%;border-radius:8px;">',
                unsafe_allow_html=True)

    section_label('Tabla de emisiones')
    tabla = res_vias[['Tipo', 'n_vias', 'longitud_km', 'emision_kg_dia', 'ton_anio']].copy()
    tabla.columns = ['Tipo de Vía', 'N° Vías', 'Longitud (km)', 'kg NO₂/día', 'Ton/año']
    st.dataframe(tabla.style.format({
        'Longitud (km)': '{:.1f}', 'kg NO₂/día': '{:,.1f}', 'Ton/año': '{:,.1f}'
    }), use_container_width=True)

    section_label('Factores de emisión utilizados')
    FACT = [('Autopista',0.62,90,4500),('Avenida',0.85,40,1800),
            ('Calle',1.10,30,800),('Puente',0.85,40,600)]
    st.dataframe(pd.DataFrame(FACT, columns=['Tipo','Factor (g/veh-km)','Vel (km/h)','Flujo (veh/h)']),
                 use_container_width=True, hide_index=True)
    st.caption('Período de operación: 20 h/día · E = Flujo × L × FE × Horas / 1000')


def tab_escenarios(D, meta_vals):
    no2_prom, no2_proy, no2_e1_prom, no2_e2_prom, proy_prom, \
    no2_max_v, no2_min_v, parr_max, parr_min, \
    n_parr, delta_27, AFP, col_proy, CNM, df_sorted, \
    A0, A1, E1T, E2T = meta_vals
    res_df = D['resultado_df']

    delta_e1 = (no2_e1_prom - no2_prom) / no2_prom * 100 if no2_prom else 0
    delta_e2 = (no2_e2_prom - no2_prom) / no2_prom * 100 if no2_prom else 0
    delta_e1_max = ((pd.to_numeric(res_df['NO2_E1'], errors='coerce') -
                     pd.to_numeric(res_df['NO2_actual'], errors='coerce')) /
                    pd.to_numeric(res_df['NO2_actual'], errors='coerce') * 100).max()
    delta_e2_max = ((pd.to_numeric(res_df['NO2_E2'], errors='coerce') -
                     pd.to_numeric(res_df['NO2_actual'], errors='coerce')) /
                    pd.to_numeric(res_df['NO2_actual'], errors='coerce') * 100).max()

    c1, c2, c3, c4 = st.columns(4)
    for col, (lbl, val, clr) in zip([c1,c2,c3,c4], [
        ('Base (actual)',       no2_prom,    '#3b82f6'),
        (f'E1 +{round((E1T-1)*100)}% tráfico', no2_e1_prom, '#f59e0b'),
        (f'E2 +{round((E2T-1)*100)}% tráfico', no2_e2_prom, '#ef4444'),
        (f'Proyección {AFP}',  proy_prom,   '#a78bfa'),
    ]):
        with col: kpi(lbl, f'{val:.4f}', 'µmol/m² promedio', '', clr)

    st.markdown('<div style="margin:12px 0;"></div>', unsafe_allow_html=True)
    d1c, d2c, d3c = st.columns(3)
    with d1c: kpi('E1 vs Actual', f'+{delta_e1:.2f}%', f'máx: +{delta_e1_max:.1f}%', '', '#f59e0b')
    with d2c: kpi('E2 vs Actual', f'+{delta_e2:.2f}%', f'máx: +{delta_e2_max:.1f}%', '', '#ef4444')
    with d3c: kpi(f'{AFP} vs Actual', f'+{delta_27:.2f}%', 'variación media DMQ', '', '#a78bfa')

    section_label('Concentraciones por parroquia y escenario')
    top_df = df_sorted[[CNM,'NO2_actual','NO2_E1','NO2_E2',col_proy]].copy()
    top_df.columns = ['Parroquia','Actual','E1','E2',f'Proy.{AFP}']
    top_df['ΔE1%'] = ((top_df['E1'] - top_df['Actual']) / top_df['Actual'] * 100).map('{:+.1f}%'.format)
    top_df['ΔE2%'] = ((top_df['E2'] - top_df['Actual']) / top_df['Actual'] * 100).map('{:+.1f}%'.format)
    top_df[f'Δ{AFP}%'] = ((top_df[f'Proy.{AFP}'] - top_df['Actual']) / top_df['Actual'] * 100).map('{:+.1f}%'.format)
    top_df = top_df.reset_index(drop=True)
    top_df.index += 1
    st.dataframe(top_df.style.format(
        {c: '{:.4f}' for c in ['Actual','E1','E2',f'Proy.{AFP}']}),
        use_container_width=True, height=450)


def tab_calculadora():
    FACT_CALC = {
        'Autopista': {'g_km': 0.62, 'vel': 90,  'flujo': 4500},
        'Avenida'  : {'g_km': 0.85, 'vel': 40,  'flujo': 1800},
        'Calle'    : {'g_km': 1.10, 'vel': 30,  'flujo': 800},
        'Puente'   : {'g_km': 0.85, 'vel': 40,  'flujo': 600},
    }
    HORAS = 20

    st.markdown("""
    <div class="meto-section">
      <div class="meto-title">Calculadora de Emisiones por Tramo Vial</div>
      <div class="meto-formula">
        E [kg/día] = Flujo [veh/h] × L [km] × FE [g/veh·km] × 20 [h/día] / 1000
      </div>
    </div>""", unsafe_allow_html=True)

    c1, c2, c3 = st.columns([2, 2, 1])
    with c1:
        tipo = st.selectbox('Tipo de vía', list(FACT_CALC.keys()))
    with c2:
        col_l, col_u = st.columns([3, 1])
        with col_l: longitud = st.number_input('Longitud', min_value=0.1, max_value=500.0,
                                                value=1.0, step=0.1)
        with col_u: unidad = st.selectbox('', ['km', 'm'], label_visibility='collapsed')
    with c3:
        st.markdown('<div style="margin-top:28px;"></div>', unsafe_allow_html=True)
        calcular = st.button('Calcular', use_container_width=True)

    if calcular or longitud:
        km = longitud if unidad == 'km' else longitud / 1000
        p  = FACT_CALC[tipo]
        kg  = p['flujo'] * km * p['g_km'] * HORAS / 1000
        ton = kg * 365 / 1000
        st.markdown(f"""
        <div class="calc-result">
          <div style="font-size:11px;color:#6ee7b7;margin-bottom:12px;font-weight:600;">
            {tipo} — {km:.2f} km</div>
          <div style="display:flex;gap:32px;margin-bottom:12px;">
            <div>
              <div style="font-size:9px;color:#34d399;font-weight:700;
                text-transform:uppercase;letter-spacing:.8px;">kg NO₂ / día</div>
              <div style="font-size:32px;font-weight:700;color:#34d399;">{kg:,.1f}</div>
            </div>
            <div>
              <div style="font-size:9px;color:#6ee7b7;font-weight:700;
                text-transform:uppercase;letter-spacing:.8px;">ton NO₂ / año</div>
              <div style="font-size:32px;font-weight:700;color:#6ee7b7;">{ton:,.2f}</div>
            </div>
          </div>
          <div style="font-size:9.5px;color:#4ade80;line-height:1.9;
            padding-top:10px;border-top:1px solid #166534;">
            E = {p['flujo']:,} × {km:.2f} × {p['g_km']} × {HORAS} / 1000<br>
            Flujo: {p['flujo']:,} veh/h | Factor: {p['g_km']} g/veh·km |
            Velocidad: {p['vel']} km/h | Horas: {HORAS} h/día
          </div>
        </div>""", unsafe_allow_html=True)


def tab_descargar(D, meta_vals):
    *_, AFP, col_proy, CNM, df_sorted, A0, A1, E1T, E2T = meta_vals
    res_df   = D['resultado_df']
    df_calib = D['df_calib']
    res_vias = D['resumen_vias']
    df_insitu = D['df_insitu']

    st.markdown('<div style="color:#7aa3cc;font-size:11px;margin-bottom:16px;">'
                'Descarga directa de los datos generados por el pipeline.</div>',
                unsafe_allow_html=True)

    ranking_df = df_sorted[[CNM, 'NO2_actual', 'NO2_E1', 'NO2_E2', col_proy]].copy()
    stats_df = pd.DataFrame({
        'Escenario': ['Base', 'E1', 'E2', f'Proy.{AFP}'],
        'Min':   [pd.to_numeric(res_df[c], errors='coerce').min()
                  for c in ['NO2_actual', 'NO2_E1', 'NO2_E2', col_proy]],
        'Media': [pd.to_numeric(res_df[c], errors='coerce').mean()
                  for c in ['NO2_actual', 'NO2_E1', 'NO2_E2', col_proy]],
        'Max':   [pd.to_numeric(res_df[c], errors='coerce').max()
                  for c in ['NO2_actual', 'NO2_E1', 'NO2_E2', col_proy]],
    })

    datasets = [
        (res_df,      'NO2_parroquias_completo.csv',   'Resultados completos',
         'Todos los escenarios y deltas por parroquia'),
        (ranking_df,  'NO2_ranking_parroquias.csv',    'Ranking de concentración',
         f'{len(df_sorted)} parroquias ordenadas por NO₂ actual'),
        (df_calib,    'NO2_serie_temporal.csv',        f'Serie temporal ({A0}–{A1})',
         'Sentinel-5P raw, corregido, in situ y bias ratio'),
        (res_vias,    'NO2_emisiones_vias.csv',        'Emisiones por tipo de vía',
         'kg/día, ton/año, porcentaje y longitud km'),
        (stats_df,    'NO2_estadisticas_globales.csv', 'Estadísticas globales DMQ',
         'Mín, media y máx por escenario'),
    ]
    if not df_insitu.empty:
        datasets.append((df_insitu, 'NO2_insitu.csv', 'Datos in situ',
                         'Estaciones de monitoreo con coordenadas y valores anuales'))

    cols = st.columns(2)
    for i, (df_obj, fname, titulo, sub) in enumerate(datasets):
        with cols[i % 2]:
            st.markdown(f"""
            <div style="background:#0d1f38;border:1px solid #1e3a5f;border-radius:8px;
              padding:14px 16px;margin-bottom:14px;">
              <div style="font-size:13px;font-weight:700;color:#e2f0ff;">{titulo}</div>
              <div style="font-size:10px;color:#4a7fa5;margin:3px 0 6px;">{sub}</div>
              <div style="font-size:9px;color:#334155;">{len(df_obj)} filas × {len(df_obj.columns)} columnas — CSV UTF-8</div>
            </div>""", unsafe_allow_html=True)
            _df_to_download(df_obj, fname)


def tab_metodologia(D, meta_vals):
    *_, AFP, col_proy, CNM, df_sorted, A0, A1, E1T, E2T = meta_vals
    meta         = D['meta']
    E1N          = meta['ESC1_NDVI']
    E2N          = meta['ESC2_NDVI']
    modelo_proy  = meta.get('modelo_proyeccion', 'tendencia lineal')
    no2_proy     = meta['no2_proyectado']
    no2_2026     = meta.get('no2_2026', no2_proy)

    pesos = [('Vías',40,'#3b82f6'),('Viento',20,'#60a5fa'),
             ('Temperatura',15,'#93c5fd'),('NDVI',20,'#34d399'),('Pendiente',5,'#a78bfa')]

    st.markdown(f"""
    <div class="meto-section">
      <div class="meto-title">Fuente de Datos Principal</div>
      <div class="meto-body">
        NO₂ troposférico de <b>Sentinel-5P / TROPOMI</b> (producto OFFL/L3_NO2),
        banda <code>tropospheric_NO2_column_number_density</code> en mol/m².
        Periodo: {A0}–{A1}. Resolución nativa ~3.5 km, reproyectado a 200 m
        (UTM zona 17S, EPSG:32717). Valores convertidos a µmol/m² (×10⁶).
      </div>
    </div>
    <div class="meto-section">
      <div class="meto-title">Índice Ponderado</div>
      <div class="meto-formula">
        I = 0.40·ProxVías + 0.20·(1−Viento) + 0.15·Temp + 0.20·(1−NDVI) + 0.05·Pendiente
      </div>
    </div>""", unsafe_allow_html=True)

    section_label('Pesos del índice ponderado')
    for lbl, pct, clr in pesos:
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:6px;">'
            f'<span style="width:90px;font-size:10px;color:#94a3b8;">{lbl}</span>'
            f'<span style="width:38px;font-size:10px;color:#60a5fa;font-weight:700;text-align:right;">{pct}%</span>'
            f'<div style="flex:1;background:#060f1e;border-radius:3px;height:7px;">'
            f'<div style="width:{pct*2.5}%;height:7px;border-radius:3px;background:{clr};"></div>'
            f'</div></div>',
            unsafe_allow_html=True)

    st.markdown(f"""
    <div class="meto-section" style="margin-top:16px;">
      <div class="meto-title">Calibración In Situ</div>
      <div class="meto-body">
        Bias correction: ratio <code>NO₂_insitu / NO₂_sentinel</code> por año.
      </div>
    </div>
    <div class="meto-section">
      <div class="meto-title">Proyección {AFP}</div>
      <div class="meto-body">
        Modelo: <b style="color:#a78bfa;">{modelo_proy}</b><br>
        Proyección 2026: <b style="color:#f59e0b;">{no2_2026:.4f} µmol/m²</b><br>
        Proyección {AFP}: <b style="color:#a78bfa;">{no2_proy:.4f} µmol/m²</b>
      </div>
    </div>
    <div class="meto-section">
      <div class="meto-title">Escenarios</div>
      <div class="meto-body">
        E1: radio de influencia vías ×{E1T} | NDVI −{round((1-E1N)*100)}%<br>
        E2: radio de influencia vías ×{E2T} | NDVI −{round((1-E2N)*100)}%
      </div>
    </div>
    <div class="meto-section">
      <div class="meto-title">Variables Auxiliares</div>
      <div class="meto-body">
        Viento: ERA5-Land u/v → magnitud. Temperatura: ERA5-Land K→°C.
        NDVI: Landsat C02 [−1,1]. Pendiente: ee.Terrain.slope().
        Distancia vías: Fast Distance Transform.
      </div>
    </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════

def main():
    D, ruta = cargar_cache()

    if D is None:
        st.error('**No se encontró la cache de resultados.**')
        st.markdown("""
        El visor necesita que el pipeline haya corrido al menos una vez.

        **Pasos:**
        1. Corre las Secciones 1 a 12 en Google Colab.
        2. Al final de la Sección 12, guarda en Google Drive.
        3. Coloca los archivos de `no2_cache/` en la raíz de este repositorio.
        4. Vuelve a lanzar la app.

        **Archivos requeridos:** `meta.json`, `tile_urls.json`, `variables_meta.json`,
        `df_calib.csv`, `resultado_df.csv`, `resumen_vias.csv`, `checksum.json`
        """)
        return

    # ── Extraer metadatos ─────────────────────────────────────
    meta     = D['meta']
    res_df   = D['resultado_df']
    res_vias = D['resumen_vias'].copy()

    if 'emision_ton_anio' in res_vias.columns and 'ton_anio' not in res_vias.columns:
        res_vias = res_vias.rename(columns={'emision_ton_anio': 'ton_anio'})
    elif 'ton_anio' not in res_vias.columns:
        res_vias['ton_anio'] = res_vias['emision_kg_dia'] * 365 / 1000
    D['resumen_vias'] = res_vias

    no2_prom    = meta['no2_prom']
    no2_proy    = meta['no2_proyectado']
    col_proy    = meta['col_proyec']
    CNM         = meta['CAMPO_NOMBRE']
    A0          = meta['ANIO_INICIO_NO2']
    A1          = meta['ANIO_FIN_NO2']
    AFP         = meta['ANIO_FIN_PROYECCION']
    E1T         = meta['ESC1_TRAFICO']
    E1N         = meta['ESC1_NDVI']
    E2T         = meta['ESC2_TRAFICO']
    E2N         = meta['ESC2_NDVI']
    chk         = D['chk']
    ts          = chk.get('timestamp', '')[:19].replace('T', ' ')

    df_sorted   = (res_df.dropna(subset=['NO2_actual']).copy()
                   .sort_values('NO2_actual', ascending=False)
                   .reset_index(drop=True))
    no2_vals    = pd.to_numeric(df_sorted['NO2_actual'], errors='coerce')
    no2_max_v   = float(no2_vals.max())
    no2_min_v   = float(no2_vals.min())
    parr_max    = df_sorted.iloc[0][CNM]  if len(df_sorted) else 'N/A'
    parr_min    = df_sorted.iloc[-1][CNM] if len(df_sorted) else 'N/A'
    n_parr      = len(df_sorted)
    no2_e1_prom = pd.to_numeric(res_df['NO2_E1'],  errors='coerce').mean()
    no2_e2_prom = pd.to_numeric(res_df['NO2_E2'],  errors='coerce').mean()
    proy_prom   = pd.to_numeric(res_df[col_proy],  errors='coerce').mean()
    delta_27    = (no2_proy - no2_prom) / no2_prom * 100 if no2_prom else 0

    meta_vals = (
        no2_prom, no2_proy, no2_e1_prom, no2_e2_prom, proy_prom,
        no2_max_v, no2_min_v, parr_max, parr_min,
        n_parr, delta_27, AFP, col_proy, CNM, df_sorted,
        A0, A1, E1T, E2T,
    )

    # ── Sidebar ───────────────────────────────────────────────
    with st.sidebar:
        st.markdown(f"""
        <div style="padding:12px 0;">
          <div style="font-size:16px;font-weight:700;color:#34d399;">NO₂ DMQ</div>
          <div style="font-size:10px;color:#4a7fa5;margin-top:2px;">
            Dióxido de Nitrógeno troposférico</div>
          <div style="font-size:9px;color:#334155;margin-top:8px;">
            Cache: {ts}<br>Fuente: {ruta}</div>
        </div>
        <hr>
        <div style="font-size:9px;color:#4a7fa5;font-weight:700;text-transform:uppercase;
          letter-spacing:.8px;margin-bottom:6px;">Resumen rápido</div>
        <div style="font-size:11px;color:#7aa3cc;">
          📍 {n_parr} parroquias<br>
          📅 {A0}–{A1}<br>
          🌫 NO₂ prom: <b style="color:#e2f0ff;">{no2_prom:.4f}</b> µmol/m²<br>
          📈 Proyección {AFP}: <b style="color:#a78bfa;">{no2_proy:.4f}</b> µmol/m²<br>
          ⚠️ Más contaminada: <b style="color:#ef4444;">{parr_max}</b><br>
          ✅ Más limpia: <b style="color:#34d399;">{parr_min}</b>
        </div>
        <hr>
        <div style="font-size:9px;color:#334155;">
          Sentinel-5P · ERA5-Land · Landsat C02<br>
          Google Earth Engine · Streamlit
        </div>
        """, unsafe_allow_html=True)

    # ── Tabs ─────────────────────────────────────────────────
    tabs = st.tabs([
        '📊 Resumen', '🗺 Mapa', '🏘 Parroquia',
        '🛣 Por Vía', '📈 Escenarios',
        '🧮 Calculadora', '⬇ Descargar', '📖 Metodología'
    ])

    with tabs[0]: tab_resumen(D, meta_vals)
    with tabs[1]: tab_mapa(D, meta_vals)
    with tabs[2]: tab_parroquia(D, meta_vals)
    with tabs[3]: tab_via(D, meta_vals)
    with tabs[4]: tab_escenarios(D, meta_vals)
    with tabs[5]: tab_calculadora()
    with tabs[6]: tab_descargar(D, meta_vals)
    with tabs[7]: tab_metodologia(D, meta_vals)


if __name__ == '__main__':
    main()
