import rdflib_logic

import unittest
import logging
logger = logging.getLogger(__name__)

import rdflib
import rdflib.serializer
import rdflib.parser
import rdflib.plugin

from rdflib import compare
import durable.lang as rls
import durable.engine as rls_engine

from rdflib_logic import group

import importlib.resources
from . import durablerules_rdf
inputalpha = importlib.resources.files(durablerules_rdf).joinpath("test1.ttl")

_DURU = rdflib.Namespace("http://example.com/durable_rules#")
from rdflib import RDF as _RDF

class TestParsingPlugin(unittest.TestCase):
    def setUp(self):
        pass
        #rdflib.plugin.register("rifxml", rdflib.parser.Parser,
        #                       "rdflib_rif", "RIFXMLParser")

    def test_alpha(self):
        g = rdflib.Graph()
        g.parse(inputalpha)
        print(g.serialize())
        mygroup_id, = g.subjects(_RDF.type, group.cls)
        print(repr(mygroup_id))
        mygroup = group.construct(g, mygroup_id)
        print(mygroup)
        mygroup.generate_ruleset("myrules")


if __name__=='__main__':
    logging.basicConfig( level=logging.WARNING )
    #flowgraph_logger = logging.getLogger("find_generationpath.Flowgraph")
    #graphstate_logger = logging.getLogger("find_generationpath.Graphstate")
    #flowgraph_logger.setLevel(logging.DEBUG)
    #graphstate_logger.setLevel(logging.DEBUG)
    logger.setLevel(logging.DEBUG)
    unittest.main()
