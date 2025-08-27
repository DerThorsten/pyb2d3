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
mkdir -p "$RECIPE_SRC_DIR"

# copy include,src,extra_licenses from REPO_ROOT to RECIPE_SRC_DIR
cp -r "$REPO_ROOT/include"              "$RECIPE_SRC_DIR/include"
cp -r "$REPO_ROOT/src"                  "$RECIPE_SRC_DIR/src"
cp -r "$REPO_ROOT/extra_licenses"       "$RECIPE_SRC_DIR/extra_licenses"
cp -r "$REPO_ROOT/companion_packages"   "$RECIPE_SRC_DIR/companion_packages"
cp    "$REPO_ROOT/CMakeLists.txt"       "$RECIPE_SRC_DIR/"
cp    "$REPO_ROOT/LICENSE"              "$RECIPE_SRC_DIR/"
cp    "$REPO_ROOT/pyproject.toml"    "$RECIPE_SRC_DIR/"


# replace PATH_PLACEHOLDER_TO_BE_REPLACED in the recipe.yaml.template with the actual path
# (ie the value of RECIPE_SRC_DIR)
sed "s|PATH_PLACEHOLDER_TO_BE_REPLACED|$RECIPE_SRC_DIR|g" "$RECIPE_YAML_TEMPLATE" > "$RECIPE_YAML"


VARIANT_URL="https://raw.githubusercontent.com/emscripten-forge/recipes/refs/heads/main/variant.yaml"
VARIANT_FILE="$EMSCRIPTEN_FORGE_DIR/variant.yaml"

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
    -c https://repo.prefix.dev/emscripten-forge-dev \
    -c microsoft \
    -c conda-forge \
    --target-platform emscripten-wasm32 \
    -m "$VARIANT_FILE" \
    --recipe "$RECIPE_DIR" \
    --output-dir "$OUTPUT_DIR" \
    ${EXTRA_ARGS[@]} \
