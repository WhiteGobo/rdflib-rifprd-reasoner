#!/usr/bin/env python
from lxml import etree

with open("PRD.xsd", "r") as f:
    schema_doc = etree.parse(f)
schema = etree.XMLSchema(schema_doc)

with open("bld-8.rif", "r") as f:
    doc = etree.parse(f)
print(schema.validate(doc))
schema.assertValid(doc)
