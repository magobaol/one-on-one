# Implementation Plan — One-on-one Automation (Python)

## Goal

Automate the workflow for managing one-on-one meetings with colleagues, integrating Slack, OmniFocus, Obsidian, and Keyboard Maestro.

## Inputs (all mandatory)

* **Name** (colleague’s name)
* **Slack handle** (colleague’s Slack username)
* **Photo** (downloaded from Slack)

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
  * Save the photo locally for later use in Obsidian.

### 3. OmniFocus Integration

* Two possible approaches:

  * **Via API** (if accessible): create a new tag for the colleague.
  * **Via x-callback-url**: leverage OmniFocus’ URL scheme to add the tag automatically.

### 4. Obsidian Integration

* In the specified vault (provided by the user at runtime, not hardcoded):

  * Create a note under a predefined folder (e.g., `People/`).
  * Include:

    * Colleague’s name.
    * Slack handle.
    * Link to the photo downloaded from Slack.

### 5. Keyboard Maestro Integration

* Attempt to **clone an existing macro** (template) automatically:

  * Replace variables/placeholders with the colleague’s name and Slack handle.
  * If cloning fails, fallback option: manually duplicate and adjust the macro.

### 6. Configuration File

The configuration file (e.g., `config.yaml`) will contain:

* Path of the Obsidian vault.
* Parameters for retrieving the Slack token from 1Password (CLI item/field or Connect Server credentials).
* Default paths/folders for storing downloaded photos.

## Deliverables

* A Python script (`one_on_one_setup.py`) capable of:

  * Retrieving the Slack photo.
  * Creating/associating the tag in OmniFocus (via API or x-callback-url).
  * Generating the Obsidian note.
  * Cloning/updating the Keyboard Maestro macro.
* A `config.yaml` (or `.json`) for specifying vault path, secret management, and default paths.
