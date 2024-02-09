# SPDX-License-Identifier: MIT
# Copyright 2024 hirmiura (https://github.com/hirmiura)
#
SHELL := /bin/bash

# このパッケージのバージョン
V_THIS := $(shell tomlq -r '.tool.poetry.version' pyproject.toml)

# 各種ディレクトリ
D_BHHOME    := bhhome
D_BHCONTENT := bhcontent
D_BHCORE    := $(D_BHCONTENT)/core
D_BIN       := bin
D_BUILD     := build
D_PACKAGE   := package

F_BHTRANSCONF := bhtrans.toml
F_COREJSON := $(D_BUILD)/core.json
F_COREPOT  := $(D_BUILD)/core.pot
F_EDITPO   := $(D_BUILD)/edit.po
F_JAPO     := $(D_BUILD)/ja.po
F_JAMO     := $(D_BUILD)/ja.mo
F_JAJSON_PAT := $(D_BUILD)/ja_*.json
F_CULTURE  := $(D_BUILD)/culture.json

B_EXTRACT  := $(D_BIN)/extract.py
B_GENPOT   := $(D_BIN)/genpot.py
B_GENTRANS := $(D_BIN)/gentrans.py

# BH本体のバージョンファイル
F_BHVERSION := $(D_BHHOME)/version.txt


#==============================================================================
# カラーコード
# ヘルプ表示
#==============================================================================
include ColorCode.mk
include Help.mk


#==============================================================================
# BHデータのリンク/ディレクトリを確認
#==============================================================================
.PHONY: check
check: ## bhへのリンク/ディレクトリを確認します
check:
	@echo '"$(D_BHHOME)" をチェックしています'
	@if [[ -L $(D_BHHOME) && `readlink $(D_BHHOME) ` ]] ; then \
		echo -e '    $(CC_BrGreen)SUCCESS$(CC_Reset): リンクです' ; \
	elif [[ -d $(D_BHHOME) ]] ; then \
		echo -e '    $(CC_BrGreen)SUCCESS$(CC_Reset): ディレクトリです' ; \
	else \
		echo -e '    \a$(CC_BrRed)ERROR: "$(D_BHHOME)" に "Book of Hours" のリンクを張って下さい$(CC_Reset)' ; \
		exit 1 ; \
	fi


#==============================================================================
# bhcontentへのリンクを作成
#==============================================================================
.PHONY: symlink
symlink: ## bhcontentへのリンクを張ります
symlink:
	@echo '"$(D_BHCONTENT)" へのリンクを張ります'
	if [[ ! -e "$(D_BHCONTENT)" ]] ; then \
		ln -s $(D_BHHOME)/bh_Data/StreamingAssets/bhcontent/ $(D_BHCONTENT) ; \
	fi


#==============================================================================
# バージョンを確認
#==============================================================================
.PHONY: version version_pre
version: ## バージョンを確認します
version: version_pre
	$(eval V_BH := $(shell head -1 $(F_BHVERSION) | sed -Ee "s/\s+$$//"))
	@printf '    BH本体     %12s\n' $(V_BH)
	@printf '    自身       %12s\n' $(V_THIS)

version_pre:
	@echo 'バージョン情報'
	@if [[ ! -f $(F_BHVERSION) ]] ; then \
		echo -e '    \a$(CC_BrRed)ERROR: $(F_BHVERSION) がありません$(CC_Reset)' ; \
		exit 1; \
	fi


#==============================================================================
# 全てをビルド
#==============================================================================
.PHONY: all build
all: ## ビルドしてパッケージにします
all: check symlink version build packaging

build: ## ビルドのみ行います
build:  build-trans


#==============================================================================
# バニラデータを抽出する
#==============================================================================
# core.jsonの作成
.PHONY: extract clean-extract
extract: $(F_COREJSON)
$(F_COREJSON): $(B_EXTRACT)
	@mkdir -p $(D_BUILD)
	poetry run $(B_EXTRACT) -i AA_Yar -i TCAT -o $(F_COREJSON) $(D_BHCORE)

clean-extract:
	rm -f $(F_COREJSON)


