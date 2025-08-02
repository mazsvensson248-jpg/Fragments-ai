{ pkgs }: {
  deps = [
    pkgs.python310Full
    pkgs.ffmpeg
    pkgs.git
  ];

  env = {
    PYTHONUNBUFFERED = "1";
    PIP_DISABLE_PIP_VERSION_CHECK = "1";
  };

  languages.python.package = pkgs.python310Full;

  packages = [
    pkgs.python310Full
    pkgs.ffmpeg
  ];
}
