# Changelog

All notable changes to this project will be documented in this file.

The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.0.0] - 2024-05-24

### Added

- Support for TeXLive 2023 and 2024.
- Support for LuaLaTeX through fontspec and unicode-math.
- Package `tummath` for common math notation.
- Documentclass `tumexam` for exams.
- Class option `handout=simple` in `tumbeamer`.
- Support for alerting in math mode in `tumbeamer`.
- TUM Tower resource as vector graphic.

### Changed

- Rename macro `\theDepartmentName` to `\theSchoolName`.
- Rename macro `\theChairName` to `\theGroupName`.
- Update PhD title page in `tumbook`.

### Removed

- Support for TeXLive 2017, 2018, and 2019.
- Support for layout with department logo in `tumbeamer` and `tumpage`.
- Package option `mahtfont` in `tumfonts`.
- Redefiniton of standard colors in `tumcolors`.

## [2.0.0] - 2021-04-19

### Added

- Documentclass `tumbook` for lecture notes and theses.
- Documentclass `tumcover` for book covers.
- Documentclass `tumletter` for letters.
- Documentclass `tumposter` for scientific posters.
- Implement scaling factor for TUM tower in `tumbeamer` class.
- Configure pdf metadata to `tumarticle` and `tumbeamer` classes.
- Implement bindingoffset, headmarks, background colors, and additional
  fontsize H4 in `tumpage` package.
- Implement TUMBoxInverse and TUMBoxBlank in `tumboxes` package
- CI support for XeLaTeX and LuaLaTeX compilers.
- Automatic formatting and linting of shell files.
- Deployment for Overleaf templates.
- CODEOWNERS file.

### Changed

- Use layers and pagestyles provided by `tumpage` in `tumarticle` class.
- Layout activation macro and headline handling in `tumpage` package.
- Load scalable roman font with helvet and consistently load helvet as
 sans serif font in `tumfonts` package.
- Replace ifsym with marvosym package for the letter symbol in `tumauthblk`
 package because of compatibility issues with Overleaf 2020.
- Windows installer automatically deduces installation path.

### Removed

- Compatibility macros in `tumpage` package.

## [1.0.0] - 2020-10-01

This is the first stable release that provides document classes for article
and presentation.

### Added

- Base packages that define the TUM CD colors, fonts, etc.
- Personalization support (e.g., adjust name of the chair or group).
- Documentclass `tumarticle` for scientific papers and small documents.
- Documentclass `tumbeamer` for presentations.
- Automated test builds using the CMake build system.
- Automatic formatting of LaTeX code.
- Support for continuous integration (CI) using `gitlab-ci`.
- Support for automated deployment (.deb, .msi, .tar.gz installers).
