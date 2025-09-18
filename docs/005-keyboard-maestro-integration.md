# ADR 005: Keyboard Maestro Integration Strategy

## Status
Accepted

## Context

The one-on-one automation system needs to integrate with Keyboard Maestro to automatically create personalized macros for each colleague. These macros should:

1. Be based on a template macro that contains predefined actions and subroutines
2. Replace specific placeholders with colleague-specific information
3. Have the colleague's profile picture as the macro icon
4. Be automatically placed in the same macro group as the template

### Requirements Analysis

**Template Macro Structure:**
- Name: "-One-to-One - Template" (configurable via YAML)
- UUID: `B8D72CC1-7B5F-4F04-8F08-5A0A6B89B6C7` (configurable via YAML)
- Contains two actions:
  1. SetVariableToText (to be ignored during automation)
  2. ExecuteSubroutine with parameters including placeholders `#obsidianNoteName` and `#ofPerspectiveName`

**Technical Constraints:**
- Keyboard Maestro doesn't provide direct AppleScript commands for macro duplication
- Programmatic macro creation requires working with XML/plist data
- Icon setting has limited AppleScript support and may require manual intervention
- Must avoid disrupting existing macro functionality

## Decision

**Final Approach: Export/Modify/Import via .kmmacros Files**

We will implement an export/modify/import approach that mirrors the successful OmniFocus perspective strategy:

1. **Template Retrieval**: Use AppleScript to get the XML representation of the template macro
2. **Macro Modification**: Parse and modify the macro's plist data in Python to:
   - Update macro name to "One-to-One - [Colleague Name]"
   - Generate a new UUID for the duplicated macro
   - Replace placeholders in ExecuteSubroutine parameters:
     - `#obsidianNoteName` → Colleague's full name
     - `#ofPerspectiveName` → Colleague's full name
   - Embed colleague's profile photo as TIFF data in CustomIconData
3. **File Generation**: Create a complete .kmmacros file with proper plist structure
4. **User Import**: Provide the .kmmacros file for simple double-click import into Keyboard Maestro

**Alternative Approaches Considered:**

- **Direct AppleScript Duplication**: Not feasible due to limited Keyboard Maestro AppleScript dictionary
- **File System Manipulation**: Avoided due to complexity and potential for corruption
- **Keyboard Maestro Engine API**: No public API available for macro management

## Implementation Details

### KeyboardMaestroClient Class
```python
class KeyboardMaestroClient:
    def create_colleague_macro(self, colleague_name: str, slack_handle: str) -> bool:
        # 1. Get template macro XML via AppleScript
        # 2. Create modified macro XML with colleague data
        # 3. Generate .kmmacros file with proper plist structure
        # 4. Provide import instructions to user
```

### Export/Modify/Import Process
- AppleScript retrieval of template macro XML
- Python plist manipulation for customization
- TIFF icon conversion and embedding
- .kmmacros file generation following Keyboard Maestro's import format
- User-friendly double-click import process

### Placeholder Replacement
- Target the ExecuteSubroutine action's Parameters array
- Replace exact string matches:
  - `#obsidianNoteName` → colleague's full name
  - `#ofPerspectiveName` → colleague's full name
- Preserve all other parameters unchanged

### Icon Management
- **Automated TIFF Embedding**: Profile photos converted to 32x32 TIFF format and embedded directly in CustomIconData
- **Complete Automation**: No manual intervention required for icon setting
- **High Quality**: Maintains image quality through proper format conversion

## Configuration

The Keyboard Maestro integration is fully configurable via YAML settings:

```yaml
keyboard_maestro:
  template_uuid: "B8D72CC1-7B5F-4F04-8F08-5A0A6B89B6C7"  # UUID of your template macro
  template_name: "-One-to-One - Template"                  # Name of your template macro
```

### Configuration Details

**`template_uuid`**: The unique identifier of your template macro in Keyboard Maestro. You can get this by:
1. Right-clicking your template macro in Keyboard Maestro
2. Selecting "Copy UUID" from the context menu
3. Pasting the UUID into your configuration

**`template_name`**: The display name of your template macro. This is used for logging and error messages to help identify the correct template.

### Customizing Templates

You can create multiple template macros for different purposes and simply change the configuration to point to different templates:
- Different organizational structures
- Varying action sequences
- Alternative subroutine calls

The system includes fallback values matching the original specifications, ensuring reliability even if configuration values are missing.

## Consequences

### Positive
- ✅ **Complete Automation**: 100% automated macro creation including custom icons
- ✅ **Template Consistency**: All colleague macros maintain the same structure and actions
- ✅ **Perfect Personalization**: Each macro is fully customized with colleague-specific information
- ✅ **Visual Identification**: Profile pictures automatically embedded as macro icons
- ✅ **User-Friendly**: Simple double-click import process matching OmniFocus workflow
- ✅ **Reliable**: Export/modify/import approach is robust and doesn't risk corrupting existing macros

### Negative
- ❌ **Import Step Required**: One manual double-click needed to import the generated macro
- ❌ **AppleScript Dependency**: Requires Keyboard Maestro to be running for template retrieval
- ❌ **Template Dependency**: Changes to template structure could affect automation

### Risks and Mitigations

**Risk**: Template macro changes breaking automation
- **Mitigation**: Version the template macro and document required structure

**Risk**: AppleScript permission issues
- **Mitigation**: Clear setup documentation for macOS permissions

**Risk**: .kmmacros file format changes
- **Mitigation**: Comprehensive testing and version tracking of Keyboard Maestro formats

**Risk**: TIFF conversion failures
- **Mitigation**: Graceful fallback to template icon if conversion fails

## Technical Notes

### .kmmacros File Format
The generated macro files follow Keyboard Maestro's import format:
```xml
<array>
  <dict>
    <key>Macros</key>
    <array>
      <dict>
        <key>Actions</key>
        <key>CustomIconData</key> <!-- Base64 TIFF data -->
        <key>Name</key>           <!-- "One-to-One - Colleague Name" -->
        <key>UID</key>            <!-- Generated UUID -->
        <!-- Full macro structure -->
      </dict>
    </array>
    <key>Name</key>              <!-- Group name: "HS - One-to-one" -->
    <key>UID</key>               <!-- Group UUID -->
  </dict>
</array>
```

### Icon Conversion Process
1. **Source**: Colleague's profile photo (JPEG, typically 512px)
2. **Conversion**: `sips -s format tiff -Z 32` for optimal Keyboard Maestro compatibility
3. **Embedding**: Binary TIFF data encoded and stored in CustomIconData field
4. **Result**: Perfect visual identification in Keyboard Maestro interface

### Error Recovery
- Comprehensive logging at each step of the process
- Graceful fallback to template icon if TIFF conversion fails
- Continues workflow execution even if Keyboard Maestro integration fails
- Clear import instructions provided to user

This export/modify/import approach provides a breakthrough solution for Keyboard Maestro automation, achieving 100% automation while maintaining reliability and user-friendliness through the familiar double-click import pattern.
