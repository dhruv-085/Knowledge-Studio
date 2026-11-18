# Session Management

The service creates a session after successful authentication. A session
contains the authenticated user identity and expires after a period of
inactivity.

## Expiration

Inactive sessions expire after 30 minutes. Any authenticated request resets
the inactivity timer. The user must authenticate again after expiration.

## Configuration

Administrators can change the timeout with the `SESSION_TIMEOUT_MINUTES`
configuration key. The value must be greater than zero.

## Security

Shorter timeouts reduce the window available to an attacker using a stolen
session. Longer timeouts may be more convenient for users but increase the
duration of potential misuse.
