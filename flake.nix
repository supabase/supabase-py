{
  description = "realtime-py: a Realtime python client.";

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
      sourcePreference = "wheel"; # or sourcePreference = "sdist";
    };

    python-for = pkgs: let
      extensions = pkgs.lib.composeManyExtensions [
        pyproject-build-systems.overlays.default
        workspace-overlay
      ];
      base-python = pkgs.callPackage pyproject-nix.build.packages {
        python = pkgs.python311;
      };
    in base-python.overrideScope extensions;
  in {
    devShells = for-all-systems (pkgs: let
      python = python-for pkgs;
      python-env = python.mkVirtualEnv "supabase-py" workspace.deps.all;
    in {
      default = pkgs.mkShell {
        packages = [ python-env ] ++ (dev-tools pkgs);
      };
    });
  };
}
