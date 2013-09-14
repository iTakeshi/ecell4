from ecell4.reaction_reader.decorator2 import species_attributes, reaction_rules
from ecell4.reaction_reader.species import generate_reactions

@species_attributes
def attributegen():
    Null | 1
    Ga | Ga_0
    PLC | PLC_0
    Ca | Ca_0

@reaction_rules
def rulegen():
    Null > Ga + Null | k1
    Ga > Ga + Ga | k2
    Ga + PLC > PLC | k3
    Ga + Ca > Ca | k5
    Ga > PLC + Ga | k7
    PLC + Null > Null | k8
    Ga > Ca + Ga | k10
    Ca + Null > Null | k11
 
if __name__ == "__main__":
    newseeds = []
    for i, (sp, attr) in enumerate(attributegen()):
        print i, sp, attr
        newseeds.append(sp)
    print ''

    rules = rulegen()
    for i, rr in enumerate(rules):
        print i, rr
    print ''

    generate_reactions(newseeds, rules)

# begin model
# begin parameters
#     Na    6.022e23      # Avogadro's # [mol^-1]
#     V     1e-21         # Volume [L]
#     #    
#     k1    0.212*Na*V    # [M s^-1]
#     k2     2.85         # [s^-1]
#     k3     1.52         # [s^-1]
#     K4     0.19*Na*V    # [M]
#     k5     4.88         # [s^-1]
#     K6     1.18*Na*V    # [M]
#     k7     1.24         # [s^-1]
#     k8    32.24*Na*V    # [M s^-1]
#     K9    29.09*Na*V    # [M]
#     k10   13.58         # [s^-1]
#     k11   153.0*Na*V    # [M s^-1]
#     K12    0.16*Na*V    # [M]
#     #
#     Ga_0   0.01*Na*V    # [M]
#     PLC_0  0.01*Na*V    # [M]
#     Ca_0   0.01*Na*V    # [M]
# end parameters
# 
# begin molecule types
#     Null()
#     Ga() 
#     PLC()
#     Ca() 
# end molecule types
# 
# begin species
#     Null()    1
#     Ga()      Ga_0
#     PLC()     PLC_0
#     Ca()      Ca_0
# end species
# 
# begin observables 
#     Molecules    G       Ga()
#     Molecules    P       PLC()
#     Molecules    C       Ca()
#     Molecules    NULL    Null()
# end observables
# 
# begin reaction rules
#     Null() -> Ga() + Null()     k1
#     Ga() -> Ga() + Ga()         k2
#     Ga() + PLC() -> PLC()       k3/(K4+G)      #Sat(k3,K4)
#     Ga() + Ca() -> Ca()         k5/(K6+G)      #Sat(k5,K6)
#     Ga() -> PLC() + Ga()        k7
#     PLC() + Null() -> Null()    k8/(K9+P)      #Sat(k8,K9)
#     Ga() -> Ca() + Ga()         k10
#     Ca() + Null() -> Null()     k11/(K12+C)    #Sat(k11,K12)
# end reaction rules
# end model
# 
# ## actions ##
# generate_network({overwrite=>1})
# simulate({method=>"ode",t_end=>20,n_output_steps=>200,verbose=>1,atol=>1e-12,rtol=>1e-12})
# #simulate({method=>"ssa",t_end=>20,n_output_steps=>200,verbose=>1})
# #simulate({method=>"pla",t_end=>20,n_output_steps=>200,verbose=>1,pla_config=>"fEuler|sb|pre:post|eps=0.03"})
# #simulate({argfile=>"Models2/simargs.txt"})