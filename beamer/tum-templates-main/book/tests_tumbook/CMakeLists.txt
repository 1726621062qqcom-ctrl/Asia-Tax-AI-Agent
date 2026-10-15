add_latex_document(
  test_tumbook_default.tex
  INPUTS content/chapter1.tex content/chapter2.tex content/chapter3.tex
  INCLUDE_DIRECTORIES ${PROJECT_SOURCE_DIR}/commons ${PROJECT_SOURCE_DIR}/book
  BIBFILES content/literature.bib
  FORCE_PDF
)

add_latex_document(
  test_tumbook_headmarks.tex
  INPUTS content/chapter1.tex content/chapter2.tex content/chapter3.tex
  INCLUDE_DIRECTORIES ${PROJECT_SOURCE_DIR}/commons ${PROJECT_SOURCE_DIR}/book
  BIBFILES content/literature.bib
  FORCE_PDF
)

add_latex_document(
  test_tumbook_phd_a4paper.tex
  INPUTS content/chapter1.tex content/chapter2.tex content/chapter3.tex
         content/phd_metadata.tex
  INCLUDE_DIRECTORIES ${PROJECT_SOURCE_DIR}/commons ${PROJECT_SOURCE_DIR}/book
  BIBFILES content/literature.bib
  FORCE_PDF
)

add_latex_document(
  test_tumbook_phd_a5paper.tex
  INPUTS content/chapter1.tex content/chapter2.tex content/chapter3.tex
         content/phd_metadata.tex
  INCLUDE_DIRECTORIES ${PROJECT_SOURCE_DIR}/commons ${PROJECT_SOURCE_DIR}/book
  BIBFILES content/literature.bib
  FORCE_PDF
)

add_latex_document(
  test_tumbook_student_twoside.tex
  INPUTS content/chapter1.tex content/chapter2.tex content/chapter3.tex
  INCLUDE_DIRECTORIES ${PROJECT_SOURCE_DIR}/commons ${PROJECT_SOURCE_DIR}/book
  BIBFILES content/literature.bib
  FORCE_PDF
)

add_latex_document(
  test_tumbook_student_oneside.tex
  INPUTS content/chapter1.tex content/chapter2.tex content/chapter3.tex
  INCLUDE_DIRECTORIES ${PROJECT_SOURCE_DIR}/commons ${PROJECT_SOURCE_DIR}/book
  BIBFILES content/literature.bib
  FORCE_PDF
)

add_latex_document(
  test_tumcover_a4paper.tex
  INCLUDE_DIRECTORIES ${PROJECT_SOURCE_DIR}/commons ${PROJECT_SOURCE_DIR}/book
  FORCE_PDF
)

add_latex_document(
  test_tumcover_a5paper.tex
  INPUTS content/phd_metadata.tex
  INCLUDE_DIRECTORIES ${PROJECT_SOURCE_DIR}/commons ${PROJECT_SOURCE_DIR}/book
  FORCE_PDF
)

add_custom_target(
  tests_tumbook
  DEPENDS test_tumbook_default
          test_tumbook_headmarks
          test_tumbook_phd_a4paper
          test_tumbook_phd_a5paper
          test_tumbook_student_twoside
          test_tumbook_student_oneside
          test_tumcover_a4paper
          test_tumcover_a5paper
)
