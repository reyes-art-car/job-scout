#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
busqueda_diaria.py — Búsqueda autónoma diaria de ofertas junior Java/Spring/Angular
Ejecución:
  python busqueda_diaria.py                  (portales España habituales)
  python busqueda_diaria.py --portal linkedin (solo LinkedIn España, exhaustivo)
  python busqueda_diaria.py --portal europa   (empresas internacionales 100%
                                                remoto, fuera de España, en
                                                inglés y/o español)
Requiere: ANTHROPIC_API_KEY en variables de entorno
Dependencias: openpyxl, python-docx, PyYAML
"""

import os
import sys
import json
import re
import datetime
import subprocess
from pathlib import Path
import openpyxl
try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("Falta PyYAML: ejecuta  pip install -r automation/requirements.txt")
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from docx import Document
from docx.shared import Inches, Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

# ── Configuración de rutas ─────────────────────────────────────────────────────
# Raíz del proyecto = carpeta padre de automation/. Los datos personales (Excel, CVs, logs) viven ahí y están fuera de git.
BASE_DIR = str(Path(__file__).resolve().parent.parent)
CV_DIR   = os.path.join(BASE_DIR, "CV_adaptados")
EXCEL    = os.path.join(BASE_DIR, "Ofertas_Maria_Reyes.xlsx")
LOG_DIR  = os.path.join(BASE_DIR, "logs")
os.makedirs(CV_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# ── Colores ────────────────────────────────────────────────────────────────────
HDR_TEAL = "1A6870"
XL_TEAL  = "006666"
XL_LIGHT = "E8F4F4"

# ── Columnas Excel ─────────────────────────────────────────────────────────────
COLS = [
    "ID","Prioridad","% Compatibilidad","Puesto","Empresa","Portal","Enlace",
    "Fecha publicación","Ubicación","Modalidad","Tipo contrato","Salario",
    "Experiencia solicitada","Tecnologías obligatorias","Tecnologías deseables",
    "Requisitos que cumplo","Requisitos que NO cumplo","Motivo puntuación",
    "Estado candidatura","Nombre CV adaptado","Observaciones"
]

# ── Perfil de la candidata (fuente única: backend/config/candidate_profile.yaml) ──
# El YAML real contiene datos de contacto y no se versiona; candidate_profile.example.yaml es la plantilla.
_PROFILE_DIR = Path(BASE_DIR) / "backend" / "config"
PROFILE_PATH = next(
    p for p in (_PROFILE_DIR / "candidate_profile.yaml", _PROFILE_DIR / "candidate_profile.example.yaml")
    if p.exists()
)
with open(PROFILE_PATH, encoding="utf-8") as _f:
    _PROFILE = yaml.safe_load(_f)

NAME              = _PROFILE["name"]
CONTACT           = _PROFILE["contact_line"]
BULLETS           = _PROFILE["bullets"]
SKILLS            = {order: [(g["label"], g["content"]) for g in groups] for order, groups in _PROFILE["skills"].items()}
CANDIDATE_PROFILE = _PROFILE["summary_prompt_block"]

# ══════════════════════════════════════════════════════════════════════════════
# LECTURA Y ESCRITURA DEL EXCEL
# ══════════════════════════════════════════════════════════════════════════════

def get_existing_urls_and_last_id():
    """Lee el Excel existente y devuelve (set de URLs conocidas, último número de ID)."""
    if not os.path.exists(EXCEL):
        return set(), 0
    wb = openpyxl.load_workbook(EXCEL)
    ws = wb.active
    known_urls = set()
    last_num = 0
    for row in ws.iter_rows(min_row=2, values_only=True):
        if row[0]:  # columna ID
            try:
                num = int(str(row[0]).replace("OF", ""))
                last_num = max(last_num, num)
            except ValueError:
                pass
        if row[6]:  # columna URL (índice 6)
            known_urls.add(str(row[6]).strip())
    wb.close()
    return known_urls, last_num


def append_offers_to_excel(new_offers):
    """Añade filas de nuevas ofertas al Excel existente (o crea uno nuevo)."""
    if os.path.exists(EXCEL):
        wb = openpyxl.load_workbook(EXCEL)
        ws = wb.active
        next_row = ws.max_row + 1
    else:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Ofertas"
        # Cabecera
        header_fill = PatternFill("solid", fgColor=XL_TEAL)
        header_font = Font(bold=True, color="FFFFFF", size=10)
        border = Border(
            left=Side(style="thin"), right=Side(style="thin"),
            top=Side(style="thin"), bottom=Side(style="thin")
        )
        for c, col_name in enumerate(COLS, 1):
            cell = ws.cell(row=1, column=c, value=col_name)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")
            cell.border = border
        ws.row_dimensions[1].height = 30
        ws.freeze_panes = "A2"
        col_widths = [8,10,12,30,20,12,45,14,20,22,18,20,18,45,35,50,45,60,20,40,40]
        for i, w in enumerate(col_widths, 1):
            ws.column_dimensions[get_column_letter(i)].width = w
        next_row = 2

    border = Border(
        left=Side(style="thin"), right=Side(style="thin"),
        top=Side(style="thin"), bottom=Side(style="thin")
    )

    for o in new_offers:
        r = next_row
        bg = XL_LIGHT if r % 2 == 0 else "FFFFFF"
        row_data = [
            o.get("id",""),
            o.get("priority",""),
            f"{o.get('compatibility',0)}%",
            o.get("title",""),
            o.get("company",""),
            o.get("portal",""),
            o.get("url",""),
            o.get("date",""),
            o.get("location",""),
            o.get("modality",""),
            o.get("contract","No especificado"),
            o.get("salary","No especificado"),
            o.get("experience","No especificado"),
            o.get("mandatory_tech",""),
            o.get("desirable_tech",""),
            o.get("meets",""),
            o.get("missing",""),
            o.get("score_reason",""),
            o.get("status","Pendiente de revisión"),
            o.get("cv_file",""),
            o.get("notes",""),
        ]
        for c, val in enumerate(row_data, 1):
            cell = ws.cell(row=r, column=c, value=val)
            cell.fill = PatternFill("solid", fgColor=bg)
            cell.font = Font(size=9)
            cell.alignment = Alignment(wrap_text=True, vertical="top")
            cell.border = border
            if c == 7 and val and str(val).startswith("http"):
                cell.hyperlink = str(val)
                cell.font = Font(size=9, color="0563C1", underline="single")

        compat = o.get("compatibility", 0)
        if compat >= 85:
            score_fill = PatternFill("solid", fgColor="C6EFCE")
        elif compat >= 70:
            score_fill = PatternFill("solid", fgColor="FFEB9C")
        else:
            score_fill = PatternFill("solid", fgColor="FFC7CE")
        ws.cell(row=r, column=3).fill = score_fill
        ws.cell(row=r, column=3).font = Font(bold=True, size=10)
        ws.cell(row=r, column=3).alignment = Alignment(horizontal="center", vertical="top")

        next_row += 1

    ws.auto_filter.ref = f"A1:{get_column_letter(len(COLS))}{ws.max_row}"
    wb.save(EXCEL)
    print(f"[OK] Excel actualizado: {EXCEL} (+{len(new_offers)} ofertas)")


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS DOCX
# ══════════════════════════════════════════════════════════════════════════════

def hex_to_rgb(h):
    h = h.lstrip("#")
    return RGBColor(int(h[0:2],16), int(h[2:4],16), int(h[4:6],16))

def set_para_spacing(para, before=0, after=0, line=None):
    pPr = para._p.get_or_add_pPr()
    spacing = OxmlElement("w:spacing")
    spacing.set(qn("w:before"), str(before))
    spacing.set(qn("w:after"), str(after))
    if line:
        spacing.set(qn("w:line"), str(line))
        spacing.set(qn("w:lineRule"), "auto")
    pPr.append(spacing)

def add_section_title(doc, title):
    para = doc.add_paragraph()
    set_para_spacing(para, before=80, after=20)
    run = para.add_run(title)
    run.bold = True
    run.font.size = Pt(9)
    run.font.color.rgb = hex_to_rgb(HDR_TEAL)
    pPr = para._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "6")
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), HDR_TEAL)
    pBdr.append(bottom)
    pPr.append(pBdr)
    return para

def add_bullet(doc, text):
    para = doc.add_paragraph(style="List Bullet")
    set_para_spacing(para, before=20, after=20)
    run = para.add_run(text)
    run.font.size = Pt(8.5)
    return para

def create_cv(offer):
    doc = Document()
    for section in doc.sections:
        section.top_margin    = Cm(1.2)
        section.bottom_margin = Cm(1.2)
        section.left_margin   = Cm(1.8)
        section.right_margin  = Cm(1.8)

    # Cabecera teal
    tbl = doc.add_table(rows=0, cols=1)
    tbl.style = "Table Grid"
    tbl.autofit = True

    for row_text, pt_size, bold, before, after in [
        (NAME,                  18, True,  60, 20),
        (offer["cv_title"],     10, False, 0,  20),
        (CONTACT,              8.5, False, 0,  60),
    ]:
        r = tbl.add_row()
        c = r.cells[0]
        tcPr = c._tc.get_or_add_tcPr()
        shd = OxmlElement("w:shd")
        shd.set(qn("w:val"), "clear"); shd.set(qn("w:color"), "auto")
        shd.set(qn("w:fill"), HDR_TEAL)
        tcPr.append(shd)
        c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.LEFT
        run = c.paragraphs[0].add_run(row_text)
        run.bold = bold
        run.font.size = Pt(pt_size)
        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        set_para_spacing(c.paragraphs[0], before=before, after=after)

    doc.add_paragraph()

    # Perfil
    add_section_title(doc, "PERFIL PROFESIONAL")
    p = doc.add_paragraph()
    set_para_spacing(p, before=30, after=30)
    run = p.add_run(offer["cv_summary"])
    run.font.size = Pt(8.5)

    # Experiencia
    add_section_title(doc, "EXPERIENCIA Y PROYECTOS")
    p_emp = doc.add_paragraph()
    set_para_spacing(p_emp, before=30, after=0)
    run_emp = p_emp.add_run("FREELANCE  |  Desarrolladora Java/Angular")
    run_emp.bold = True
    run_emp.font.size = Pt(9)
    run_date = p_emp.add_run("                                                       Marzo 2026 - Actualidad")
    run_date.font.size = Pt(8.5)

    p_proj = doc.add_paragraph()
    set_para_spacing(p_proj, before=0, after=10)
    run_proj = p_proj.add_run("CRM de gestion comercial · Desarrollo, despliegue y evolucion continua")
    run_proj.italic = True
    run_proj.font.size = Pt(8.5)
    run_proj.font.color.rgb = hex_to_rgb(HDR_TEAL)

    ordered = offer.get("cv_bullets", [0,1,2,3,4,5])
    for idx in ordered:
        if idx < len(BULLETS):
            add_bullet(doc, BULLETS[idx])

    # Competencias
    add_section_title(doc, "COMPETENCIAS TECNICAS")
    skill_order = offer.get("cv_skills_order", "backend_first")
    skill_list  = SKILLS.get(skill_order, SKILLS["backend_first"])
    for label, content in skill_list:
        p_skill = doc.add_paragraph()
        set_para_spacing(p_skill, before=20, after=10)
        run_label = p_skill.add_run(label + ": ")
        run_label.bold = True
        run_label.font.size = Pt(8.5)
        run_content = p_skill.add_run(content)
        run_content.font.size = Pt(8.5)

    # Formacion
    add_section_title(doc, "FORMACION")
    p_edu = doc.add_paragraph()
    set_para_spacing(p_edu, before=30, after=10)
    run_edu1 = p_edu.add_run("Tecnica Superior en Desarrollo de Aplicaciones Web (DAW)")
    run_edu1.bold = True
    run_edu1.font.size = Pt(8.5)
    run_edu2 = p_edu.add_run("  |  MEDAC Sevilla  |  2024-2026")
    run_edu2.font.size = Pt(8.5)

    # Idiomas
    add_section_title(doc, "IDIOMAS")
    p_lang = doc.add_paragraph()
    set_para_spacing(p_lang, before=30, after=10)
    run_lang1 = p_lang.add_run("Ingles C1")
    run_lang1.bold = True
    run_lang1.font.size = Pt(8.5)
    run_lang2 = p_lang.add_run(" - acreditado por la Universidad de Cambridge")
    run_lang2.font.size = Pt(8.5)

    out_path = os.path.join(CV_DIR, offer["cv_file"])
    doc.save(out_path)
    print(f"  [CV] Guardado: {offer['cv_file']}")


# ══════════════════════════════════════════════════════════════════════════════
# BÚSQUEDA CON CLAUDE API
# ══════════════════════════════════════════════════════════════════════════════

def build_search_prompt(known_urls, last_id_num, today, portal_filter=None):
    """Construye el prompt detallado para Claude.

    portal_filter: None para todos los portales habituales, "linkedin" para
    restringir la búsqueda exclusivamente a LinkedIn España, o "europa" para
    buscar empresas internacionales (fuera de España) con puestos 100% remoto
    en páginas de empresa directas y bolsas de empleo internacionales.
    """
    cutoff_date = (today - datetime.timedelta(days=7)).strftime("%Y-%m-%d")
    known_list = "\n".join(f"  - {u}" for u in sorted(known_urls)) if known_urls else "  (ninguna aún)"
    next_id = last_id_num + 1

    if portal_filter == "linkedin":
        portales_txt = """- LinkedIn España (es.linkedin.com/jobs) — ÚNICO portal a buscar en esta ejecución.
  Busca de forma exhaustiva: recorre varias páginas de resultados y varias
  combinaciones de términos, no te quedes solo con los primeros resultados."""
        max_ofertas = 40
        terminos_txt = """- "Java junior", "Spring Boot junior", "desarrollador Java junior"
