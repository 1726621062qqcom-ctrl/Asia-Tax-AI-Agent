latex_get_output_path(CMAKE_CURRENT_BINARY_DIR)

# Default options

set(CLASSOPTIONS "")
configure_file("test_tumexam_en.tex"
               "${CMAKE_CURRENT_BINARY_DIR}/test_tumexam_en_default.tex"
)
add_latex_document(
  test_tumexam_en_default.tex
  INCLUDE_DIRECTORIES ${PROJECT_SOURCE_DIR}/commons ${PROJECT_SOURCE_DIR}/exam
  FORCE_PDF
)

set(CLASSOPTIONS "")
configure_file("test_tumexam_de.tex"
               "${CMAKE_CURRENT_BINARY_DIR}/test_tumexam_de_default.tex"
)
add_latex_document(
  test_tumexam_de_default.tex
  INCLUDE_DIRECTORIES ${PROJECT_SOURCE_DIR}/commons ${PROJECT_SOURCE_DIR}/exam
  FORCE_PDF
)

# Times Font test 11pt

set(CLASSOPTIONS "11pt, font=times")
configure_file("test_tumexam_en.tex"
               "${CMAKE_CURRENT_BINARY_DIR}/test_tumexam_en_times_11pt.tex"
)
add_latex_document(
  test_tumexam_en_times_11pt.tex
  INCLUDE_DIRECTORIES ${PROJECT_SOURCE_DIR}/commons ${PROJECT_SOURCE_DIR}/exam
  FORCE_PDF
)

set(CLASSOPTIONS "11pt, font=times, answers")
configure_file(
  "test_tumexam_en.tex"
  "${CMAKE_CURRENT_BINARY_DIR}/test_tumexam_en_times_11pt-answers.tex"
)
add_latex_document(
  test_tumexam_en_times_11pt-answers.tex
  INCLUDE_DIRECTORIES ${PROJECT_SOURCE_DIR}/commons ${PROJECT_SOURCE_DIR}/exam
  FORCE_PDF
)

set(CLASSOPTIONS "11pt, font=times")
configure_file("test_tumexam_de.tex"
               "${CMAKE_CURRENT_BINARY_DIR}/test_tumexam_de_times_11pt.tex"
)
add_latex_document(
  test_tumexam_de_times_11pt.tex
  INCLUDE_DIRECTORIES ${PROJECT_SOURCE_DIR}/commons ${PROJECT_SOURCE_DIR}/exam
  FORCE_PDF
)

set(CLASSOPTIONS "11pt, font=times, answers")
configure_file(
  "test_tumexam_de.tex"
  "${CMAKE_CURRENT_BINARY_DIR}/test_tumexam_de_times_11pt-answers.tex"
)
add_latex_document(
  test_tumexam_de_times_11pt-answers.tex
  INCLUDE_DIRECTORIES ${PROJECT_SOURCE_DIR}/commons ${PROJECT_SOURCE_DIR}/exam
  FORCE_PDF
)

# Helvetica Font test 11pt

set(CLASSOPTIONS "11pt, font=helvet")
configure_file("test_tumexam_en.tex"
               "${CMAKE_CURRENT_BINARY_DIR}/test_tumexam_en_helvet_11pt.tex"
)
add_latex_document(
  test_tumexam_en_helvet_11pt.tex
  INCLUDE_DIRECTORIES ${PROJECT_SOURCE_DIR}/commons ${PROJECT_SOURCE_DIR}/exam
  FORCE_PDF
)

set(CLASSOPTIONS "11pt, font=helvet, answers")
configure_file(
  "test_tumexam_en.tex"
  "${CMAKE_CURRENT_BINARY_DIR}/test_tumexam_en_helvet_11pt-answers.tex"
)
add_latex_document(
  test_tumexam_en_helvet_11pt-answers.tex
  INCLUDE_DIRECTORIES ${PROJECT_SOURCE_DIR}/commons ${PROJECT_SOURCE_DIR}/exam
  FORCE_PDF
)

set(CLASSOPTIONS "11pt, font=helvet")
configure_file("test_tumexam_de.tex"
               "${CMAKE_CURRENT_BINARY_DIR}/test_tumexam_de_helvet_11pt.tex"
)
add_latex_document(
  test_tumexam_de_helvet_11pt.tex
  INCLUDE_DIRECTORIES ${PROJECT_SOURCE_DIR}/commons ${PROJECT_SOURCE_DIR}/exam
  FORCE_PDF
)

set(CLASSOPTIONS "11pt, font=helvet, answers")
configure_file(
  "test_tumexam_de.tex"
  "${CMAKE_CURRENT_BINARY_DIR}/test_tumexam_de_helvet_11pt-answers.tex"
)
add_latex_document(
  test_tumexam_de_helvet_11pt-answers.tex
  INCLUDE_DIRECTORIES ${PROJECT_SOURCE_DIR}/commons ${PROJECT_SOURCE_DIR}/exam
  FORCE_PDF
)

# Libertine Font test 11pt

set(CLASSOPTIONS "11pt, font=libertine")
configure_file(
  "test_tumexam_en.tex"
  "${CMAKE_CURRENT_BINARY_DIR}/test_tumexam_en_libertine_11pt.tex"
)
add_latex_document(
  test_tumexam_en_libertine_11pt.tex
  INCLUDE_DIRECTORIES ${PROJECT_SOURCE_DIR}/commons ${PROJECT_SOURCE_DIR}/exam
  FORCE_PDF
)

