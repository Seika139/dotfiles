# OSを自動検出 (windows or macos)
ifeq ($(OS),Windows_NT)
	DETECTED_OS := windows
else
	UNAME_S := $(shell uname -s)
	ifeq ($(UNAME_S),Darwin)
		DETECTED_OS := macos
	endif
endif

# jq コマンドで config.json を読み込む。rオプションは出力のダブルクォートを削除する。
JQ_CMD := jq -r

# `make sync profile=xxx` のようにプロファイルを指定可能。なければjsonのデフォルト値を使用
PROFILE	  	   := $(or $(profile),$(shell $(JQ_CMD) .default_profile config.json))
PROFILES_DIR   := $(shell $(JQ_CMD) .profiles_dir config.json)
PROFILE_PATH   := $(PROFILES_DIR)/$(PROFILE)

# OSに応じてパスを読み込む
VSCODE_PATH    := $(shell $(JQ_CMD) .paths.$(DETECTED_OS).vscode config.json | sed "s|^~|$${HOME}|")
CURSOR_PATH    := $(shell $(JQ_CMD) .paths.$(DETECTED_OS).cursor config.json | sed "s|^~|$${HOME}|")
TARGET_PATHS   := "$(VSCODE_PATH)" "$(CURSOR_PATH)"

# 同期対象のリストを読み込む
CONFIG_FILES   := $(shell $(JQ_CMD) '.config_files[]' config.json)
CONFIG_DIRS    := $(shell $(JQ_CMD) '.config_dirs[]' config.json)

.PHONY: help
help: ## このヘルプを表示する
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

.PHONY: show-vars
show-vars: ## 変数の値を表示
	@echo "Detected OS =  \033[36m$(DETECTED_OS)\033[0m"
	@echo "PROFILE_PATH = \033[36m$(PROFILE_PATH)\033[0m"
	@echo "VSCODE_PATH =  \033[36m$(VSCODE_PATH)\033[0m"
	@echo "CURSOR_PATH =  \033[36m$(CURSOR_PATH)\033[0m"
	@echo "CONFIG_FILES = \033[36m$(CONFIG_FILES)\033[0m: これらのファイルを同期します"
	@echo "CONFIG_DIRS =  \033[36m$(CONFIG_DIRS)\033[0m: これらのディレクトリを再起的に同期します"

.PHONY: vars
vars: show-vars ## 変数の値を表示

.PHONY: check-paths
check-paths: ## VS Code と Cursor のパスをチェック
	@IFS='\n'; for path in $(TARGET_PATHS); do \
		real_path=$$(echo "$$path" | sed "s|^~|$$HOME|"); \
		if [ -d "$$real_path" ]; then \
			echo "✅ Found \033[36m$$real_path\033[0m"; \
		else \
			echo "❌ Not Found \033[31m$$real_path\033[0m"; \
		fi; \
	done

.PHONY: status
status: ## 現在の同期状態を確認
	@echo "Checking sync status for profile: \033[36m$(PROFILE)\033[0m"
	@$(MAKE) status-settings
	@$(MAKE) status-extensions