- "Angular junior", "Full Stack Java Angular junior"
- "programador Java", "backend Java junior España\""""
        exclusion_6 = (
            "6. Modalidad 100% Presencial en una ciudad distinta de Sevilla (la candidata NO "
            "puede trabajar presencialmente fuera de Sevilla). Solo son válidas: cualquier "
            "oferta remota (100% remoto, sea cual sea la ciudad), cualquier oferta híbrida en "
            "España, o presencial exclusivamente si es en Sevilla."
        )
        exclusion_extra = ""
        rubrica_ubicacion = (
            "- 10 pts: Ubicación/Modalidad (remoto 100%=10, Sevilla presencial=10, híbrido "
            "España=7). Presencial fuera de Sevilla: EXCLUIR (ver regla 6), no puntuar."
        )
        portal_campo = "LinkedIn/Indeed/Infojobs/Tecnoempleo/etc"
        nota_extra = ""
    elif portal_filter == "europa":
        portales_txt = """- Páginas de carreras DIRECTAS de empresas tecnológicas internacionales (no
  agregadores): busca en sus propios dominios de empleo, por ejemplo páginas
  alojadas en Lever (jobs.lever.co), Greenhouse (boards.greenhouse.io),
  Workable (jobs.workable.com / apply.workable.com), Recruitee
  (*.recruitee.com) o SmartRecruiters (careers.smartrecruiters.com) de
  empresas con sede fuera de España (Europa, Reino Unido, Latinoamérica,
  etc.).
- Bolsas de empleo remoto internacionales: Himalayas (himalayas.app),
  Jobgether (jobgether.com), WeWorkRemotely (weworkremotely.com), Working
  Nomads (workingnomads.com), Get on Board (getonbrd.com, foco Latinoamérica
  e hispanohablante), Remotive (remotive.com)."""
        max_ofertas = 20
        terminos_txt = """- "junior java developer remote" / "junior full stack java angular remote"
- "desarrollador junior Java Angular remoto" (foco empresas Latinoamérica)
- "junior software engineer java" + "remote from Europe" / "remote worldwide\""""
        exclusion_6 = (
            "6. CUALQUIER modalidad que no sea 100% remota (la candidata NO se va a reubicar "
            "a otro país, así que un puesto híbrido o presencial fuera de España queda "
            "excluido salvo que el propio puesto sea remoto desde cualquier lugar)."
        )
        exclusion_extra = (
            "\n7. La empresa tiene sede en España (esta búsqueda es específicamente para "
            "empresas con sede FUERA de España; las españolas ya se cubren en la búsqueda "
            "general).\n"
            "8. El puesto exige un idioma obligatorio distinto de español o inglés (por "
            "ejemplo, alemán, francés, neerlandés o polaco nativo). El inglés fluido/C1 SÍ es "
            "válido como requisito.\n"
            "9. La oferta restringe explícitamente la residencia a un país o región "
            "incompatible con España (por ejemplo, \"solo India\", \"solo LatAm con residencia "
            "en Chile\", \"solo ciudadanos de EE.UU.\"). Verifica esto con cuidado: muchas "
            "ofertas de consultoras de outsourcing (BairesDev, Miratech, Software Mind, etc.) "
            "anuncian \"remoto mundial\" pero en la descripción real solo aceptan candidatos de "
            "una región concreta que no incluye España — descártalas si detectas esa "
            "restricción."
        )
        rubrica_ubicacion = (
            "- 10 pts: Ubicación/Modalidad (100% remoto sin restricción de país=10, 100% "
            "remoto con restricción ambigua pero probablemente compatible con España=6). "
            "Cualquier cosa no remota o con restricción de país que excluya España: EXCLUIR "
            "(ver reglas 6 y 9), no puntuar."
        )
        portal_campo = "Nombre de la empresa / bolsa donde se publicó (Lever, Greenhouse, Workable, Himalayas, Jobgether, Get on Board, etc.)"
        nota_extra = (
            "\n- Antes de incluir una oferta, confirma explícitamente en el texto real del "
            "anuncio (no en el título de búsqueda) que un candidato residente en España puede "
            "aplicar en remoto sin reubicarse. Si la elegibilidad geográfica no está clara, "
            "indícalo en el campo \"notes\" en vez de asumir que es válida."
        )
    else:
        portales_txt = """- LinkedIn España (es.linkedin.com/jobs)
- Indeed España (indeed.es)
- Infojobs (infojobs.net)
- Tecnoempleo (tecnoempleo.com)
- Computrabajo España (computrabajo.es)
- Jobandtalent (jobandtalent.com)"""
        max_ofertas = 30
        terminos_txt = """- "Java junior", "Spring Boot junior", "desarrollador Java junior"
- "Angular junior", "Full Stack Java Angular junior"
- "programador Java", "backend Java junior España\""""
        exclusion_6 = (
            "6. Modalidad 100% Presencial en una ciudad distinta de Sevilla (la candidata NO "
            "puede trabajar presencialmente fuera de Sevilla). Solo son válidas: cualquier "
            "oferta remota (100% remoto, sea cual sea la ciudad), cualquier oferta híbrida en "
            "España, o presencial exclusivamente si es en Sevilla."
        )
        exclusion_extra = ""
        rubrica_ubicacion = (
            "- 10 pts: Ubicación/Modalidad (remoto 100%=10, Sevilla presencial=10, híbrido "
            "España=7). Presencial fuera de Sevilla: EXCLUIR (ver regla 6), no puntuar."
        )
        portal_campo = "LinkedIn/Indeed/Infojobs/Tecnoempleo/etc"
        nota_extra = ""

    return f"""Actúa como reclutador técnico senior. Hoy es {today.strftime("%d/%m/%Y")}.

TAREA: Busca ofertas de trabajo publicadas desde {cutoff_date} hasta hoy para la candidata junior siguiente.

{CANDIDATE_PROFILE}

PORTALES A BUSCAR:
{portales_txt}

TÉRMINOS DE BÚSQUEDA (usa variaciones):
{terminos_txt}

REGLAS DE EXCLUSIÓN (descarta si aplica cualquiera):
1. El título incluye: Senior, Lead, Manager, Architect, Principal, Tech Lead
2. Requiere más de 5 años de experiencia (perfil claramente senior). Si pide
   entre 2 y 5 años pero el resto del perfil encaja bien (mismas tecnologías,
   misma función backend/fullstack/frontend), NO la descartes solo por eso:
   inclúyela y penalízala únicamente en el apartado "Nivel" de la rúbrica.
3. Es práctica no remunerada o beca sin salario
4. La oferta no es accesible (link roto, requiere login para ver descripción)
5. Duplicado de URL ya conocida
{exclusion_6}{exclusion_extra}

URLS YA CONOCIDAS (no incluir):
{known_list}

RUBRICA DE PUNTUACIÓN (100 puntos total):
- 40 pts: Tecnología obligatoria (Java/Spring Boot = 20pts, APIs REST/JPA = 10pts, Angular/TypeScript = 10pts)
- 20 pts: Función (backend puro=20, fullstack=18, frontend puro=15, otros=10)
- 15 pts: Nivel (junior/entry explícito=15, no especificado=13, "hasta 2 años"=10,
  "2 años req."=8, "3 años req."=6, "4-5 años req."=4 — nunca 0 si el resto del
  perfil técnico encaja bien, para no descartar perfiles muy afines solo por la
  experiencia pedida)
- 10 pts: Formación/Idiomas (CFGS DAW válido=6, inglés C1 cuando lo pidan=4)
{rubrica_ubicacion}
- 5 pts: Skills deseables (Docker, JUnit, Scrum, Swagger, etc.)

PRIORIDAD:
- Alta: compatibilidad >= 75%
- Secundaria: compatibilidad 60-74%
- Descartar: compatibilidad < 60%

PARA CADA OFERTA VÁLIDA (compatibilidad >= 60%) devuelve JSON con estos campos exactos:
{{
  "id": "OF{next_id:03d}",  // incrementar por cada oferta
  "priority": "Alta" o "Secundaria",
  "compatibility": 78,  // número entero 0-100
  "title": "Título exacto de la oferta",
  "company": "Nombre empresa",
  "portal": "{portal_campo}",
  "url": "URL directa a la oferta",
  "date": "YYYY-MM-DD",  // fecha de publicación
  "location": "Ciudad o España",
  "modality": "Remoto 100% / Híbrido / Presencial",
  "contract": "Indefinido / Temporal / No especificado",
  "salary": "X.000 – Y.000 €/año o No especificado",
  "experience": "1-2 años / No especificado / etc",
  "mandatory_tech": "lista de tecn. obligatorias de la oferta",
  "desirable_tech": "lista de tecn. deseables",
  "meets": "Java ✓  Spring Boot ✓  ...",
  "missing": "Lo que no cumple o Ninguno",
  "score_reason": "Explicación de la puntuación por categoría",
  "status": "Pendiente de revisión",
  "notes": "Observaciones útiles para la candidata",
  "cv_file": "OF{next_id:03d}_Empresa_Puesto.docx",  // solo si compatibility >= 65
  "cv_title": "TITULO CV ADAPTADO EN MAYUSCULAS",  // solo si compatibility >= 65
  "cv_summary": "Resumen profesional adaptado a esta oferta (3-4 frases, keywords exactas de la oferta)",
  "cv_skills_order": "backend_first / fullstack / frontend_first",
  "cv_bullets": [0,1,2,3,4,5]  // reordenar según relevancia para esta oferta
}}

IMPORTANTE:
- cv_file, cv_title, cv_summary, cv_skills_order, cv_bullets: solo incluir si compatibility >= 65
- cv_bullets: lista de índices 0-5 reordenados (0=producción CRM, 1=JWT/Security, 2=JPA/SQL, 3=Angular frontend, 4=Excel/CSV, 5=Docker/CI/CD)
- Verifica que cada URL existe y la oferta es accesible antes de incluirla
- Verifica la fecha de publicación (debe ser {cutoff_date} o posterior)
- No inventes información: solo incluye lo que está en la oferta real
- Máximo {max_ofertas} ofertas válidas{nota_extra}

Devuelve SOLO el array JSON, sin texto adicional antes ni después:
[
  {{ ... }},
  {{ ... }}
]"""


