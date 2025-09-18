# Implementation Plan — One-on-one Automation (Python)

## Goal

Automate the complete workflow for managing one-on-one meetings with colleagues, integrating Slack, OmniFocus, Obsidian, Keyboard Maestro, and Stream Deck to create a seamless, one-button automation experience.

## Inputs (all mandatory)

* **Name** (colleague's name)
* **Slack handle** (colleague's Slack username)
* **Photo** (downloaded from Slack and used across all integrations)

## Steps

### 1. Token and Secrets Management

* The Slack API token **must not** be stored in the Python script configuration.
* The script must retrieve the token from **1Password**.

  * **Preferred option**: 1Password CLI integration.
  * **Alternative**: 1Password Connect Server.
* The file `config.json` (or `.yaml`) will contain either:

  * For CLI: item/field identifiers where the token is stored.
  * For Connect Server: connection parameters + item/field references.

### 2. Slack Integration

* Using Slack API:

  * Retrieve the profile photo of the colleague based on the Slack handle.
  * Save the photo locally for use across all integrations (Obsidian notes, OmniFocus icons, Keyboard Maestro macros, Stream Deck buttons).

### 3. OmniFocus Integration

* **Hierarchical Tag Creation**: Using AppleScript integration to create colleague tags under existing organizational structure.

* **Custom Perspective Generation**: Automatically generate focused perspectives using template-based plist approach:

  * Parse existing perspective templates and replace placeholders.
  * Generate colleague-specific tag filtering rules.
  * Embed profile photo as perspective icon.
  * Create importable `.ofocus-perspective` bundles for double-click import.

### 4. Obsidian Integration

* **Structured Note Creation** within the configured vault:

  * Create colleague-specific folders under organized hierarchy (e.g., `80 Spaces/people/Colleague Name/`).
  * Generate notes with embedded profile photos using Obsidian-style image links.
  * Implement conflict resolution for existing notes (automatic numbering).
  * Copy profile photos directly into vault structure for seamless integration.

### 5. Keyboard Maestro Integration

* Automatically generate colleague-specific macros using an **export/modify/import approach**:

  * Retrieve template macro XML via AppleScript.
  * Replace placeholders (`#obsidianNoteName`, `#ofPerspectiveName`) with colleague information.
  * Embed colleague's profile photo as custom TIFF icon data.
  * Generate UUID for macro identification and inter-service linking.
  * Create importable `.kmmacros` file for seamless double-click import.

### 6. Stream Deck Integration

* Create visual automation buttons that complete the workflow chain:

  * Generate colleague-specific Stream Deck actions using included template (`resources/streamDeckButton.streamDeckAction`).
  * Link actions to Keyboard Maestro macros via UUID chaining.
  * Convert profile photos to Stream Deck format (288x288 PNG icons).
  * Create importable `.streamDeckAction` files for one-button colleague access.
  * Enable instant workflow execution directly from Stream Deck interface with standardized template.

### 7. Configuration File

The configuration file (e.g., `config.yaml`) will contain:

* Path of the Obsidian vault.
* Parameters for retrieving the Slack token from 1Password (CLI item/field or Connect Server credentials).
* Keyboard Maestro template macro configuration (UUID and name).
* Stream Deck integration (fully automated with fixed template and position from resources directory).
* Output folder organization settings for colleague-specific file structure.

## Deliverables

* A Python script (`one_on_one_setup.py`) capable of:

  * **Slack Integration**: Retrieving colleague profile photos with pagination support.
  * **OmniFocus Integration**: Creating hierarchical tags and generating custom perspectives with embedded icons.
  * **Obsidian Integration**: Creating structured notes with embedded profile photos in organized vault folders.
  * **Keyboard Maestro Integration**: Generating personalized macros with custom icons and parameter replacement.
  * **Stream Deck Integration**: Creating visual automation buttons linked to Keyboard Maestro macros.
  * **Output Organization**: Generating colleague-specific folders with all automation artifacts.
  * **UUID Chaining**: Seamless integration between Keyboard Maestro and Stream Deck via shared identifiers.

* A comprehensive `config.yaml` for specifying:
  * Vault paths and folder structure.
  * Secure 1Password CLI integration.
  * Template macro and action configurations.
  * Output organization preferences.

* **Complete Automation Chain**: One command generates all files needed for:
  * Double-click imports (OmniFocus perspectives, Keyboard Maestro macros, Stream Deck actions).
  * Instant colleague setup with visual interface via Stream Deck.
  * Organized, scalable file structure for long-term management.
