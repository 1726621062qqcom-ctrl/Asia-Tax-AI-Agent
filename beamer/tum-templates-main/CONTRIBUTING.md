# Contributing Guide

In this guide, we summarize useful information for developers and
contributors. Please make yourself familiar with the workflow and conventions
if you would like to contribute to this project, and don't hesitate to ask
a maintainer if you have any questions. We are a small team working on this
project in our (limited) spare time, and any help is very welcome!

- [Git Workflow](#git-workflow)
- [Build System](#build-system)
  - [Software dependencies](#software-dependencies)
  - [Build](#build)
  - [Test](#test)
  - [Format](#format)
- [Coding Conventions and Style Guide](#coding-conventions-and-style-guide)
  - [Project Structure](#project-structure)
  - [Formatting Rules](#formatting-rules)
  - [Macro Names](#macro-names)
  - [Key-Value System](#key-value-system)
- [Editor Setup](#editor-setup)
- [License Notes](#license-notes)

## Git Workflow

We follow the
[Git Feature Branch Workflow](https://www.atlassian.com/git/tutorials/comparing-workflows/feature-branch-workflow)
to develop new features and maintain the existing code base. This flow can be
summarized in the following steps:

- Every non-trivial change starts with an
  [issue](https://gitlab.lrz.de/latex4ei/tum-templates/issues).
  Please check if there is an existing issue addressing your concern or
  create one with a meaningful title, description, and a suitable label.

- Create a feature branch to work on the solution to an issue. The branch
  name should be related to the issue, e.g., include the issue number.
  All feature branches must base on the `main` branch.

  ```shell
  git checkout -b 153-new-feature origin/main
  ```

- Create a
  [merge request](https://gitlab.lrz.de/latex4ei/tum-templates/merge_requests)
  for your feature branch in GitLab early and start the title with `Draft`
  to mark it as "work in progress".

- Work on the solution to the issue, make commits to the feature branch,
  and push them to the repository to share and discuss your code changes
  with the other developers.

  ```shell
  git add <file list>
  git commit -m "meaningful commit message"
  git push
  ```

- Feel free to rearrange the commits on your feature branch.
  Use git rebase with e.g., squash, edit, reword (the interactive mode is
  very helpful).

  ```shell
  # Interactively rebase the last 5 commits
  git rebase -i HEAD~5
  ```

  In fact, it is your duty to provide clean and non-redundant commits before
  your code can be merged. Please note that it is not allowed to alter
  commits outside of the feature branch.

- Follow these rules for clean commit messages:
  - Make sure the author's name and e-mail address are set up correctly in
    the git settings.
  - Each commit is dedicated to one particular chunk of work.
  - The commit message has to contain the file name, package or class,
    which was modified.
  - If the commit addresses a particular issue, add the issue number.
  - The one-line commit message should be limited to 76 characters. If a
    detailed description is necessary, add a multi-line commit description.

    ```shell
    git commit -m ".gitignore: Added BibTeX output files."
    git commit -m "poster: Fixed indentation issue #325."
    ```

  - After each commit all continuous integration (CI) pipelines must pass,
    in particular the format pipeline (see the style guide below).

- Before your feature branch can be merged, you have to rebase it on top of
  the `main` branch, so a fast-forward merge is possible.

  ```shell
  git fetch --all
  git rebase main
  ```

- Once you feel your code is ready, assign the merge request to a
  maintainer and remove the `Draft` status of the request.

- The maintainer may require amendments or restart/continue the discussion.
  Otherwise the merge will be performed. The feature branch is removed
  during the merge.

## Build System

In the following section we introduce the build system we use, summarize
dependencies and useful commands.

We use the CMake build framework. The project
[UseLATEX](https://gitlab.kitware.com/kmorel/UseLATEX)
is used to compile LaTeX documents with CMake.

### Software dependencies

- **git** version control system ([project site](https://git-scm.com/))

  ```shell
  apt-get install git
  ```

- **CMake** version 3.13 or higher ([project site](https://cmake.org/))

  ```shell
  apt-get install cmake
  ```

- **latexindent** version 3.16 or higher
  ([project site](https://github.com/cmhughes/latexindent.pl))\
  The perl script is used for automatic formatting of LaTeX documents and
  it is distributed with TeXLive. It depends on the perl libraries
  `YAML::Tiny`, `File::HomeDir`, `Unicode::GCString`, `Log::Log4perl`,
  and `Log::Dispatch`, that may need to be installed separately.

  ```shell
  apt-get install libyaml-tiny-perl libfile-homedir-perl \
                  liblog-log4perl-perl liblog-dispatch-perl
  ```

- **cmake-format** version 0.6 or higher
  ([project site](https://github.com/cheshirekow/cmake_format))\
  This python module is used for automatic formatting of CMake documents.
  It requires `python3` and can be installed with `pip`.

  ```shell
  pip install cmake-format[YAML]
  ```

- **shellcheck**
  ([project site](https://github.com/shellcheck-py/shellcheck-py))\
  This python module is used for automatic linting of shell documents.
  It requires `python3` and can be installed with `pip`.

  ```shell
  pip install shellcheck-py
  ```

- **shfmt**
  ([project site](https://github.com/mvdan/sh))\
  This python module is used for automatic formatting of shell documents.
  It can be installed with snap.

  ```shell
  snap install shfmt
  ```

- **NSIS** Nullsoft Scriptable Install System
  ([project site](https://nsis.sourceforge.io/))\
  This package is needed to build the Windows installer. If you are just
  developing LaTeX classes and packages you don't need this.
  Installer build and distribution is done by GitLab CI/CD.

  ```shell
  apt-get install nsis
  ```

### Build

The entire project can be built with

```shell
mkdir -p build
cd build
cmake ..

# Build all tests, templates, and documentation
make

# Build installer packages
make package
```

The CMake variable `PDFLATEX_COMPILER` can be used to set the LaTeX compiler.
It defaults to `pdflatex`, but it might be set to `lualatex` or `xelatex`.\
**Caution:** This feature is mentioned in the UseLATEX documentation,
but not strictly supported.

```shell
cmake -D PDFLATEX_COMPILER:STRING=$(which lualatex) ..
```

### Test

We implement test cases for all classes and packages to ensure functionality.
Every option and macro should be triggered once by the test cases.
If packages or classes are extended, or new classes are implemented,
the contributor has to implement test cases for the new features.

```shell
# Execute single test
make test_<package>_<name>

# Execute all tests of one package or class
make tests_<package>

# Execute all tests
make tests
```

### Format

We use the tools `latexindent`, `shfmt` and `cmake-format` for automatic code
formatting and checking the format. Please refer to the next section for
details on our code conventions and style guide.
We provide settings for LaTeX (`format_latex_settings.yaml`)
and CMake (`format_cmake_settings.yaml`) that implement our style guide.
It is recommended to integrate these formating tools with our settings into
your editor.

Additionally, the project's `Makefile` provides commands to format all files
in the source directory.

```shell
# Format everything
make format

# Format CMake files
make format_cmake

# Format LaTeX files
make format_latex

# Format LaTeX files
make format_sh

# Check for correct format
make check_format
make check_format_cmake
make check_format_latex
make check_format_sh
```

New features can only be merged into the `main` branch if the format checks
are passed!

## Coding Conventions and Style Guide

In this section we summarize rules for the project's file structure,
formatting rules, and naming conventions.

### Project Structure

- Classes are located in subdirectories. The directory name corresponds to
  the class name.
- Packages that are used by multiple classes are located in the `commons`
  subdirectory.
- Package and class names are lower-case and start with the letters `tum`.
- Test cases are located in subdirectories named `tests_<package>`.
- The naming scheme for test cases is `test_<package>_<name>.tex`.

### Formatting Rules

The following rules ensure that redundant white space changes are avoided and
the source code is in an easily readable form:

- Indentation: Use two spaces. No tabs.
- The maximum line length is 78 characters (exception: verbatim content).
- Remove all trailing white space at the end of line.
- Add exactly one newline at the end of file.
- Use one empty line between your macro definitions.
- Avoid empty lines within your macro definitions.
- If your macro produces text output, use comment symbols `%` at the end of
  line to ensure no unintended whitespace is added.
- To structure long documents, you can group related code parts in sections
  starting with a comment of the following style.

  ```latex
  <2 empty lines>
  % .:: <section name>
  % -------------------------------------<repeat until column 78>
  <code>
  ```

- If you have to split your macros optional or mandatory arguments across
  multiple lines, use one indentation.
- The environment `\begin{}` and `\end{}` commands always have their own
  line.
- Use one indent for the environment's content.
- If you have to split the environment's optional or mandatory arguments
  across multiple lines, use two indentations.
- Vertically align `&` and `\\` in environments with alignment delimiters.
- in lists of key-value pairs, use one additional indentation for better
  readability.

  ```latex
  \pgfkeys{
    /TUM/my/key/.code = {
        <some code>
        <spread over multiple lines>
      },
    /TUM/another key/.code = {
        <some code>
      }
  }
  ```

### Macro Names

Macros for internal use only (i.e., the macros are only used by the same
package or class they are created in), the `@` symbol should be used as a
limiter, and the macros should use the prefix `tum`, e.g.,
`\@tum@margin@width@`.
At the beginning and the end of the macro name an `@` should be used for good
alignment with Boolean variables, e.g., `\if@tum@use@times@true`.

Macros that may be used by other classes, packages, or even by the end-user
in the document itself should be named in camel-case, e.g., `\TUMBlue`.
If the macro yields a certain output, the prefix `the` should be used, e.g.,
`\theSchoolName`.

### Key-Value System

We use a key-value system for package and class options as well as options for
macros. This gives the user an intuitive and easy to use, yet versatile
interface to configure and use our templates.

The LaTeX package [pgfkeys](https://ctan.org/pkg/pgfkeys) is used to define
and process keys. The [pgfopts](https://ctan.org/pkg/pgfopts) package adds
the functionality to process pgfkeys as package options.

- pgfkeys are organized in a key tree.
  The root directory for all keys is `/TUM`.
- pgfkeys that are used as package or class options should be located in a
  directory with the package or class name, e.g., `/TUM/tumarticle/option`.
- Keys that are processed as package options may not contain spaces.
- Keys that are only used as options for a specific macro should be
  located in a subdirectory corresponding the macro name,
  e.g., `/TUM/authors/orcid`.

## Editor Setup

We can recommend the editor
[Visual Studio Code](https://code.visualstudio.com/).
With a few extensions and settings we will describe in this section, it can
be configured to follow most of the aforementioned conventions automatically.

- Go to the extensions tab (Ctrl+Shift+X) and install the packages
  - [LaTeX Workshop](https://marketplace.visualstudio.com/items?itemName=James-Yu.latex-workshop)
    for language support, build system, pdf preview, and auto-formatting
  - [CMake](https://marketplace.visualstudio.com/items?itemName=twxs.cmake)
    for language support (highlighting and completion)
  - [CMake Tools](https://marketplace.visualstudio.com/items?itemName=ms-vscode.cmake-tools)
    for CMake build system support
  - [cmake-format](https://marketplace.visualstudio.com/items?itemName=cheshirekow.cmake-format)
    for auto-formatting

- Add the following configuration to your workspace settings

  ```json
  {
    "editor.rulers": [78],
    "editor.tabSize": 2,
    "files.insertFinalNewline": true,
    "files.trimFinalNewlines": true,
    "files.trimTrailingWhitespace": true,
    "cmakeFormat.args": [
      "-c=/<path to>/tum-templates/.cmake-format.yaml"
    ],
    "latex-workshop.latexindent.args": [
      "-m",
      "-c=%DIR%/",
      "-l=/<path to>/tum-templates/.latexindent.yaml",
      "%TMPFILE%"
    ]
  }
  ```

## License Notes

By contributing to this project you agree, that your code will be published
as part of this project under the license agreement explained on the
[main page](https://gitlab.lrz.de/latex4ei/tum-templates)
of this GitLab project.
