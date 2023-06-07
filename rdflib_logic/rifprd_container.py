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
        for ruletype in (forall, implies, Do_action, And_action, Atom_action, Frame_Action):
            if (formula_node, _RDF.type, ruletype.cls) in rdfgraph:
                formula = ruletype.construct(rdfgraph, formula_node)
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
    def construct(cls, rdfgraph, focusnode):
        if_node, = rdfgraph.objects(focusnode, getattr(_RIF, "if"))
        for t in (And, AtomicFormula, Or, INeg, Exists):
            if (if_node, _RDF.type, t.cls) in rdfgraph:
                if_ = t.construct(rdfgraph, if_node)
                break
        then_node, = rdfgraph.objects(focusnode, getattr(_RIF, "then"))
        for t in (Do_action, And_action, Atom_action, Frame_Action):
            if (then_node, _RDF.type, t.cls) in rdfgraph:
                then_node = t.construct(rdfgraph, then_node)
                break
        try:
            if_, then_
        except UnboundLocalError as err:
            raise Exception("Ooops something went wrong") from err
        return cls(focusnode, if_, then_)

class Actionblock(rule):
    """This is an unconditional actionblock as specified here
    `https://www.w3.org/TR/rif-prd/#ACTION_BLOCK_2`_

    This might be just a placeholder for (do, and, atom, frame) which are the normal actions.
    there is no syntax specified in link above, but im not sure yet. Hence this class still exists.
    """
    cls = _RIF.Actionblock

    @classmethod
    def construct(cls, rdfgraph, focusnode):
        raise NotImplementedError()
        (Do_action, And_action, Atom_action, Frame_Action)

class _action:
    pass

class Do_action(_action):
    @classmethod
    def construct(cls, rdfgraph, focusnode):
        raise NotImplementedError()
        for t in (Assert, Retract, Modify, Execute):
            pass

class And_action(_action):
    pass

class Atom_action(_action):
    pass

class Frame_action(_action):
    pass

class New(_action):
    pass
    

class formula(abc.ABC):
    cls: rdflib.URIRef

class And(formula):
    cls = _RIF.And
    formulas: typ.List
    def __init__(self, formulas):
        self.formulas = formulas

    @classmethod
    def construct(cls, rdfgraph, focusnode):
        formula_listnode, = rdfgraph.objects(focusnode, _RIF.formulas)
        formula_list = rdflib.collection.Collection(rdfgraph, formula_listnode)
        formulas = []
        for n in formula_list:
            for t in (Atom, Equal, Member, Subclass, Frame, External_atomic, None):
                if t is None:
                    raise Exception("Oops something went wrong", list(rdfgraph.predicate_objects(n)))
                if (n, _RDF.type, t.cls) in rdfgraph:
                    formulas.append(t.construct(rdfgraph, n))
                    break
        return cls(formulas)

class AtomicFormula(formula):
    cls = _RIF.Atom
    op: typ.Any
    args: typ.Any
    def __init__(self, op, args):
        self.op = op
        self.args = args
    
    @classmethod
    def construct(cls, rdfgraph, focusnode):
        op_node, = rdfgraph.objects(focusnode, _RIF.op)
        for t in (Const_term, Var_term, List_term, External_term):
            if (op_node, _RDF.type, t.cls) in rdfgraph:
                op = t.construct(rdfgraph, op_node)
                break
        try:
            op
        except UnboundLocalError as err:
            raise Exception("Ooops something went wrond.") from err
        args_listnode, = rdfgraph.objects(focusnode, _RIF.args)
        args_list = rdflib.collection.Collection(rdfgraph, args_listnode)
        args = []
        for q_node in args_list:
            for t in (Const_term, Var_term, List_term, External_term, None):
                if t is None:
                    raise Exception("Ooops something went wrong.")
                if (q_node, _RDF.type, t.cls) in rdfgraph:
                    args.append(t.construct(rdfgraph, q_node))
                    break
        return cls(op, args)


class Or(formula):
    cls = _RIF.Or

    @classmethod
    def construct(cls, rdfgraph, focusnode):
        formula_listnode, = rdfgraph.objects(focusnode, _RIF.formula)
        formula_list = rdflib.container(formula_listnode)
        formulas = []
        for n in formula_list:
            for t in (And, AtomicFormula, Or, INeg, Exists, None):
                if t is None:
                    raise Exception("Oops something went wrong")
                if (n, _RDF.type, t.cls) in rdfgraph:
                    formulas.append(t.construct(rdfgraph, n))
                    break
        return cls(focusnode, formulas)

class INeg(formula):
    cls = _RIF.INeg

    @classmethod
    def construct(cls, rdfgraph, focusnode):
        raise NotImplementedError()

class Exists(formula):
    cls = _RIF.Exists

    @classmethod
    def construct(cls, rdfgraph, focusnode):
        raise NotImplementedError()

class term(abc.ABC):
    pass

class Const_term(term):
    cls = _RIF.Const
    val: str
    val_type: rdflib.URIRef
    def __init__(self, val, val_type):
        self.val = val
        self.val_type = val_type

    @classmethod
    def construct(cls, rdfgraph, focusnode):
        val, val_type = None, None
        for val_type in (_RIF.constIRI, _RIF.value, _RIF.constname):
            try:
                val, = rdfgraph.objects(focusnode, val_type)
            except ValueError:
                pass
        try:
            val
        except UnboundLocalError as err:
            raise Exception("Oops something went wrong")
        return cls(val, val_type)

