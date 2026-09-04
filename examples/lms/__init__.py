"""Extendable LMS namespace for dependencies of the canonical example.

The standalone ``courses`` application can therefore use the remaining LMS
applications from a checkout without copying them into this repository.
"""

from pkgutil import extend_path

__path__ = extend_path(__path__, __name__)
