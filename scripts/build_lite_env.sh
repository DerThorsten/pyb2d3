
#dir of this script
THIS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
REPO_ROOT=$THIS_DIR/..
REPO_ROOT=$(readlink -f "$REPO_ROOT")

echo "REPO_ROOT: $REPO_ROOT"


# where is the freshly build emscripten-forge package?
EMSCRIPTEN_FORGE_DIR=$REPO_ROOT/emscripten_forge
OUTPUT_DIR="$EMSCRIPTEN_FORGE_DIR/output"



echo "EMSCRIPTEN_FORGE_DIR: $EMSCRIPTEN_FORGE_DIR"
echo "OUTPUT_DIR: $OUTPUT_DIR"


# content dir (ie where are the notebooks)
CONTENT_DIR=$REPO_ROOT/examples/notebooks


WASM_ENV_NAME=pyb2d3wasm
WASM_ENV_PREFIX=$MAMBA_ROOT_PREFIX/envs/$WASM_ENV_NAME

#  create the emscripten-forge package
if true ; then

    rm -rf $WASM_ENV_PREFIX

    micromamba create -n $WASM_ENV_NAME \
        --platform=emscripten-wasm32 \
        -c $OUTPUT_DIR \
        -c https://repo.prefix.dev/emscripten-forge-dev \
        --yes \
        "python>=3.13" \
        xeus-python  \
        ipywidgets \
        "ipycanvas>=0.14.1" \
        "pyb2d3>=0.5.6" \
        "pyb2d3-sandbox>=0.5.6" \
        "pyb2d3-sandbox-ipycanvas>=0.5.6" \
        "pillow"
fi
