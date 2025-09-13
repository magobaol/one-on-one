# One-on-One Meeting Setup Automation

A Python script to automate the workflow for managing one-on-one meetings with colleagues. This is the foundation project with integrations to be added incrementally.

## Current Features

- **Configuration management**: YAML-based configuration system
- **Command-line interface**: Structured CLI for colleague setup
- **Logging system**: Configurable logging levels
- **Project structure**: Clean modular foundation for integrations

## Setup

1. **Install dependencies:**
   ```bash
   pip3 install -r requirements.txt
   ```

2. **Create configuration file:**
   ```bash
   cp config.yaml.example config.yaml
   ```
   
3. **Configure your settings in `config.yaml`:**
   - Adjust logging levels if needed
   - Configure download paths

## Usage

```bash
python3 one_on_one_setup.py "Colleague Name" "slack-handle"
```

Currently this runs the foundation setup. Integrations (Slack, OmniFocus, etc.) will be added in subsequent updates.

## Configuration

Edit `config.yaml` (created from the template) to customize:

- Logging levels (`logging.level`)
- Download temp folder (`paths.download_temp`)

### Security Note

`config.yaml` is gitignored and contains your personal settings. Never commit this file to version control.

## Requirements

- Python 3.7+