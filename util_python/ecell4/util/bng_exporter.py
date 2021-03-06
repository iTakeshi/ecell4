import ecell4.reaction_reader.species as species
import string   # for convert into .bngl
import copy
from types import MethodType

from collections import defaultdict

# Label Related
def is_label(s):
    return 1 < len(s) and s[0] == '_'

def check_labeled_modification(su):
    retval = []
    for mod, (state, binding) in su.get_modifications_list().items():
        if 1 < len(state) and state[0] == '_':
            retval.append( (state,mod) )    # state should be label.
    return retval

def check_labeled_subunit(su):
    retval = []
    if is_label(su.get_name()):
        for mod, (state, binding) in su.get_modifications_list().items():
            retval.append( (mod, state, binding) )
    return retval

def check_label_containing_reaction(rr):
    reactant_labels = defaultdict(list)
    product_labels = defaultdict(list)
    subunit_labels = defaultdict(lambda:defaultdict(set))
    for r in rr.reactants():
        for su in r.get_subunit_list():
            # check modification-state labels.
            d = check_labeled_modification(su)
            for (label, mod) in d:
                reactant_labels[label].append( (su.get_name(), mod) )
            # check the subunit label
            if is_label(su.get_name()):
                for (su_mod, su_state, su_binding) in check_labeled_subunit(su):
                    subunit_labels[su.get_name()][su_mod].add(su_state)
                #subunit_labels[su.get_name()].extend(check_labeled_subunit(su))

    for p in rr.products():
        for su in p.get_subunit_list():
            # check modification-state labels.
            d = check_labeled_modification(su)
            for (lebel, mod) in d:
                product_labels[label].append( (su.get_name(), mod) )
            # check the subunit label
            #if is_label(su.get_name()):
            #    subunit_labels[su.get_name()].extend(check_labeled_subunit(su))
            if is_label(su.get_name()):
                for (su_mod, su_state, su_binding) in check_labeled_subunit(su):
                    subunit_labels[su.get_name()][su_mod].add(su_state)

    return (reactant_labels, product_labels, subunit_labels)

        
# Formatters for each class
# class Species
def convert2bng_species(self, labels = None):
    return ".".join([subunit.convert2bng(labels) for subunit in self.subunits])

# class Subunit
def convert2bng_subunit(self, labels = None):
    mods1, mods2 = [], []
    for mod, (state, binding) in self.modifications.items():
        if state == '':
            if binding == '_':
                mods1.append("%s!+" % (mod))
            elif binding != '':
                mods1.append("%s!%s" % (mod, binding))
            else:
                mods1.append(mod)
        elif is_label(state):
            if labels != None and (state in labels) and 0 < len(labels[state]):
                if binding == '_':
                    mods2.append("%s~%s!+" % (mod, binding))
                elif binding == "":
                    mods2.append("%s~%s" % (mod, labels[state]))
                else:
                    mods2.append("%s~%s!%s" % (mod, labels[state], binding))
            else:
                print ("Warning: The candidate for label %s was not found" % state)
                if binding == '_':
                    mods2.append("%s~%s!+" % (mod, binding))
                elif binding == "":
                    mods2.append("%s~%s" % (mod, state))
                else:
                    mods2.append("%s~%s!%s" % (mod, state, binding))
        else:
            if binding == '_':
                mods2.append("%s~%s!+" % (mod, state))
            elif binding == "":
                mods2.append("%s~%s" % (mod, state))
            else:
                mods2.append("%s~%s!%s" % (mod, state, binding))
    mods1.sort()
    mods2.sort()
    mods1.extend(mods2)
    su_name = self.name
    if is_label(su_name):
        #import ipdb; ipdb.set_trace()
        if labels != None and labels.has_key(su_name):
            su_name = labels[su_name]
        else:
            print ("Warning: The candidate for label %s was not found" % su_name)
    #return str(self).translate(string.maketrans('=^', '~!'))
    return "%s(%s)" % (su_name, ",".join(mods1))

def generate_Null():
    sp = species.Species()
    su = species.Subunit("Null")
    sp.add_subunit(su)
    return sp

def generate_Src():
    sp = species.Species()
    su = species.Subunit("Src")
    sp.add_subunit(su)
    return sp

species_Null = generate_Null()
species_Src  = generate_Src()

# class ReactionRule
def convert2bng_reactionrule(self, labels = None):
    reactants_bng_queries = [sp.convert2bng(labels) for sp in self.reactants()]
    products_bng_queries = [sp.convert2bng(labels) for sp in self.products()]
    if self.is_degradation() == True:
        reactants_bng_queries.append("Null")
        products_bng_queries.append("Null")
    elif self.is_synthesis() == True:
        reactants_bng_queries.append("Src")
        products_bng_queries.append("Src")

    return "%s -> %s" % (
            #"+".join([sp.convert2bng(labels) for sp in self.reactants()]),
            #"+".join([sp.convert2bng(labels) for sp in self.products()]))
            "+".join(reactants_bng_queries),
            "+".join(products_bng_queries))