def call_claude_with_search(prompt):
    """Llama a Claude Code CLI por stdin en modo no interactivo (usa la suscripcion existente)."""
    print("[CLI] Iniciando busqueda con Claude Code (puede tardar 3-6 minutos)...")

    NODE_EXE    = os.environ.get("NODE_EXE", r"C:\Program Files\nodejs\node.exe")
    CLAUDE_CJS  = os.environ.get("CLAUDE_CJS", os.path.join(os.environ.get("APPDATA", ""), "npm", "node_modules", "@anthropic-ai", "claude-code", "cli-wrapper.cjs"))

    # El prompt se pasa por stdin para evitar límites de longitud de argumento
    result = subprocess.run(
        [NODE_EXE, CLAUDE_CJS, "--print", "--output-format", "json",
         "--allowedTools", "WebSearch,WebFetch"],
        input=prompt,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=1200,  # 20 minutos (la búsqueda web puede tardar)
    )

    if result.returncode != 0:
        stderr = result.stderr[:800] if result.stderr else "(sin detalle)"
        raise RuntimeError(f"Claude CLI termino con error (codigo {result.returncode}):\n{stderr}")

    if not result.stdout.strip():
        raise RuntimeError("Claude CLI no devolvio ninguna respuesta.")

    # --output-format json devuelve un objeto envolvente; extraemos el campo "result"
    try:
        wrapper = json.loads(result.stdout)
        if isinstance(wrapper, dict) and "result" in wrapper:
            return wrapper["result"]
        # Si ya es texto plano (versiones antiguas del CLI)
        return result.stdout
    except json.JSONDecodeError:
        # La salida ya es texto plano directamente
        return result.stdout


