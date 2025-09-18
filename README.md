# One-on-One Meeting Setup Automation

A Python script to automate the workflow for managing one-on-one meetings with colleagues, integrating 1Password, Slack, OmniFocus, Obsidian, Keyboard Maestro, and Stream Deck for complete automation.

## Features

- **Secure token management**: Retrieves Slack API tokens from 1Password CLI
- **Slack integration**: Downloads colleague profile photos with pagination support
- **OmniFocus integration**: 
  - Creates hierarchical tags using AppleScript automation
  - Generates complete perspectives with custom icons
  - Uses XML templates for reliable perspective creation
- **Obsidian integration**: Creates structured notes with profile photos in configurable vaults
- **Keyboard Maestro integration**: Generates complete macro files with parameter replacement and custom icons
- **Stream Deck integration**: Creates visual automation buttons linked to Keyboard Maestro macros with standardized template
- **Organized output structure**: Creates colleague-specific folders for all generated content
- **Photo management**: Automatic image processing and format conversion (JPEG/PNG)
- **Configuration management**: YAML-based configuration with graceful feature disabling
- **Command-line interface**: Simple CLI with dry-run support
- **Comprehensive logging**: Detailed progress tracking and error reporting

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
   - **OmniFocus**: Set `omnifocus.tag_id` to your parent tag ID (get from "Copy as Link")
   - **Obsidian** (optional): Set `obsidian.vault_path` to your vault location
   - **Output folder**: Configure `output.base_folder` for organized file storage
   - **Logging**: Adjust logging levels if needed

4. **Install and authenticate 1Password CLI:**
   ```bash
   # Install 1Password CLI (if not already installed)
   # Then sign in and authenticate
   op account list
   ```

## Usage

```bash
python3 one_on_one_setup.py "Colleague Name" "slack-handle"

# Or test without making changes
python3 one_on_one_setup.py "Colleague Name" "slack-handle" --dry-run
```

This will:
1. Securely retrieve your Slack API token from 1Password
2. Look up the colleague in your Slack workspace 
3. Download their profile photo to organized colleague folders
4. Create a hierarchical tag in OmniFocus under your specified parent tag
5. Generate a complete OmniFocus perspective with custom icon from profile photo
6. Create an Obsidian note with the colleague's photo in your configured vault
7. Generate a complete Keyboard Maestro macro with parameters replaced and custom icon
8. Create a Stream Deck action button that triggers the Keyboard Maestro macro

## Configuration

### Required Settings

Edit `config.yaml` (created from the template) to set:

- **Slack API**: `slack.onepassword.cli.item_name` - Name of your 1Password item containing Slack token
- **OmniFocus**: `omnifocus.tag_id` - Parent tag ID where colleague tags will be created
- **Keyboard Maestro**: Configure your template macro details:
  - `keyboard_maestro.template_uuid` - UUID of your template macro (get via "Copy UUID" in Keyboard Maestro)
  - `keyboard_maestro.template_name` - Name of your template macro (for identification)

### Optional Settings

- **Obsidian vault**: `obsidian.vault_path` - Path to your Obsidian vault for note creation
- **Output organization**: `output.base_folder` - Base folder for all generated colleague content  
- **Photo settings**: `slack.photo_size` - Slack profile photo size (72, 192, 512, 1024)
- **OmniFocus method**: `omnifocus.method` and `omnifocus.create_task`
- **Logging levels**: `logging.level` - DEBUG, INFO, WARNING, ERROR

### Security Note

`config.yaml` is gitignored and contains your personal settings. Never commit this file to version control.

### OmniFocus Perspective Import

The script generates complete perspective files that can be imported into OmniFocus:

1. **Automatic generation**: Perspectives are created with correct tag filters and custom icons
2. **Import process**: Double-click the generated `.ofocus-perspective` folder to import
3. **Ready to use**: Perspectives are pre-configured to show Available and Waiting tasks for the colleague
4. **Custom icons**: Profile photos are automatically converted and included as perspective icons

### Obsidian Integration

When configured, the script creates structured notes in your Obsidian vault:

- **Location**: `vault/80 Spaces/people/Colleague Name/`
- **Content**: Title and profile photo with 200px display width  
- **Format**: `![[Colleague Name.jpg|200]]` for proper Obsidian display
- **Conflict handling**: Automatic numbering for duplicate notes

### Keyboard Maestro Integration

The script generates complete macro files using an export/modify/import approach:

- **Fully configurable template**: Uses your specified template macro (configured via `template_uuid` and `template_name`)
- **Parameter replacement**: Automatically replaces `#obsidianNoteName` and `#ofPerspectiveName` placeholders
- **Custom icons**: Embeds colleague's profile photo as TIFF icon data
- **Import process**: Double-click the generated `.kmmacros` file to import
- **Ready to use**: Macro is added to the same group as your template with all parameters configured

### Stream Deck Integration

The script creates visual automation buttons that complete the workflow chain:

- **Standardized template**: Uses fixed template from `resources/streamDeckButton.streamDeckAction` (no configuration required)
- **UUID chaining**: Automatically links to the generated Keyboard Maestro macro via shared UUID
- **Custom icons**: Converts profile photos to Stream Deck format (288x288 PNG) for visual identification
- **Fixed positioning**: Actions are placed at position 0,0 for consistency
- **Import process**: Double-click the generated `.streamDeckAction` file to import
- **One-button automation**: Press the Stream Deck button to trigger the complete colleague workflow
- **Visual workflow**: Creates an instant, visual interface for colleague management

### File Organization

The script creates an organized folder structure for all generated content:

```
output_folder/
├── Colleague_Name/
│   ├── profile_photo.jpg
│   ├── Colleague_Name.ofocus-perspective/
│   │   ├── Info-v3.plist
│   │   └── icon.png
│   ├── One-to-One - Colleague_Name.kmmacros
│   └── One-to-One - Colleague_Name.streamDeckAction
```

- **Colleague-specific folders**: Each person gets their own dedicated folder
- **Clean file names**: Simple, readable naming conventions  
- **Complete automation chain**: All files needed for double-click imports (perspectives, macros, actions)
- **Visual interface ready**: Stream Deck button provides instant colleague workflow access
- **Configurable location**: Set via `output.base_folder` (defaults to `.output`)

## Requirements

- Python 3.7+
- 1Password CLI (for secure token management)
- OmniFocus (for tag and perspective creation)
- Keyboard Maestro (for macro generation)
- Active Slack workspace access
- Pillow (for image processing - installed via requirements.txt)
- Obsidian (optional - for note creation)
- Stream Deck (optional - for visual automation buttons)