if(BUILD_TESTING)
  add_subdirectory(tests_tumposter)
endif()

install(FILES "tumposter.cls" DESTINATION ${LATEX_PACKAGE_DIR})
