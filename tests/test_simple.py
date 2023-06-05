import rdflib_logic

import unittest
import logging
logger = logging.getLogger(__name__)

import rdflib
import rdflib.serializer
import rdflib.parser
import rdflib.plugin

from rdflib import compare

import py_rete as rete
#from py_rete import conditions
from py_rete.conditions import Cond
from py_rete.conditions import Ncc
from py_rete.common import WME
from py_rete.common import Token
from py_rete.common import V
from py_rete.fact import Fact
from py_rete.network import ReteNetwork
from py_rete.production import Production
from py_rete.conditions import AND
from py_rete.conditions import Bind
from py_rete.conditions import OR
from py_rete.conditions import NOT
from py_rete.conditions import Filter


#import importlib.resources
#from . import data
#input8bld = importlib.resources.files(data).joinpath("bld-8.rif")
#output8bld = importlib.resources.files(data).joinpath("bld-8.ttl")

class TestParsingPlugin(unittest.TestCase):
    def setUp(self):
        pass
        #rdflib.plugin.register("rifxml", rdflib.parser.Parser,
        #                       "rdflib_rif", "RIFXMLParser")

    def test_pyrete(self):
        @Production(Fact(lastname = V('ln')))
        def found(ln):
            print(f"brubru : {ln}")

        net = ReteNetwork()
        net.add_production(found)
        f1 = Fact(lastname="sdf")
        net.add_fact(f1)

        net.run(2)


if __name__=='__main__':
    logging.basicConfig( level=logging.WARNING )
    #flowgraph_logger = logging.getLogger("find_generationpath.Flowgraph")
    #graphstate_logger = logging.getLogger("find_generationpath.Graphstate")
    #flowgraph_logger.setLevel(logging.DEBUG)
    #graphstate_logger.setLevel(logging.DEBUG)
    logger.setLevel(logging.DEBUG)
    unittest.main()
