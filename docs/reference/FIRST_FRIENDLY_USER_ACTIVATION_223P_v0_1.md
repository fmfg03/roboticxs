# First Friendly User Activation 223P v0.1

223P adds `/pilot_activate` as the local first friendly user activation receipt.

The command answers one pilot question: can a specific friendly user be activated for first use without losing control, trust, or traceability?

## Telegram surface

`/pilot_activate <alias>` renders:

- activation status
- setup status
- pilot alias and local pilot user id
- activation checklist
- first successful command
- first useful output signal
- first feedback signal
- first issue signal
- activation receipt id
- safety boundaries

If the command is run without an alias, it uses an explicit local fallback alias. If the first token is numeric, the token is treated as the local pilot user id and the remaining text is the alias.

## Authority boundary

223P does not:

- provision external accounts
- send invites
- activate connectors
- claim live data
- send Gmail
- write Calendar events
- write CRM records
- use WhatsApp
- perform destructive actions
- perform external writes
- expose secrets

The receipt keeps approval, source trace, and usage/cost semantics visible as preserved boundaries.

## Acceptance

223P is closed only when `/pilot_activate` can show:

1. activation checklist
2. setup status
3. first successful command
4. first useful output status
5. first feedback status
6. first issue status
7. activation receipt
8. explicit no-write safety boundaries
