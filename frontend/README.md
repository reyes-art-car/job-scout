# Frontend · JobHunter

Angular 20 con componentes standalone, signals y carga diferida por ruta. Ver [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md).

```bash
npm ci
npm start                                                    # http://localhost:4200 · /api → localhost:8000
npm run build                                                # dist/job-hunter/browser
npx ng test --watch=false --browsers=ChromeHeadless          # 25 pruebas (necesita Chrome)
```

Sin backend, la aplicación arranca en **modo demo** con `data/demo/*.json` (se copian al compilar) y guarda los cambios en `localStorage`. Con el backend en marcha y alguna oferta cargada, usa la API automáticamente.

Para publicar la demo en GitHub Pages, usa el flujo `.github/workflows/pages.yml` (activa Pages con «GitHub Actions» como origen).

## Código

| Ruta | Contenido |
|---|---|
| `src/app/core/` | Modelos, `OfferStore`, catálogo de tecnologías, adaptación de CV, carta y exportación (con tests) |
| `src/app/features/` | Panel, ofertas, adaptar CV, carta de presentación y brecha de skills |
| `src/app/shared/` | Componentes compartidos (iconos SVG) |
