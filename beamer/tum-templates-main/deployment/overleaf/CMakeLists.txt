set(overleaf_dir "${PROJECT_BINARY_DIR}/overleaf")

function(add_overleaf_template template_dir)
  # copy latexmkrc file to make overleaf aware of our packages and classes
  file(COPY "latexmkrc" DESTINATION "${overleaf_dir}/${template_dir}")
  # copy the tumuser.sty file to the project root for user customizations
  file(COPY "${PROJECT_SOURCE_DIR}/commons/tumuser.sty"
       DESTINATION "${overleaf_dir}/${template_dir}"
  )
  # copy the content of the template subdirectory to the project root
  file(COPY "${template_dir}/" DESTINATION "${overleaf_dir}/${template_dir}")
  # create a target that zips the entire template directory
  add_custom_target(
    overleaf_${template_dir}
    WORKING_DIRECTORY ${overleaf_dir}/${template_dir}
    # install our class and package files into the current working directory
    COMMAND ${CMAKE_COMMAND} --install ${PROJECT_BINARY_DIR} --prefix .
    # pack the current working directory into a .zip archive
    COMMAND ${CMAKE_COMMAND} -E tar cf ../${template_dir}.zip --format=zip .
  )
  # add the current template to the overleaf target
  add_dependencies(overleaf overleaf_${template_dir})
endfunction(add_overleaf_template)

# target to create all overleaf templates
add_custom_target(overleaf)

# add the overlaf template targets
add_overleaf_template(article)
add_overleaf_template(letter)
add_overleaf_template(poster)
add_overleaf_template(poster_boxed)
add_overleaf_template(presentation)
add_overleaf_template(thesis)
add_overleaf_template(phdthesis)
