if(BUILD_TESTING)
  add_subdirectory(tests_tumbeamer)
endif()

install(FILES "tumbeamer.cls" DESTINATION ${LATEX_PACKAGE_DIR})
