# define directories to exclude from auto-formatting
EXCLUDES = \( -path './build/*' -o -path './cmake/*' -o -path './venv/*' \)
# define helper function to find files for auto-formatting
file_finder = find . -type f $(1) -not $(EXCLUDES)
# define file filters for auto-formatting
CMAKE_FILTER = \( -name '*.cmake' -o -name 'CMakeLists.txt' \)
LATEX_FILTER = -regex '.*\.\(cls\|sty\|tex\)'
SH_FILTER = -name '*.sh'
# find and store files for auto-formatting
CMAKE_FILES = $(shell $(call file_finder, $(CMAKE_FILTER)))
LATEX_FILES = $(shell $(call file_finder, $(LATEX_FILTER)))
SH_FILES = $(shell $(call file_finder, $(SH_FILTER)))

# define cruft directory for latexindent
CRUFT_DIR = $(shell pwd)/build/format

LATEST_RELEASE=$(shell git tag --sort=committerdate | tail -1)

.PHONY: docs
docs:
	cd docs && docker compose run -e RELEASE_VERSION=$(LATEST_RELEASE) html
	cd docs && docker compose run -e RELEASE_VERSION=$(LATEST_RELEASE) pdf

# targets to apply auto-formatting to files in-place
format: format_cmake format_latex format_sh

format_cmake:
	@for src in $(CMAKE_FILES); do \
		echo "-- Formatting CMake file $$src"; \
		cmake-format --in-place $$src; \
	done

format_latex:
	@mkdir -p $(CRUFT_DIR)
	@for src in $(LATEX_FILES); do \
		echo "-- Formatting LaTeX file $$src"; \
		latexindent --silent --cruft=$(CRUFT_DIR) \
			--local --modifylinebreaks --overwrite $$src; \
	done

format_sh:
	@echo "-- Formatting shell script files"
	@shfmt -l -w .

# targets to check file formatting
check_format: check_format_cmake check_format_latex check_format_sh

check_format_cmake:
	@for src in $(CMAKE_FILES); do \
		echo "-- Checking format of CMake file $$src"; \
		cmake-format --check $$src; \
	done

check_format_latex:
	@mkdir -p $(CRUFT_DIR)
	@for src in $(LATEX_FILES); do \
		echo "--Checking format of LaTeX file $$src"; \
		latexindent --silent --cruft=$(CRUFT_DIR) \
			--local --modifylinebreaks --check $$src || exit $$?; \
	done

check_format_sh:
	@echo "-- Checking format of shell script files"
	@shfmt -d .

shellcheck:
	@shellcheck $(SH_FILES)
