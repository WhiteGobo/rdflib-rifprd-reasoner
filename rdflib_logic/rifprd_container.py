import rdflib
_RIF = rdflib.Namespace("http://www.w3.org/2007/rif#")
from rdflib import RDF as _RDF

import abc
import typing as typ

class BadRifSyntax(SyntaxError):
    pass

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
    def from_rdf(cls, rdfgraph: rdflib.Graph):
        """

        :TODO: rework focusnode
        """
        name = ""
        focusnode = rdfgraph.identifier
        
        rules = []
        for result in rdfgraph.query(group.startquery):
            rules.append(group.construct(rdfgraph, **result.asdict()))
        return cls(name, focusnode, rules)

_GROUP = typ.TypeVar("group")

class group(queryable):
    cls = _RIF.Group
    startquery = """prefix rif: <http://www.w3.org/2007/rif#>
            SELECT ?focusnode WHERE {
                    ?focusnode a rif:Group.
            }"""

    sentences: typ.Any

    def __init__(self, sentences):
        self.sentences = sentences

    @classmethod
    @property
    def sentence_targets(cls):
        """Defines which classes are used for loading the sentence targets.
        Can be changed in children to change the behaviour of construct
        """
        return (forall, implies, Actionblock)

    @classmethod
    def construct(cls: _GROUP, rdfgraph:rdflib.Graph,
                  focusnode: rdflib.IdentifiedNode) -> _GROUP:
        try:
            meta, = rdfgraph.objects(focusnode, _RIF.meta)
        except ValueError as err:
            meta = None
        sentences_node, = rdfgraph.objects(focusnode, _RIF.sentences)
        sentences_list = rdflib.collection.Collection(rdfgraph, sentences_node)
        sentences = []
        for sent in sentences_list:
            for ruletype in cls.sentence_targets:
                if (sent, _RDF.type, ruletype.cls) in rdfgraph:
                    sentences.append(ruletype.construct(rdfgraph, sent))
                    break
            else:
                raise Exception("Oops something went wrong")

        return cls(sentences)


class rule(queryable):
    pass

class forall(rule):
    """

    Please note: :term:`rif:declare` will be expressed in :term:`RDF` as
        :term:`vars`. See :term:`RIF in RDF` for more information 
    """
    cls = _RIF.Forall
    declare: typ.Any
    pattern: typ.Any
    formula: typ.Any

    @classmethod
    @property
    def formula_targets(cls):
        """Defines which classes are used for loading the formula targets.
        Can be changed in children to change the behaviour of construct
        """
        actionblock = (Do_action, And_action, Atom, Frame_action)
        return (forall, implies, *actionblock)


    @classmethod
    @property
    def pattern_targets(cls):
        ATOMIC = (Atom, Equal, Member, Subclass, Frame, External)
        return (*ATOMIC, And, Or, INeg, Exists)

    @classmethod
    @property
    def declare_target(cls):
        return Var

    def __init__(self, declare, pattern, formula):
        self.declare = declare
        self.pattern = pattern
        self.formula = formula

    @classmethod
    def construct(cls, rdfgraph, focusnode):
        declare = []
        declare_listid, = rdfgraph.objects(focusnode, _RIF.vars)
        for x in rdflib.collection.Collection(rdfgraph, declare_listid):
            declare.append(cls.declare_target.construct(rdfgraph, x))
        assert len(declare) >= 1
        pattern = []
        for x in rdfgraph.objects(focusnode, _RIF.pattern):
            for qq in cls.pattern_targets:
                if (x, _RDF.type, qq.cls) in rdfgraph:
                    pattern.append(qq.construct(rdfgraph, x))
                    break
            else:
                raise Exception("Ooops something went wrong")
        formula_node, = rdfgraph.objects(focusnode, _RIF.formula)
        for ruletype in cls.formula_targets:
            if (formula_node, _RDF.type, ruletype.cls) in rdfgraph:
                formula = ruletype.construct(rdfgraph, formula_node)
                break
        try:
            formula
        except UnboundLocalError as err:
            raise Exception("Ooops something went wrong",
                            list(rdfgraph.predicate_objects(formula_node)),
                            ) from err
        return cls(declare, pattern, formula)

