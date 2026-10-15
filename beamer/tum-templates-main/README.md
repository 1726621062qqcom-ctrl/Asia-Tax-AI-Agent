# TUM Templates

<!-- badges -->

[![pipeline][pipeline-badge]][pipeline-page]
[![release][release-badge]][release-page]
[![package][package-badge]][package-registry]
[![container][container-badge]][container-project]
[![overleaf][overleaf-badge]][sharelatex-tum]

<!-- links -->

[pipeline-badge]: https://gitlab.lrz.de/latex4ei/tum-templates/badges/main/pipeline.svg
[pipeline-page]: https://gitlab.lrz.de/latex4ei/tum-templates/-/pipelines?ref=main

[release-badge]: https://img.shields.io/badge/release-v3.0.0-blue
[release-page]: https://gitlab.lrz.de/latex4ei/tum-templates/-/releases

[package-badge]: https://img.shields.io/badge/package-tum--templates-blue?logo=gitlfs&logoColor=white
[package-registry]: https://gitlab.lrz.de/latex4ei/tum-templates/-/packages

[container-badge]: https://img.shields.io/badge/container-texlive--tum-blue?logo=docker&logoColor=white
[container-project]: https://gitlab.lrz.de/latex4ei/texlive-tum

[overleaf-badge]: https://img.shields.io/badge/overleaf-sharelatex.tum.de-47a141?logo=overleaf&logoColor=white
[sharelatex-tum]: https://sharelatex.tum.de

[tum-cd]: https://portal.mytum.de/corporatedesign/regeln/index_styleguide

[miktex]: https://miktex.org/download
[texlive]: https://www.tug.org/texlive

<!-- table of contents-->

- [Features](#features)
  - [LaTeX classes](#latex-classes)
  - [LaTeX packages](#latex-packages)
  - [Personalization](#personalization)
- [How to get the templates](#how-to-get-the-templates)
- [Installation](#installation)
  - [Windows](#windows)
  - [Debian-based Linux distributions](#debian-based-linux-distributions)
  - [Other Linux distributions](#other-linux-distributions)
  - [Build from source](#build-from-source)
- [Bug Reports, Suggestions and Feedback](#bug-reports-suggestions-and-feedback)
- [Contributing](#contributing)
- [License Notes](#license-notes)

## Features

We provide comprehensive and easy-to-use LaTeX classes and packages for
TUM employees and students.
Our aim is to facilitate the creation of commonly needed document types in
research and teaching at TUM.
The provided classes follow the [TUM Corporate Design Manual][tum-cd]
as closely as possible.

### LaTeX classes

| LaTeX class  | Document type                   |
| ------------ | ------------------------------- |
| `tumarticle` | Scientific articles and reports |
| `tumbeamer`  | Presentations                   |
| `tumbook`    | Theses and lecture notes        |
| `tumexam`    | Exams                           |
| `tumletter`  | Letters                         |
| `tumposter`  | Posters                         |

### LaTeX packages

| LaTeX package | Description                                 |
| ------------- | ------------------------------------------- |
| `tumboxes`    | Colored boxes for posters and presentations |
| `tumcolors`   | Provides the TUM color scheme               |
| `tumlogo`     | Provides the TUM logo                       |
| `tummath`     | Common mathematical notation                |
| `tumuser`     | Personalization                             |

### Personalization

Macros intended for customization by the user are defined in the `tumuser`
package. The `tumuser.sty` file distributed with the TUM templates is
intended as a guideline and should be overwritten by the user.

The `tumuser` package can be overwritten in multiple places:

- in the project directory for project-level customization
- in the `TEXMFHOME` directory for user-level customization
- in the `TEXMFLOCAL` directory for system-wide customization

LaTeX will load the `tumuser` package from the first location it finds it.

To ensure metadata such as group name, school name, address, etc. is correct,
admins can distribute a customized `tumuser` package with a configuration
management tool (e.g. group policy for Windows or ansible for Linux) to all
managed employee and student computers. Or provide it as a simple download
from the group website or a git repository.

## How to get the templates

We provide installers for both Windows and Linux systems.
Links to the installers can be found on our [Releases Page][release-page]
and in our [Package Registry][package-registry]. In addition to all the
released versions, you can find packages of the most recent development
version of our templates in the [Package Registry][package-registry].

If you want to automatically build LaTeX documents in your CI/CD pipelines,
we provide ready-to-use docker container images with TeXLive and
pre-installed TUM templates in our
[TeXLive TUM docker images][container-project] project.

The [ShareLaTeX][sharelatex-tum] service hosted by TUM provides project
templates for all our LaTeX classes. Just click on *New Project* and select
the template you would like to use.
If you want to use the same templates but on a different service, you can
download the *overleaf-templates* package from our
[Package Registry][package-registry].

## Installation

Make sure you have a working LaTeX environment installed.
We support [TeX Live][texlive] versions above 2020 and
[MiKTeX][miktex] above version 20.6.

### Windows

If you use MiKTeX, we recommend to install all packages via the
MiKTeX Package Manager to ensure all required fonts and packages are
installed and up to date.

```powershell
mpm --admin --verbose --package-level=complete --update --upgrade
```

Our windows installer will search for your LaTeX environment automatically
and use the correct installation directory. The TeXLive or MiKTeX binaries
must be in your `PATH`. Our installer will abort if no binaries were found.

For a silent installation use the `/S` switch and choose either
`/AllUsers` or `/CurrentUser` to control wheter you want a system wide
installation or not.

### Debian-based Linux distributions

If you use a Debian-based Linux distribution, you can install TeXLive
directly from your package manager.

We recommend to install `texlive-full` to ensure all required fonts and
packages are installed.

```shell
# install texlive from apt repository
sudo apt install texlive-full
# install our tum templates package
sudo apt install /<path>/<to>/tum-templates-v3.0.0.deb
```

### Other Linux distributions

Download and extract our `.tar.gz` package and run the provided bash script
with one of the following options.

```shell
# install tum templates system wide to TEXMFLOCAL
sudo bash install-linux.sh
# install tum templates with user privileges to TEXMFHOME
bash install-linux.sh --user
# install tum templates to a custom directory
bash install-linux.sh --dir="/custom/directory"
```

**Warning**:
If you install the TUM templates to a custom directory,
you have to add it to your TEXMF root directories manually.

### Build from source

An alternative way to install the TUM templates is to clone or download
this git repository and run the installation from the source files.
We use the CMake build framework.

```shell
mkdir -p build
cd build
# configure build without test documents
cmake .. -DBUILD_TESTING=OFF
# install tum templates to TEXMFHOME
make install DESTDIR=$(kpsewhich -var-value TEXMFHOME)
# install tum templates to a custom directory
make install DESTDIR=/custom/directory
```

**Warning**:
If you install the TUM templates to a custom directory,
you have to add it to your TEXMF root directories manually.

## Bug Reports, Suggestions and Feedback

If you encounter any bugs/errors or you have suggestions for new features and
improvements, please feel free to open an
[issue](https://gitlab.lrz.de/latex4ei/tum-templates/issues).
Please make sure to give a meaningful title, description, and label of the
issue.

In case of an error provide a minimal example that triggers the error and
state name and version of your operating system and LaTeX environment.

## Contributing

We are a small team of TUM students and employees maintaining this project,
so help is always very welcome!
If you are an experienced LaTeX user and you would like to contribute to the
project, please take a look at the [contributing guide](./CONTRIBUTING.md)
and start coding.

## License Notes

This project may be distributed and/or modified under the conditions of the
LaTeX Project Public License Version 1.3c.
