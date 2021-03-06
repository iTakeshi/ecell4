from ecell4.reaction_reader.decorator2 import species_attributes, reaction_rules
from ecell4.reaction_reader.species import generate_reactions

k1 = 0.1
k2 = 0.2
k3 = 0.3
k4 = 0.4

@species_attributes
def attributegen():
    S(e,y=zero)  | 1
    kinase(s) | 2
    pptase(s) | 3
    ATP()     | 4
    ADP()     | 5

@reaction_rules
def rulegen():
    # binding rules
    S(e) + kinase(s) == S(e^1).kinase(s^1) | (1,2)
    S(e) + pptase(s) == S(e^1).pptase(s^1) | (3,4)
    # catalysis
    S(e^1,y=zero).kinase(s^1) + ATP == S(e^1,y=P).kinase(s^1) + ADP | (5,6)
    S(e^1,y=P).pptase(s^1)       == S(e^1,y=zero).pptase(s^1)       | (7,8)

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


## Catalysis in energy BNG
## justin.s.hogg@gmail.com, 9 Apr 2013
#
## requires BioNetGen version >= 2.2.4
#version("2.2.4")
## Quantities have units in moles, so set this to Avogadro's Number
#setOption("NumberPerQuantityUnit",6.0221e23)
#
#begin model
#begin parameters
#    # fundamental constants
#    RT               2.577       # kJ/mol
#    NA               6.022e23    # /mol
#    # simulation volume, L
#    volC             1e-12
#    # initial concentrations, mol/L
#    conc_S_0         1e-6
#    conc_kinase_0    10e-9
#    conc_pptase_0    10e-9
#    conc_ATP_0       1.0e-3
#    conc_ADP_0       0.1e-3
#    # standard free energy of formation, kJ/mol
#    Gf_Sp            51.1
#    Gf_S_kinase     -41.5
#    Gf_S_pptase     -41.5
#    Gf_ATP           51.1
#    # baseline activation energy, kJ/mol
#    Ea0_S_kinase    -7.7
#    Ea0_S_pptase    -7.7
#    Ea0_cat_kinase  -11.9
#    Ea0_cat_pptase   11.9
#    # rate distribution parameter, no units
#    phi              0.5
#end parameters
#begin compartments
#    # generic compartment
#    C  3  volC
#end compartments
#begin molecule types
#    S(e,y~0~P)  # substrate with enzyme binding domain and site of phosphorylation
#    kinase(s)   # kinase enzyme
#    pptase(s)   # phosphotase enzyme
#    ATP()
#    ADP()
#end molecule types
#begin species
#    S(e,y~0)@C   conc_S_0*NA*volC
#    kinase(s)@C  conc_kinase_0*NA*volC
#    pptase(s)@C  conc_pptase_0*NA*volC
#    $ATP()@C     conc_ATP_0*NA*volC     # ATP concentration held constant
#    $ADP()@C     conc_ADP_0*NA*volC     # ADP concentration held constant
#end species
#begin reaction rules
#    # binding rules
#    S(e) + kinase(s) <-> S(e!1).kinase(s!1)  Arrhenius(phi,Ea0_S_kinase)
#    S(e) + pptase(s) <-> S(e!1).pptase(s!1)  Arrhenius(phi,Ea0_S_pptase)
#    # catalysis
#    S(e!1,y~0).kinase(s!1) + ATP <-> S(e!1,y~P).kinase(s!1) + ADP  Arrhenius(phi,Ea0_cat_kinase)
#    S(e!1,y~P).pptase(s!1)       <-> S(e!1,y~0).pptase(s!1)        Arrhenius(phi,Ea0_cat_pptase)
#end reaction rules
#begin energy patterns
#    S(y~P)              Gf_Sp/RT        # phosphorylated subtrate
#    S(e!0).kinase(s!0)  Gf_S_kinase/RT  # substrate-kinase binding
#    S(e!0).pptase(s!0)  Gf_S_pptase/RT  # substrate-pptase binding
#    ATP()               Gf_ATP/RT       # ATP energy (relative to ADP)
#end energy patterns
#begin observables
#    Molecules  Sp         S(y~P)     
#    Molecules  S_kinase   S(e!1).kinase(s!1)
#    Molecules  S_pptase   S(e!1).pptase(s!1)
#    Molecules  Stot       S()
#    Molecules  kinaseTot  kinase()
#    Molecules  pptaseTot  pptase()
#end observables
#end model
#
## generate reaction network..
#generate_network({overwrite=>1})
#
## simulate ODE system to steady state..
#simulate({method=>"ode",t_start=>0,t_end=>3600,n_steps=>120,atol=>1e-3,rtol=>1e-7})
#