class implies(rule):
    cls = _RIF.Implies
    def __init__(self, if_, then_):
        self.if_ = if_
        self.then_ = then_

    def __repr__(self):
        name = type(self).__name__
        return f"<{name}:{self.if_} => {self.then_}>"

    @classmethod
    @property
    def if_targets(cls):
        """Defines which classes are used for loading the if targets.
        Can be changed in children to change the behaviour of construct
        """
        ATOMIC = (Atom, Equal, Member, Subclass, Frame, External)
        return (*ATOMIC, And, Atom, Or, INeg, Exists)

    @classmethod
    @property
    def then_targets(cls):
        """Defines which classes are used for loading the then targets.
        Can be changed in children to change the behaviour of construct
        """
        ATOMIC_ACTIONS = (Assert, Retract, Modify, Execute)
        return (*ATOMIC_ACTIONS, Do_action, And_action, Atom, Frame_action)

    @classmethod
    def construct(cls, rdfgraph, focusnode):
        if_node, = rdfgraph.objects(focusnode, getattr(_RIF, "if"))
        print(list(cls.if_targets), len(cls.if_targets))
        for i, t in enumerate(cls.if_targets):
            if (if_node, _RDF.type, t.cls) in rdfgraph:
                if_ = t.construct(rdfgraph, if_node)
                break
        then_node, = rdfgraph.objects(focusnode, getattr(_RIF, "then"))
        for t in cls.then_targets:
            if (then_node, _RDF.type, t.cls) in rdfgraph:
                then_ = t.construct(rdfgraph, then_node)
                break
        try:
            if_
            then_
        except UnboundLocalError as err:
            q, = rdfgraph.objects(if_node, _RDF.type)
            raise Exception("Ooops something went wrong",
                            q, [x.cls for x in cls.if_targets]) from err
        return cls(if_, then_)

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
        (Do_action, And_action, Atom, Frame_action)

class _action:
    pass

class Do_action(_action):
    cls = _RIF.Do

    @classmethod
    def construct(cls, rdfgraph, focusnode):
        raise NotImplementedError()
        for t in (Assert, Retract, Modify, Execute):
            pass


class And_action(_action):
    cls = _RIF.And

    @classmethod
    def construct(cls, rdfgraph, focusnode):
        raise NotImplementedError()


class Frame_action(_action):
    cls = _RIF.Frame

    @classmethod
    def construct(cls, rdfgraph, focusnode):
        raise NotImplementedError()


class New(_action):
    cls = _RIF.New

    @classmethod
    def construct(cls, rdfgraph, focusnode):
        raise NotImplementedError()


class formula(queryable):
    cls: rdflib.URIRef

class And(formula):
    cls = _RIF.And
    formulas: typ.List
    def __init__(self, formulas):
        self.formulas = formulas

    @classmethod
    @property
    def formulas_targets(cls):
        """Defines which classes are used for loading the formulas targets.
        Can be changed in children to change the behaviour of construct
        """
        return (Atom, Equal, Member, Subclass, Frame, External)

    @classmethod
    def construct(cls, rdfgraph, focusnode):
        formula_listnode, = rdfgraph.objects(focusnode, _RIF.formulas)
        formula_list = rdflib.collection.Collection(rdfgraph, formula_listnode)
        formulas = []
        for n in formula_list:
            for t in cls.formulas_targets:
                if (n, _RDF.type, t.cls) in rdfgraph:
                    formulas.append(t.construct(rdfgraph, n))
                    break
            else:
                raise Exception("Oops something went wrong", list(rdfgraph.predicate_objects(n)))
        return cls(formulas)

class Atom(formula):
    cls = _RIF.Atom
    op: typ.Any
    args: typ.Any
    def __init__(self, op, args):
        self.op = op
        self.args = args
    
    @classmethod
    @property
    def op_targets(cls):
        """Defines which classes are used for loading the op targets.
        Can be changed in children to change the behaviour of construct
        """
        return (Const, Var, List, External)

    @classmethod
    def construct(cls, rdfgraph, focusnode):
        op_node, = rdfgraph.objects(focusnode, _RIF.op)
        for t in cls.op_targets:
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
            for t in (Const, Var, List, External, None):
                if t is None:
                    raise Exception("Ooops something went wrong.")
                if (q_node, _RDF.type, t.cls) in rdfgraph:
                    args.append(t.construct(rdfgraph, q_node))
                    break
        return cls(op, args)


class Or(formula):
    cls = _RIF.Or

    @property
    def formula_targets(self):
        """Defines which classes are used for loading the formula targets.
        Can be changed in children to change the behaviour of construct
        """
        return (And, Atom, Or, INeg, Exists)

    @classmethod
    def construct(cls, rdfgraph, focusnode):
        formula_listnode, = rdfgraph.objects(focusnode, _RIF.formula)
        formula_list = rdflib.container(formula_listnode)
        formulas = []
        for n in formula_list:
            for t in cls.formula_targets:
                if (n, _RDF.type, t.cls) in rdfgraph:
                    formulas.append(t.construct(rdfgraph, n))
                    break
            else:
                raise Exception("Oops something went wrong")
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

class term(queryable):
    pass

