import rdflib
_RIF = rdflib.Namespace("http://www.w3.org/2007/rif#")
from rdflib import RDF as _RDF

import abc
import typing as typ

class queryable(abc.ABC):
    startquery: str
    """Query to find a startingpoint for construction of this type of rule"""

class ruleset:
    name: str
    focusnode: rdflib.IdentifiedNode
    def __init__(self, name, focusnode=None, rules=[]):
        self.name = name
        self.focusnode = focusnode
        self.rules = list(rules)

    @classmethod
    def from_rdf(self, rdfgraph: rdflib.Graph):
        """

        :TODO: rework focusnode
        """
        focusnode = rdfgraph.identifier
        
        for result in rdfgraph.query(group.startquery):
            q = group.construct(rdfgraph, **result.asdict())
            raise Exception(q)

_GROUP = typ.TypeVar("group")

class group(queryable):
    startquery = """prefix rif: <http://www.w3.org/2007/rif#>
            SELECT ?focusnode WHERE {
                    ?focusnode a rif:Group.
            }"""

    def __init__(self, sentences):
        self.sentences = sentences

    @classmethod
    def construct(cls: _GROUP, rdfgraph:rdflib.Graph,
                  focusnode: rdflib.IdentifiedNode) -> _GROUP:
        meta, = rdfgraph.objects(focusnode, _RIF.meta)
        sentences_node, = rdfgraph.objects(focusnode, _RIF.sentences)
        sentences_list = rdflib.collection.Collection(rdfgraph, sentences_node)
        sentences = []
        for sent in sentences_list:
            for ruletype in (forall, implies, Actionblock, None):
                if ruletype is None:
                    raise Exception("Oops something went wrong")
                if (sent, _RDF.type, ruletype.cls) in rdfgraph:
                    sentences.append(ruletype.construct(rdfgraph, sent))
                    break

        return cls(sentences)


class rule(abc.ABC):
    pass

class forall(rule):
    cls = _RIF.Forall
    @classmethod
    def construct(cls, rdfgraph, focusnode):
        vars_node, = rdfgraph.objects(focusnode, _RIF.vars)
        vars_ = []
        rdflib.collection.Collection(rdfgraph, vars_node)
        formula_node, = rdfgraph.objects(focusnode, _RIF.formula)
        for ruletype in (forall, implies, Actionblock):
            if (formula_node, _RDF.type, ruletype.cls) in rdfgraph:
                formula = ruletype.construct(formula_node, rdfgraph)
                break
        try:
            formula
        except UnboundLocalError as err:
            raise Exception("Ooops something went wrong",
                            list(rdfgraph.predicate_objects(formula_node)),
                            ) from err
        return cls(vars_, formula)

class implies(rule):
    cls = _RIF.Implies

    @classmethod
    def construct(cls, focusnode, rdfgraph):
        if_node, = rdfgraph.objects(focusnode, getattr(_RIF, "if"))
        then_node, = rdfgraph.objects(focusnode, getattr(_RIF, "then"))
        for t in (And, AtomicFormula, Or, INeg, Exists):
            if (if_node, _RDF.type, t.cls) in rdfgraph:
                if_ = t.construct(if_node, rdfgraph)
                break

        try:
            if_, then_
        except UnboundLocalError as err:
            raise Exception("Ooops something went wrong") from err
        return cls(focusnode, if_, then_)

class Actionblock(rule):
    cls = _RIF.Actionblock

    @classmethod
    def construct(cls, rdfgraph, focusnode):
        raise NotImplementedError()


class formula(abc.ABC):
    cls: rdflib.URIRef

class And(formula):
    cls = _RIF.And

    @classmethod
    def construct(cls, focusnode, rdfgraph):
        formula_listnode, = rdfgraph.objects(focusnode, _RIF.formulas)
        formula_list = rdflib.collection.Collection(rdfgraph, formula_listnode)
        formulas = []
        for n in formula_list:
            for t in (And, AtomicFormula, Or, INeg, Exists, None):
                if t is None:
                    raise Exception("Oops something went wrong")
                if (n, _RDF.type, t.cls) in rdfgraph:
                    formulas.append(t.construct(n, rdfgraph))
                    break
        return cls(focusnode, formulas)

class AtomicFormula(formula):
    cls = _RIF.Atom
    
    @classmethod
    def construct(cls, focusnode, rdfgraph):
        _RIF.op
        _RIF.args
        raise NotImplementedError()

        return cls(focusnode, args, op)


class Or(formula):
    cls = _RIF.Or

    @classmethod
    def construct(cls, focusnode, rdfgraph):
        formula_listnode, = rdfgraph.objects(focusnode, _RIF.formula)
        formula_list = rdflib.container(formula_listnode)
        formulas = []
        for n in formula_list:
            for t in (And, AtomicFormula, Or, INeg, Exists, None):
                if t is None:
                    raise Exception("Oops something went wrong")
                if (n, _RDF.type, t.cls) in rdfgraph:
                    formulas.append(t.construct(n, rdfgraph))
                    break
        return cls(focusnode, formulas)

class INeg(formula):
    cls = _RIF.INeg

    @classmethod
    def construct(cls, focusnode, rdfgraph):
        raise NotImplementedError()

class Exists(formula):
    cls = _RIF.Exists

    @classmethod
    def construct(cls, focusnode, rdfgraph):
        raise NotImplementedError()

class term(abc.ABC):
    pass

class Const(term):
    cls = _RIF.Const

    @classmethod
    def construct(cls, focusnode, rdfgraph):
        raise NotImplementedError()

class Var(term):
    cls = _RIF.Const

    @classmethod
    def construct(cls, focusnode, rdfgraph):
        raise NotImplementedError()

class List(term):
    pass
    cls = _RIF.Const

    @classmethod
    def construct(cls, focusnode, rdfgraph):
        raise NotImplementedError()

class External(term):
    pass
    cls = _RIF.Const

    @classmethod
    def construct(cls, focusnode, rdfgraph):
        raise NotImplementedError()

class Atomic(abc.ABC):
    pass

class Atom(Atomic):
    cls = _RIF.Atom

    @classmethod
    def construct(cls, focusnode, rdfgraph):
        raise NotImplementedError()

class Equal(Atomic):
    cls = _RIF.Equal

    @classmethod
    def construct(cls, focusnode, rdfgraph):
        raise NotImplementedError()

class Member(Atomic):
    cls = _RIF.Member

    @classmethod
    def construct(cls, focusnode, rdfgraph):
        raise NotImplementedError()

class Subclass(Atomic):
    cls = _RIF.Subclass

    @classmethod
    def construct(cls, focusnode, rdfgraph):
        raise NotImplementedError()

class Frame(Atomic):
    cls = _RIF.Frame

    @classmethod
    def construct(cls, focusnode, rdfgraph):
        raise NotImplementedError()

class External(Atomic):
    cls = _RIF.External

    @classmethod
    def construct(cls, focusnode, rdfgraph):
        raise NotImplementedError()
