import rdflib
import typing as typ
import abc

import durable.lang as rls
import durable.engine as rls_engine


_DURU = rdflib.Namespace("http://example.com/durablerules#")
_RIF = rdflib.Namespace("http://www.w3.org/2007/rif#")
from rdflib import RDF as _RDF
from . import rifprd_container as rif_cont

_grouptype = typ.TypeVar("group")

class NotLocatedVariable(Exception):
    """Is thrown when trying to get the location of a certain variable
    but it is not yet given
    """

class _constructable(abc.ABC):
    @abc.abstractmethod
    def construct(cls: _grouptype,
                             rdfgraph: rdflib.Graph,
                             identifier:rdflib.IdentifiedNode,
                             ) -> _grouptype:
        ...

class rule_container:
    def __init__(self, sentences):
        self.sentences = sentences


class rule_generator:
    def generate_rule(self, ruleset: typ.Union[str, rls.ruleset]):
        if isinstance(ruleset, str):
            ruleset = rls.ruleset(ruleset)
        elif isinstance(ruleset, rls.ruleset):
            pass
        else:
            raise TypeError("ruleset must be str or durable.lang.ruleset. "
                            "Got %s" %type(ruleset))
        variables = set(self.condition.get_variables())
        variables = {getattr(rls.c, v): v for v in variables}
        q = self.process_forall()
        #@rls.when_all(rls.m.subject,rls.m.predicate,rls.m.object)
        try:
            condition = self.process_condition()
        except Exception:
            condition = None
        actions = self.process_actions()
        with ruleset:
            if condition is None:
                @rls.when_all(*q)
                def my_function(c: rls_engine.closure):
                    for x in actions:
                        x(c)
            else:
                raise NotImplementedError("no conditions supported yet")
                @rls.when_all(*q)
                def my_function(c: rls_engine.closure):
                    if condition(c):
                        for x in actions:
                            x(c)

    def process_forall(self):
        raise NotImplementedError()

    def process_condition(self):
        raise NotImplementedError()

    def process_actions(self):
        raise NotImplementedError()



class rule(rule_generator, _constructable):
    def __init__(self, action, forall=None, condition=None):
        self.action = action
        self.forall = forall
        self.condition = condition

    @classmethod
    def construct(cls: _grouptype,
                             rdfgraph: rdflib.Graph,
                             identifier: rdflib.IdentifiedNode,
                             ) -> _grouptype:
        try:
            id_forall, = rdfgraph.objects(identifier, _DURU.sentences)
        except ValueError:
            id_forall = None
        try:
            id_condition, = rdfgraph.objects(identifier, _DURU.condition)
        except ValueError:
            id_condition = None
        try:
            id_action, = rdfgraph.objects(identifier, _DURU.action)
        except ValueError as err:
            raise SyntaxError("Each rule must have exactly one action.")\
                    from err
        extraargs = {}
        if id_forall is not None:
            forall = []
            extraargs["forall"] = forall
            for x in rdflib.collection.Collection(rdfgraph, id_forall):
                for cc in ():
                    if (x, _RDF.type, cc.cls) in rdfgraph:
                        forall.append(cc.construct(rdfgraph, x))
        if id_condition is not None:
            for cc in (rif_cont.Atom, rif_cont.Equal, rif_cont.Member,
                       rif_cont.Subclass, rif_cont.Frame,
                       rif_cont.External,
                       rif_cont.And, rif_cont.Or,
                       rif_cont.INeg, rif_cont.Exists):
                if (id_condition, _RDF.type, cc.cls) in rdfgraph:
                    extraargs["condition"] = cc.construct(rdfgraph, id_condition)
        for x in rdflib.collection.Collection(rdfgraph, id_action):
            for cc in (rif_cont.Assert, rif_cont.Retract, rif_cont.Execute):
                if (x, _RDF.type, cc.cls) in rdfgraph:
                    action = cc.construct(rdfgraph, x)
                break
        return cls(action, **extraargs)