# classe Options
def convert2bng_include_reactants(self):
    return "include_reactants(%d,%s)" % (self._IncludeReactants__idx, self._IncludeReactants__pttrn)
def convert2bng_exclude_reactants(self):
    return "exclude_reactants(%d,%s)" % (self._ExcludeReactants__idx, self._ExcludeReactants__pttrn)
def convert2bng_include_products(self):
    return "include_products(%d,%s)" % (self._IncludeProducts__idx, self._IncludeProducts__pttrn)
def convert2bng_exclude_products(self):
    return "exclude_products(%d,%s)" % (self._ExcludeProducts__idx, self._ExcludeProducts__pttrn)

class Convert2BNGManager(object):
    def __init__(self, species, rules):
        self.__expanded = False
        self.__species = species
        self.__rules = rules
        self.__rules_notes = []
        self.__modification_collection_dict = defaultdict(lambda:defaultdict(set))
        self.__modification_collection_dict_ext = defaultdict(lambda:defaultdict(set))
        if 0 < len(species) and 0 < len(rules):
            self.build_modification_collection_dict()

        # add convert2bng method for related classes
        self.initialize_methods()
        # analyze all reactions
        self.expand_reactions()

    def initialize_methods(self):
        species.Species.convert2bng = MethodType(convert2bng_species, None, species.Species)
        species.Subunit.convert2bng = MethodType(convert2bng_subunit, None, species.Subunit)
        species.ReactionRule.convert2bng = MethodType(convert2bng_reactionrule, None, species.ReactionRule)
        species.IncludeReactants.convert2bng = MethodType(convert2bng_include_reactants, None, species.IncludeReactants)
        species.ExcludeReactants.convert2bng = MethodType(convert2bng_exclude_reactants, None, species.ExcludeReactants)
        species.IncludeProducts.convert2bng = MethodType(convert2bng_include_products, None, species.IncludeProducts)
        species.ExcludeProducts.convert2bng = MethodType(convert2bng_exclude_products, None, species.ExcludeProducts)

    def expand_reactions(self):
        # Expand labels and update modification collection
        for i, rr in enumerate(self.__rules):
            notes = self.build_label_expanded_reactionrule(rr)
            self.__rules_notes.append(notes)
        self.__expanded = True

    def build_modification_collection_dict(self):
        # The first argumet (current_dict) is dict(defaultdict(set))
        def add_modification_collection_dict_subunit(current_dict, subunit):
            su_name = subunit.get_name()
            if is_label(su_name):
                # do nothing
                return current_dict

            if not current_dict.has_key(su_name):
                current_dict[subunit.get_name()] = defaultdict(set)
            for mod, (state, binding) in subunit.get_modifications_list().items():
                if not is_label(state):
                        current_dict[su_name][mod].add(state)
            return current_dict

        # style:  dict[subunit][modification] = set(states)
        temp_dict = {}
        # Build modification dictionary by species
        for (sp, attr) in self.__species:
            for su in sp.get_subunit_list():
                temp_dict = add_modification_collection_dict_subunit(temp_dict, su)
        # Build modification dictionary by ReactionRules
        reactants = []
        products = []
        for rr in self.__rules:
            reacntants = rr.reactants()
            products = rr.products()
            # Following if-else statements is to enable output Null and Src
            # in 'molecule_types' section in degradation/synthesis reactions.
            if rr.is_degradation() == True:
                temp_dict = add_modification_collection_dict_subunit(
                        temp_dict, species_Null.get_subunit_list()[0])
            elif rr.is_synthesis() == True:
                temp_dict = add_modification_collection_dict_subunit(
                        temp_dict, species_Src.get_subunit_list()[0])
            for r in reactants:
                for su in r.get_subunit_list():
                    temp_dict = add_modification_collection_dict_subunit(temp_dict, su)
            for p in products:
                for su in p.get_subunit_list():
                    temp_dict = add_modification_collection_dict_subunit(temp_dict, su)
        # Replace instance-member
        self.__modification_collection_dict = temp_dict
        self.__modification_collection_dict_ext = copy.deepcopy(
                self.__modification_collection_dict)
    
    def get_modification_collection_dict(self):
        return self.__modification_collection_dict

    def build_label_expanded_reactionrule(self, rr):
        def find_subunit_candidates(mod, state_set):
            ret = set()
            for (subunit, modification) in self.__modification_collection_dict.items():
                for (candidate_mod, candidate_state_set) in modification.items():
                    if candidate_mod == mod and state_set.issubset(candidate_state_set):
                        ret.add(subunit)
            return ret

        (reactant_labels, product_labels, subunit_labels) = check_label_containing_reaction(rr)
        # Find candidates that is asigned for Subunits' registers.
        subunit_candidates = None
        modification_candidates = None
        if subunit_labels:
            subunit_candidates = {}
            for (label, states_dict) in subunit_labels.items():
                subunit_candidates[label] = set()
                for (mod, states_set) in states_dict.items():
                    subunit_candidates[label] = subunit_candidates[label] | find_subunit_candidates(mod, states_set) 
        # Find candidates that is asigned for Modifications' registers.
        if reactant_labels or product_labels:
            bngl_strs = []
            modification_candidates = {}    # key is label(::string), value is a set of states.
            for label, pos in reactant_labels.items():
                modification_candidates[label] = set()
                for (su, mod) in pos:
                    modification_candidates[label] = modification_candidates[label] | self.__modification_collection_dict[su][mod]
            # Update modification_collection_dict for molecule_types section.
            for (label, pos) in reactant_labels.items():
                for (su, mod) in pos:
                    self.__modification_collection_dict_ext[su][mod] = self.__modification_collection_dict_ext[su][mod] | modification_candidates[label]
            for (label, pos) in product_labels.items():
                for (su, mod) in pos:
                    self.__modification_collection_dict_ext[su][mod] = self.__modification_collection_dict_ext[su][mod] | modification_candidates[label]

        return (modification_candidates, subunit_candidates)

    def write_section_seed_species(self, fd):
        fd.write("begin seed species\n")
        for i, (sp, attr) in enumerate( self.__species ):
            fd.write("\t%s\t%f\n" % (sp.convert2bng(), attr))
        fd.write("end seed species\n")

    def write_section_molecule_types(self, fd):
        def build_molecules_type_query_list(current_dict):
            retval = []
            for su_name in current_dict:
                mod_list = []
                for m, state_list in current_dict[su_name].items():
                    mod = "%s" % m
                    for state in list(set(state_list)):
                        if state != '' and state != "_":
                            mod = "%s~%s" % (mod, state)
                    mod_list.append(mod)
                retval.append("%s(%s)" % (su_name, ','.join(mod_list) ))
            return retval

        # write
        fd.write("begin molecule types\n")
        for s in build_molecules_type_query_list(self.__modification_collection_dict_ext):
            fd.write("\t%s\n" % s)
        fd.write("end molecule types\n")

    def write_section_reaction_rules(self, fd):
        def merge_candidates_dict(d1, d2):
            retval = defaultdict(set)
            if d1:
                if d2:
                    for (key, val_set) in d1.items():
                        retval[key] = val_set
                    for (key, val_set) in d2.items():
                        retval[key] = retval[key] | val_set
                else:
                    retval = d1
            else:
                if d2:
                    retval = d2
            return retval

        def convert2bngl_label_expanded_reactionrule_recursive(
                rr, label_list, candidates, acc, bnglstr_acc):
            acc_conbination = copy.deepcopy(acc)
            for mod in candidates[ label_list[0] ]:
                acc_conbination[label_list[0]] = mod
                if len(label_list) == 1:
                    bnglstr_acc.append( rr.convert2bng(acc_conbination) )
                else:
                    convert2bngl_label_expanded_reactionrule_recursive(
                            rr, label_list[1:], candidates, acc_conbination, bnglstr_acc)

        fd.write("begin reaction rules\n")
        for i, rr in enumerate(self.__rules):
            fd.write( ("\t# %s\n" % rr) )
            (modification_candidates, subunit_candidates) = self.__rules_notes[i]
            if modification_candidates or subunit_candidates:
                candidates = merge_candidates_dict(modification_candidates, subunit_candidates)
                fd.write("\t# candidates for labels:\n")        #Comments
                fd.write("\t#   %s\n" % candidates)             #Comments
                bngl_strs = []
                convert2bngl_label_expanded_reactionrule_recursive(
                        rr, candidates.keys(), candidates, {}, bngl_strs)
                for applied in bngl_strs:
                    s = "\t%s\t%f" % (applied, rr.options()[0])
                    for cond in rr.options():
                        if isinstance(cond, species.Option):
                            s = "%s %s" % (s, cond.convert2bng())
                    s += "\n"
                    fd.write(s)

            else:   # containing no labels
                s = "\t%s\t%f" % (rr.convert2bng(), rr.options()[0])
                for cond in rr.options():
                    if isinstance(cond, species.Option):
                        s = "%s %s" % (s, cond.convert2bng() )
                s += "\n"
                fd.write(s)
        fd.write("end reaction rules\n")

