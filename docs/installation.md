# Installation

## Prerequisites

- Python 3.10+
- pipx (recommended) or pip

## Install pipx

### Linux (Debian/Ubuntu)

```bash
sudo apt update
sudo apt install pipx
pipx ensurepath
```

### Linux (Fedora)

```bash
sudo dnf install pipx
pipx ensurepath
```

### macOS

```bash
brew install pipx
pipx ensurepath
```

### Windows

```powershell
# Option 1: With scoop
scoop install pipx
pipx ensurepath

# Option 2: With pip
pip install --user pipx
python -m pipx ensurepath
```

**Important:** Restart your terminal after running `ensurepath`.

## Install otomata-tools

```bash
pipx install git+https://github.com/AlexisLaporte/otomata-tools.git
```

Verify installation:

```bash
otomata --help
```

## Update

```bash
pipx upgrade otomata
```

## Uninstall

```bash
pipx uninstall otomata
```

## Configuration

Create a `.env.local` file in your project directory:

```bash
GOOGLE_SERVICE_ACCOUNT='{"type":"service_account",...}'
NOTION_API_KEY='ntn_xxx...'
```

See [Google Service Account Setup](google-service-account-setup.md) for detailed instructions.

Verify configuration:

```bash
cd /path/to/your/project
otomata config
```

## Alternative: pip install (in virtualenv)

If you prefer using pip in a virtual environment:

```bash
# Create and activate venv
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or: venv\Scripts\activate  # Windows

# Install
pip install git+https://github.com/AlexisLaporte/otomata-tools.git
```

## Troubleshooting

### Command not found after install

Run `pipx ensurepath` and restart your terminal.

### Permission denied (Linux/macOS)

Don't use `sudo` with pipx. If needed:

```bash
pipx install --force git+https://github.com/AlexisLaporte/otomata-tools.git
```

### Python version error

Ensure Python 3.10+ is installed:

```bash
python3 --version
```

### Windows: 'pipx' is not recognized

Add Python Scripts to PATH or use the full path:

```powershell
python -m pipx install git+https://github.com/AlexisLaporte/otomata-tools.git
```
