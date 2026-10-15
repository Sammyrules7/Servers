# Actions access

The deployed Forgejo 15.0.9 has no `DEFAULT_ACTIONS_ENABLED` /
`default-actions-enabled` user setting or admin user Actions checkbox. New
repositories default to units excluding `repo.actions`; fork and mirror defaults
also exclude Actions. Existing repository units are unchanged.

Repository administrators can enable Actions themselves. Therefore accounts must
be trusted: public registration and OAuth automatic registration are disabled.
Existing users and linked external logins continue to work. To onboard someone,
an instance administrator provisions their account (including external identity
association under Site Administration → User Accounts). Then a trusted repository
administrator enables **Repository Settings → Units → Actions**. There is no
separate per-user Actions grant in this version. Do not provision untrusted repo
administrators while using instance-wide privileged runners.

Both existing database runner registrations are instance-wide (`owner_id=0`,
`repo_id=0`). Labels (`nix`, `default`, etc.) select execution environments, not
permissions. Per-repository isolation requires registering a runner with that
repository's registration token (or a trusted user's/organization's token for
owner scope), rather than assigning an instance runner by label. This change
preserves registrations, labels, host Nix store/daemon mounts, and NetworkPolicy.

`REQUIRE_SIGNIN_VIEW` controls anonymous reading; CAPTCHA only deters automated
signup. Manual registration approval (`REGISTER_MANUAL_CONFIRM`) is an alternative
to closed registration, not a per-user Actions permission. Restricted users and
private/limited profile visibility do not provide a general Actions execution
gate. None of these substitutes for controlling account admission here.

Verified against the deployed version's source:
- [Repository defaults](https://code.forgejo.org/forgejo/forgejo/src/tag/v15.0.9/custom/conf/app.example.ini)
- [Workflow repository-unit check](https://code.forgejo.org/forgejo/forgejo/src/tag/v15.0.9/services/actions/notifier_helper.go)
- [Runner scope](https://code.forgejo.org/forgejo/forgejo/src/tag/v15.0.9/models/actions/runner.go)
