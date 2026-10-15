latex_get_output_path(CMAKE_CURRENT_BINARY_DIR)

set(CLASSOPTIONS "")
configure_file("test_tumarticle.tex"
               "${CMAKE_CURRENT_BINARY_DIR}/test_tumarticle_default.tex"
)
add_latex_document(
  test_tumarticle_default.tex
  INCLUDE_DIRECTORIES ${PROJECT_SOURCE_DIR}/commons
                      ${PROJECT_SOURCE_DIR}/article
  IMAGES fig1.pdf fig2.png fig3.png
  FORCE_PDF
)

set(CLASSOPTIONS "font=libertine,twocolumn")
configure_file("test_tumarticle.tex"
               "${CMAKE_CURRENT_BINARY_DIR}/test_tumarticle_libertine.tex"
)
add_latex_document(
  test_tumarticle_libertine.tex
  INCLUDE_DIRECTORIES ${PROJECT_SOURCE_DIR}/commons
                      ${PROJECT_SOURCE_DIR}/article
  IMAGES fig1.pdf fig2.png fig3.png
  FORCE_PDF
)

set(CLASSOPTIONS "font=palatino")
configure_file("test_tumarticle.tex"
               "${CMAKE_CURRENT_BINARY_DIR}/test_tumarticle_palatino.tex"
)
add_latex_document(
  test_tumarticle_palatino.tex
  INCLUDE_DIRECTORIES ${PROJECT_SOURCE_DIR}/commons
                      ${PROJECT_SOURCE_DIR}/article
  IMAGES fig1.pdf fig2.png fig3.png
  FORCE_PDF
)

set(CLASSOPTIONS "font=times,twocolumn,printmail=oneline")
configure_file("test_tumarticle.tex"
               "${CMAKE_CURRENT_BINARY_DIR}/test_tumarticle_times.tex"
)
add_latex_document(
  test_tumarticle_times.tex
  INCLUDE_DIRECTORIES ${PROJECT_SOURCE_DIR}/commons
                      ${PROJECT_SOURCE_DIR}/article
  IMAGES fig1.pdf fig2.png fig3.png
  FORCE_PDF
)

add_custom_target(
  tests_tumarticle DEPENDS test_tumarticle_default test_tumarticle_libertine
                           test_tumarticle_palatino test_tumarticle_times
)
