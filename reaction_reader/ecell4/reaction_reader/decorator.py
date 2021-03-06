import copy
import types
import numbers
import warnings
import functools

import parseobj

import ecell4.core


def generate_Species(obj):
    if isinstance(obj, parseobj.AnyCallable):
        obj = obj._as_ParseObj()

    if isinstance(obj, parseobj.ParseObj):
        elems = obj._elements()
        if len(elems) != 1:
            raise NotImplementedError, (
                'complex is not allowed yet; "%s"' % str(obj))
        if (elems[0].args is not None
            or elems[0].kwargs is not None
            or elems[0].key is not None
            or elems[0].modification is not None):
            raise NotImplementedError, (
                'modification is not allowed yet; "%s"' % str(obj))
        return (ecell4.core.Species(elems[0].name), )
    elif isinstance(obj, parseobj.InvExp):
        return (None, )
    elif isinstance(obj, parseobj.AddExp):
        subobjs = obj._elements()
        return tuple(generate_Species(subobj)[0] for subobj in subobjs)

    raise RuntimeError, 'invalid expression; "%s" given' % str(obj)

def generate_ReactionRule(lhs, rhs, k=0.0):
    if len(lhs) == 0:
        if len(rhs) != 1:
            raise RuntimeError, (
                "the number of products must be 1; %d given" % len(rhs))
        return ecell4.core.create_synthesis_reaction_rule(rhs[0], k)
    elif len(lhs) == 1:
        if len(rhs) == 0:
            return ecell4.core.create_degradation_reaction_rule(lhs[0], k)
        elif len(rhs) == 1:
            return ecell4.core.create_unimolecular_reaction_rule(
                lhs[0], rhs[0], k)
        elif len(rhs) == 2:
            return ecell4.core.create_unbinding_reaction_rule(
                lhs[0], rhs[0], rhs[1], k)
        else:
            raise RuntimeError, (
                "the number of products must be less than 3; %d given"
                % len(rhs))
    elif len(lhs) == 2:
        if len(rhs) == 1:
            return ecell4.core.create_binding_reaction_rule(
                lhs[0], lhs[1], rhs[0], k)
        else:
            raise RuntimeError, (
                "the number of products must be 1; %d given" % len(rhs))
    raise RuntimeError, (
        "the number of reactants must be less than 3; %d given" % len(lhs))

class Callback(object):
    """callback before the operations"""

    def __init__(self):
        pass

    def get(self):
        return None

    def notify_unary_operations(self, obj):
        pass

    def notify_bitwise_operations(self, obj):
        pass

    def notify_comparisons(self, obj):
        pass

class SpeciesAttributesCallback(Callback):

    def __init__(self, *args):
        Callback.__init__(self)

        self.keys = None
        if len(args) > 0:
            for key in args:
                if not isinstance(key, types.StringType):
                    raise RuntimeError, 'non string key "%s" was given' % key
            self.keys = args

        self.bitwise_operations = []

    def get(self):
        return copy.copy(self.bitwise_operations)

    def notify_bitwise_operations(self, obj):
        if not isinstance(obj, parseobj.OrExp):
            raise RuntimeError, 'an invalid object was given [%s]' % (repr(obj))
        elif len(obj._elements()) != 2:
            raise RuntimeError, 'only one attribute is allowed. [%d] given' % (
                len(obj._elements()))

        lhs, rhs = obj._elements()

        species_list = generate_Species(lhs)
        if len(species_list) != 1:
            raise RuntimeError, (
                'only a single species must be given; %d given'
                % len(species_list))

        sp = species_list[0]
        if sp is None:
            raise RuntimeError, "no species given [%s]" % (repr(obj))

        if self.keys is None:
            if not isinstance(rhs, types.DictType):
                raise RuntimeError, (
                    'parameter must be given as a dict; "%s" given'
                    % str(rhs))
            for key, value in rhs.items():
                if not (isinstance(key, types.StringType)
                    and isinstance(value, types.StringType)):
                    raise RuntimeError, (
                        'attributes must be given as a pair of strings;'
                        + ' "%s" and "%s" given'
                        % (str(key), str(value)))
                sp.set_attribute(key, value)
        else:
            if not (isinstance(rhs, types.TupleType)
                and isinstance(rhs, types.ListType)):
                if len(self.keys) == 1:
                    rhs = (rhs, )
                else:
                    raise RuntimeError, (
                        'parameters must be given as a tuple or list; "%s" given'
                        % str(rhs))
            if len(rhs) != len(self.keys):
                raise RuntimeError, (
                    'the number of parameters must be %d; %d given'
                    % (len(self.keys), len(rhs)))
            else:
                for key, value in zip(self.keys, rhs):
                    if not isinstance(value, types.StringType):
                        raise RuntimeError, (
                            'paramter must be given as a string; "%s" given'
                            % str(value))
                    sp.set_attribute(key, value)

        self.bitwise_operations.append(sp)

    def notify_comparisons(self, obj):
        raise RuntimeError, (
            'ReactionRule definitions are not allowed'
            + ' in "species_attributes"')