class Const(term):
    cls = _RIF.Const
    val: str
    val_type: rdflib.URIRef
    def __init__(self, val, val_type):
        self.val = val
        self.val_type = val_type

    def __repr__(self):
        name = type(self).__name__
        return f"<{name}:{self.val}>"

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

class Var(term):
    cls = _RIF.Var
    varname: str
    def __init__(self, varname):
        self.varname = varname

    def __eq__(self, other):
        if type(self) == type(other):
            return self.varname
        else:
            return False

    @classmethod
    def construct(cls, rdfgraph, focusnode):
        try:
            varname, = rdfgraph.objects(focusnode, _RIF.varname)
        except Exception as err:
            raise Exception(list(rdfgraph.predicate_objects(focusnode))) from err
        return cls(varname)

    def __repr__(self):
        name = type(self).__name__
        return f"<{name}:{self.varname}>"

class List(term):
    pass
    cls = _RIF.List

    @classmethod
    def construct(cls, rdfgraph, focusnode):
        raise NotImplementedError()

class External(term):
    cls = _RIF.External
    def __init__(self, op, args):
        self.op = op
        self.args = args

    @classmethod
    @property
    def op_targets(cls):
        return (Const, Var, List, External)

    @classmethod
    @property
    def args_targets(cls):
        return (Const, Var, List, External)

    @classmethod
    def construct(cls, rdfgraph, focusnode):
        #This shouldnt be needed, because this should be checked via other tool
        content_node, = rdfgraph.objects(focusnode, _RIF.content)
        #this depends on if this is used in an execute or not
        #very strange i need to look at this further
        assert (content_node, _RDF.type, _RIF.Atom) in rdfgraph\
                or (content_node, _RDF.type, _RIF.Expr) in rdfgraph

        op_node, = rdfgraph.objects(content_node, _RIF.op)
        for t in cls.op_targets:
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
            for t in cls.args_targets:
                if (q_node, _RDF.type, t.cls) in rdfgraph:
                    args.append(t.construct(rdfgraph, q_node))
                    break
            else:
                raise Exception("Ooops something went wrong.")
        return cls(op, args)


class Atomic(queryable):
    pass

class Equal(Atomic):
    cls = _RIF.Equal
    def __init__(self, left, right):
        self.left = left
        self.right = right

    @classmethod
    @property
    def side_targets(cls):
        return (Const, Var, List, External)

    @classmethod
    def construct(cls, rdfgraph, focusnode):
        left_node, = rdfgraph.objects(focusnode, _RIF.left)
        for t in cls.side_targets:
            if (left_node, _RDF.type, t.cls) in rdfgraph:
                left = t.construct(rdfgraph, left_node)
                break
        right_node, = rdfgraph.objects(focusnode, _RIF.right)
        for t in cls.side_targets:
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
    instance: typ.Any
    class_: typ.Any

    def __init__(self, instance, class_):
        self.instance = instance
        self.class_ = class_

    def __repr__(self):
        name = type(self).__name__
        return f"<{name}:{self.instance}:{self.class_}>"

    @classmethod
    @property
    def instance_targets(cls):
        return (Const, Var, List, External)

    @classmethod
    def construct(cls, rdfgraph, focusnode):
        instance_node, = rdfgraph.objects(focusnode, _RIF.instance)
        class_node, = rdfgraph.objects(focusnode, getattr(_RIF, "class"))
        for t in cls.instance_targets:
            if (instance_node, _RDF.type, t.cls) in rdfgraph:
                instance = t.construct(rdfgraph, instance_node)
                break
        for t in cls.instance_targets:
            if (class_node, _RDF.type, t.cls) in rdfgraph:
                class_ = t.construct(rdfgraph, class_node)
                break
        try:
            return cls(instance, class_)
        except UnboundLocalError as err:
            raise Exception("Ooops something went wrond.", class_node) from err

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


class Action(queryable):
    pass

class Assert(Action):
    cls = _RIF.Assert
    target: typ.Any
    def __init__(self, target):
        self.target = target

    @classmethod
    def construct(cls, rdfgraph, focusnode):
        target_node, = rdfgraph.objects(focusnode, _RIF.target)
        for t in (Atom, Frame, Member):
            if (target_node, _RDF.type, t.cls) in rdfgraph:
                target = t.construct(rdfgraph, target_node)
                break
        try:
            return cls(target)
        except UnboundLocalError as err:
            raise BadRifSyntax("couldnt find target") from err

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
    cls = _RIF.Execute
    def __init__(self, target):
        self.target = target

    @classmethod
    def construct(cls, rdfgraph, focusnode):
        target_node, = rdfgraph.objects(focusnode, _RIF.target)
        assert (target_node, _RDF.type, _RIF.Atom)
        target = Atom.construct(rdfgraph, target_node)
        return cls(target)