#==============================================================================
# POTファイルを生成する
#==============================================================================
# core.potの作成
.PHONY: build-pot clean-pot
build-pot: $(F_COREPOT)
$(F_COREPOT): $(F_COREJSON) $(F_BHTRANSCONF) $(B_GENPOT)
	poetry run $(B_GENPOT) -c $(F_BHTRANSCONF)
	msguniq -s $(F_COREPOT) -o $(F_COREPOT)

clean-pot:
	rm -f $(F_COREPOT)


#==============================================================================
# 作業用POファイルを生成する
#==============================================================================
# edit.poの作成
.PHONY: build-edit clean-edit
build-edit: $(F_EDITPO)
$(F_EDITPO): $(F_COREPOT)
	if [[ -f "$@" ]] ; then \
		# 既にある場合はマージ ; \
		msgmerge --no-fuzzy-matching -U $@ $< ; \
	else \
		# 無ければ新規に作る ; \
		msginit --no-translator -l ja_JP.utf8 -i $< -o $@ ; \
	fi
	if [[ -f "$(F_JAPO)" ]] ; then \
		# 管理用POファイルが在ればマージ ; \
		msgmerge --no-fuzzy-matching -U $(F_JAPO) $<  # まずPOTと ; \
		msgcat --use-first -o $@ $@ $(F_JAPO)  # 作業用POを優先 ; \
	fi

clean-edit:
	rm -f $(F_EDITPO)


#==============================================================================
# 管理用POファイルを生成する
#==============================================================================
# ja.poの作成
.PHONY: build-po clean-po
build-po: $(F_JAPO)
$(F_JAPO): $(F_EDITPO) $(F_COREPOT)
	if [[ -f "$@" ]] ; then \
		# 既にある場合はマージ ; \
		msgmerge --no-fuzzy-matching --no-location --no-wrap -U $@ $(F_COREPOT) ; \
		msgcat --use-first --no-location --no-wrap -o $@ $< $@ ; \
	else \
		# 無ければコピーして作る ; \
		cp -f $< $@ ; \
	fi
	# バージョン管理用に修正
	msgattrib --no-obsolete --no-location --no-wrap --sort-output -o - $@ \
	| grep -vE '^"(POT-Creation-Date|X-Generator):.*\\n"' \
	| sponge $@

clean-po:
	rm -f $(F_JAPO)


#==============================================================================
# MOファイルを生成する
#==============================================================================
# ja.moの作成
.PHONY: build-mo clean-mo
build-mo: $(F_JAMO)
$(F_JAMO): $(F_JAPO)
	msgfmt --statistics -o $@ $^

clean-mo:
	rm -f $(F_JAMO)


#==============================================================================
# 翻訳ファイルを生成する
#==============================================================================
# ja.jsonとculture.jsonの作成
.PHONY: build-trans clean-trans
build-trans: $(F_CULTURE)
$(F_CULTURE): $(F_JAMO) $(F_COREJSON) $(F_BHTRANSCONF) $(B_GENTRANS)
	poetry run $(B_GENTRANS) -c $(F_BHTRANSCONF)

clean-trans:
	rm -f $(F_CULTURE) $(F_JAJSON_PAT)


#==============================================================================
# 翻訳パッケージを作成
#==============================================================================
.PHONY: packaging clean-package
packaging: $(F_JAJSON)
	@mkdir -p $(D_PACKAGE)/bhcontent/core/cultures/ja
	@mkdir -p $(D_PACKAGE)/bhcontent/loc_ja
	if [[ -f "$(F_CULTURE)" ]] ; then \
		cp -f "$(F_CULTURE)" $(D_PACKAGE)/bhcontent/core/cultures/ja ; \
	fi
	cp -f $(F_JAJSON_PAT) $(D_PACKAGE)/bhcontent/loc_ja
	$(eval V_BH := $(shell head -1 $(F_BHVERSION) | sed -Ee "s/\s+$$//"))
	rm -f bhja-$(V_BH).zip
	cd $(D_PACKAGE) ; zip -r9 ../bhja-$(V_BH).zip bhcontent

clean-package:
	rm -fr $(D_PACKAGE)


#==============================================================================
# Clean
#==============================================================================
.PHONY: clean clean-all
clean: ## edit.po以外の全てを削除します
clean: clean-extract clean-pot clean-po clean-mo clean-trans clean-package
	rm -f $(D_BUILD)/*~

clean-all: ## edit.poも含めて全てを削除します
clean-all: clean clean-edit
