cmake_minimum_required(VERSION 3.13)

project(tum-templates
        LANGUAGES NONE
        VERSION 3.0.0
)

set(PRETTY_PROJECT_NAME "TUM LaTeX Templates")
set(LATEX_PACKAGE_DIR "tum")
set(CMAKE_INSTALL_PREFIX "/tex/latex")

# cmake option to enable/disable build of test documents
option(BUILD_TESTING "Build test documents." ON)

# load module to build latex documents (only needed for test documents)
if(BUILD_TESTING)
  include(cmake/UseLATEX.cmake)
endif()

# add project components
add_subdirectory(article)
add_subdirectory(beamer)
add_subdirectory(book)
add_subdirectory(commons)
add_subdirectory(exam)
add_subdirectory(letter)
add_subdirectory(poster)

# target to run all tests together
add_custom_target(
  tests
  DEPENDS tests_commons
          tests_tumarticle
          tests_tumbeamer
          tests_tumbook
          tests_tumexam
          tests_tumletter
          tests_tumposter
)

# add subdirectory to create overleaf templates
add_subdirectory(deployment/overleaf)

# CPack variable setup common to all generators
set(CPACK_PACKAGE_NAME "${PROJECT_NAME}")
set(CPACK_PACKAGE_VENDOR "TUM LaTeX4EI Team")
set(CPACK_PACKAGE_HOMEPAGE_URL "https://gitlab.lrz.de/latex4ei/tum-templates")
set(CPACK_PACKAGE_DESCRIPTION_SUMMARY "TUM Corporate Design LaTeX Templates")
set(CPACK_PACKAGE_FILE_NAME "${CPACK_PACKAGE_NAME}")
set(CPACK_RESOURCE_FILE_LICENSE "${PROJECT_SOURCE_DIR}/LICENSE")
set(CPACK_RESOURCE_FILE_README "${PROJECT_SOURCE_DIR}/README.md")

# list of package generators
set(CPACK_GENERATOR "TGZ;DEB;NSIS")
# config file will be loaded once for every generator
set(CPACK_PROJECT_CONFIG_FILE
    "${CMAKE_BINARY_DIR}/deployment/CPackGeneratorConf.cmake"
)
# include path for NSIS template
set(CPACK_MODULE_PATH "${PROJECT_SOURCE_DIR}/deployment/NSIS")

# configure generator config file for packaging
configure_file("${PROJECT_SOURCE_DIR}/deployment/CPackGeneratorConf.cmake"
               "${PROJECT_BINARY_DIR}/deployment/CPackGeneratorConf.cmake"
               @ONLY
)

# module include has to be after all CPack variables are set
include(CPack)
