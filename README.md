# bh-trans-ja

Book of Hours 翻訳支援スクリプト

## TL;DR (3行で)

`git clone https://github.com/hirmiura/bh-trans-ja.git` して、ゴニョゴニョする。  
`make build-edit` で出来た `build/edit.po` を [Poedit] とかで良い感じに翻訳する。  
`make all` すると、packageディレクトリに `bhcontent` が出来るので [Book of Hours] の該当箇所にコピーする。

## 翻訳対象

### ディレクトリ構成

```txt
Book of Hours
└ bh_Data/StreamingAssets/
    ├ *.txt (ニュース等, 現時点では翻訳しない)
    │
    └ bhcontent/
        ├ core/
        │   ├ *.json (culturesを除くサブフォルダ以下の全て)
        │   │
        │   └ cultures/
        │       ├ en/culture.json
        │       │ ↓コピーして翻訳
        │       └ ja/culture.json (ロケール設定, coreに置く)
        │
        └ loc_ja/
            └ 翻訳済みファイルを置く
```

### 出力

* 未翻訳データは出力しない
* 必須キー: id
* 1ファイルに出す `ja.json`
* `culture.json` は特別扱いする

## 流れ

1. バニラからデータ`core.json`を抽出する
   * `extract.py -o build/core.json bhcontent/core`
     * ファイルエンコードの修正
     * データの抽出
     * キーの小文字化
     * 重複idの処理
     * データ構造の変更
       * `dict[type, list[item]]` -> `dict[type, dict[id, item]]`

2. POTファイル`core.pot`を生成する
   * `genpot.py -c bhtrans.toml`
     * 翻訳対象を抽出する
     * `msgctxt`に`core.json`でのJSONPathを使う
       * コンテキストが付くのは`/cultures/en/*`のみ(2024-02-07時点)
   * `msguniq -s build/core.pot -o build/core.pot`
     * 重複を削除する

3. 作業用POファイル`edit.po`を生成する
   * 新規: `msginit  --no-translator -l ja_JP.utf8 -i core.pot -o edit.po`
   * 継続: `msgmerge  --no-fuzzy-matching -U edit.po core.pot`
   * 管理用POファイルが在ればマージする

     ```sh
     msgmerge --no-fuzzy-matching -U ja.pot core.pot  # まずPOTと
     msgcat --use-first -o edit.po edit.po ja.pot  # 作業用POを優先
     ```

4. 管理用POファイル`ja.po`を生成する
   * 新規: コピー

     ```sh
     cp -f edit.po ja.po
     ```

   * 継続: マージ

     ```sh
     msgmerge --no-fuzzy-matching --no-location --no-wrap -U ja.po core.pot
     msgcat --use-first --no-location --no-wrap -o ja.po edit.po ja.po
     ```

   * 共通: バージョン管理用に修正する

     ```sh
     msgattrib --no-obsolete --no-location --no-wrap --sort-output -o - ja.po \
     | grep -vE '^"(POT-Creation-Date|X-Generator):.*\\n"' \
     | sponge ja.po
     ```

5. MOファイル`ja.mo`を生成する
   * `msgfmt --statistics -o ja.mo ja.po`

6. 翻訳ファイルを生成する
   * `gentrans.py -c bhtrans.toml`
     * `cultures.json`は特別に処理する
     * データ構造を戻す
       * `dict[type, dict[id, item]]` -> `dict[type, list[item]]`
     * 一括で`loc_ja/ja.json`に書き出す

7. 配布用zipを作る

## ライセンス

[MIT License] としています。

---

[Book of Hours]: https://store.steampowered.com/app/1028310/BOOK_OF_HOURS/
[poedit]: https://poedit.net/
[MIT License]: https://opensource.org/license/mit/
