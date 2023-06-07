PYTHON3 ?= python3

.PHONY: test
test:
	pytest

.PHONY: test1
test1:
	$(PYTHON3) -m tests.test_simple -k asdf
