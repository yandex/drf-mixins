# Security Policy

> **Draft:** The fallback reporting contact and response targets in this policy
> must be approved by the relevant Information Security team before the public
> release.

## Supported Versions

Only the latest released version of `yandex-drf-mixins` is supported with
security updates.

## Reporting a Vulnerability

Please do not report security vulnerabilities through public GitHub issues,
discussions, or pull requests.

Use GitHub private vulnerability reporting for this repository. A fallback
reporting contact will be added here after it has been approved by the relevant
Information Security team.

Please include:

- the affected version;
- a description of the vulnerability and its potential impact;
- the affected component or API;
- the steps required to reproduce the issue;
- a minimal reproducing example, if possible;
- any suggested mitigation.

The acknowledgement and update targets for reports will be added after they
have been approved by the relevant Information Security team. Please allow a
reasonable amount of time for a fix to be released before disclosing the
vulnerability publicly.

## Scope

Reports are in scope when the vulnerable behavior is caused by
`yandex-drf-mixins`, including its DRF or ADRF components and the testing
helpers shipped in the package.

Vulnerabilities in Django, Django REST Framework, ADRF, or another dependency
should be reported to the corresponding upstream project unless
`yandex-drf-mixins` introduces or exposes the vulnerable behavior.
