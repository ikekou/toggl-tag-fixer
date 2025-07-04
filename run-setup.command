#!/bin/bash

# Toggl Tag Fixer セットアップスクリプト
# 初回セットアップ用

# スクリプトの場所を取得
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# ターミナルでの表示を見やすくする
clear
echo "=========================================="
echo "🛠️  Toggl Tag Fixer セットアップ"
echo "=========================================="
echo ""

# Python3の確認
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 がインストールされていません"
    echo "   https://www.python.org/downloads/ からインストールしてください"
    echo ""
    echo "Press any key to exit..."
    read -n 1
    exit 1
fi

echo "✅ Python 3 確認完了: $(python3 --version)"

# 仮想環境の作成
if [ ! -d "venv" ]; then
    echo "📦 仮想環境を作成中..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "❌ 仮想環境の作成に失敗しました"
        echo ""
        echo "Press any key to exit..."
        read -n 1
        exit 1
    fi
    echo "✅ 仮想環境作成完了"
else
    echo "✅ 仮想環境は既に存在します"
fi

# 仮想環境をアクティベート
echo "🔧 仮想環境をアクティベート中..."
source venv/bin/activate

# 依存関係のインストール
echo "📚 依存関係をインストール中..."
pip install -r requirements.txt
if [ $? -eq 0 ]; then
    touch venv/.dependencies_installed
    echo "✅ 依存関係のインストール完了"
else
    echo "❌ 依存関係のインストールに失敗しました"
    echo ""
    echo "Press any key to exit..."
    read -n 1
    exit 1
fi

# .envファイルの設定
echo ""
echo "📝 環境設定ファイルのセットアップ"
if [ ! -f ".env" ]; then
    if [ -f ".env.sample" ]; then
        cp .env.sample .env
        echo "✅ .env.sample を .env にコピーしました"
    else
        # .env.sampleが存在しない場合の備用
        cat > .env << 'EOF'
# Toggl API設定
TOGGL_API_TOKEN=your_toggl_api_token_here
WORKSPACE_ID=your_workspace_id_here

# タイムゾーン設定（オプション）
TIMEZONE=Asia/Tokyo
EOF
        echo "✅ .env ファイルを作成しました"
    fi
else
    echo "✅ .env ファイルは既に存在します"
fi

# config.jsonの確認
echo ""
if [ ! -f "config.json" ]; then
    echo "📋 config.json サンプルを作成中..."
    cat > config.json << 'EOF'
{
  "サンプルプロジェクト1": ["tag1", "tag2"],
  "サンプルプロジェクト2": ["tag3"],
  "サンプルプロジェクト3": ["tag4", "tag5"]
}
EOF
    echo "✅ config.json サンプルを作成しました"
else
    echo "✅ config.json は既に存在します"
fi

echo ""
echo "=========================================="
echo "🎉 セットアップ完了！"
echo "=========================================="
echo ""
echo "次の手順:"
echo "1. .env ファイルを編集して Toggl API トークンとワークスペースIDを設定"
echo "2. config.json を編集してプロジェクト→タグのマッピングを設定"
echo "3. run-toggl-tag-fixer.command をダブルクリックしてツールを実行"
echo ""
echo "詳細な設定方法は README.ja.md を参照してください"
echo ""
echo "設定ファイルを今すぐ開きますか？"
echo "1. .env ファイルを開く"
echo "2. config.json ファイルを開く"
echo "3. README.ja.md を開く"
echo "4. 後で設定する"
echo ""
echo -n "選択 (1-4): "
read choice

case $choice in
    1)
        if command -v code &> /dev/null; then
            code .env
        elif command -v nano &> /dev/null; then
            nano .env
        else
            open -a TextEdit .env
        fi
        ;;
    2)
        if command -v code &> /dev/null; then
            code config.json
        elif command -v nano &> /dev/null; then
            nano config.json
        else
            open -a TextEdit config.json
        fi
        ;;
    3)
        open README.ja.md
        ;;
    4)
        echo "後で設定してください"
        ;;
esac

echo ""
echo "Press any key to close this window..."
read -n 1