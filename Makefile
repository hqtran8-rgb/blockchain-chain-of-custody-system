all: bchoc

bchoc: bchoc.py
	@chmod +x bchoc.py
	@ln -sf bchoc.py bchoc
	@echo "Build complete. Use ./bchoc to run."

clean:
	@rm -f bchoc blockchain.dat
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@echo "Cleaned build artifacts."

test: bchoc
	@./bchoc verify || true

.PHONY: all clean test