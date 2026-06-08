{
  description = "Supabase-py development flake";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    pyproject-nix = {
      url = "github:pyproject-nix/pyproject.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    uv2nix = {
      url = "github:pyproject-nix/uv2nix";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    pyproject-build-systems = {
      url = "github:pyproject-nix/build-system-pkgs";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.uv2nix.follows = "uv2nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { nixpkgs, pyproject-nix, uv2nix, pyproject-build-systems, ... }: let
    for-all-systems = f:
      nixpkgs.lib.genAttrs [
        "x86_64-linux"
        "aarch64-darwin"
        "aarch64-linux"
        "x86_64-darwin"
      ] (system: f nixpkgs.legacyPackages.${system});

    dev-tools = pkgs: [
      pkgs.supabase-cli
      pkgs.uv
      pkgs.gnumake
      pkgs.docker
    ];
    workspace = uv2nix.lib.workspace.loadWorkspace { workspaceRoot = ./.; };

    workspace-overlay = workspace.mkPyprojectOverlay {
      sourcePreference = "wheel";
    };

    editable-overlay = workspace.mkEditablePyprojectOverlay {
      root = "$REPO_ROOT";
    };

    pyproject-overlay = pkgs: final: prev: {
      ruamel-yaml-clib = prev.ruamel-yaml-clib.overrideAttrs (old: {
        nativeBuildInputs = old.nativeBuildInputs ++ [
          (final.resolveBuildSystem {
            setuptools = [];
          })
        ];
      });
      pyiceberg = prev.pyiceberg.overrideAttrs (old: {
        buildInputs = (old.buildInputs or []) ++ [ final.poetry-core ];
      });
      pyroaring = prev.pyroaring.overrideAttrs (old: {
        postPatch = (old.postPatch or "") + ''
          sed -i '1i from Cython.Build import cythonize' setup.py
          sed -i 's/ext_modules=[pyroaring_module]/ext_modules=[cythonize(pyroaring_module)]/' setup.py
        '';
        nativeBuildInputs = old.nativeBuildInputs ++ [
          (final.resolveBuildSystem {
            setuptools = [];
          })
          final.cython
        ];
      });
    };

    python-for = pkgs: let
      extensions = pkgs.lib.composeManyExtensions [
        pyproject-build-systems.overlays.default
        workspace-overlay
        editable-overlay
        (pyproject-overlay pkgs)
      ];
      base-python = pkgs.callPackage pyproject-nix.build.packages {
        python = pkgs.python314;
      };
    in base-python.overrideScope extensions;
  in {
    devShells = for-all-systems (pkgs: let
      python = python-for pkgs;
      python-env = python.mkVirtualEnv "supabase-py" workspace.deps.all;
    in {
      default = pkgs.mkShell {
        env = {
          # Don't create venv using uv
          UV_NO_SYNC = "1";

          # Force uv to use nixpkgs Python interpreter
          UV_PROJECT_ENVIRONMENT = python-env;
          UV_PYTHON = pkgs.python314.interpreter;

          # Prevent uv from downloading managed Python's
          UV_PYTHON_DOWNLOADS = "never";
        };
        shellHook = ''
          # Undo dependency propagation by nixpkgs.
          unset PYTHONPATH
          export REPO_ROOT=$(git rev-parse --show-toplevel)
        '';
        packages = [ python-env ] ++ (dev-tools pkgs);
      };
    });
    lib = for-all-systems (pkgs: { 
      python = python-for pkgs;
    });
  };
}
