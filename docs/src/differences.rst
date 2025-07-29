
Differences to Box2D C
=======================

This document outlines the differences between the Python implementation of Box2D (pyb2d3)
and the original Box2D C library. It is intended to help users understand how to adapt their code when transitioning from Box2D C++ to pyb2d3.


Wrapper Classes
-----------------

The C API of Box2D is a bunch of free functions that operate on IDs of objects.

.. code-block:: C

    b2WorldId b2CreateWorld( const b2WorldDef* def );
    void b2DestroyWorld( b2WorldId worldId );
    bool b2World_IsValid( b2WorldId id );
    void b2World_Step( b2WorldId worldId, float timeStep, int subStepCount );
    void b2World_Draw( b2WorldId worldId, b2DebugDraw* draw );
    b2BodyEvents b2World_GetBodyEvents( b2WorldId worldId );
    b2SensorEvents b2World_GetSensorEvents( b2WorldId worldId );

    /// [...]

    b2BodyId b2CreateBody( b2WorldId worldId, const b2BodyDef* def );
    void b2DestroyBody( b2BodyId bodyId );
    bool b2Body_IsValid( b2BodyId id );
    b2BodyType b2Body_GetType( b2BodyId bodyId );
    void b2Body_SetType( b2BodyId bodyId, b2BodyType type );
    void b2Body_SetName( b2BodyId bodyId, const char* name );
    const char* b2Body_GetName( b2BodyId bodyId );



In pyb2d3, the API is object-oriented, and you interact with objects directly rather than through IDs. For example, creating a world and a body looks like this:

.. code-block:: python

    world = pyb2d3.create_world(gravity=(0, -10))
    body = world.create_dynamic_body(position=(0, 0), angle=0)

The python types are just cheap wrappers around the IDs.
Ie you can think of a  :class:`pyb2d3.Body` as a lightweight representation of the underlying body ID.

In fact, on the C++ side, we create thin wrapper structs like the one below,
and exported these classes to Python using nanobind.

.. code-block:: C++

    struct Body {
        b2BodyId id;

        bool is_valid() const {
            return b2Body_IsValid(id);
        }
        // [...] other methods that operate on the body

    };


Factory methods
--------------------
For all `b2<Thingy>Def` structs (ie `b2BodyDef`, `b2DistanceJointDef`, etc.),
pyb2d3 provides factory methods that return instances of these classes.
These methods are named snake_case named.
These methods take **only keyword arguments** and return an instance of the corresponding class.

For example, to create a `b2BodyDef`, you can use:

.. code-block:: python

    body_def = pyb2d3.body_def()
    another_body_def = pyb2d3.body_def(
        position=(0, 0),
        type=pyb2d3.BodyType.DYNAMIC,
    )
    yet_another_body_def = pyb2d3.body_def(
        position=(0, 0),
        type=b2d.BodyType.DYNAMIC,
        rotation=3.14/2
    )

Convenient Methods
--------------------
pyb2d3 provides several convenient methods that are not present in the original Box2D C library.
These methods are designed to simplify common tasks, make everything more Pythonic, and improve usability.

..  TODO




Additional Goodies
--------------------
    * :class:`pyb2d3.PathBuilder`: An utility class for constructing line segments in a convenient way
