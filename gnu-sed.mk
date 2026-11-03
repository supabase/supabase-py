# build-sync recipes use GNU sed syntax. BSD sed (macOS default) fails midway
# and leaves _sync/ half-converted, so check before unasync touches any file.
SED := $(shell command -v gsed 2>/dev/null || echo sed)

.PHONY: gnu-sed
gnu-sed:
	@$(SED) --version 2>/dev/null | grep -q GNU || { echo "build-sync needs GNU sed: 'brew install gnu-sed' or 'nix develop'" >&2; exit 1; }
