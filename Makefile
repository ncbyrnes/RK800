TARGETS = android_aarch64 android_arm32 android_x86_64
PROJECTS = client
ANDROID_NDK = /opt/cross/android-ndk-r28c-linux/android-ndk-r28c

android_aarch64_ABI = arm64-v8a
android_arm32_ABI = armeabi-v7a
android_x86_64_ABI = x86_64

CMAKE_COMMON_ARGS = -G "Unix Makefiles" -DCMAKE_MAKE_PROGRAM=/usr/bin/make
CMAKE_ANDROID_ARGS = -DCMAKE_TOOLCHAIN_FILE=$(ANDROID_NDK)/build/cmake/android.toolchain.cmake \
                     -DANDROID_NDK=$(ANDROID_NDK) -DANDROID_PLATFORM=android-21

.PHONY: lint format apk build clean debug release keystore $(TARGETS) all-targets debug-% release-% $(foreach proj,$(PROJECTS),$(proj)-debug-% $(proj)-release-% $(proj)-%)

build: debug

debug: debug-android_aarch64 debug-android_arm32 debug-android_x86_64

release: release-android_aarch64 release-android_arm32 release-android_x86_64

all-targets: $(TARGETS)

define TARGET_RULE
$(1):
	@mkdir -p build/$(1)
	@if echo "$(1)" | grep -q "^android_"; then \
		cmake -S . -B ./build/$(1) $(CMAKE_COMMON_ARGS) $(CMAKE_ANDROID_ARGS) -DANDROID_ABI=$($(1)_ABI); \
	else \
		cmake -S . -B ./build/$(1) $(CMAKE_COMMON_ARGS); \
	fi
	cmake --build ./build/$(1)

debug-$(1):
	@mkdir -p build/$(1)_debug
	@if echo "$(1)" | grep -q "^android_"; then \
		cmake -S . -B ./build/$(1)_debug $(CMAKE_COMMON_ARGS) $(CMAKE_ANDROID_ARGS) -DANDROID_ABI=$($(1)_ABI) -DCMAKE_BUILD_TYPE=Debug; \
	else \
		cmake -S . -B ./build/$(1)_debug $(CMAKE_COMMON_ARGS) -DCMAKE_BUILD_TYPE=Debug; \
	fi
	cmake --build ./build/$(1)_debug

release-$(1):
	@mkdir -p build/$(1)_release
	@if echo "$(1)" | grep -q "^android_"; then \
		cmake -S . -B ./build/$(1)_release $(CMAKE_COMMON_ARGS) $(CMAKE_ANDROID_ARGS) -DANDROID_ABI=$($(1)_ABI) -DCMAKE_BUILD_TYPE=Release; \
	else \
		cmake -S . -B ./build/$(1)_release $(CMAKE_COMMON_ARGS) -DCMAKE_BUILD_TYPE=Release; \
	fi
	cmake --build ./build/$(1)_release
endef

define PROJECT_TARGET_RULE
$(1)-$(2):
	@mkdir -p build/$(2)_$(1)
	@if echo "$(2)" | grep -q "^android_"; then \
		cmake -S . -B ./build/$(2)_$(1) $(CMAKE_COMMON_ARGS) $(CMAKE_ANDROID_ARGS) -DANDROID_ABI=$($(2)_ABI) -DBUILD_$(shell echo $(1) | tr a-z A-Z)=ON $(foreach p,$(filter-out $(1),$(PROJECTS)),-DBUILD_$(shell echo $(p) | tr a-z A-Z)=OFF); \
	else \
		cmake -S . -B ./build/$(2)_$(1) $(CMAKE_COMMON_ARGS) -DBUILD_$(shell echo $(1) | tr a-z A-Z)=ON $(foreach p,$(filter-out $(1),$(PROJECTS)),-DBUILD_$(shell echo $(p) | tr a-z A-Z)=OFF); \
	fi
	cmake --build ./build/$(2)_$(1)

$(1)-debug-$(2):
	@mkdir -p build/$(2)_debug_$(1)
	@if echo "$(2)" | grep -q "^android_"; then \
		cmake -S . -B ./build/$(2)_debug_$(1) $(CMAKE_COMMON_ARGS) $(CMAKE_ANDROID_ARGS) -DANDROID_ABI=$($(2)_ABI) -DCMAKE_BUILD_TYPE=Debug -DBUILD_$(shell echo $(1) | tr a-z A-Z)=ON $(foreach p,$(filter-out $(1),$(PROJECTS)),-DBUILD_$(shell echo $(p) | tr a-z A-Z)=OFF); \
	else \
		cmake -S . -B ./build/$(2)_debug_$(1) $(CMAKE_COMMON_ARGS) -DCMAKE_BUILD_TYPE=Debug -DBUILD_$(shell echo $(1) | tr a-z A-Z)=ON $(foreach p,$(filter-out $(1),$(PROJECTS)),-DBUILD_$(shell echo $(p) | tr a-z A-Z)=OFF); \
	fi
	cmake --build ./build/$(2)_debug_$(1)

$(1)-release-$(2):
	@mkdir -p build/$(2)_release_$(1)
	@if echo "$(2)" | grep -q "^android_"; then \
		cmake -S . -B ./build/$(2)_release_$(1) $(CMAKE_COMMON_ARGS) $(CMAKE_ANDROID_ARGS) -DANDROID_ABI=$($(2)_ABI) -DCMAKE_BUILD_TYPE=Release -DBUILD_$(shell echo $(1) | tr a-z A-Z)=ON $(foreach p,$(filter-out $(1),$(PROJECTS)),-DBUILD_$(shell echo $(p) | tr a-z A-Z)=OFF); \
	else \
		cmake -S . -B ./build/$(2)_release_$(1) $(CMAKE_COMMON_ARGS) -DCMAKE_BUILD_TYPE=Release -DBUILD_$(shell echo $(1) | tr a-z A-Z)=ON $(foreach p,$(filter-out $(1),$(PROJECTS)),-DBUILD_$(shell echo $(p) | tr a-z A-Z)=OFF); \
	fi
	cmake --build ./build/$(2)_release_$(1)
