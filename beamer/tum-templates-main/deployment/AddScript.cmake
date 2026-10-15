# include additional bash install script in TGZ archive
configure_file("${PROJECT_SOURCE_DIR}/deployment/install-linux.sh"
               "${CMAKE_INSTALL_PREFIX}/install-linux.sh" @ONLY
)
