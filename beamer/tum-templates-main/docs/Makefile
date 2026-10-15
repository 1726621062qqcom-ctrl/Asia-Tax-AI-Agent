html:
	asciidoctor --backend html5 --attribute data-uri --attribute release-version=$(RELEASE_VERSION) --destination-dir output 'index.adoc'

pdf:
	asciidoctor-pdf --require asciidoctor-mathematical -a pdf-theme=theme/tum.yml --attribute release-version=$(RELEASE_VERSION) --destination-dir output 'index.adoc'
