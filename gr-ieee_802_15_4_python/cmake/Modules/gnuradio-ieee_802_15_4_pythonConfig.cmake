find_package(PkgConfig)

PKG_CHECK_MODULES(PC_GR_IEEE_802_15_4_PYTHON gnuradio-ieee_802_15_4_python)

FIND_PATH(
    GR_IEEE_802_15_4_PYTHON_INCLUDE_DIRS
    NAMES gnuradio/ieee_802_15_4_python/api.h
    HINTS $ENV{IEEE_802_15_4_PYTHON_DIR}/include
        ${PC_IEEE_802_15_4_PYTHON_INCLUDEDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/include
          /usr/local/include
          /usr/include
)

FIND_LIBRARY(
    GR_IEEE_802_15_4_PYTHON_LIBRARIES
    NAMES gnuradio-ieee_802_15_4_python
    HINTS $ENV{IEEE_802_15_4_PYTHON_DIR}/lib
        ${PC_IEEE_802_15_4_PYTHON_LIBDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/lib
          ${CMAKE_INSTALL_PREFIX}/lib64
          /usr/local/lib
          /usr/local/lib64
          /usr/lib
          /usr/lib64
          )

include("${CMAKE_CURRENT_LIST_DIR}/gnuradio-ieee_802_15_4_pythonTarget.cmake")

INCLUDE(FindPackageHandleStandardArgs)
FIND_PACKAGE_HANDLE_STANDARD_ARGS(GR_IEEE_802_15_4_PYTHON DEFAULT_MSG GR_IEEE_802_15_4_PYTHON_LIBRARIES GR_IEEE_802_15_4_PYTHON_INCLUDE_DIRS)
MARK_AS_ADVANCED(GR_IEEE_802_15_4_PYTHON_LIBRARIES GR_IEEE_802_15_4_PYTHON_INCLUDE_DIRS)
