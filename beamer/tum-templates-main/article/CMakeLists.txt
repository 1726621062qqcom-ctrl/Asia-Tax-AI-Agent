if(BUILD_TESTING)
  add_subdirectory(tests_tumarticle)
endif()

install(FILES "tumarticle.cls" DESTINATION ${LATEX_PACKAGE_DIR})
