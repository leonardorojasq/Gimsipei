# Gimsipei

Construcción de un sistema de gestion de pruebas enfocado a la educación.

## Herramientas utilizadas

- Python 3.11+ (este proyecto está pinneado a 3.13 vía `.python-version`)
- Flask
- [uv](https://docs.astral.sh/uv/) (gestor de paquetes y entornos)
- [ruff](https://docs.astral.sh/ruff/) (linter + formateador)

## Pasos para inicializar el proyecto

### 1. Instalar uv

```bash
# Linux / macOS
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# o con pip / pipx
pip install uv
```

### 2. Clonar el repositorio

```bash
git clone git@github.com:lrojasq/Gimsipei.git
cd Gimsipei
```

### 3. Crear el entorno virtual

`uv` lee `.python-version` para saber qué versión de Python usar y crea el venv en `.venv/`:

```bash
uv venv
```

### 4. Activar el entorno virtual

```bash
# Linux / macOS
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

### 5. Sincronizar dependencias

Con el venv activado, `uv sync` instala en él todo lo declarado en `pyproject.toml` + `uv.lock`:

```bash
uv sync
```

### 6. Configurar variables de entorno

Copiá `.env` (si no existe) y completá los valores de tu base de datos.

### 7. Ejecutar el proyecto

```bash
# Con el venv activado
python main.py
```

> Si preferís no activar el venv manualmente, podés usar `uv run python main.py` que hace ambos pasos por vos.

### 8. Abrir en el navegador

```
http://localhost:5010/
```

## Versión de Python

El archivo `.python-version` (en la raíz) le dice a `uv` qué versión de Python usar. Si tu sistema no la tiene, uv la descarga automáticamente:

```bash
uv python install   # instala la versión indicada en .python-version
```

`pyproject.toml` declara `requires-python = ">=3.11"`. Si querés cambiar la versión pinneada:

```bash
uv python pin 3.12
```

## Linting y formateo

```bash
# Verificar estilo y errores de lint
uv run ruff check .

# Aplicar fixes automáticos (imports, unused, etc.)
uv run ruff check . --fix

# Formatear el código
uv run ruff format .

# Ver qué cambiaría sin aplicar
uv run ruff format . --check
uv run ruff check . --diff
```

## Pre-commit (opcional)

Para que `ruff` corra automáticamente antes de cada commit:

```bash
uv run pre-commit install
```

A partir de ese momento, `git commit` ejecutará `ruff check --fix` y `ruff format` sobre los archivos modificados. Si algo falla, el commit se rechaza.
