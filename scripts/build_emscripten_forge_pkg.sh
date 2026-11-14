# this dir
THIS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
REPO_ROOT=$THIS_DIR/..
REPO_ROOT=$(readlink -f "$REPO_ROOT")


EMSCRIPTEN_FORGE_DIR=$REPO_ROOT/emscripten_forge
RECIPE_DIR="$EMSCRIPTEN_FORGE_DIR/recipe"
RECIPE_YAML_TEMPLATE="$RECIPE_DIR/recipe.yaml.template"
RECIPE_YAML="$RECIPE_DIR/recipe.yaml"
OUTPUT_DIR="$EMSCRIPTEN_FORGE_DIR/output"

# we copy only the relevant parts there
RECIPE_SRC_DIR="$EMSCRIPTEN_FORGE_DIR/recipe_src"
# start fresh, otherwise `cp -r` nests the dirs (include/include) and builds stale sources
rm -rf "$RECIPE_SRC_DIR"
mkdir -p "$RECIPE_SRC_DIR"

# copy include,src,extra_licenses from REPO_ROOT to RECIPE_SRC_DIR
cp -r "$REPO_ROOT/include"              "$RECIPE_SRC_DIR/include"
cp -r "$REPO_ROOT/src"                  "$RECIPE_SRC_DIR/src"
cp -r "$REPO_ROOT/extra_licenses"       "$RECIPE_SRC_DIR/extra_licenses"
cp    "$REPO_ROOT/CMakeLists.txt"       "$RECIPE_SRC_DIR/"
cp    "$REPO_ROOT/LICENSE"              "$RECIPE_SRC_DIR/"
cp    "$REPO_ROOT/pyproject.toml"       "$RECIPE_SRC_DIR/"


# the package version = the version of the sources (pyproject.toml): a stale
# version in the recipe lets a solver prefer a newer published pyb2d3
VERSION=$(sed -n 's/^version = "\(.*\)"/\1/p' "$REPO_ROOT/pyproject.toml" | head -n 1)
if [ -z "$VERSION" ]; then
    echo "could not read the version from $REPO_ROOT/pyproject.toml"
    exit 1
fi
echo "pyb2d3 version: $VERSION"

# replace the placeholders in the recipe.yaml.template with the actual path
# (ie the value of RECIPE_SRC_DIR) and the version
sed -e "s|PATH_PLACEHOLDER_TO_BE_REPLACED|$RECIPE_SRC_DIR|g" \
    -e "s|VERSION_PLACEHOLDER_TO_BE_REPLACED|$VERSION|g" \
    "$RECIPE_YAML_TEMPLATE" > "$RECIPE_YAML"


# emscripten-forge 6x: packages from the prefix channel emscripten-forge/6x,
# pinnings from the emscripten-6x branch of the recipes repo
EMSCRIPTEN_FORGE_CHANNEL="https://repo.prefix.dev/emscripten-forge/6x"
VARIANT_URL="https://raw.githubusercontent.com/emscripten-forge/recipes/refs/heads/emscripten-6x/variant.yaml"
VARIANT_FILE="$EMSCRIPTEN_FORGE_DIR/variant-6x.yaml"

# IF VARIANT_FILE does not exist, download it
if [ ! -f "$VARIANT_FILE" ]; then
    echo "Downloading variant file from $VARIANT_URL"
    curl -o "$VARIANT_FILE" "$VARIANT_URL"
else
    echo "Variant file already exists at $VARIANT_FILE"
fi


# get extra args
EXTRA_ARGS=()
if [ $# -gt 0 ]; then
    echo "Using extra args: $@"
    EXTRA_ARGS=("$@")
else
    echo "No extra args provided"
fi


rattler-build build \
    --package-format tar-bz2 \
    -c "$EMSCRIPTEN_FORGE_CHANNEL" \
    -c microsoft \
    -c conda-forge \
    --target-platform emscripten-wasm32 \
    -m "$VARIANT_FILE" \
    --recipe "$RECIPE_DIR" \
    --output-dir "$OUTPUT_DIR" \
    ${EXTRA_ARGS[@]} \
