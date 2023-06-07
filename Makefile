<<<<<<< HEAD
PYTHON3 ?= python3

test1:
	$(PYTHON3) -m tests.test_simple
=======
.PHONY: test
test:
	pytest

.PHONY: test1
test1:
	python -m tests.test_simple -k asdf
>>>>>>> d4b6e50d2ba404bd9213ee07b3d23e7cc1a21071
