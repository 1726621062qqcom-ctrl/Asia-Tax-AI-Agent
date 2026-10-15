# list to store loop generated targets
set(TUMFONTS_TARGETS "")

set(TEXTFONT_NAMES "helvet" "libertine" "palatino" "times")

latex_get_output_path(CMAKE_CURRENT_BINARY_DIR)

# default version with empty option strings
set(TEXTFONT "")
configure_file("test_tumfonts.tex"
               "${CMAKE_CURRENT_BINARY_DIR}/test_tumfonts_default.tex"
)
add_latex_document(
  "test_tumfonts_default.tex"
  INCLUDE_DIRECTORIES ${PROJECT_SOURCE_DIR}/commons
  FORCE_PDF
)

# loop through options
foreach(TF IN LISTS TEXTFONT_NAMES)
  set(TEXTFONT "font=${TF}")
  set(CURRENT_LATEX_TARGET "test_tumfonts_${TF}")
  list(APPEND TUMFONTS_TARGETS "${CURRENT_LATEX_TARGET}")
  configure_file("test_tumfonts.tex"
                  "${CMAKE_CURRENT_BINARY_DIR}/${CURRENT_LATEX_TARGET}.tex"
  )
  add_latex_document(
    "${CURRENT_LATEX_TARGET}.tex"
    INCLUDE_DIRECTORIES ${PROJECT_SOURCE_DIR}/commons
    FORCE_PDF
  )
endforeach()

add_custom_target(
  tests_tumfonts DEPENDS test_tumfonts_default "${TUMFONTS_TARGETS}"
)
