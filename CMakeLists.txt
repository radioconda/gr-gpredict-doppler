cmake_minimum_required(VERSION 3.8)

project(gr-gpredict-doppler)

#install to PyBOMBS target prefix if defined
if(DEFINED ENV{PYBOMBS_PREFIX})
    set(CMAKE_INSTALL_PREFIX $ENV{PYBOMBS_PREFIX})
    message(STATUS "PyBOMBS installed GNU Radio. Setting CMAKE_INSTALL_PREFIX to $ENV{PYBOMBS_PREFIX}")
endif()

#select the release build type by default to get optimization flags
if(NOT CMAKE_BUILD_TYPE)
   set(CMAKE_BUILD_TYPE "Release")
   message(STATUS "Build type not specified: defaulting to release.")
endif(NOT CMAKE_BUILD_TYPE)
set(CMAKE_BUILD_TYPE ${CMAKE_BUILD_TYPE} CACHE STRING "")

# Ensure Modules are first on path
list(INSERT CMAKE_MODULE_PATH 0 ${CMAKE_SOURCE_DIR}/cmake/Modules)


# GNU Radio config
include(GrPlatform)

set(GR_RUNTIME_DIR bin)
set(GR_LIBRARY_DIR lib${LIB_SUFFIX})
set(GR_INCLUDE_DIR include/gpredict)
set(GR_DATA_DIR share)
set(GR_PKG_DATA_DIR ${GR_DATA_DIR}/${CMAKE_PROJECT_NAME})
set(GR_DOC_DIR ${GR_DATA_DIR}/doc)
set(GR_PKG_DOC_DIR ${GR_DOC_DIR}/${CMAKE_PROJECT_NAME})
set(GR_CONF_DIR etc)
set(GR_PKG_CONF_DIR ${GR_CONF_DIR}/${CMAKE_PROJECT_NAME}/conf.d)
set(GR_LIBEXEC_DIR libexec)
set(GR_PKG_LIBEXEC_DIR ${GR_LIBEXEC_DIR}/${CMAKE_PROJECT_NAME})
set(GRC_BLOCKS_DIR ${GR_PKG_DATA_DIR}/grc/blocks)

set(GR_REQUIRED_COMPONENTS RUNTIME)
include(FindPkgConfig)
find_package(Gnuradio "3.9" REQUIRED)

include(GrVersion)

include(GrPlatform) #define LIB_SUFFIX

# Uninstall target
configure_file(
  ${CMAKE_SOURCE_DIR}/cmake/cmake_uninstall.cmake.in
  ${CMAKE_CURRENT_BINARY_DIR}/cmake_uninstall.cmake
  @ONLY
)
add_custom_target(
  uninstall ${CMAKE_COMMAND} -P ${CMAKE_CURRENT_BINARY_DIR}/cmake_uninstall.cmake
)


# Add subdirectories
add_subdirectory(examples)
add_subdirectory(python)
add_subdirectory(grc)

install(FILES MANIFEST.yml
    RENAME MANIFEST-${VERSION_MAJOR}.${VERSION_API}.${VERSION_ABI}${VERSION_PATCH}.yml
    DESTINATION share/gnuradio/manifests/gpredict_doppler)
