if(BUILD_TESTING)
  add_subdirectory(tests_tumexam)
endif()

install(FILES "tumexam.cls" DESTINATION ${LATEX_PACKAGE_DIR})
