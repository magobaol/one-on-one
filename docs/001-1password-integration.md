# ADR-001: 1Password Integration Method

## Status
**Accepted** - December 2025

## Context
The application needs to securely retrieve API tokens (specifically Slack API tokens) without storing them in configuration files or environment variables. Two primary approaches were considered:

1. **1Password CLI (`op` command)**: Direct subprocess calls to the 1Password CLI
2. **1Password Connect Server**: HTTP API calls to a self-hosted 1Password Connect server

## Decision
**Use 1Password CLI (`op` command) for secret retrieval.**

### Implementation Details
- Use `subprocess.run(['op', 'item', 'get', item_name, '--field', field_name, '--reveal'])`
- Configure via `config.yaml` with item name and field name
- Handle authentication transparently through system keychain/biometrics

## Consequences

### Positive
- **Zero network dependencies**: Works offline and in air-gapped environments
- **Simple authentication**: Leverages system keychain and biometrics, no token management needed
- **No server infrastructure**: Self-contained solution, no additional services to maintain
- **Familiar workflow**: Uses same commands as manual `op` CLI usage
- **Lower complexity**: Fewer moving parts, easier to debug and maintain
- **Direct access**: No intermediary services or additional failure points

### Negative
- **Subprocess overhead**: Process spawn per API call (~1-2 second latency)
- **Platform dependency**: Requires `op` CLI to be installed and authenticated on the system
- **Session management**: May require periodic re-authentication
- **Text-based error handling**: Parsing stderr for error messages vs. structured JSON

### Risks and Mitigations
- **Risk**: CLI not installed → **Mitigation**: Clear error messaging and setup documentation
- **Risk**: Authentication expired → **Mitigation**: Graceful error handling with re-auth instructions
- **Risk**: Subprocess timeout → **Mitigation**: 30-second timeout with clear error messages

## Alternatives Considered
**1Password Connect Server** was rejected because:
- Adds network dependency and server maintenance overhead
- Requires additional token management and security considerations
- Current use case (single-user, local automation) doesn't justify the complexity
- Can be reconsidered later if scaling to multi-user/server deployment is needed
