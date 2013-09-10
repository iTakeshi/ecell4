#ifndef __ECELL4_MOLECULE_TYPE_HPP
#define __ECELL4_MOLECULE_TYPE_HPP

#include <vector>
#include "Species.hpp"
#include "Voxel.hpp"

namespace ecell4
{

class MolecularType
{

public:

    typedef std::vector<Voxel&> voxel_container_type;

public:

    MolecularType(Species& species);
    void addVoxel(const Voxel& voxel);
    void removeVoxel(const Voxel& voxel);
    const Species& species() const;
    const voxel_container_type voxels() const;

protected:

    Species& spesies_;
    std::vector<Voxel&> voxels_;

};

class VacantType
    : public MolecularType
{
};

}

#endif