set(CLASSOPTIONS "11pt, font=libertine, answers")
configure_file(
  "test_tumexam_en.tex"
  "${CMAKE_CURRENT_BINARY_DIR}/test_tumexam_en_libertine_11pt-answers.tex"
)
add_latex_document(
  test_tumexam_en_libertine_11pt-answers.tex
  INCLUDE_DIRECTORIES ${PROJECT_SOURCE_DIR}/commons ${PROJECT_SOURCE_DIR}/exam
  FORCE_PDF
)

set(CLASSOPTIONS "11pt, font=libertine")
configure_file(
  "test_tumexam_de.tex"
  "${CMAKE_CURRENT_BINARY_DIR}/test_tumexam_de_libertine_11pt.tex"
)
add_latex_document(
  test_tumexam_de_libertine_11pt.tex
  INCLUDE_DIRECTORIES ${PROJECT_SOURCE_DIR}/commons ${PROJECT_SOURCE_DIR}/exam
  FORCE_PDF
)

set(CLASSOPTIONS "11pt, font=libertine, answers")
configure_file(
  "test_tumexam_de.tex"
  "${CMAKE_CURRENT_BINARY_DIR}/test_tumexam_de_libertine_11pt-answers.tex"
)
add_latex_document(
  test_tumexam_de_libertine_11pt-answers.tex
  INCLUDE_DIRECTORIES ${PROJECT_SOURCE_DIR}/commons ${PROJECT_SOURCE_DIR}/exam
  FORCE_PDF
)

# Palatino Font test 11pt

set(CLASSOPTIONS "11pt, font=palatino")
configure_file("test_tumexam_en.tex"
               "${CMAKE_CURRENT_BINARY_DIR}/test_tumexam_en_palatino_11pt.tex"
)
add_latex_document(
  test_tumexam_en_palatino_11pt.tex
  INCLUDE_DIRECTORIES ${PROJECT_SOURCE_DIR}/commons ${PROJECT_SOURCE_DIR}/exam
  FORCE_PDF
)

set(CLASSOPTIONS "11pt, font=palatino, answers")
configure_file(
  "test_tumexam_en.tex"
  "${CMAKE_CURRENT_BINARY_DIR}/test_tumexam_en_palatino_11pt-answers.tex"
)
add_latex_document(
  test_tumexam_en_palatino_11pt-answers.tex
  INCLUDE_DIRECTORIES ${PROJECT_SOURCE_DIR}/commons ${PROJECT_SOURCE_DIR}/exam
  FORCE_PDF
)

set(CLASSOPTIONS "11pt, font=palatino")
configure_file("test_tumexam_de.tex"
               "${CMAKE_CURRENT_BINARY_DIR}/test_tumexam_de_palatino_11pt.tex"
)
add_latex_document(
  test_tumexam_de_palatino_11pt.tex
  INCLUDE_DIRECTORIES ${PROJECT_SOURCE_DIR}/commons ${PROJECT_SOURCE_DIR}/exam
  FORCE_PDF
)

set(CLASSOPTIONS "11pt, font=palatino, answers")
configure_file(
  "test_tumexam_de.tex"
  "${CMAKE_CURRENT_BINARY_DIR}/test_tumexam_de_palatino_11pt-answers.tex"
)
add_latex_document(
  test_tumexam_de_palatino_11pt-answers.tex
  INCLUDE_DIRECTORIES ${PROJECT_SOURCE_DIR}/commons ${PROJECT_SOURCE_DIR}/exam
  FORCE_PDF
)

# Multirow question table

set(CLASSOPTIONS "")
configure_file(
  "test_tumexam_multirow_en.tex"
  "${CMAKE_CURRENT_BINARY_DIR}/test_tumexam_multirow_en_default.tex"
)
add_latex_document(
  test_tumexam_multirow_en_default.tex
  INCLUDE_DIRECTORIES ${PROJECT_SOURCE_DIR}/commons ${PROJECT_SOURCE_DIR}/exam
  FORCE_PDF
)

set(CLASSOPTIONS "")
configure_file(
  "test_tumexam_multirow_de.tex"
  "${CMAKE_CURRENT_BINARY_DIR}/test_tumexam_multirow_de_default.tex"
)
add_latex_document(
  test_tumexam_multirow_de_default.tex
  INCLUDE_DIRECTORIES ${PROJECT_SOURCE_DIR}/commons ${PROJECT_SOURCE_DIR}/exam
  FORCE_PDF
)

add_custom_target(
  tests_tumexam
  DEPENDS test_tumexam_en_default
          test_tumexam_de_default
          test_tumexam_en_helvet_11pt
          test_tumexam_en_helvet_11pt-answers
          test_tumexam_de_helvet_11pt
          test_tumexam_de_helvet_11pt-answers
          test_tumexam_en_libertine_11pt
          test_tumexam_en_libertine_11pt-answers
          test_tumexam_de_libertine_11pt
          test_tumexam_de_libertine_11pt-answers
          test_tumexam_en_palatino_11pt
          test_tumexam_en_palatino_11pt-answers
          test_tumexam_de_palatino_11pt
          test_tumexam_de_palatino_11pt-answers
          test_tumexam_en_times_11pt
          test_tumexam_en_times_11pt-answers
          test_tumexam_de_times_11pt
          test_tumexam_de_times_11pt-answers
          test_tumexam_multirow_de_default
          test_tumexam_multirow_en_default
)
