if(BUILD_TESTING)
  add_subdirectory(tests_tumbook)
endif()

install(FILES "tumbook.sty" "tumbook.cls" "tumcover.cls"
        DESTINATION ${LATEX_PACKAGE_DIR}
)
