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



import importlib.resources
from . import test_rif
input8bld = importlib.resources.files(test_rif).joinpath("bld-8.ttl")

class TestParsingPlugin(unittest.TestCase):
    def setUp(self):
        pass
        #rdflib.plugin.register("rifxml", rdflib.parser.Parser,
        #                       "rdflib_rif", "RIFXMLParser")

    def test_asdf(self):
        g = rdflib.Graph()
        g.parse(input8bld)
        print(g.serialize())

    def test_pyrete(self):
        return
        silver = "silver"
        gold = "gold"
        new = "new"
        bronze = "bronze"
        shopping_cart = "sc"
        worth = "worth"
        typeof = "typeof"
        status = "status"

        s, p, o = 'subject', 'predicate', 'object'
        with rls.ruleset("test"):
            @rls.when_all(rls.m.subject == 'World',
                          #rls.c.first << rls.m.subject == 'World',
                          #rls.c.second << rls.c.first.object == rls.m.subject,
                          )
            def say_hello(c: "durable.engine.closure"):
                print(c)
            @rls.when_all(rls.m.subject,
                          rls.m.predicate,
                          rls.m.object)
            def ignore(c):
                pass
        for f in [{s: "world", p:"a", o:"introobject"},
                  {s: "World", p:"ab", o:"introobject"},
                  {s: "world", p:"ab", o:"introobject"},
                  {s: "World", p:"ab", o:"introobject"},
                  ]:
            try:
                rls.assert_fact('test', f)
            except rls_engine.MessageNotHandledException: pass
            except rls_engine.MessageObservedException: pass
        print( rls.get_facts('test') )

    def test_row(self):
        with rls.ruleset('test2'):
            @rls.when_all(rls.m.number < 5,
                          #rls.c.first << rls.m.subject == 'World',
                          #rls.c.second << rls.c.first.object == rls.m.subject,
                          )
            def say_hello(c: "durable.engine.closure"):
                n1 = c.m.number+1
                print(n1)
                print("brubru")
                n = c.m.q
                if n is None:
                    n = 0
                try:
                    #c.assert_fact({"number": c.m.number+1, "q":n+1})
                    print("qwe")
                    c.assert_fact({"number": n1, "q":n+1})
                    print("qwe2")
                except rls_engine.MessageNotHandledException: pass
                except rls_engine.MessageObservedException: pass
                print(c.m, {"number": n1})
                c.retract_fact(c.m)

            @rls.when_all(rls.m.number == 5,
                          #rls.c.first << rls.m.subject == 'World',
                          #rls.c.second << rls.c.first.object == rls.m.subject,
                          )
            def say_helloq(c: "durable.engine.closure"):
                pass
        try:
            rls.assert_facts('test2', [{"number":1},
                                       {"number":-3},
                                      ])
        except rls_engine.MessageNotHandledException: pass
        except rls_engine.MessageObservedException: pass
        
        print("myfacts: ", rls.get_facts('test2') )



if __name__=='__main__':
    logging.basicConfig( level=logging.WARNING )
    #flowgraph_logger = logging.getLogger("find_generationpath.Flowgraph")
    #graphstate_logger = logging.getLogger("find_generationpath.Graphstate")
    #flowgraph_logger.setLevel(logging.DEBUG)
    #graphstate_logger.setLevel(logging.DEBUG)
    logger.setLevel(logging.DEBUG)
    unittest.main()