class ReactionRulesCallback(Callback):

    def __init__(self):
        Callback.__init__(self)

        self.comparisons = []

    def get(self):
        return copy.copy(self.comparisons)

    def notify_comparisons(self, obj):
        if not isinstance(obj, parseobj.CmpExp):
            raise RuntimeError, 'an invalid object was given [%s]' % (repr(obj))
        elif isinstance(obj, parseobj.NeExp):
            warnings.warn('"<>" is deprecated; use "==" instead',
                          DeprecationWarning)

        lhs, rhs = obj._lhs, obj._rhs

        if isinstance(lhs, parseobj.OrExp):
            lhs = lhs._elements()[0]

        if not isinstance(rhs, parseobj.OrExp):
            raise RuntimeError, ('an invalid object was given'
                + ' as a right-hand-side [%s].' % (repr(rhs))
                + ' OrExp must be given')
        elif len(rhs._elements()) != 2:
            raise RuntimeError, 'only one attribute is allowed. [%d] given' % (
                len(rhs._elements()))

        rhs, params = rhs._elements()
        lhs, rhs = generate_Species(lhs), generate_Species(rhs)
        lhs = tuple(sp for sp in lhs if sp is not None)
        rhs = tuple(sp for sp in rhs if sp is not None)

        if isinstance(obj, parseobj.EqExp) or isinstance(obj, parseobj.NeExp):
            if not (isinstance(params, types.ListType)
                or isinstance(params, types.TupleType)):
                raise RuntimeError, (
                    'parameter must be a list or tuple with length 2; "%s" given'
                    % str(params))
            elif len(params) != 2:
                raise RuntimeError, (
                    "parameter must be a list or tuple with length 2;"
                    + " length %d given" % len(params))
            elif not (isinstance(params[0], numbers.Number)
                and isinstance(params[1], numbers.Number)):
                raise RuntimeError, (
                    'parameters must be given as a list or tuple of numbers;'
                    + ' "%s" given' % str(params))
            self.comparisons.append(generate_ReactionRule(lhs, rhs, params[0]))
            self.comparisons.append(generate_ReactionRule(rhs, lhs, params[1]))
        elif isinstance(obj, parseobj.GtExp):
            if params is None:
                raise RuntimeError, 'no parameter is specified'
            elif not isinstance(params, numbers.Number):
                raise RuntimeError, (
                    'parameter must be given as a number; "%s" given'
                    % str(params))
            self.comparisons.append(generate_ReactionRule(lhs, rhs, params))
        else:
            raise RuntimeError, 'an invalid object was given [%s]' % (repr(obj))

class JustParseCallback(Callback):

    def __init__(self):
        Callback.__init__(self)

        self.comparisons = []

    def get(self):
        return copy.copy(self.comparisons)

    def notify_comparisons(self, obj):
        if isinstance(obj, parseobj.NeExp):
            warnings.warn('"<>" is deprecated; use "==" instead',
                          DeprecationWarning)
        self.comparisons.append(obj)

def parse_decorator(callback_class, func):
    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        cache = callback_class()
        vardict = copy.copy(func.func_globals)
        for k in func.func_code.co_names:
            if (not k in vardict.keys()
                and not k in dir(vardict['__builtins__'])): # is this enough?
                vardict[k] = parseobj.AnyCallable(cache, k)
        g = types.FunctionType(func.func_code, vardict)
        with warnings.catch_warnings():
            # warnings.simplefilter("always")
            g(*args, **kwargs)
        return cache.get()
    return wrapped

# reaction_rules = functools.partial(parse_decorator, Callback)
reaction_rules = functools.partial(parse_decorator, ReactionRulesCallback)
species_attributes = functools.partial(parse_decorator, SpeciesAttributesCallback)
just_parse = functools.partial(parse_decorator, JustParseCallback)

def species_attributes_with_keys(*args):
    def create_callback():
        return SpeciesAttributesCallback(*args)
    return functools.partial(parse_decorator, create_callback)
