
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
if false ; then

    rm -rf $WASM_ENV_PREFIX

    micromamba create -n $WASM_ENV_NAME \
        --platform=emscripten-wasm32 \
        -c $OUTPUT_DIR \
        -c https://repo.prefix.dev/emscripten-forge-dev \
        --yes \
        "python>=3.13" xeus-python  ipywidgets box2d "pyb2d3>=0.5.6" "ipycanvas>=0.14.1"
fi

# ensure we make a fresh build
rm -rf deploy
mkdir -p deploy
cd deploy



#we mount pyb2d3_sandbox_ipycanvas and pyb2d3_sandbox instead
# of installing them into the environment
# this is because then we can iterate on these packages without rebuilding the emscripten-forge package
WASM_SIDE_PACKAGE_DIR="/lib/python3.13/site-packages/"
PYB2D3_SANDBOX_IPYCANVAS_DIR=$REPO_ROOT/companion_packages/pyb2d3_sandbox_ipycanvas/pyb2d3_sandbox_ipycanvas
PYB2D3_SANDBOX_DIR=$REPO_ROOT/companion_packages/pyb2d3_sandbox/pyb2d3_sandbox
SIDE_PACKAGE_DIR="/lib/python3.13/site-packages/"


jupyter lite build \
    --XeusAddon.prefix=$WASM_ENV_PREFIX \
    --contents=$CONTENT_DIR \
    --XeusAddon.mounts=$PYB2D3_SANDBOX_IPYCANVAS_DIR:$WASM_SIDE_PACKAGE_DIR/pyb2d3_sandbox_ipycanvas \
    --XeusAddon.mounts=$PYB2D3_SANDBOX_DIR:$WASM_SIDE_PACKAGE_DIR/pyb2d3_sandbox \
