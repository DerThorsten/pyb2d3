#pragma once

#include <vector>

#include <box2d/box2d.h>

// like chain def, but owns the memory for the vertices
struct PyChainDef
{
    inline PyChainDef()
    {
        chain_def = b2DefaultChainDef();
        chain_def.count = 0;
    }

    b2ChainDef chain_def;

    std::vector<b2Vec2> points;                // vertices of the chain
    std::vector<b2SurfaceMaterial> materials;  // materials for each segment
};
