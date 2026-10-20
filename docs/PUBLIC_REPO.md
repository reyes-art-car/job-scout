# Publicar este repositorio sin problemas

Un repositorio público lo ve cualquiera, incluidos recruiters, empresas a las que has aplicado y bots que rastrean
secretos. Y **git guarda todo el historial**: borrar un dato en un commit nuevo no lo quita de los anteriores.

## Qué se ha comprobado

| Revisión | Resultado |
|---|---|
| Claves, tokens y claves privadas en todo el historial (patrones de Anthropic, AWS, GitHub, Slack, Google, PEM) | Ninguno |
| Ficheros sensibles alguna vez versionados (`.env`, `.db`, `.xlsx`, CV `.docx`/`.pdf`, `private/`, `candidate_profile.yaml`) | Ninguno |
| Teléfono real | No aparece: solo el ficticio `600 000 000` |
| Dependencias con vulnerabilidades conocidas (`pip-audit`, `npm audit`) | Ninguna |
| Workflows de CI | Sin `pull_request_target` y sin más secreto que `GITHUB_TOKEN`: un fork no puede sacar nada |
| Imagen Docker | `.dockerignore` excluye `private/`, `.env`, bases de datos y datos personales |

## Problemas encontrados

### 1. Tu búsqueda de empleo real estaba en los datos de la demo (corregido en el código, **no en el historial**)

`data/demo/offers.json` contenía 19 ofertas **reales** con el estado de cada candidatura (por ejemplo, empresas con
estado «Entrevista», «Oferta» o «Rechazo») y notas sobre tu perfil. Lo mismo ocurría en `docs/BUSQUEDA_2026-10-17.md` y
`docs/SKILLS_GAP.md`. Cualquier empresa podría ver en qué procesos estás y cómo te han tratado.

Ya está corregido en la rama de trabajo:

- `offers.json` se ha sustituido por datos ficticios con la misma forma (empresas inventadas, enlaces a `example.com`).
- Los dos informes dejan de versionarse y están en `.gitignore` (siguen en tu disco).

**Pero el historial sigue conteniendo los datos antiguos**, en 38 ramas remotas (incluidas las de Dependabot).

### 2. Tu email personal está en el historial

El árbol actual usa el alias `mariareyesartcar+github@gmail.com`, pero 70 commits tienen como autor tu email real y 5
ficheros lo contenían en versiones antiguas. Es menos grave que lo anterior (un email, no tu proceso de selección), pero
es justo lo que el alias intentaba evitar.

### 3. Información tuya que sí es pública a propósito

`data/demo/profile.json`, `backend/config/candidate_profile.example.yaml` y el README incluyen tu nombre, ciudad, el
alias de email, LinkedIn y tu situación laboral actual (freelance, desde marzo de 2026). El README lo declara. Revísalo:
si prefieres no indicar fechas ni el tipo de actividad, es una línea en cada fichero.

## Qué hacer, según el caso

### Si el repositorio todavía es privado (lo ideal)

**No lo hagas público todavía.** Limpia el historial primero (abajo) o publica un repositorio nuevo con un único commit
con el estado actual: es lo más sencillo y no deja rastro.

### Si ya es público

Asume que los datos antiguos **ya han sido copiados** (clones, forks, cachés, archivos web): reescribir el historial
reduce la exposición, no la elimina. Pasa el repositorio a privado mientras limpias, limpia el historial, y pide a GitHub
que purgue sus cachés (formulario de soporte «Sensitive data removal», indicando los commits afectados).

## Limpiar el historial

> Esto reescribe todos los commits y exige `push --force`. Es irreversible para quien no tenga una copia: trabaja siempre
> sobre un clon espejo, conserva el repositorio original como copia de seguridad y avisa a quien tenga clones (tendrá que
> volver a clonar). **Los ficheros de la receta (con tu email real y nombres de empresas reales) no deben vivir dentro
> del repositorio**: guárdalos fuera, o reintroducirías justo lo que quieres borrar.

