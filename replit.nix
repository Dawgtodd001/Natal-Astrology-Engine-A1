{pkgs}: {
  deps = [
    pkgs.redis
    pkgs.libxcrypt
    pkgs.postgresql
    pkgs.openssl
  ];
}