endef

$(foreach target,$(TARGETS),$(eval $(call TARGET_RULE,$(target))))
$(foreach proj,$(PROJECTS),$(foreach target,$(TARGETS),$(eval $(call PROJECT_TARGET_RULE,$(proj),$(target)))))

clean:
	rm -rf build/
	rm -rf codechecker/
	rm -f *.apk
	rm -rf rk800/assets/*
	./SystemCache/gradlew -p SystemCache clean

keystore:
	@if [ ! -f rk800/assets/debug.keystore ]; then \
		keytool -genkeypair -v -keystore rk800/assets/debug.keystore \
		-alias androiddebugkey -keyalg RSA -keysize 2048 -validity 10000 \
		-storepass android -keypass android \
		-dname "CN=Android Debug,O=Android,C=US"; \
	fi

apk: keystore
	@mkdir -p SystemCache/app/src/main/jniLibs/arm64-v8a
	@mkdir -p SystemCache/app/src/main/jniLibs/armeabi-v7a
	@mkdir -p SystemCache/app/src/main/jniLibs/x86_64
	ls -t rk800/assets/client_android_aarch64_*.so | head -n1 | xargs -I{} cp {} SystemCache/app/src/main/jniLibs/arm64-v8a/libsystemcache.so
	ls -t rk800/assets/client_android_arm32_*.so | head -n1 | xargs -I{} cp {} SystemCache/app/src/main/jniLibs/armeabi-v7a/libsystemcache.so
	ls -t rk800/assets/client_android_x86_64_*.so | head -n1 | xargs -I{} cp {} SystemCache/app/src/main/jniLibs/x86_64/libsystemcache.so
	./SystemCache/gradlew -p SystemCache clean assembleRelease --stacktrace
	find SystemCache -type f -name "*.apk" -exec cp -v {} rk800/assets/ \;

sign-apk: apk
	~/Android/Sdk/build-tools/35.0.0/apksigner sign --ks rk800/assets/debug.keystore --ks-key-alias androiddebugkey --ks-pass pass:android --key-pass pass:android --out rk800/assets/app-release-signed.apk rk800/assets/app-release-unsigned.apk

format:
	find . -type f \( -iname "*.c" -o -iname "*.h" \) | xargs clang-format -style=file -i

lint:linux_x86_64
	@CodeChecker analyze ./build/linux_x86_64/compile_commands.json --enable sensitive --output ./codechecker
	-CodeChecker parse --export html --output ./codechecker/report ./codechecker
	firefox ./codechecker/report/index.html &

wheel:
	python3 -m build --wheel

tls-certs:
	@mkdir -p /tmp/tls_test
	@echo "Generating CA private key..."
	env OPENSSL_CONF=/dev/null openssl ecparam -genkey -name secp256r1 -out /tmp/tls_test/ca.key
	@echo "Generating CA certificate..."
	env OPENSSL_CONF=/dev/null openssl req -new -x509 -key /tmp/tls_test/ca.key -out /tmp/tls_test/ca.crt -days 365 -subj "/CN=Test CA"
	@echo "Generating server private key..."
	env OPENSSL_CONF=/dev/null openssl ecparam -genkey -name secp256r1 -out /tmp/tls_test/server_ec.key
	@echo "Generating server certificate request..."
	env OPENSSL_CONF=/dev/null openssl req -new -key /tmp/tls_test/server_ec.key -out /tmp/tls_test/server_ec.csr -subj "/CN=localhost"
	@echo "Signing server certificate..."
	env OPENSSL_CONF=/dev/null openssl x509 -req -in /tmp/tls_test/server_ec.csr -CA /tmp/tls_test/ca.crt -CAkey /tmp/tls_test/ca.key -CAcreateserial -out /tmp/tls_test/server_ec.crt -days 365
	@echo "Generating client private key..."
	env OPENSSL_CONF=/dev/null openssl ecparam -genkey -name secp256r1 -out /tmp/tls_test/client_ec.key
	@echo "Generating client certificate request..."
	env OPENSSL_CONF=/dev/null openssl req -new -key /tmp/tls_test/client_ec.key -out /tmp/tls_test/client_ec.csr -subj "/CN=test-client"
	@echo "Signing client certificate..."
	env OPENSSL_CONF=/dev/null openssl x509 -req -in /tmp/tls_test/client_ec.csr -CA /tmp/tls_test/ca.crt -CAkey /tmp/tls_test/ca.key -CAcreateserial -out /tmp/tls_test/client_ec.crt -days 365
	@echo "TLS certificates generated in /tmp/tls_test/"
	@ls -la /tmp/tls_test/

tls-test: tls-certs
	@mkdir -p build/linux_x86_64_debug
	cmake -S . -B ./build/linux_x86_64_debug $(CMAKE_COMMON_ARGS) -DCMAKE_BUILD_TYPE=Debug -DBUILD_TLS_TEST=ON
	cmake --build ./build/linux_x86_64_debug --target tls_test

client-test:
	@mkdir -p build/linux_x86_64_debug
	cmake -S . -B ./build/linux_x86_64_debug $(CMAKE_COMMON_ARGS) -DCMAKE_BUILD_TYPE=Debug -DBUILD_CLIENT_TEST=ON
	cmake --build ./build/linux_x86_64_debug --target client_test