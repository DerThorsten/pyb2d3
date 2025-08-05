# this dir
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
REPO_ROOT=$DIR/..
REPO_ROOT=$(readlink -f "$REPO_ROOT")
EXAMPLES_DIR="$REPO_ROOT/examples"


cd $EXAMPLES_DIR


mkdir -p notebooks
for file in pyb2d3_samples/*.py; do
    filename=$(basename "$file")
    if [ "$filename" = "__init__.py" ]; then
        continue
    fi
    base="${filename%.py}"
    jupytext "$file" --to notebook --output "notebooks/${base}.ipynb"  --update-metadata '{"kernelspec": {"name": "xpython"}}'
done

cp -r pyb2d3_samples/examples_common/ notebooks/examples_common
