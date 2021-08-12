cmake_minimum_required(VERSION 3.13.4)

project(BulkLabelStatistics)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "https://www.slicer.org/wiki/Documentation/Nightly/Extensions/BulkLabelStatistics")
set(EXTENSION_CATEGORY "Statistics")
set(EXTENSION_CONTRIBUTORS "Rafael Palomar (Oslo University Hospital)")
set(EXTENSION_DESCRIPTION "This is a wrapper around the labelmap statistics to compute the statistics on bulk.	")
set(EXTENSION_ICONURL "http://www.example.com/Slicer/Extensions/BulkLabelStatistics.png")
set(EXTENSION_SCREENSHOTURLS "http://www.example.com/Slicer/Extensions/BulkLabelStatistics/Screenshots/1.png")
set(EXTENSION_DEPENDS "NA") # Specified as a list or "NA" if no dependencies

#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

#-----------------------------------------------------------------------------
# Extension modules
add_subdirectory(BulkLabelStatistics)
## NEXT_MODULE

#-----------------------------------------------------------------------------
include(${Slicer_EXTENSION_GENERATE_CONFIG})
include(${Slicer_EXTENSION_CPACK})
