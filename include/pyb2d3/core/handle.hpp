#pragma once

#include <cstdint>

#include <box2d/box2d.h>

namespace pyb2d3
{
    /// Per id-type glue: how to pack an id into an integer (and back), how to check
    /// validity and how to access the user data pointer. Everything that is generic
    /// over box2d ids goes through this single table.
    template <class IdT>
    struct IdTraits;

    // (full function names on purpose, no token pasting: they stay greppable for
    //  the api coverage test and for IDE navigation)
#define PYB2D3_ID_TRAITS(ID, LOAD, STORE, IS_VALID, GET_USER_DATA, SET_USER_DATA) \
    template <>                                                                  \
    struct IdTraits<ID>                                                          \
    {                                                                            \
        static ID load(uint64_t v)                                               \
        {                                                                        \
            return LOAD(v);                                                      \
        }                                                                        \
        static uint64_t store(ID id)                                             \
        {                                                                        \
            return STORE(id);                                                    \
        }                                                                        \
        static bool is_valid(ID id)                                              \
        {                                                                        \
            return IS_VALID(id);                                                 \
        }                                                                        \
        static void* get_user_data(ID id)                                        \
        {                                                                        \
            return GET_USER_DATA(id);                                            \
        }                                                                        \
        static void set_user_data(ID id, void* data)                             \
        {                                                                        \
            SET_USER_DATA(id, data);                                             \
        }                                                                        \
    }

    PYB2D3_ID_TRAITS(b2WorldId, b2LoadWorldId, b2StoreWorldId, b2World_IsValid, b2World_GetUserData, b2World_SetUserData);
    PYB2D3_ID_TRAITS(b2BodyId, b2LoadBodyId, b2StoreBodyId, b2Body_IsValid, b2Body_GetUserData, b2Body_SetUserData);
    PYB2D3_ID_TRAITS(b2ShapeId, b2LoadShapeId, b2StoreShapeId, b2Shape_IsValid, b2Shape_GetUserData, b2Shape_SetUserData);
    PYB2D3_ID_TRAITS(b2JointId, b2LoadJointId, b2StoreJointId, b2Joint_IsValid, b2Joint_GetUserData, b2Joint_SetUserData);

#undef PYB2D3_ID_TRAITS

    // chains have no user data
    template <>
    struct IdTraits<b2ChainId>
    {
        static b2ChainId load(uint64_t v)
        {
            return b2LoadChainId(v);
        }

        static uint64_t store(b2ChainId id)
        {
            return b2StoreChainId(id);
        }

        static bool is_valid(b2ChainId id)
        {
            return b2Chain_IsValid(id);
        }
    };

    /// Base class of all wrappers around an opaque box2d id.
    template <class IdT>
    struct Handle
    {
        using id_type = IdT;
        using traits = IdTraits<IdT>;

        IdT id;

        Handle(IdT id_)
            : id(id_)
        {
        }

        explicit Handle(uint64_t int_id)
            : id(traits::load(int_id))
        {
        }

        static IdT int_to_id(uint64_t v)
        {
            return traits::load(v);
        }

        static uint64_t id_to_int(IdT id)
        {
            return traits::store(id);
        }

        uint64_t int_id() const
        {
            return traits::store(id);
        }

        bool IsValid() const
        {
            return traits::is_valid(id);
        }

        bool operator==(const Handle& other) const
        {
            return int_id() == other.int_id();
        }

        bool operator!=(const Handle& other) const
        {
            return !(*this == other);
        }
    };

}  // namespace pyb2d3
