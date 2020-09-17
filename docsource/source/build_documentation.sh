sphinx-build -b html ./ ../../docs
sphinx-build -M markdown ./ ../../docs
printf "\n\n" >> ../../docs/markdown/README.md
mv ../../docs/markdown/README.md ../../README.md
cat ../../README.md  ../../docs/markdown/classes.md > ../../docs/markdown/docusaurus.md
