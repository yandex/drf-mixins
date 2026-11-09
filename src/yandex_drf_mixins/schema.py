from typing import Any

DJANGO_ERROR_ITEM_COMPONENT_NAME = "DjangoErrorItem"
DJANGO_4XX_ERROR_COMPONENT_NAME = "Django4xxError"
DJANGO_4XX_ERROR_RESPONSE_COMPONENT_NAME = "Django4xxErrorResponse"


def _error_item_schema(ref: str) -> dict[str, Any]:
    return {
        "oneOf": [
            {"type": "string"},
            {
                "type": "array",
                "items": {"$ref": ref},
            },
            {
                "type": "object",
                "additionalProperties": {"$ref": ref},
            },
        ]
    }


def _error_response_schema(item_ref: str) -> dict[str, Any]:
    return {
        "oneOf": [
            {
                "type": "array",
                "items": {"$ref": item_ref},
            },
            {
                "type": "object",
                "additionalProperties": {"$ref": item_ref},
            },
        ]
    }


_JSON_SCHEMA_ERROR_ITEM_REF = "#/definitions/errorItem"

DJANGO_4XX_ERROR_JSON_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    **_error_response_schema(_JSON_SCHEMA_ERROR_ITEM_REF),
    "definitions": {
        "errorItem": _error_item_schema(_JSON_SCHEMA_ERROR_ITEM_REF),
    },
}

_DJANGO_ERROR_ITEM_COMPONENT_REF = f"#/components/schemas/{DJANGO_ERROR_ITEM_COMPONENT_NAME}"

DJANGO_4XX_ERROR_OPENAPI_SCHEMAS = {
    DJANGO_ERROR_ITEM_COMPONENT_NAME: _error_item_schema(_DJANGO_ERROR_ITEM_COMPONENT_REF),
    DJANGO_4XX_ERROR_COMPONENT_NAME: _error_response_schema(_DJANGO_ERROR_ITEM_COMPONENT_REF),
}

DJANGO_4XX_ERROR_OPENAPI_REF = {"$ref": f"#/components/schemas/{DJANGO_4XX_ERROR_COMPONENT_NAME}"}
DJANGO_4XX_ERROR_OPENAPI_EXAMPLES = {
    "detail": {
        "summary": "General request error",
        "value": {"detail": "Authentication credentials were not provided."},
    },
    "fieldErrors": {
        "summary": "Field errors",
        "value": {
            "name": ["This field is required."],
            "start_date": ["Date has wrong format."],
        },
    },
    "nestedErrors": {
        "summary": "Nested object errors",
        "value": {"author": {"email": ["Enter a valid email address."]}},
    },
    "listErrors": {
        "summary": "Object list errors",
        "value": [
            {"email": ["This field is required."]},
            {},
        ],
    },
}
DJANGO_4XX_ERROR_OPENAPI_RESPONSE_REF = {"$ref": f"#/components/responses/{DJANGO_4XX_ERROR_RESPONSE_COMPONENT_NAME}"}

__all__ = [
    "DJANGO_4XX_ERROR_COMPONENT_NAME",
    "DJANGO_4XX_ERROR_JSON_SCHEMA",
    "DJANGO_4XX_ERROR_OPENAPI_EXAMPLES",
    "DJANGO_4XX_ERROR_OPENAPI_REF",
    "DJANGO_4XX_ERROR_OPENAPI_RESPONSE_REF",
    "DJANGO_4XX_ERROR_OPENAPI_SCHEMAS",
    "DJANGO_4XX_ERROR_RESPONSE_COMPONENT_NAME",
    "DJANGO_ERROR_ITEM_COMPONENT_NAME",
]
