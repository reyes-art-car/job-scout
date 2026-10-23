# Frontend · Job Hopping & Learning

Angular 20 con componentes standalone, signals y carga diferida por ruta. Ver [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md).

```bash
npm ci
npm start                                                    # http://localhost:4200 · /api → localhost:8000
npm run build                                                # dist/job-hunter/browser
npx ng test --watch=false --browsers=ChromeHeadless          # 95 pruebas (necesita Chrome)
npx ng lint                                                  # ESLint con reglas de código limpio y seguridad
```

Si la API exige sesión, la aplicación lleva a `/acceso` (inicio de sesión o alta con email y contraseña). El token de sesión se guarda en `sessionStorage` y solo se envía a `/api/`. En `/buscar` cada usuario rellena su perfil y lanza búsquedas de ofertas.

Sin backend, la aplicación arranca en **modo demo** con `data/demo/*.json` (se copian al compilar) y guarda los cambios en `localStorage`. Con el backend en marcha y alguna oferta cargada, usa la API automáticamente.

Para publicar la demo en GitHub Pages, usa el flujo `.github/workflows/pages.yml` (activa Pages con «GitHub Actions» como origen).

## Código

| Ruta | Contenido |
|---|---|
| `src/app/core/` | Modelos, `OfferStore` y gateways (API/demo), validación de datos, token, catálogo de tecnologías, análisis, adaptación de CV, carta y exportación (con tests) |
| `src/app/features/` | Panel, ofertas, adaptar CV, carta de presentación y brecha de skills |
| `src/app/shared/` | Componentes compartidos (iconos SVG) |