.PHONY: status-settings
status-settings: ## VS Code と Cursor の設定ファイルの同期状態を確認
	@for target_dir in $(TARGET_PATHS); do \
		echo "\n--- Settings for \033[33m$$target_dir\033[0m ---"; \
		for item in $(CONFIG_FILES) $(CONFIG_DIRS); do \
			expected_src=$$(realpath "$(PROFILE_PATH)/$$item" 2>/dev/null || echo ""); \
			dest_file="$$target_dir/$$item"; \
			if [ ! -e "$$dest_file" ] && [ ! -L "$$dest_file" ]; then \
				echo "  ❔ \033[36m$$item\033[0m: does not exist."; \
			elif [ -L "$$dest_file" ]; then \
				actual_src=$$(readlink "$$dest_file"); \
				if [ "$$actual_src" = "$$expected_src" ]; then \
					echo "  ✅ \033[36m$$item\033[0m: correctly synced."; \
				else \
					echo "  ❌ \033[36m$$item\033[0m: linked to other source: \033[36m$$actual_src\033[0m"; \
				fi; \
			else \
				if [ -f "$$dest_file" ] && [ -f "$(PROFILE_PATH)/$$item" ]; then \
					diff -q "$$dest_file" "$(PROFILE_PATH)/$$item" >/dev/null; \
					if [ $$? -eq 0 ]; then \
						echo "  ⚠️  \033[36m$$item\033[0m: identical to profile but not a symlink."; \
					else \
						echo "  🚨 \033[36m$$item\033[0m: differs from profile."; \
					fi; \
				elif [ -d "$$dest_file" ] && [ -d "$(PROFILE_PATH)/$$item" ]; then \
					diff_output=$$(diff -qr "$$dest_file" "$(PROFILE_PATH)/$$item"); \
					if [ -z "$$diff_output" ]; then \
						echo "  ⚠️  \033[36m$$item\033[0m: directory is identical to profile but not a symlink."; \
					else \
						echo "  🚨 \033[36m$$item\033[0m: directory differs from profile:"; \
						echo "$$diff_output" | sed 's/^/    /'; \
					fi; \
				else \
					echo "  🚨 \033[36m$$item\033[0m: is not a symlink and cannot compare contents."; \
				fi; \
			fi; \
		done; \
	done

.PHONY: status-extensions
status-extensions: ## VS Code と Cursor の拡張機能の同期状態を確認
	@for target_dir in $(TARGET_PATHS); do \
		echo "\n--- Extensions for \033[33m$$target_dir\033[0m ---"; \
		if [ -f "$(PROFILE_PATH)/extensions.txt" ]; then \
			if [ "$${target_dir}" = "$(VSCODE_PATH)" ]; then \
				if command -v code >/dev/null 2>&1; then \
					echo "\n  Checking VS Code extensions sync..."; \
					tmp_installed_exts=$$(mktemp); \
					tmp_missing_exts=$$(mktemp); \
					code --list-extensions 2>/dev/null > "$$tmp_installed_exts"; \
					grep -Fxvf "$$tmp_installed_exts" "$(PROFILE_PATH)/extensions.txt" > "$$tmp_missing_exts"; \
					extra_exts=$$(grep -Fxvf "$(PROFILE_PATH)/extensions.txt" "$$tmp_installed_exts"); \
					if [ -s "$$tmp_missing_exts" ]; then \
						echo "  🚨 Missing extensions:"; \
						cat "$$tmp_missing_exts" | sed 's/^/    - /'; \
					else \
						echo "  ✅ All extensions in extensions.txt are installed."; \
					fi; \
					if [ -n "$${extra_exts}" ]; then \
						echo "  ⚠️  Extra installed extensions (not in extensions.txt):"; \
						echo "$${extra_exts}" | sed 's/^/    - /'; \
					fi; \
					rm -f "$$tmp_installed_exts" "$$tmp_missing_exts"; \
				else \
					echo "  ⚠️  'code' コマンドが見つかりません。VS Code の拡張機能の状態は確認できません。"; \
				fi; \
			elif [ "$${target_dir}" = "$(CURSOR_PATH)" ]; then \
				if command -v cursor >/dev/null 2>&1; then \
					echo "\n  Checking Cursor extensions sync..."; \
					tmp_installed_exts=$$(mktemp); \
					tmp_missing_exts=$$(mktemp); \
					cursor --list-extensions 2>/dev/null > "$$tmp_installed_exts"; \
					grep -Fxvf "$$tmp_installed_exts" "$(PROFILE_PATH)/extensions.txt" > "$$tmp_missing_exts"; \
					extra_exts=$$(grep -Fxvf "$(PROFILE_PATH)/extensions.txt" "$$tmp_installed_exts"); \
					if [ -s "$$tmp_missing_exts" ]; then \
						echo "  🚨 Missing extensions:"; \
						cat "$$tmp_missing_exts" | sed 's/^/    - /'; \
					else \
						echo "  ✅ All extensions in extensions.txt are installed."; \
					fi; \
					if [ -n "$${extra_exts}" ]; then \
						echo "  ⚠️  Extra installed extensions (not in extensions.txt):"; \
						echo "$${extra_exts}" | sed 's/^/    - /'; \
					fi; \
					rm -f "$$tmp_installed_exts" "$$tmp_missing_exts"; \
				else \
					echo "  ⚠️  'cursor' コマンドが見つかりません。Cursor の拡張機能の状態は確認できません。"; \
				fi; \
			fi; \
		fi; \
	done


