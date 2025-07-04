#!/bin/bash

# Toggl Tag Fixer - Mac用実行スクリプト
# ダブルクリックで実行できます

# スクリプトの場所を取得
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# ターミナルでの表示を見やすくする
clear
echo "=========================================="
echo "🏷️  Toggl Tag Fixer"
echo "=========================================="
echo ""

# Python仮想環境の確認と作成
if [ ! -d "venv" ]; then
    echo "📦 仮想環境を作成中..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "❌ 仮想環境の作成に失敗しました"
        echo "   Python 3.9以上がインストールされているか確認してください"
        echo ""
        echo "Press any key to exit..."
        read -n 1
        exit 1
    fi
fi

# 仮想環境をアクティベート
echo "🔧 仮想環境をアクティベート中..."
source venv/bin/activate

# 依存関係のインストール
if [ ! -f "venv/.dependencies_installed" ]; then
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
fi

echo ""

# .envファイルの確認
if [ ! -f ".env" ]; then
    echo "⚠️  .envファイルが見つかりません"
    echo "   セットアップが必要です："
    echo ""
    echo "   1. .env.sample を .env にコピー"
    echo "   2. .env に Toggl API トークンとワークスペースIDを設定"
    echo "   3. config.json にプロジェクト→タグのマッピングを設定"
    echo ""
    echo "   詳細は README.ja.md を参照してください"
    echo ""
    echo "Press any key to exit..."
    read -n 1
    exit 1
fi

# メニュー表示
while true; do
    echo "==========================================\\n"
    echo "実行オプションを選択してください:"
    echo ""
    echo "1. 📊 Dry-run（確認のみ、実際の更新なし）"
    echo "2. 🚀 通常実行（昨日のエントリーを処理）"
    echo "3. 📅 今日のエントリーを処理"
    echo "4. 🎯 インタラクティブモード（対話的選択）"
    echo "5. 📋 特定の日付を指定"
    echo "6. 📖 ヘルプを表示"
    echo "7. 🚪 終了"
    echo ""
    echo -n "選択 (1-7): "
    read choice
    echo ""
    
    case $choice in
        1)
            echo "🔍 Dry-runモードで実行中..."
            python main.py --dry-run
            ;;
        2)
            echo "🚀 通常モードで実行中..."
            python main.py
            ;;
        3)
            echo "📅 今日のエントリーを処理中..."
            python main.py --today
            ;;
        4)
            echo "🎯 インタラクティブモードで実行中..."
            python main.py --interactive
            ;;
        5)
            echo -n "日付を入力してください (YYYY-MM-DD): "
            read target_date
            echo "📅 $target_date のエントリーを処理中..."
            python main.py --date "$target_date"
            ;;
        6)
            python main.py --help
            ;;
        7)
            echo "👋 終了します"
            break
            ;;
        *)
            echo "❌ 無効な選択です。1-7の数字を入力してください。"
            ;;
    esac
    
    if [ $choice -ne 6 ] && [ $choice -ne 7 ]; then
        echo ""
        echo "Press any key to continue..."
        read -n 1
        echo ""
    fi
done

echo ""
echo "Press any key to close this window..."
read -n 1