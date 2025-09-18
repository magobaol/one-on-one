# ADR 006: Stream Deck Integration

## Status
Accepted

## Context
We need to integrate with Elgato Stream Deck to create colleague-specific action buttons that trigger the corresponding Keyboard Maestro macros. This completes the automation chain: Stream Deck → Keyboard Maestro → OmniFocus/Obsidian workflows.

## Key Requirements
- Create colleague-specific Stream Deck actions automatically
- Link actions to Keyboard Maestro macros via UUID
- Use colleague profile photos as custom button icons
- Provide importable action files for easy setup
- Maintain consistency with existing export/modify/import pattern

## Decision
We will use a **Template-Based ZIP Manipulation** approach:

### Core Architecture
1. **Fixed Template**: Use `resources/streamDeckButton.streamDeckAction` as base
2. **ZIP File Format**: Stream Deck actions are ZIP archives containing JSON manifests and image assets
3. **JSON Manifest Modification**: Parse and modify action configuration programmatically
4. **Custom Icon Integration**: Convert profile photos to 288x288 PNG format for button display
5. **UUID Chaining**: Link to Keyboard Maestro macros using generated macro UUIDs

### Technical Implementation
- **Template Extraction**: Unzip template action to temporary directory
- **Manifest Parsing**: Read and modify JSON configuration files
- **Image Processing**: Convert profile photos using Pillow (PIL)
- **Asset Management**: Replace template images with colleague-specific icons
- **ZIP Repackaging**: Create new .streamDeckAction file for import
- **Automatic Import**: Double-click workflow for seamless user experience

### Fixed Configuration
- **Grid Position**: Always use `0,0` for consistent placement
- **Template Path**: Fixed to `resources/streamDeckButton.streamDeckAction`
- **Image Format**: 288x288 PNG for optimal Stream Deck display
- **Action Structure**: Standard Keyboard Maestro trigger action

## Alternatives Considered

### 1. Stream Deck SDK Integration
- **Pros**: Direct API access, real-time updates
- **Cons**: Complex setup, requires Stream Deck software running, platform-specific
- **Rejected**: Too complex for our use case

### 2. Manual Configuration Instructions
- **Pros**: Simple, no code complexity
- **Cons**: Time-consuming, error-prone, breaks automation chain
- **Rejected**: Defeats the purpose of automation

### 3. XML-Based Configuration
- **Pros**: Structured format
- **Cons**: Stream Deck uses JSON, not XML
- **Rejected**: Wrong file format

## Consequences

### Positive
- **Complete Automation Chain**: Stream Deck → Keyboard Maestro → Workflows
- **Visual Consistency**: Custom icons using colleague profile photos  
- **Simple Import**: Double-click .streamDeckAction files
- **UUID Chaining**: Seamless integration with Keyboard Maestro macros
- **Template Consistency**: All actions have identical structure and behavior
- **Cross-Platform**: ZIP manipulation works on any system

### Negative
- **ZIP Complexity**: Requires understanding of Stream Deck action file format
- **Dependency on Template**: Changes to template affect all generated actions
- **Image Processing**: Requires Pillow library for photo conversion
- **Stream Deck Specific**: Only works with Elgato Stream Deck hardware

### Neutral
- **Fixed Configuration**: No customization of grid position or template (by design)
- **External Import Step**: Actions must be imported manually or via automation

## Implementation Notes

### File Structure
```
colleague_folder/
├── profile_photo.jpg
└── One-to-One - Colleague_Name.streamDeckAction (ZIP containing):
    └── Profile.sdProfile/
        ├── manifest.json (modified with colleague data)
        ├── Profiles/
        │   └── UUID/
        │       ├── manifest.json (action configuration)
        │       └── Images/
        │           └── colleague_icon.png (288x288)
```

### Key Modifications
- **Action Label**: `"One-to-One - {colleague_name}"`
- **Button Title**: `{colleague_name}`
- **Keyboard Maestro UUID**: Links to generated macro UUID
- **Custom Icon**: Colleague profile photo as 288x288 PNG
- **Image References**: Updated to point to new icon file

### Integration Points
- **Input**: Colleague name, Keyboard Maestro macro UUID, profile photo
- **Output**: Importable .streamDeckAction file
- **Chaining**: Receives UUID from Keyboard Maestro integration
- **Usage**: Part of 10-step automation workflow

## Monitoring
- Success measured by successful .streamDeckAction file generation
- Error handling for missing templates, image conversion failures
- Graceful degradation when Stream Deck app not installed
- Manual import instructions as fallback

This decision enables the complete automation chain while maintaining the export/modify/import pattern that proved successful with OmniFocus perspectives and Keyboard Maestro macros.