.PHONY: export-profile
export-profile: ## エディタの設定を新しいプロファイルとして書き出す
	@if [ -z "$(profile)" ] || [ -z "$(editor)" ]; then \
		echo "❌ Error: 'profile' and 'editor' arguments are required."; \
		echo "   Usage: make export-profile profile=<new-profile-name> editor=<vscode|cursor>"; \
		exit 1; \
	fi
	@echo "Exporting current \033[36m$(editor)\033[0m settings to new profile: \033[36m$(profile)\033[0m"
	@if [ -d "$(PROFILES_DIR)/$(profile)" ]; then \
		echo "❌ Error: Profile '$(PROFILES_DIR)/$(profile)' already exists. Please choose a different name."; \
		exit 1; \
	fi
	@if [ "$(editor)" = "vscode" ]; then \
		src_path="$(VSCODE_PATH)"; \
	elif [ "$(editor)" = "cursor" ]; then \
		src_path="$(CURSOR_PATH)"; \
	else \
		echo "❌ Error: Invalid editor specified. Use 'vscode' or 'cursor'."; \
		exit 1; \
	fi; \
	echo "Using source path: \033[36m$$src_path\033[0m"; \
	echo "Creating new profile directory: \033[36m$(PROFILES_DIR)/$(profile)\033[0m"; \
	mkdir -p "$(PROFILES_DIR)/$(profile)"; \
	for item in $(CONFIG_FILES); do \
		src_item="$$src_path/$$item"; \
		if [ -f "$$src_item" ]; then \
			echo "  Copying file $$item to \033[36m$(PROFILES_DIR)/$(profile)\033[0m"; \
			cp "$$src_item" "$(PROFILES_DIR)/$(profile)/"; \
		else \
			echo "  Skipping \033[36m$$item\033[0m (not found in editor config)."; \
		fi; \
	done; \
	for item in $(CONFIG_DIRS); do \
		src_item="$$src_path/$$item"; \
		if [ -d "$$src_item" ]; then \
			echo "  Copying directory \033[36m$$item\033[0m to  \033[36m$(PROFILES_DIR)/$(profile)\033[0m"; \
			cp -r "$$src_item" "$(PROFILES_DIR)/$(profile)/"; \
		else \
			echo "  Skipping $$item (not found in editor config)."; \
		fi; \
	done; \
	tmp_ext_vscode=""; tmp_ext_cursor=""; \
	if command -v code >/dev/null 2>&1; then \
		tmp_ext_vscode="$(PROFILES_DIR)/$(profile)/.tmp_vscode_extensions.txt"; \
		echo "  Exporting VS Code extensions to $$tmp_ext_vscode"; \
		code --list-extensions > "$$tmp_ext_vscode"; \
	fi; \
	if command -v cursor >/dev/null 2>&1; then \
		tmp_ext_cursor="$(PROFILES_DIR)/$(profile)/.tmp_cursor_extensions.txt"; \
		echo "  Exporting Cursor extensions to $$tmp_ext_cursor"; \
		cursor --list-extensions > "$$tmp_ext_cursor"; \
	fi; \
	cat $$tmp_ext_vscode $$tmp_ext_cursor 2>/dev/null | sort | uniq > "$(PROFILES_DIR)/$(profile)/extensions.txt"; \
	rm -f $$tmp_ext_vscode $$tmp_ext_cursor
	@echo "✅ Export complete! New profile \033[36m$(profile)\033[0m is ready in \033[36m$(PROFILES_DIR)/$(profile)\033[0m."

