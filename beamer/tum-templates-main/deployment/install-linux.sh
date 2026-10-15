#!/bin/bash

# default installation directory is TEXMFLOCAL
TEXDIR=$(kpsewhich -var-value=TEXMFLOCAL)

# flags for user interaction and privileges
WAITFLAG=true
USERFLAG=false

# switches to change installation directory
for i in "$@"; do
  case $i in
    --user)
      TEXDIR=$(kpsewhich -var-value=TEXMFHOME)
      USERFLAG=true
      shift
      ;;
    --dir=*)
      TEXDIR="${i#*=}"
      shift
      ;;
    -y | --yes)
      WAITFLAG=false
      shift
      ;;
    *) ;; # unknown option
  esac
done

echo "The @PRETTY_PROJECT_NAME@ will be installed to '$TEXDIR'."

while $WAITFLAG; do
  read -r -p "Continue installation? [y|n] " yn
  case $yn in
    [Yy]*) break ;;
    [Nn]*)
      echo "@PRETTY_PROJECT_NAME@ installation aborted!"
      exit
      ;;
    *) ;;
  esac
done

# append tex/latex for proper TeX Directory Structure (TDS)
INSTALLDIR="$TEXDIR/tex/latex/"
# make directory if not present and copy files
mkdir -p "$INSTALLDIR"
if ! cp -r "@LATEX_PACKAGE_DIR@" "$INSTALLDIR"; then
  echo "@PRETTY_PROJECT_NAME@ installation failed!"
  exit
fi

# update texmf filename database (only for root installation)
if ! $USERFLAG; then
  mktexlsr
fi

echo "@PRETTY_PROJECT_NAME@ successfully installed."
