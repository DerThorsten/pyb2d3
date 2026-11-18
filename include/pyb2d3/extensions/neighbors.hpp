#pragma once

// Neighbor search: a pyb2d3 extension, not part of Box2D.
//
// All pairs of points closer than a radius, each pair once (flocking, particle fluids, short
// range forces). Points go into a grid of radius-sized cells, so the neighbors of a point are
// in its own cell or in one of the 8 around it: O(n + pairs) instead of testing all n^2 pairs.

#include <cmath>
#include <cstddef>
#include <cstdint>
#include <unordered_map>
#include <vector>

namespace pyb2d3::extensions
{
    struct NeighborPairs
    {
        std::vector<int32_t> i, j;     // the two points of each pair (i < j)
        std::vector<double> delta;     // point j - point i, (x, y) per pair
        std::vector<double> distance;  // length of delta
    };

    // `xy`: n points as x0, y0, x1, y1, ...
    inline NeighborPairs neighbor_pairs(const double* xy, std::size_t n, double radius)
    {
        auto cell_key = [](int64_t cx, int64_t cy)
        {
            return (static_cast<uint64_t>(static_cast<uint32_t>(cx)) << 32) | static_cast<uint32_t>(cy);
        };
        auto cell_of = [&](std::size_t k, int64_t& cx, int64_t& cy)
        {
            cx = static_cast<int64_t>(std::floor(xy[2 * k] / radius));
            cy = static_cast<int64_t>(std::floor(xy[2 * k + 1] / radius));
        };

        // the points of each cell, in index order
        std::unordered_map<uint64_t, std::vector<int32_t>> grid;
        for (std::size_t k = 0; k < n; ++k)
        {
            int64_t cx, cy;
            cell_of(k, cx, cy);
            grid[cell_key(cx, cy)].push_back(static_cast<int32_t>(k));
        }

        NeighborPairs pairs;
        const double radius_squared = radius * radius;
        for (std::size_t a = 0; a < n; ++a)
        {
            int64_t cx, cy;
            cell_of(a, cx, cy);
            for (int64_t dy = -1; dy <= 1; ++dy)
            {
                for (int64_t dx = -1; dx <= 1; ++dx)
                {
                    auto cell = grid.find(cell_key(cx + dx, cy + dy));
                    if (cell == grid.end())
                    {
                        continue;
                    }
                    for (int32_t b : cell->second)
                    {
                        if (static_cast<std::size_t>(b) <= a)
                        {
                            continue;  // each pair once (and not a point with itself)
                        }
                        const double ddx = xy[2 * b] - xy[2 * a];
                        const double ddy = xy[2 * b + 1] - xy[2 * a + 1];
                        const double d2 = ddx * ddx + ddy * ddy;
                        if (d2 < radius_squared)
                        {
                            pairs.i.push_back(static_cast<int32_t>(a));
                            pairs.j.push_back(b);
                            pairs.delta.push_back(ddx);
                            pairs.delta.push_back(ddy);
                            pairs.distance.push_back(std::sqrt(d2));
                        }
                    }
                }
            }
        }
        return pairs;
    }
}  // namespace pyb2d3::extensions