.PHONY: sync
sync: ## VS Code と Cursor の設定をプロファイルのシンボリックリンクとして同期する
	@echo "Syncing with profile: \033[36m$(PROFILE)\033[0m"
	@if [ ! -d "$(PROFILE_PATH)" ]; then \
		echo "❌ \033[31mError\033[0m: Profile directory '$(PROFILE_PATH)' not found."; exit 1; \
	fi
	@for target_dir in $(TARGET_PATHS); do \
		echo "\n--- Applying to \033[36m$$target_dir\033[0m ---"; \
		if [ ! -d "$$target_dir" ]; then mkdir -p "$$target_dir"; fi; \
		for item in $(CONFIG_FILES) $(CONFIG_DIRS); do \
			src_item="$$(realpath "$(PROFILE_PATH)/$$item" 2>/dev/null)";  \
			dest_item="$$target_dir/$$item"; \
			if [ -z "$$src_item" ] || [ ! -e "$$src_item" ]; then \
				echo "  ⚠️  \033[33mSKIPPED: \033[0m\033[36m${PROFILE_PATH}/$$item\033[0m not found."; \
			elif [ -e "$$dest_item" ] && ! [ -L "$$dest_item" ]; then \
				echo "  Found existing file/dir (NOT a symlink) at \033[36m$$dest_item\033[0m. Comparing content..."; \
				if diff -r -q "$$src_item" "$$dest_item" >/dev/null 2>&1; then \
					echo "  ✅ Content \033[36m${PROFILE_PATH}/$$item\033[0m is identical. Replacing with symlink."; \
					rm -rf "$$dest_item"; \
					ln -snf "$$src_item" "$$dest_item"; \
				else \
					echo "  ❌ \033[31mCONFLICT:\033[0m Resolve manually and sync again."; \
					echo "     \033[36m${PROFILE_PATH}/$$item\033[0m != \033[36m$$dest_item\033[0m"; \
				fi; \
			else \
				ln -snf "$$src_item" "$$dest_item"; \
				echo "  ✅ Linked:  ${PROFILE_PATH}/$$item"; \
			fi; \
		done; \
		if [ -f "$(PROFILE_PATH)/extensions.txt" ]; then \
			if [ "$${target_dir}" = "$(VSCODE_PATH)" ] && command -v code >/dev/null 2>&1; then \
				echo "  Installing VS Code extensions from \033[36m$(PROFILE_PATH)/extensions.txt\033[0m ..."; \
				installed_exts="$$(code --list-extensions 2>/dev/null)"; \
				grep -vxF "$${installed_exts}" "$(PROFILE_PATH)/extensions.txt" | xargs -r -n 1 code --install-extension --force; \
			elif [ "$${target_dir}" = "$(CURSOR_PATH)" ] && command -v cursor >/dev/null 2>&1; then \
				echo "  Installing Cursor extensions from \033[36m$(PROFILE_PATH)/extensions.txt\033[0m ..."; \
				installed_exts="$$(cursor --list-extensions 2>/dev/null)"; \
				grep -vxF "$${installed_exts}" "$(PROFILE_PATH)/extensions.txt" | xargs -r -n 1 cursor --install-extension --force; \
			else \
				echo "  Skipping extensions install: suitable command not found for $$target_dir."; \
			fi; \
		fi; \
	done
	@echo "\n✅ Sync complete!"

# sync にて拡張機能インストール時の出力が冗長な場合は以下の部分を
# grep -vxF "$${installed_exts}" "$(PROFILE_PATH)/extensions.txt" | xargs -r -n 1 code --install-extension --force; \
# このようにします
# grep -vxF "$${installed_exts}" "$(PROFILE_PATH)/extensions.txt" | xargs -r -n 1 -I{} sh -c 'echo "    Installing: {}"; code --install-extension {} --force >/dev/null 2>&1'; \