Receta con `git-filter-repo` (`pip install git-filter-repo`; se invoca como `python -m git_filter_repo`):

```bash
git clone --mirror <ruta-o-url-del-repo> limpio.git && cd limpio.git

# reemplazos.txt  (una regla por línea: texto==>reemplazo)
#   <EMAIL_REAL>==><EMAIL_ALIAS>
#   <EMPLEADOR_ANTIGUO>==>Freelance
# mailmap.txt     (autoría y committer)
#   Tu Nombre <EMAIL_ALIAS> <EMAIL_REAL>

python -m git_filter_repo --force \
  --replace-text reemplazos.txt --replace-message reemplazos.txt --mailmap mailmap.txt \
  --file-info-callback '
    if filename == b"data/demo/offers.json":      # cada versión antigua pasa a ser la versión ficticia
        return (filename, mode, value.insert_file_with_contents(open("offers_ficticio.json", "rb").read()))
    if filename.startswith(b"docs/BUSQUEDA_") or filename == b"docs/SKILLS_GAP.md":
        return (None, None, None)                 # informes personales: se eliminan de todo el historial
    return (filename, mode, blob_id)
  '

# Comprobación: las tres búsquedas deben dar 0
git grep -I -c -i "<EMPRESA_REAL>" $(git rev-list --all) | wc -l
git grep -I -c "<EMAIL_REAL>" $(git rev-list --all) | wc -l
git log --all --format='%ae %ce' | grep -c "<EMAIL_REAL>"

# Publicar solo ramas y etiquetas (nunca refs/pull ni refs/remotes)
git push --force origin 'refs/heads/*:refs/heads/*'
git push --force origin --tags
```

Notas de la reescritura:

- Cada commit cambia de hash: el hash de `.gitleaksignore` deja de valer. La regla de `.gitleaks.toml` (contenido, no hash)
  cubre las contraseñas ficticias de las pruebas.
- Las ramas de Dependabot se pueden borrar: se recrean solas con la historia nueva.
- Las confirmaciones de GitHub sobre un PR abierto o un fork existente no se reescriben: pide a GitHub que purgue sus cachés
  (formulario de soporte «Sensitive data removal») y revisa si hay forks.

## Ajustes de GitHub antes de publicar

- [ ] **Settings → Code security**: activar *Secret scanning*, *Push protection*, *Dependabot alerts* y *Private
      vulnerability reporting* (así no hace falta que un fallo de seguridad se cuente en un issue público).
- [ ] **Settings → Actions → General**: *Require approval for all outside collaborators* para que un PR de un fork no
      ejecute workflows sin tu permiso, y permisos del `GITHUB_TOKEN` en «Read repository contents».
- [ ] **Settings → Branches**: proteger `main` (PR obligatorio, CI en verde, sin force-push).
- [ ] **Settings → Pages → Source: GitHub Actions** solo cuando `offers.json` esté saneado: la demo publica esos datos.
- [ ] Verificación en dos pasos en tu cuenta de GitHub.
- [ ] Decidir la licencia: hoy es «todos los derechos reservados». Un repositorio público con esa licencia se puede
      ver y GitHub permite forks dentro de la plataforma, pero nadie puede reutilizar el código. Si quieres que otros lo
      usen, necesitas otra licencia (y no podrás cobrar por exclusividad del código).

## Reglas para no volver a caer

1. Los datos de la demo son **siempre ficticios**. Nunca copies ofertas, estados ni notas de tu búsqueda real.
2. Tus informes de búsqueda (`docs/BUSQUEDA_*.md`, `docs/SKILLS_GAP.md`), CV y Excel viven solo en local
   (`.gitignore` ya los excluye).
3. Antes de cada publicación: `gitleaks detect` (también corre en CI) y una búsqueda de nombres de empresas reales en
   `data/`.
4. El archivo `.env` real no se versiona nunca; solo `.env.example` con valores vacíos.
