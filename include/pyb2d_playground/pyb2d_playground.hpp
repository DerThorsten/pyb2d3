#pragma once

#ifdef _WIN32 // Check if we are on Windows
    #ifdef PYB2D_PLAYGROUND_EXPORTS
        // Define PYB2D_PLAYGROUND_EXPORTS in the project that builds the DLL
        #define PYB2D_PLAYGROUND_API __declspec(dllexport)
    #else
        // Consumers of the DLL use this
        #define PYB2D_PLAYGROUND_API __declspec(dllimport)
    #endif
#else
    // On non-Windows platforms, these macros are not needed
    #define PYB2D_PLAYGROUND_API
#endif
