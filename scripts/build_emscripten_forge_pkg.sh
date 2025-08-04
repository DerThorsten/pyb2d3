# this dir
THIS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
REPO_ROOT=$THIS_DIR/..
REPO_ROOT=$(readlink -f "$REPO_ROOT")


EMSCRIPTEN_FORGE_DIR=$REPO_ROOT/emscripten_forge
RECIPE_DIR="$EMSCRIPTEN_FORGE_DIR/recipe"
RECIPE_YAML_TEMPLATE="$RECIPE_DIR/recipe.yaml.template"
RECIPE_YAML="$RECIPE_DIR/recipe.yaml"
OUTPUT_DIR="$EMSCRIPTEN_FORGE_DIR/output"

# replace PATH_PLACEHOLDER_TO_BE_REPLACED in the recipe.yaml.template with the actual path
# (ie the value of REPO_ROOT)
sed "s|PATH_PLACEHOLDER_TO_BE_REPLACED|$REPO_ROOT|g" "$RECIPE_YAML_TEMPLATE" > "$RECIPE_YAML"


VARIANT_URL="https://raw.githubusercontent.com/emscripten-forge/recipes/refs/heads/main/variant.yaml"
VARIANT_FILE="$EMSCRIPTEN_FORGE_DIR/variant.yaml"

# IF VARIANT_FILE does not exist, download it
if [ ! -f "$VARIANT_FILE" ]; then
    echo "Downloading variant file from $VARIANT_URL"
    curl -o "$VARIANT_FILE" "$VARIANT_URL"
else
    echo "Variant file already exists at $VARIANT_FILE"
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
    --test=skip \
