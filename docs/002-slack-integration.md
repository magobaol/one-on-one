# ADR-002: Slack Integration Strategy

## Status
**Accepted** - December 2025

## Context
The application needs to:
1. Look up Slack users by handle/username to retrieve profile information
2. Download profile photos from Slack
3. Handle large workspaces (5000+ users) efficiently
4. Balance API usage limits with user experience

Multiple approaches were considered for user lookup and photo retrieval.

## Decision
**Use `users.list` API with pagination for user lookup, direct HTTP download for photos.**

### Implementation Details
- **User Lookup**: Paginated `users.list` API calls (1000 users per page, max 5 pages)
- **Matching Logic**: Match on `name`, `display_name`, `real_name_normalized` (case-insensitive)
- **Photo Download**: Extract photo URL from user profile, download via HTTP GET to Slack CDN
- **API Efficiency**: Stop pagination immediately when user is found
- **Error Handling**: Graceful degradation for missing users or photos

## Consequences

### Positive
- **Single API for all data**: `users.list` provides both user info and photo URLs
- **Efficient for common cases**: Most active users are on page 1 (1 API call)
- **Comprehensive matching**: Handles various handle formats (@ff, ben.cathers, etc.)
- **No additional auth**: Photo URLs from Slack CDN don't require API authentication
- **Robust pagination**: Handles workspaces of any size within reasonable limits

### Negative
- **Linear search complexity**: Users on later pages require multiple API calls
- **API usage scales with user position**: Page 2 users = 2 API calls, Page 3 = 3 calls
- **Not found users expensive**: Search all 5 pages = 5 API calls for non-existent users
- **No caching**: Repeated lookups for same workspace re-fetch user list

### Performance Characteristics
| User Location | API Calls | Typical Users |
|---------------|-----------|---------------|
| Page 1        | 1         | Active users (~80%) |
| Page 2        | 2         | Less active users |
| Page 3-5      | 3-5       | Inactive/former users |
| Not Found     | 5         | Typos/external users |

### Risks and Mitigations
- **Risk**: API rate limiting → **Mitigation**: Built-in rate limit handling in `slack_sdk`
- **Risk**: High API usage for inactive users → **Mitigation**: 5-page limit prevents excessive calls
- **Risk**: Photo download failures → **Mitigation**: Continue workflow even if photo fails

## Alternatives Considered

### 1. `users.lookupByEmail` API
**Rejected** because:
- Requires email addresses (not available in our use case)
- Only works for exact email matches
- Doesn't solve the fundamental lookup problem

### 2. User Search API (`users.search`)
**Not available** in Slack API - no general user search endpoint

### 3. Caching Strategy
**Deferred** because:
- Current use case (single colleague setup) doesn't justify complexity
- Can be added later if batch processing becomes common
- Adds state management and cache invalidation concerns

## Future Optimizations
If API usage becomes a concern:
1. **User list caching**: Cache `users.list` results for batch processing
2. **Background prefetch**: Fetch full user list once, search locally
3. **Smart pagination**: Use workspace analytics to optimize page limits
