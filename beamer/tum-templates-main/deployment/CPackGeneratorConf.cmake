# Windows installer
if(CPACK_GENERATOR MATCHES "NSIS")
  set(CPACK_NSIS_PACKAGE_NAME "@PRETTY_PROJECT_NAME@")
  # directory with necessary plugin .dll files
  set(CPACK_NSIS_PLUGINDIR "@PROJECT_SOURCE_DIR@/deployment/NSIS")
  # default install directory in case no texlive or miktex installation found
  set(CPACK_NSIS_INSTALL_ROOT "$PROGRAMFILES\\@PRETTY_PROJECT_NAME@")
  set(CPACK_NSIS_INSTALL_ROOT_USER "$PROFILE\\@PRETTY_PROJECT_NAME@")
  # install subdirectory appended to ensure TeX Directory Structure (TDS)
  set(CPACK_PACKAGE_INSTALLDIR "tex/latex/")
  # include custom images
  set(CPACK_NSIS_MUI_WELCOMEFINISHPAGE_BITMAP
      "@PROJECT_SOURCE_DIR@/deployment/NSIS/wizard.bmp"
  )
  # include custom icon
  set(CPACK_NSIS_MUI_ICON "@PROJECT_SOURCE_DIR@/deployment/NSIS/tum.ico")
endif()

# Linux DEB installer
if(CPACK_GENERATOR MATCHES "DEB")
  set(CPACK_DEBIAN_PACKAGE_MAINTAINER "@CPACK_PACKAGE_VENDOR@")
  set(CPACK_DEBIAN_PACKAGE_HOMEPAGE "@CPACK_PACKAGE_HOMEPAGE_URL@")
  set(CPACK_DEBIAN_PACKAGE_SECTION "devel")
  set(CPACK_DEBIAN_PACKAGE_DEPENDS "texlive-base")
  set(CPACK_DEBIAN_PACKAGE_SUGGESTS "texlive-full")
  # location of TEXMFLOCAL for standard texlive installation
  set(CPACK_PACKAGING_INSTALL_PREFIX "/usr/local/share/texmf/tex/latex")
  # post installation script to update texmf filename database
  set(postinst_script "@PROJECT_SOURCE_DIR@/deployment/DEB/postinst")
  set(postrm_script "@PROJECT_SOURCE_DIR@/deployment/DEB/postrm")
  set(CPACK_DEBIAN_PACKAGE_CONTROL_EXTRA
      "${postinst_script};${postrm_script}"
  )
endif()

# Linux Script installer
if(CPACK_GENERATOR MATCHES "TGZ")
  # cache variables for later configuration
  set(PROJECT_SOURCE_DIR "@PROJECT_SOURCE_DIR@")
  set(PRETTY_PROJECT_NAME "@PRETTY_PROJECT_NAME@")
  set(LATEX_PACKAGE_DIR "@LATEX_PACKAGE_DIR@")
  # run cmake script to add additional files to archive
  set(CPACK_INSTALL_SCRIPT "@PROJECT_SOURCE_DIR@/deployment/AddScript.cmake")
endif()
