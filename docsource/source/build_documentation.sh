sphinx-build -b html ./ ../../docs
sphinx-build -M markdown ./ ../../docs
cp ../../docs/markdown/README.md ../../README.md
