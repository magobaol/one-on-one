# One-on-One Meeting Setup Automation

A Python script to automate the workflow for managing one-on-one meetings with colleagues, featuring secure token management and Slack integration.

## Features

- **Secure token management**: Retrieves Slack API tokens from 1Password CLI
- **Slack integration**: Downloads colleague profile photos with pagination support
- **Photo management**: Organizes profile photos with proper naming and storage
- **Configuration management**: YAML-based configuration system
- **Command-line interface**: Structured CLI for colleague setup
- **Logging system**: Configurable logging levels

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
   - **Slack API**: Set `slack.onepassword.cli.item_name` to your Slack API token item
   - **Photo settings**: Configure photo size and storage location
   - **Logging**: Adjust logging levels if needed
   - **Paths**: Configure download paths

4. **Install and authenticate 1Password CLI:**
   ```bash
   # Install 1Password CLI (if not already installed)
   # Then sign in and authenticate
   op account list
   ```

## Usage

```bash
python3 one_on_one_setup.py "Colleague Name" "slack-handle"
```

This will:
1. Securely retrieve your Slack API token from 1Password
2. Look up the colleague in your Slack workspace 
3. Download their profile photo to local storage

## Configuration

### Required Settings

Edit `config.yaml` (created from the template) to set:

- **Slack API**: `slack.onepassword.cli.item_name` - Name of your 1Password item containing Slack token

### Optional Settings

- **Photo settings**: `slack.photo_size` and `slack.photo_storage`
- **Logging levels**: `logging.level`
- **Download temp folder**: `paths.download_temp`

### Security Note

`config.yaml` is gitignored and contains your personal settings. Never commit this file to version control.

## Requirements

- Python 3.7+
- 1Password CLI
- Active Slack workspace access