class Member(rif_cont.Member):
    #instance: typ.Any
    #class_: typ.Any
    def _generate_pattern(self, fact_container: "_fact_container"):
        fact = fact_container.new_fact()
        if isinstance(self.instance, rif_cont.Var):
            varname = self.instance.varname
            try:
                var_locator = fact_container.get_var_locator(varname)
                fact.add_constraint(var_locator == fact.subj)
            except NotLocatedVariable:
                fact.add_var_location(varname, "subj")
        fact.add_constraint(fact.pred == _RDF.type)
        #obj = self.class_._generate_pattern(varname2var)
        yield fact << rls.m.pred == pred
        yield fact.subj == subj
        yield fact.obj == obj

class Atom(rif_cont.Atom):
    pass

class Equal(rif_cont.Equal):
    pass

class Subclass(rif_cont.Subclass):
    pass

class Frame(rif_cont.Frame):
    pass

class External(rif_cont.External):
    pass

class And(rif_cont.And):
    pass

class Or(rif_cont.Or):
    pass

class INeg(rif_cont.INeg):
    pass

class Exists(rif_cont.Exists):
    pass

class forall(rif_cont.forall):
    pattern_targets = (Atom, Equal, Member, Subclass, Frame, External,
                       And, Or, INeg, Exists)

    def generate_rule(self, ruleset):
        if isinstance(ruleset, str):
            ruleset = rls.ruleset(ruleset)
        elif isinstance(ruleset, rls.ruleset):
            pass
        else:
            raise TypeError("ruleset must be str or durable.lang.ruleset. "
                            "Got %s" %type(ruleset))
        varname2var = {var.varname: getattr(rls.c, var.varname)
                       for var in self.declare}
        factcontainer = _fact_container()
        patterns = list(self._generate_pattern(factcontainer))
        action = list(self._generate_actions(factcontainer))
        with ruleset:
            @rls.whan_all(*patterns)
            def automatic_processed_rule(c: rls_engine.closure):
                action()

    def _generate_pattern(self, factcontainer):
        #self.variables
        #self.pattern
        for part in self.pattern:
            for x in part._generate_pattern(factcontainer):
                yield x

    def _generate_actions(self, factcontainer):
        #self.variables
        #self.formula
        raise NotImplementedError()

class implies(rif_cont.implies):
    def generate_rule(self, ruleset):
        if isinstance(ruleset, str):
            ruleset = rls.ruleset(ruleset)
        elif isinstance(ruleset, rls.ruleset):
            pass
        else:
            raise TypeError("ruleset must be str or durable.lang.ruleset. "
                            "Got %s" %type(ruleset))
        raise NotImplementedError()

class Actionblock(rif_cont.implies):
    def generate_rule(self, ruleset):
        if isinstance(ruleset, str):
            ruleset = rls.ruleset(ruleset)
        elif isinstance(ruleset, rls.ruleset):
            pass
        else:
            raise TypeError("ruleset must be str or durable.lang.ruleset. "
                            "Got %s" %type(ruleset))
        raise NotImplementedError()

class group(rif_cont.group):
    sentence_targets = (forall, implies, Actionblock)

    def generate_ruleset(self, ruleset: typ.Union[str, rls.ruleset]):
        if isinstance(ruleset, str):
            ruleset = rls.ruleset(ruleset)
        elif isinstance(ruleset, rls.ruleset):
            pass
        else:
            raise TypeError("ruleset must be str or durable.lang.ruleset. "
                            "Got %s" %type(ruleset))
        for s in self.sentences:
            s.generate_rule(ruleset)


class _fact:
    def __init__(self, fact_container, name):
        self.name = name
        self.durable_reference = getattr(rls.c, self.name)
        self.fact_container = fact_container
        self.initialized = False

    def add_var_location(self, varname, location):
        if self.initialized:
            getattr(self.durable_reference, location)
        else:
            getattr(rls.m, location)
            self.initialized = True
        locator 
        self.fact_container
        


class _fact_container:
    def __init__(self):
        self._i = 0
        self._var_locations = {}

    def __iter__(self):
        raise NotImplementedError()

    def __contains__(self, thing):
        raise NotImplementedError()

    def get_locator_of_varname(self, varname):
        raise NotImplementedError()

    def get_var_locator(self, varname):
        try:
            self._var_locations[varname]
        except KeyError as err:
            raise NotLocatedVariable() from err

    def new_fact(self):
        factname = "f{self._i}"
        self._i += 1
        return _fact(self, factname)
