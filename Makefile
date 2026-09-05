.PHONY: test benchmark
test:
	PYTHONPATH=src python -m unittest discover -s tests -v
benchmark:
	PYTHONPATH=src python scripts/benchmark.py | tee benchmark-results.txt

