# RK800

## Build

*Installing Requirements*


```bash 
# python requirements (needed for linting as well)
pip install -r requirements.txt

# other requirements (if system has apt)
# NOTE: This installs android studio (needed for apk builds) you need to open it and accept the tos to be able to build the apk
./install_deps.sh

# downloads android toolchain to /opt/cross
sudo ./cross_comp.sh
```


*Make targets*
```bash 
all-targets                     daemon-android_arm32            debug-android_arm32
android_aarch64                 daemon-debug-android_aarch64    format
android_arm32                   daemon-debug-android_arm32      lint
apk                             daemon-release-android_aarch64  release
build                           daemon-release-android_arm32    release-android_aarch64
clean                           debug                           release-android_arm32
daemon-android_aarch64          debug-android_aarch64           wheel

```

`make wheel` will build the project as needed for install