{
  description = "realtime-py: a Realtime python client.";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    pyproject-nix = {
      url = "github:pyproject-nix/pyproject.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { nixpkgs, pyproject-nix, ... }: let
    for-all-systems = f:
      nixpkgs.lib.genAttrs [
        "x86_64-linux"
        "aarch64-darwin"
        "aarch64-linux"
        "x86_64-darwin"
      ] (system: f nixpkgs.legacyPackages.${system});
    project = pyproject-nix.lib.project.loadPyproject {
      projectRoot = ./.;
    };
    dev-tools = pkgs: [
      pkgs.supabase-cli
    ];
    dependencies-for = pkgs: let
      # override to add top-level packages in nixpkgs as
      # python3.pkgs packages, so that the renderers can find them
      python = pkgs.python3.override {
        packageOverrides = self: super: {
          ruff = self.toPythonModule pkgs.ruff;
          pre-commit = self.toPythonModule pkgs.pre-commit;
          basedpyright = self.toPythonModule pkgs.basedpyright;
        };
      };
      all-dependencies = project.renderers.withPackages {
        inherit python;
        groups = [ "dev" ];
      };
      dependencies = builtins.groupBy (pkg: if python.pkgs.hasPythonModule pkg then "python" else "toplevel") (all-dependencies python);
    in {
      python-env = python.buildEnv.override {
        extraLibs = dependencies.python or [];
      };
      toplevel = dependencies.toplevel or [];
    };
  in {
    devShells = for-all-systems (pkgs: let
      inherit (dependencies-for pkgs) python-env toplevel;
    in {
      default = pkgs.mkShell {
        packages = [ python-env ] ++ (dev-tools pkgs) ++ toplevel;
      };
    });
  };
}
