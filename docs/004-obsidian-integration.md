# ADR-004: Obsidian Integration Strategy

## Status
Accepted - Implemented

## Context

The one-on-one automation system needs to create structured notes in Obsidian for each colleague, including their profile photo and basic information. The integration must handle complex folder structures.

## Decision

### Integration Approach
- **Direct file system approach**: Create markdown files and copy photos directly into the vault folder structure
- **No Obsidian API**: Avoid plugin dependencies or API complexity - work with standard markdown files
- **Configurable vault path**: Support any vault location via `config.yaml` with proper path expansion

### Folder Structure
```
vault/
└── 80 Spaces/
    └── people/
        └── Colleague Name/
            ├── Colleague Name.md
            └── Colleague Name.jpg
```

- **Person-specific folders**: Each colleague gets their own dedicated folder within the vault
- **Configurable base path**: `people_folder` setting allows customization of the base folder structure
- **Natural naming**: Use colleague's full name for both folders and files

### Note Content Format
```markdown
# Colleague Name

![[Colleague Name.jpg|200]]

```

- **Minimal structure**: Just title and photo, allowing users to expand as needed
- **Obsidian-style image links**: Use `![[]]` syntax for proper internal linking
- **Image sizing**: Include `|200` parameter for appropriate display width (200px)
- **No frontmatter**: Keep notes simple without YAML headers

### Photo Handling
- **Copy from output folder**: Source photos from the organized output structure
- **JPEG format**: Maintain original JPEG format from Slack (no conversion needed)
- **Consistent naming**: `Colleague Name.jpg` matches the folder and note naming pattern

### Conflict Resolution
- **Incremental numbering**: If note exists, create `Colleague Name (1).md`, `Colleague Name (2).md`, etc.
- **Non-destructive**: Never overwrite existing notes
- **Clear logging**: Inform user when conflicts are resolved

### Configuration Management
```yaml
obsidian:
  vault_path: "~/path/to/vault"  # Supports ~ expansion and complex paths
  people_folder: "80 Spaces/people"  # Relative path within vault
```

- **Optional integration**: Works when configured, gracefully disabled when not
- **Path flexibility**: Handle Google Drive paths with special characters
- **Error resilience**: Validation and clear error messages

## Alternatives Considered

### Obsidian Plugin Integration
- **Rejected**: Would require users to install specific plugins
- **Complexity**: Plugin API changes over time
- **Dependencies**: Creates external dependencies beyond our control

### API-based Approach
- **Rejected**: Obsidian doesn't have a comprehensive public API
- **Limitations**: Most automation requires plugins anyway

### Templating System
- **Rejected for now**: Keep initial implementation simple
- **Future consideration**: Could add template support later if needed

### Single Shared Folder
- **Rejected**: All colleagues in one folder would create clutter
- **Scalability**: Person-specific folders scale better with many colleagues

## Consequences

### Positive
- **Simple and reliable**: Direct file system operations are robust
- **No external dependencies**: Works with any Obsidian vault setup
- **Flexible vault locations**: Supports Google Drive, iCloud, local vaults
- **Clean organization**: Person-specific folders prevent clutter
- **Proper image display**: 200px width provides good visual balance
- **Graceful degradation**: Works without configuration, just skips step

### Negative
- **Manual vault path configuration**: Users must provide correct vault path
- **No template customization**: Note format is fixed (could be addressed later)
- **Potential sync conflicts**: Direct file manipulation during sync could cause issues
- **Path complexity**: Google Drive paths with special characters require careful handling

### Risks Mitigated
- **Path validation**: Check vault exists before attempting operations
- **Graceful error handling**: Don't fail entire workflow if Obsidian step fails
- **Clear logging**: Provide detailed feedback about what's happening
- **Non-destructive operations**: Never overwrite existing content

## Implementation Notes

### Key Components
- **ObsidianClient class**: Handles all vault operations
- **Path expansion**: Proper handling of `~` and complex Google Drive paths  
- **Folder creation**: Automatic directory structure creation
- **Photo copying**: Reliable file copying with error handling
- **Conflict detection**: Smart filename generation for existing notes

### Integration Points
- **OutputManager**: Source photos from organized colleague folders
- **Main workflow**: Obsidian step integrated as Step 5 after OmniFocus operations
- **Configuration**: Seamlessly integrated into existing config.yaml structure

### Error Handling
- **Vault not found**: Graceful disable with clear warning
- **Permission issues**: Clear error messages for file system problems
- **Photo missing**: Continue note creation even if photo copy fails
- **Path problems**: Detailed logging for debugging path issues

This approach provides a solid foundation for Obsidian integration that can be extended with additional features (templates, metadata, etc.) in future iterations while maintaining simplicity and reliability.