def parse_offers_json(raw_text):
    """Extrae y parsea el array JSON de la respuesta de Claude."""
    # 1. Buscar bloque de código markdown ```json [...] ```
    match = re.search(r'```(?:json)?\s*(\[.*?\])\s*```', raw_text, re.DOTALL)
    if match:
        json_str = match.group(1)
    else:
        # 2. Buscar array JSON con objetos o vacío en el texto
        match = re.search(r'\[\s*(?:\{.*?\}\s*,?\s*)*\]', raw_text, re.DOTALL)
        if match:
            json_str = match.group(0)
        else:
            json_str = raw_text.strip()

    try:
        offers = json.loads(json_str)
        if not isinstance(offers, list):
            raise ValueError("El JSON no es un array.")
        return offers
    except json.JSONDecodeError as e:
        print(f"[ERROR] No se pudo parsear el JSON: {e}")
        print(f"Texto recibido (primeros 500 chars):\n{raw_text[:500]}")
        return []


# ══════════════════════════════════════════════════════════════════════════════
# LOG
# ══════════════════════════════════════════════════════════════════════════════

def write_log(today, new_offers, skipped_count, label=None):
    """Añade un bloque de resultados al log del día (no lo sobrescribe si ya
    hubo otra ejecución hoy, p.ej. la automática y luego una manual de LinkedIn)."""
    log_path = os.path.join(LOG_DIR, f"busqueda_{today.strftime('%Y%m%d')}.txt")
    is_new_file = not os.path.exists(log_path)
    now_str = datetime.datetime.now().strftime("%H:%M:%S")
    with open(log_path, "a", encoding="utf-8") as f:
        if is_new_file:
            f.write(f"Busqueda diaria — {today.strftime('%d/%m/%Y')}\n")
            f.write("=" * 60 + "\n\n")
        else:
            f.write("\n" + "-" * 60 + "\n\n")
        f.write(f"Ejecucion {now_str}" + (f" ({label})" if label else "") + "\n")
        f.write(f"Ofertas nuevas encontradas: {len(new_offers)}\n")
        f.write(f"Ofertas descartadas (duplicadas o excluidas): {skipped_count}\n\n")
        for o in new_offers:
            f.write(f"[{o['id']}] {o['compatibility']}% — {o['title']} @ {o['company']}\n")
            f.write(f"        {o['url']}\n\n")
    print(f"[LOG] Guardado: {log_path}")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    if "--portal" in sys.argv and "linkedin" in sys.argv:
        portal_filter = "linkedin"
    elif "--portal" in sys.argv and "europa" in sys.argv:
        portal_filter = "europa"
    else:
        portal_filter = None
    label = {"linkedin": "LinkedIn", "europa": "Europa/Internacional"}.get(portal_filter)

    today = datetime.date.today()
    print(f"\nBusqueda diaria — {today.strftime('%d/%m/%Y')}" + (f" ({label})" if label else ""))
    print("=" * 60)

    # 1. Leer Excel existente
    known_urls, last_id_num = get_existing_urls_and_last_id()
    print(f"[Excel] URLs ya conocidas: {len(known_urls)} | Ultimo ID: OF{last_id_num:03d}")

    # 2. Llamar a Claude para buscar nuevas ofertas
    prompt = build_search_prompt(known_urls, last_id_num, today, portal_filter=portal_filter)
    raw_response = call_claude_with_search(prompt)

    # 3. Parsear JSON
    all_offers = parse_offers_json(raw_response)
    print(f"[API] Claude devolvio {len(all_offers)} ofertas candidatas.")

    # 4. Filtrar duplicados (por URL)
    new_offers = []
    skipped = 0
    used_ids = set()
    next_num = last_id_num + 1

    for o in all_offers:
        url = o.get("url","").strip()
        if url in known_urls:
            skipped += 1
            continue
        if not url:
            skipped += 1
            continue
        known_urls.add(url)
        # Reasignar ID secuencial para garantizar unicidad
        o["id"] = f"OF{next_num:03d}"
        if o.get("cv_file"):
            # Actualizar nombre de archivo con el nuevo ID
            parts = o["cv_file"].split("_", 1)
            if len(parts) == 2:
                o["cv_file"] = f"OF{next_num:03d}_{parts[1]}"
        next_num += 1
        new_offers.append(o)

    print(f"[Filtro] Ofertas nuevas: {len(new_offers)} | Duplicadas/invalidas: {skipped}")

    if not new_offers:
        print("[INFO] No hay nuevas ofertas para añadir hoy.")
        write_log(today, [], skipped, label=label)
        return

    # 5. Añadir al Excel
    append_offers_to_excel(new_offers)

    # 6. Generar CVs adaptados para ofertas >= 65%
    cv_count = 0
    for o in new_offers:
        if o.get("cv_file") and o.get("compatibility", 0) >= 65:
            try:
                create_cv(o)
                cv_count += 1
            except Exception as e:
                print(f"  [WARN] Error generando CV para {o['id']}: {e}")

    # 7. Log y resumen
    write_log(today, new_offers, skipped, label=label)

    print("\n" + "=" * 60)
    print(f"RESUMEN {today.strftime('%d/%m/%Y')}")
    print(f"  Nuevas ofertas añadidas al Excel : {len(new_offers)}")
    print(f"  CVs adaptados generados          : {cv_count}")
    print(f"  Excel                            : {EXCEL}")
    print(f"  CVs en                           : {CV_DIR}")
    print("=" * 60)

    # Tabla top ofertas
    top = sorted(new_offers, key=lambda x: x.get("compatibility",0), reverse=True)[:10]
    print("\nTop ofertas de hoy:")
    print(f"{'ID':<7} {'%':<5} {'Empresa':<22} {'Puesto':<35} {'Modalidad'}")
    print("-" * 95)
    for o in top:
        print(f"{o['id']:<7} {o['compatibility']:<5} {o['company'][:20]:<22} {o['title'][:33]:<35} {o.get('modality','')[:20]}")


if __name__ == "__main__":
    main()
