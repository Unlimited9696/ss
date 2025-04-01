{pkgs}: {
  deps = [
    pkgs.zlib
    pkgs.xcodebuild
    pkgs.chromedriver
    pkgs.chromium
    pkgs.geckodriver
    pkgs.postgresql
    pkgs.openssl
  ];
}
