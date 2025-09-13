# ADR-003: OmniFocus Integration Strategy

## Status
**Accepted** - December 2025

## Context
The application needs to create colleague tags in OmniFocus under an existing hierarchical structure. Multiple integration approaches were evaluated:

1. **x-callback-url scheme**: URL-based automation
2. **AppleScript**: Direct application scripting via `osascript`
3. **OmniFocus API**: Third-party REST API (not officially supported)

Key requirements:
- Create tags under existing hierarchy (People → Hootsuite → Colleague)
- Avoid creating tasks (tags only)
- Handle emoji characters and special formatting in tag names
- Ensure idempotency (don't create duplicates)
- Reference existing tag structure reliably

## Decision
**Use AppleScript with tag ID references for OmniFocus integration.**

### Implementation Details
- **Method**: Direct AppleScript execution via `subprocess.run(['osascript', '-e', script])`
- **Parent Tag Reference**: Use OmniFocus tag ID (`atN5uWs5bJo`) instead of name-based lookup
- **Tag Creation**: Create colleague name as child of specified parent tag
- **Idempotency**: Check for existing tags before creation
- **Error Handling**: Structured AppleScript responses with success/error indicators

### AppleScript Architecture
```applescript
-- Find parent tag by ID (recursive search through all tag levels)
-- Check if colleague tag already exists under parent
-- Create new tag only if it doesn't exist
-- Return structured status message
```

## Consequences

### Positive
- **Direct tag creation**: No intermediate tasks required (vs. x-callback-url limitation)
- **Reliable parent reference**: Tag ID eliminates emoji/whitespace matching issues
- **Full OmniFocus access**: Complete AppleScript API available
- **Idempotent operations**: Safe to run multiple times
- **Structured responses**: Clear success/failure indicators
- **No external dependencies**: Uses built-in macOS AppleScript engine

### Negative
- **Platform locked**: macOS/AppleScript only, not cross-platform
- **Process overhead**: Subprocess spawn for each operation (~500ms)
- **AppleScript complexity**: More complex than URL scheme
- **Application dependency**: Requires OmniFocus to be installed and accessible

### Performance Characteristics
- **Tag ID lookup**: O(n) search through all tags (including nested)
- **Execution time**: ~500ms per tag creation
- **Memory usage**: Minimal (subprocess cleanup)
- **Reliability**: High (native AppleScript integration)

### Risks and Mitigations
- **Risk**: OmniFocus not running → **Mitigation**: Clear error messaging
- **Risk**: Invalid tag ID → **Mitigation**: Graceful error handling with specific messages
- **Risk**: AppleScript syntax errors → **Mitigation**: Extensive testing and validation
- **Risk**: Permissions issues → **Mitigation**: macOS automation permission prompts

## Alternatives Considered

### 1. x-callback-url Scheme
**Initial implementation, then rejected** because:
- **Major limitation**: Cannot create tags without creating tasks
- **Workaround complexity**: Required creating temporary tasks to get tags
- **User experience**: Left unwanted tasks in OmniFocus
- **Inflexibility**: Limited parameter support

### 2. Hierarchical Path Matching
**Rejected** due to technical challenges:
- **Emoji handling**: AppleScript string comparison failed with `👨‍👩‍👦‍👦 People`
- **Whitespace sensitivity**: Extra spaces in tag names caused match failures  
- **Name ambiguity**: Multiple tags with similar names caused confusion
- **Maintenance burden**: Name changes would break references

### 3. OmniFocus REST API (Third-party)
**Not pursued** because:
- **Unofficial**: No official Omni Group API support
- **Reliability concerns**: Third-party implementations may break
- **Additional dependencies**: HTTP client libraries and authentication
- **Limited functionality**: May not support all required operations

## Evolution History
1. **Initial**: Hierarchical path matching with name strings
2. **Problem**: Emoji and whitespace matching failures
3. **Solution**: Switch to tag ID-based references
4. **Refinement**: Recursive tag search for nested hierarchies
5. **Final**: Clean tag ID approach with structured error handling

## Configuration Requirements
```yaml
omnifocus:
  method: "applescript"
  tag_id: "atN5uWs5bJo"  # Parent tag ID from "Copy as Link"
  create_task: false      # Tags only, no tasks
```

## Future Considerations
- **Cross-platform**: If Windows/Linux support needed, consider alternative task managers
- **Batch operations**: AppleScript could be optimized for multiple tag creation
- **OmniFocus 4+**: Monitor for official API support in future versions
