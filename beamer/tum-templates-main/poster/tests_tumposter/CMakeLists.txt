add_latex_document(
  test_tumposter_a0.tex
  INCLUDE_DIRECTORIES ${PROJECT_SOURCE_DIR}/commons
                      ${PROJECT_SOURCE_DIR}/poster
  BIBFILES sample.bib
  FORCE_PDF
)

add_latex_document(
  test_tumposter_a0_landscape.tex
  INCLUDE_DIRECTORIES ${PROJECT_SOURCE_DIR}/commons
                      ${PROJECT_SOURCE_DIR}/poster
  BIBFILES sample.bib
  FORCE_PDF
)

add_latex_document(
  test_tumposter_a1.tex
  INCLUDE_DIRECTORIES ${PROJECT_SOURCE_DIR}/commons
                      ${PROJECT_SOURCE_DIR}/poster
  BIBFILES sample.bib
  FORCE_PDF
)

add_latex_document(
  test_tumposter_a2.tex
  INCLUDE_DIRECTORIES ${PROJECT_SOURCE_DIR}/commons
                      ${PROJECT_SOURCE_DIR}/poster
  BIBFILES sample.bib
  FORCE_PDF
)

add_latex_document(
  test_tumposter_a3_landscape.tex
  INCLUDE_DIRECTORIES ${PROJECT_SOURCE_DIR}/commons
                      ${PROJECT_SOURCE_DIR}/poster
  BIBFILES sample.bib
  FORCE_PDF
)

add_custom_target(
  tests_tumposter
  DEPENDS test_tumposter_a0 test_tumposter_a0_landscape test_tumposter_a1
          test_tumposter_a2 test_tumposter_a3_landscape
)
