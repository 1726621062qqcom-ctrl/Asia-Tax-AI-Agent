add_latex_document(
  test_tumbeamer_default.tex
  INPUTS content.tex
  INCLUDE_DIRECTORIES ${PROJECT_SOURCE_DIR}/commons
                      ${PROJECT_SOURCE_DIR}/beamer
  FORCE_PDF
)

add_latex_document(
  test_tumbeamer_pretty.tex
  INPUTS content.tex
  INCLUDE_DIRECTORIES ${PROJECT_SOURCE_DIR}/commons
                      ${PROJECT_SOURCE_DIR}/beamer
  FORCE_PDF
)

add_latex_document(
  test_tumbeamer_flags.tex
  INPUTS content.tex
  INCLUDE_DIRECTORIES ${PROJECT_SOURCE_DIR}/commons
                      ${PROJECT_SOURCE_DIR}/beamer
  FORCE_PDF
)

add_latex_document(
  test_tumbeamer_handout_21.tex
  INPUTS content.tex
  INCLUDE_DIRECTORIES ${PROJECT_SOURCE_DIR}/commons
                      ${PROJECT_SOURCE_DIR}/beamer
  FORCE_PDF
)

add_latex_document(
  test_tumbeamer_handout_41.tex
  INPUTS content.tex
  INCLUDE_DIRECTORIES ${PROJECT_SOURCE_DIR}/commons
                      ${PROJECT_SOURCE_DIR}/beamer
  FORCE_PDF
)

add_latex_document(
  test_tumbeamer_handout_simple.tex
  INPUTS content.tex
  INCLUDE_DIRECTORIES ${PROJECT_SOURCE_DIR}/commons
                      ${PROJECT_SOURCE_DIR}/beamer
  FORCE_PDF
)

add_latex_document(
  test_tumbeamer_43_default.tex
  INPUTS content.tex
  INCLUDE_DIRECTORIES ${PROJECT_SOURCE_DIR}/commons
                      ${PROJECT_SOURCE_DIR}/beamer
  FORCE_PDF
)

add_latex_document(
  test_tumbeamer_43_pretty.tex
  INPUTS content.tex
  INCLUDE_DIRECTORIES ${PROJECT_SOURCE_DIR}/commons
                      ${PROJECT_SOURCE_DIR}/beamer
  FORCE_PDF
)

add_latex_document(
  test_tumbeamer_43_flags.tex
  INPUTS content.tex
  INCLUDE_DIRECTORIES ${PROJECT_SOURCE_DIR}/commons
                      ${PROJECT_SOURCE_DIR}/beamer
  FORCE_PDF
)

add_custom_target(
  tests_tumbeamer
  DEPENDS test_tumbeamer_default
          test_tumbeamer_pretty
          test_tumbeamer_flags
          test_tumbeamer_43_default
          test_tumbeamer_43_pretty
          test_tumbeamer_43_flags
          test_tumbeamer_handout_21
          test_tumbeamer_handout_41
          test_tumbeamer_handout_simple
)
