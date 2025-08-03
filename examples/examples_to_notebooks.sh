mkdir -p notebooks
for file in pyb2d3_samples/*.py; do
    filename=$(basename "$file")
    if [ "$filename" = "__init__.py" ]; then
        continue
    fi
    base="${filename%.py}"
    jupytext "$file" --to notebook --output "notebooks/${base}.ipynb" --set-kernel python3
done

cp -r pyb2d3_samples/examples_common/ notebooks/examples_common