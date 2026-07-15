#!/usr/bin/env python3
"""Post-generation fixups for the OpenAPI-generated Go client.

openapi-generator maps a free-form (empty `{}`) schema property to
`map[string]interface{}` when the source spec is Swagger 2.0, because the
Swagger -> OpenAPI 3 converter assigns `type: object` to any typeless schema.
For fields that are genuinely "any JSON value" this is the wrong Go type; it
should be `interface{}`.

This script rewrites those fields (and their generated getters/setters) to use
`interface{}`, matching exactly what openapi-generator emits for a free-form
value under an OpenAPI 3.x spec. It is idempotent: running it on an
already-converted file is a no-op. It fails loudly if a target file is present
but contains neither the expected `map[string]interface{}` form nor the
already-converted `interface{}` form, so generator drift is caught in CI.

Add new (file, struct) pairs to TARGETS as needed.
"""

import os
import re

# Repo root is two levels up from .github/workflows/.
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# The struct field line's whitespace is set by gofmt (column alignment), so it
# is matched with a whitespace-tolerant regex rather than an exact string.
FIELD_MAP_RE = re.compile(
    r'(\bValue[ \t]+)map\[string\]interface\{\}([ \t]+`json:"value,omitempty"`)'
)
FIELD_IFACE_RE = re.compile(
    r'\bValue[ \t]+interface\{\}[ \t]+`json:"value,omitempty"`'
)

# (relative go file, generated struct name) pairs whose `Value` field should be
# `interface{}` instead of `map[string]interface{}`.
TARGETS = [
    ("model_device_entities_device_fact.go", "DeviceEntitiesDeviceFact"),
]


def blocks(struct):
    """Return (map_form, interface_form) exact string pairs to swap for a struct.

    The struct field itself is handled separately by regex (see FIELD_*_RE),
    because gofmt controls its inter-token whitespace.
    """
    return [
        # GetValue
        (
            "// GetValue returns the Value field value if set, zero value otherwise.\n"
            "func (o *%s) GetValue() map[string]interface{} {\n"
            "\tif o == nil || IsNil(o.Value) {\n"
            "\t\tvar ret map[string]interface{}\n"
            "\t\treturn ret\n"
            "\t}\n"
            "\treturn o.Value\n"
            "}" % struct,
            "// GetValue returns the Value field value if set, zero value otherwise (both if not set or set to explicit null).\n"
            "func (o *%s) GetValue() interface{} {\n"
            "\tif o == nil {\n"
            "\t\tvar ret interface{}\n"
            "\t\treturn ret\n"
            "\t}\n"
            "\treturn o.Value\n"
            "}" % struct,
        ),
        # GetValueOk
        (
            "// GetValueOk returns a tuple with the Value field value if set, nil otherwise\n"
            "// and a boolean to check if the value has been set.\n"
            "func (o *%s) GetValueOk() (map[string]interface{}, bool) {\n"
            "\tif o == nil || IsNil(o.Value) {\n"
            "\t\treturn map[string]interface{}{}, false\n"
            "\t}\n"
            "\treturn o.Value, true\n"
            "}" % struct,
            "// GetValueOk returns a tuple with the Value field value if set, nil otherwise\n"
            "// and a boolean to check if the value has been set.\n"
            "// NOTE: If the value is an explicit nil, `nil, true` will be returned\n"
            "func (o *%s) GetValueOk() (*interface{}, bool) {\n"
            "\tif o == nil || IsNil(o.Value) {\n"
            "\t\treturn nil, false\n"
            "\t}\n"
            "\treturn &o.Value, true\n"
            "}" % struct,
        ),
        # SetValue
        (
            "// SetValue gets a reference to the given map[string]interface{} and assigns it to the Value field.\n"
            "func (o *%s) SetValue(v map[string]interface{}) {\n"
            "\to.Value = v\n"
            "}" % struct,
            "// SetValue gets a reference to the given interface{} and assigns it to the Value field.\n"
            "func (o *%s) SetValue(v interface{}) {\n"
            "\to.Value = v\n"
            "}" % struct,
        ),
    ]


def fix(path, struct):
    with open(path, "r") as fh:
        src = fh.read()

    changed = False

    # Struct field (whitespace-tolerant).
    if FIELD_MAP_RE.search(src):
        src = FIELD_MAP_RE.sub(r"\1interface{}\2", src)
        changed = True
    elif not FIELD_IFACE_RE.search(src):
        raise SystemExit(
            "postprocess: %s: could not find the Value struct field for %s.\n"
            "Generator output may have changed; update postprocess.py." % (path, struct)
        )

    for map_form, iface_form in blocks(struct):
        if map_form in src:
            src = src.replace(map_form, iface_form)
            changed = True
        elif iface_form in src:
            # already converted
            continue
        else:
            raise SystemExit(
                "postprocess: %s: could not find expected block for %s.\n"
                "Generator output may have changed; update postprocess.py.\n"
                "--- expected ---\n%s" % (path, struct, map_form)
            )

    if changed:
        with open(path, "w") as fh:
            fh.write(src)
        print("postprocess: rewrote Value -> interface{} in %s" % os.path.basename(path))
    else:
        print("postprocess: %s already up to date" % os.path.basename(path))


def main():
    for rel, struct in TARGETS:
        path = os.path.join(REPO_ROOT, rel)
        if not os.path.exists(path):
            raise SystemExit("postprocess: expected file not found: %s" % path)
        fix(path, struct)


if __name__ == "__main__":
    main()