class Var_term(term):
    cls = _RIF.Var
    varname: str
    def __init__(self, varname):
        self.varname = varname

    @classmethod
    def construct(cls, rdfgraph, focusnode):
        varname, = rdfgraph.objects(focusnode, _RIF.varname)
        return cls(varname)

class List_term(term):
    pass
    cls = _RIF.List

    @classmethod
    def construct(cls, rdfgraph, focusnode):
        raise NotImplementedError()

class _External:
    cls = _RIF.External
    def __init__(self, op, args):
        self.op = op
        self.args = args

    @classmethod
    def construct(cls, rdfgraph, focusnode):
        content_node, = rdfgraph.objects(focusnode, _RIF.content)
        op_node, = rdfgraph.objects(content_node, _RIF.op)
        for t in (Const_term, Var_term, List_term, External_term):
            if (op_node, _RDF.type, t.cls) in rdfgraph:
                op = t.construct(rdfgraph, op_node)
                break
        try:
            op
        except UnboundLocalError as err:
            raise Exception("Ooops something went wrond.") from err
        args_listnode, = rdfgraph.objects(content_node, _RIF.args)
        args_list = rdflib.collection.Collection(rdfgraph, args_listnode)
        args = []
        for q_node in args_list:
            for t in (Const_term, Var_term, List_term, External_term, None):
                if t is None:
                    raise Exception("Ooops something went wrong.")
                if (q_node, _RDF.type, t.cls) in rdfgraph:
                    args.append(t.construct(rdfgraph, q_node))
                    break
        return cls(op, args)

class External_term(_External, term):
    @classmethod
    def construct(cls, rdfgraph, focusnode):
        #This shouldnt be needed, because this should be checked via other tool
        content_node, = rdfgraph.objects(focusnode, _RIF.content)
        assert (content_node, _RDF.type, _RIF.Expr) in rdfgraph
        return super().construct(rdfgraph, focusnode)

class Atomic(abc.ABC):
    pass

class Atom(AtomicFormula, Atomic):
    pass

class Equal(Atomic):
    cls = _RIF.Equal
    def __init__(self, left, right):
        self.left = left
        self.right = right

    @classmethod
    def construct(cls, rdfgraph, focusnode):
        left_node, = rdfgraph.objects(focusnode, _RIF.left)
        for t in (Const_term, Var_term, List_term, External_term):
            if (left_node, _RDF.type, t.cls) in rdfgraph:
                left = t.construct(rdfgraph, left_node)
                break
        right_node, = rdfgraph.objects(focusnode, _RIF.right)
        for t in (Const_term, Var_term, List_term, External_term):
            if (right_node, _RDF.type, t.cls) in rdfgraph:
                right = t.construct(rdfgraph, right_node)
                break
        try:
            right, left
        except UnboundLocalError as err:
            raise Exception("Ooops something went wrond.") from err
        return cls(left, right)

class Member(Atomic):
    cls = _RIF.Member

    @classmethod
    def construct(cls, rdfgraph, focusnode):
        raise NotImplementedError()

class Subclass(Atomic):
    cls = _RIF.Subclass

    @classmethod
    def construct(cls, rdfgraph, focusnode):
        raise NotImplementedError()

class Frame(Atomic):
    cls = _RIF.Frame

    @classmethod
    def construct(cls, rdfgraph, focusnode):
        raise NotImplementedError()

class External_atomic(_External, Atomic):
    @classmethod
    def construct(cls, rdfgraph, focusnode):
        #This shouldnt be needed, because this should be checked via other tool
        content_node, = rdfgraph.objects(focusnode, _RIF.content)
        assert (content_node, _RDF.type, _RIF.Atom) in rdfgraph
        return super().construct(rdfgraph, focusnode)


class Action:
    pass

class Assert(Action):
    cls = _RIF.Assert
    target: typ.Any
    def __init__(self, target):
        self.target = target

    @classmethod
    def construct(cls, rdfgraph, focusnode):
        target_node = rdfgraph.objects(focusnode, _RIF.target)
        raise NotImplementedError("atom frame member")
        for t in (Atom, Frame, Member):
            if (target_node, _RDF.type, t.cls) in rdfgraph:
                target = t.construct(rdfgraph, target_node)
                break
        return cls(target)

class Retract(Action):
    cls = _RIF.Retract
    target: typ.Any
    def __init__(self, targets):
        self.targets = targets

    @classmethod
    def construct(cls, rdfgraph, focusnode):
        target_listnode = rdfgraph.objects(focusnode, _RIF.target)
        raise NotImplementedError("atom frame member")
        target_list = rdflib.collection.Collection(rdfgraph, target_listnode)
        targets = []
        for target_node in target_list:
            for t in (Atom, Frame, Member):
                if (target_node, _RDF.type, t.cls) in rdfgraph:
                    targets.append(t.construct(rdfgraph, target_node))
                    break
        return cls(targets)

class Modify(Action):
    cls = _RIF.Retract

    @classmethod
    def construct(cls, rdfgraph, focusnode):
        raise NotImplementedError()
        return cls()

class Execute(Action):
    cls = _RIF.Assert

    @classmethod
    def construct(cls, rdfgraph, focusnode):
        raise NotImplementedError()
        return cls()
