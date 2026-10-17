# Automatización

`busqueda_diaria.py` pide a Claude Code que busque ofertas junior Java/Spring/Angular, las puntúa con la rúbrica de 100 puntos, las añade a `Ofertas_Maria_Reyes.xlsx` sin duplicar URLs y genera un CV adaptado por cada oferta con ≥ 65 % de compatibilidad.

## Uso

```bash
pip install -r automation/requirements.txt
python automation/busqueda_diaria.py                    # portales de España
python automation/busqueda_diaria.py --portal linkedin  # solo LinkedIn, exhaustivo
python automation/busqueda_diaria.py --portal europa    # empresas internacionales 100 % remoto
```

Requiere Claude Code instalado (`npm i -g @anthropic-ai/claude-code`) y sesión iniciada. Si `node` o el *wrapper* no están en las rutas habituales, define `NODE_EXE` y `CLAUDE_CJS`.

## Perfil

Lee `backend/config/candidate_profile.yaml` (datos reales, fuera de git) o, si no existe, `candidate_profile.example.yaml`.

## Programarlo en Windows

`ejecutar_busqueda.bat` lanza las tres búsquedas y `tarea_busqueda_ofertas.xml` es la tarea del Programador de tareas (lunes a viernes, 08:00). Ajusta las fechas y la ruta del `.bat` antes de importarla:

```powershell
schtasks /Create /XML automation\tarea_busqueda_ofertas.xml /TN "BusquedaOfertas"
```

Los datos personales (Excel, CVs, logs) se guardan en la raíz del proyecto y están ignorados por git.
