PYTHON3 ?= python3
PYTHON_TEST ?= pytest

.PHONY: test
test:
	$(PYTHON_TEST)

.PHONY: test1
test1:
	$(PYTHON3) -m tests.test_simple -k asdf

.PHONY: test2
test2: tests/test_durabletest_rdf.py
	$(PYTHON3) -m tests.test_durabletest_rdf
