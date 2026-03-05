# For more information about using CMake with Android Studio, read the
# documentation: https://d.android.com/studio/projects/add-native-code.html

# Sets the minimum version of CMake required to build the native library.

cmake_minimum_required(VERSION 3.4.1)

# Creates and names a library, sets it as either STATIC
# or SHARED, and provides the relative paths to its source code.
# You can define multiple libraries, and CMake builds them for you.
# Gradle automatically packages shared libraries with your APK.
file(GLOB SOURCES "src/*.h")
add_library(my_lib STATIC IMPORTED)
set_target_properties(my_lib PROPERTIES IMPORTED_LOCATION Libraries/libopennurbs_public.a)
set_target_properties(my_lib PROPERTIES INCLUDE_DIRECTORIES Libraries)

add_library( # Sets the name of the library.
        my-native-lib

        # Sets the library as a shared library.
        SHARED
        ${SOURCES}
        opennurbs
        # Provides a relative path to your source file(s).
        native-lib.cpp)


find_library( # Sets the name of the path variable.
        log-lib
        log)

# Specifies libraries CMake should link to your target library. You
# can link multiple libraries, such as libraries you define in this
# build script, prebuilt third-party libraries, or system libraries.
# Set the header files directory.
include_directories(${CMAKE_CURRENT_SOURCE_DIR})
target_link_libraries( # Specifies the target library.
        my-native-lib
        my_lib
        ${log-lib})