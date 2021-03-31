line_len=120

targets=jupyterblack/ tests/

# FORMAT ---------------------------------------------------------------------------------------------------------------
fmt: black isort docformatter autoflake

black:
	black $(targets)

isort:
	isort -m 2 -l $(line_len) $(targets)

docformatter:
	docformatter --in-place --wrap-summaries=$(line_len) --wrap-descriptions=$(line_len) -r $(targets)

autoflake:
	autoflake --in-place --remove-all-unused-imports -r $(targets)

# LINT -----------------------------------------------------------------------------------------------------------------
lint: docformatter-check isort-check black-check autoflake-check flake8 pylint

black-check:
	black --check $(targets)


docformatter-check:
	docformatter --wrap-summaries=$(line_len) --wrap-descriptions=$(line_len) -r $(targets) && \
	docformatter --check --wrap-summaries=$(line_len) --wrap-descriptions=$(line_len) -r $(targets)

isort-check:
	isort --diff --color --check-only -m 2 -l $(line_len) $(targets)

autoflake-check:
	autoflake --in-place --remove-all-unused-imports -r $(targets)

flake8:
	flake8 $(targets)

pylint:
	pylint $(targets)

# TYPE CHECK -----------------------------------------------------------------------------------------------------------
mypy:
	mypy --config-file mypy.ini $(targets)

# TEST -----------------------------------------------------------------------------------------------------------------
test:
	pytest -vv $(targets)


# CLEAN ----------------------------------------------------------------------------------------------------------------
clean-pyc:
	find . -name *.pyc | xargs rm -f && find . -name *.pyo | xargs rm -f;

clean-build:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info


# OTHERS  --------------------------------------------------------------------------------------------------------------
pre-commit: mypy flake8 isort docformatter

check-all: mypy lint test