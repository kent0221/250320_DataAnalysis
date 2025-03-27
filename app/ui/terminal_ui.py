import os
import time
from typing import List, Dict, Optional
from datetime import datetime
import pandas as pd
from tabulate import tabulate

from app.utils import extract_video_id

class TerminalUI:
    def __init__(self):
        self.header = "===== TikTok動画データ取得・分析アプリ ====="
        self.width = 60
        self.data_summary: Dict = {}

    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def display_header(self, subtitle: str = ""):
        """ヘッダー表示"""
        self.clear_screen()
        print("\n" + self.header)
        if subtitle:
            print(f"- {subtitle} -")
        print("-" * len(self.header))

    def initial_screen(self) -> str:
        """初期画面"""
        while True:
            self.display_header("初期画面")
            print("1. TikTokと連携してデータを取得")
            print("2. プライバシーポリシーを表示")
            print("3. 利用規約を表示")
            print("4. 終了")
            
            choice = input("\n選択してください (1-4): ")
            
            if choice == "2":
                self.show_privacy_policy()
                continue
            elif choice == "3":
                self.show_terms()
                continue
            
            return choice

    def connecting_screen(self) -> str:
        """接続画面"""
        self.display_header("接続画面")
        print("1. 接続を開始")
        print("2. 戻る")
        return input("\n選択してください (1-2): ")

    def auth_screen(self) -> None:
        """認証画面"""
        self.display_header("認証画面")
        print("TikTokとの認証を行います...")
        input("Enterキーを押して続行...")

    def data_settings_screen(self) -> Optional[Dict]:
        """データ取得設定画面"""
        self.display_header("データ取得設定")
        print("取得方法を選択してください：")
        print("1. トレンド動画")
        print("2. ハッシュタグ検索")
        print("3. 特定動画")
        print("4. 戻る")
        
        choice = input("\n選択してください (1-4): ")
        
        if choice == "4":
            return None
            
        settings = None
        if choice == "1":
            settings = self._get_trend_settings()
        elif choice == "2":
            settings = self._get_hashtag_settings()
        elif choice == "3":
            settings = self._get_video_settings()
            
        if settings and self._confirm_settings(settings):
            return settings
        return None

    def _get_trend_settings(self) -> Dict:
        """トレンド動画の設定を取得"""
        print("\n=== トレンド動画の取得設定 ===")
        count = input("取得する動画数 (未入力=10): ") or "10"
        
        print("\nソート順を選択してください：")
        print("1. 再生回数順")
        print("2. いいね数順")
        print("3. コメント数順")
        print("4. シェア数順")
        sort_choice = input("選択してください (未入力=1): ") or "1"
        
        sort_map = {
            "1": "views",
            "2": "likes",
            "3": "comments",
            "4": "shares"
        }
        
        min_views = input("最小再生回数 (未入力=100): ") or "100"
        min_likes = input("最小いいね数 (未入力=100): ") or "100"
        time_range = input("期間（日数、1-10） (未入力=10): ") or "10"
        
        return {
            "type": "trend",
            "count": int(count),
            "sort_by": sort_map.get(sort_choice, "views"),
            "min_views": int(min_views),
            "min_likes": int(min_likes),
            "time_range": int(time_range)
        }

    def _get_hashtag_settings(self) -> Dict:
        """ハッシュタグ検索の設定を取得"""
        print("\n=== ハッシュタグ検索の設定 ===")
        hashtag = input("ハッシュタグを入力 (#なし): ")
        # ハッシュタグが空でも続行可能に変更
        
        count = input("取得する動画数 (未入力=10): ") or "10"
        
        print("\nソート順を選択してください：")
        print("1. 再生回数順")
        print("2. いいね数順")
        print("3. コメント数順")
        sort_choice = input("選択してください (未入力=1): ") or "1"
        
        sort_map = {
            "1": "views",
            "2": "likes",
            "3": "comments"
        }
        
        min_views = input("最小再生回数 (未入力=100): ") or "100"
        
        return {
            "type": "hashtag",
            "hashtag": hashtag,  # 空文字列の場合もそのまま渡す
            "count": int(count),
            "sort_by": sort_map.get(sort_choice, "views"),
            "min_views": int(min_views)
        }

    def _get_video_settings(self) -> Dict:
        """特定動画の設定を取得"""
        print("\n=== 特定動画の設定 ===")
        video_urls = []
        
        while True:
            url = input("\n動画URLを入力してください: ")
            if not url:
                print("URLを入力してください")
                continue
            
            # 入力がnだった場合はスキップ
            if url.lower() == 'n':
                continue
            
            video_urls.append(url)
            
            if input("\n動画を追加しますか？ (y/N): ").lower() != 'y':
                break
        
        # URLからIDを抽出
        video_ids = []
        for url in video_urls:
            video_id = extract_video_id(url)
            if video_id:
                video_ids.append(video_id)
        
        return {
            "type": "video",
            "video_ids": video_ids  # video_urlsではなくvideo_idsを返す
        }

    def _confirm_settings(self, settings: Dict) -> bool:
        """設定内容の確認"""
        print("\n=== 設定内容の確認 ===")
        for key, value in settings.items():
            print(f"{key}: {value}")
        
        return input("\nこの設定で取得を実行しますか？ (y/N): ").lower() == 'y'

    def results_screen(self, stats: Dict) -> str:
        """結果画面"""
        self.display_header("結果")
        
        print(f"\n取得した動画数: {stats['total_videos']:,}")
        print(f"総再生回数: {stats['total_views']:,}")
        print(f"総いいね数: {stats['total_likes']:,}")
        print(f"平均再生回数: {stats['avg_views']:,.1f}")
        print(f"平均いいね数: {stats['avg_likes']:,.1f}")
        
        print("\n1. CSVエクスポート")
        print("2. データサマリー表示")
        print("3. データ削除")
        print("4. 終了")
        
        return input("\n選択してください (1-4): ")

    def show_privacy_policy(self):
        """プライバシーポリシーの表示"""
        self.display_header("プライバシーポリシー")
        try:
            with open('docs/PRIVACY.md', 'r', encoding='utf-8') as f:
                print(f.read())
        except FileNotFoundError:
            print("プライバシーポリシーファイルが見つかりません。")
        input("\nEnterキーを押して戻る...")

    def show_terms(self):
        """利用規約の表示"""
        self.display_header("利用規約")
        try:
            with open('docs/TERMS.md', 'r', encoding='utf-8') as f:
                print(f.read())
        except FileNotFoundError:
            print("利用規約ファイルが見つかりません。")
        input("\nEnterキーを押して戻る...")

    def display_data_summary(self, data: List[Dict]):
        """データサマリーの表示"""
        self.display_header("データサマリー")
        
        if not data:
            print("表示するデータがありません。")
            input("\nEnterキーで続行...")
            return
            
        try:
            # データの整形
            summary_data = []
            for video in data:
                stats = video.get("stats", {})
                author = video.get("author", {})
                create_time = datetime.fromtimestamp(video.get("createTime", 0))
                
                # 動画URLを取得（playAddrから）
                video_url = video.get("video", {}).get("playAddr", "")
                
                summary_data.append({
                    "投稿日時": create_time.strftime("%Y/%m/%d %H:%M"),
                    "作成者": author.get("uniqueId", "不明"),
                    "タイトル": video.get("desc", "")[:30] + "..." if len(video.get("desc", "")) > 30 else video.get("desc", ""),
                    "再生数": f'{stats.get("playCount", 0):,}',
                    "いいね数": f'{stats.get("diggCount", 0):,}',
                    "コメント数": f'{stats.get("commentCount", 0):,}',
                    "動画URL": video_url
                })
            
            df = pd.DataFrame(summary_data)
            print("\n" + tabulate(df, headers='keys', tablefmt='grid', showindex=False))
            
        except Exception as e:
            print(f"データ表示エラー: {e}")
        
        input("\nEnterキーで続行...")