# Gimsipei

Construcción de un sistema de gestion de pruebas enfocado a la educación.

## Herramientas utilizadas

- Python 3.11+
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

### 3. Sincronizar dependencias

`uv` crea `.venv/` automáticamente e instala todo lo declarado en `pyproject.toml` + `uv.lock`:

```bash
uv sync
```

### 4. Activar el entorno virtual

```bash
# Linux / macOS
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

O ejecutá los comandos directamente con `uv run ...` sin necesidad de activar.

### 5. Configurar variables de entorno

Copiá `.env` (si no existe) y completá los valores de tu base de datos.

### 6. Ejecutar el proyecto

```bash
# Con el venv activado
python main.py

# O sin activar
uv run python main.py
```

### 7. Abrir en el navegador

```
http://localhost:5010/
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

## Versión de Python

`pyproject.toml` declara `requires-python = ">=3.11"`. Si tu sistema tiene una versión distinta, uv puede administrar la versión correcta automáticamente:

```bash
uv python install 3.11
```
