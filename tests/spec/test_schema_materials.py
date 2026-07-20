from ncad.spec.schema_validator import SchemaValidator


def test_material_fields_validate():
    doc = {"units": "mm",
        "materials_library": "lib/materials.hocon",
        "materials": {"brass": {"physical": {"density": 8500}}},
        "parts": {
            "p": {
                "profile": "solid",
                "material": "steel_1018",
                "features": [
                    {"id": "sk", "op": "sketch", "plane": "XY",
                     "elements": [{"id": "r", "type": "rectangle", "w": 10, "h": 10}]},
                    {"id": "blk", "op": "extrude", "profile": "sk", "distance": 5,
                     "material": "aluminium_6061", "mat_data": {"physical": {"density": 2600}}},
                ],
            }
        },
    }
    assert SchemaValidator().validate(doc) == []
