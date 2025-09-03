#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
list_speakers.py - AIVIS Speech話者一覧取得ツール

このスクリプトを実行すると、利用可能な話者とそのIDが表示されます。
表示されたIDをconfig.jsonのspeaker_idに設定してください。

使用方法:
    python list_speakers.py
"""

import requests
import json
import sys


def list_available_speakers():
    """利用可能な話者を一覧表示"""
    
    # AIVIS Speech Engineのデフォルトポート
    engine_url = "http://localhost:10101"
    
    try:
        print("AIVIS Speech Engineに接続中...")
        
        # 話者一覧を取得
        response = requests.get(f"{engine_url}/speakers", timeout=5)
        response.raise_for_status()
        
        speakers = response.json()
        
        if not speakers:
            print("話者が見つかりません。")
            print("AIVIS Speechが正しくインストールされているか確認してください。")
            return
        
        print("\n" + "=" * 70)
        print("📢 利用可能な話者一覧")
        print("=" * 70)
        
        # 設定用のサンプルも生成
        sample_ids = []
        
        for speaker in speakers:
            print(f"\n【{speaker['name']}】")
            
            if 'speaker_uuid' in speaker:
                print(f"UUID: {speaker['speaker_uuid']}")
            
            # 各スタイルのIDを表示
            if 'styles' in speaker:
                print("\n利用可能なスタイル:")
                for style in speaker['styles']:
                    style_id = style['id']
                    style_name = style['name']
                    print(f"  ✓ スタイル: {style_name}")
                    print(f"    ID: {style_id}")
                    print(f"    → config.jsonに設定: \"speaker_id\": {style_id}")
                    
                    # 最初のスタイルIDを記録
                    if not sample_ids:
                        sample_ids.append((speaker['name'], style_name, style_id))
            
            print("-" * 50)
        
        # 使用例を表示
        if sample_ids:
            print("\n" + "=" * 70)
            print("💡 設定例")
            print("=" * 70)
            name, style, sid = sample_ids[0]
            print(f"\n例: {name}の{style}を使用する場合")
            print("\nconfig.jsonを以下のように編集:")
            print("""
{
  "voice": {
    "speaker_id": %d,  // %s - %s
    ...
  }
}
""" % (sid, name, style))
        
        print("\n✅ 話者一覧の取得が完了しました")
        
    except requests.exceptions.ConnectionError:
        print("\n" + "=" * 70)
        print("❌ エラー: AIVIS Speech Engineに接続できません")
        print("=" * 70)
        print("\n以下を確認してください：")
        print("1. AIVIS Speechが起動している")
        print("2. AIVIS Speech Engineがポート10101で動作している")
        print("3. ファイアウォールがポート10101をブロックしていない")
        print("\nAIVIS Speechの起動方法:")
        print("1. AIVIS Project公式サイトからダウンロード")
        print("   https://aivis-project.com/")
        print("2. インストール後、AIVIS Speechを起動")
        
    except requests.exceptions.Timeout:
        print("\n❌ エラー: 接続タイムアウト")
        print("AIVIS Speech Engineの応答に時間がかかっています。")
        
    except Exception as e:
        print(f"\n❌ 予期しないエラーが発生しました: {e}")
        print("\n詳細なエラー情報:")
        import traceback
        traceback.print_exc()


def check_engine_status():
    """エンジンの状態を確認"""
    engine_url = "http://localhost:10101"
    
    try:
        response = requests.get(f"{engine_url}/version", timeout=2)
        if response.status_code == 200:
            version_info = response.json()
            print(f"✅ AIVIS Speech Engine バージョン: {version_info}")
            return True
    except:
        pass
    
    return False


if __name__ == "__main__":
    print("=" * 70)
    print("AIVIS Speech 話者一覧取得ツール")
    print("=" * 70)
    
    # エンジンの状態確認
    if not check_engine_status():
        print("\n⚠️  AIVIS Speech Engineが起動していない可能性があります")
        print("AIVIS Speechアプリケーションを起動してから再度実行してください。")
        print("")
    
    # 話者一覧を表示
    list_available_speakers()
    
    print("\n終了するにはEnterキーを押してください...")
    input()