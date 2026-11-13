#pragma once

#include <vector>

#include <box2d/box2d.h>
#include <box2d/math_functions.h>

// like b2ChainDef, but owns the memory for the points and materials
struct PyChainDef
{
    PyChainDef()
        : chain_def(b2DefaultChainDef())
    {
        sync();
    }

    PyChainDef(const PyChainDef& other)
        : chain_def(other.chain_def)
        , points(other.points)
        , materials(other.materials)
        , ghost1_set(other.ghost1_set)
        , ghost2_set(other.ghost2_set)
    {
        sync();
    }

    PyChainDef& operator=(const PyChainDef& other)
    {
        chain_def = other.chain_def;
        points = other.points;
        materials = other.materials;
        ghost1_set = other.ghost1_set;
        ghost2_set = other.ghost2_set;
        sync();
        return *this;
    }

    // re-point the raw pointers of the b2ChainDef to the owned storage.
    // box2d >= 3.2 requires 1 or one-per-segment materials: without materials
    // the default surface material is used for all segments.
    void sync()
    {
        static const b2SurfaceMaterial default_material = b2DefaultSurfaceMaterial();
        chain_def.points = points.data();
        chain_def.pointCount = static_cast<int>(points.size());
        if (materials.empty())
        {
            chain_def.materials = &default_material;
            chain_def.materialCount = 1;
        }
        else
        {
            chain_def.materials = materials.data();
            chain_def.materialCount = static_cast<int>(materials.size());
        }
    }

    // the def handed to b2CreateChain. box2d >= 3.2 needs explicit ghost points for
    // open chains: unless set by the user they continue the first / last segment.
    b2ChainDef prepared() const
    {
        b2ChainDef def = chain_def;
        const std::size_t n = points.size();
        if (!def.isLoop && n >= 2)
        {
            if (!ghost1_set)
            {
                def.ghost1 = b2Sub(b2MulSV(2.0f, points[0]), points[1]);
            }
            if (!ghost2_set)
            {
                def.ghost2 = b2Sub(b2MulSV(2.0f, points[n - 1]), points[n - 2]);
            }
        }
        return def;
    }

    b2ChainDef chain_def;
    std::vector<b2Vec2> points;
    std::vector<b2SurfaceMaterial> materials;
    bool ghost1_set = false;
    bool ghost2_set = false;
};
