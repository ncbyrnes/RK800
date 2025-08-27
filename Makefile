TARGETS = android_aarch64 android_arm32 linux_x86_64
PROJECTS = daemon
ANDROID_NDK = /opt/cross/android-ndk-r28c-linux/android-ndk-r28c

android_aarch64_ABI = arm64-v8a
android_arm32_ABI = armeabi-v7a

CMAKE_COMMON_ARGS = -G "Unix Makefiles" -DCMAKE_MAKE_PROGRAM=/usr/bin/make
CMAKE_ANDROID_ARGS = -DCMAKE_TOOLCHAIN_FILE=$(ANDROID_NDK)/build/cmake/android.toolchain.cmake \
                     -DANDROID_NDK=$(ANDROID_NDK) -DANDROID_PLATFORM=android-21

.PHONY: lint format build clean debug release $(TARGETS) all-targets debug-% release-% $(foreach proj,$(PROJECTS),$(proj)-debug-% $(proj)-release-% $(proj)-%)

build: debug

debug: debug-linux_x86_64 debug-android_aarch64 debug-android_arm32

release: release-linux_x86_64 release-android_aarch64 release-android_arm32

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
	rm -rf rk800/assets/*

format:
	find . -type f \( -iname "*.c" -o -iname "*.h" \) | xargs clang-format -style=file -i

lint:linux_x86_64
	@CodeChecker analyze ./build/linux_x86_64/compile_commands.json --enable sensitive --output ./codechecker
	-CodeChecker parse --export html --output ./codechecker/report ./codechecker
	firefox ./codechecker/report/index.html &