import os
import time
from typing import List, Dict

class TerminalUI:
    def __init__(self):
        self.width = 60
        self.data_summary: Dict = {}

    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def display_header(self, title: str):
        self.clear_screen()
        print("=" * self.width)
        print(f"{title:^{self.width}}")
        print("=" * self.width)
        print()

    def initial_screen(self) -> str:
        """初期画面の表示"""
        self.display_header("TikTok Data Analytics Tool")
        print("Welcome to TikTok Data Analytics Tool")
        print("\nThis tool allows you to:")
        print("- Collect public video statistics")
        print("- Store data securely")
        print("- Export analysis results")
        print("\nOptions:")
        print("1. Connect to TikTok")
        print("2. View Privacy Policy")
        print("3. View Terms of Service")
        print("4. Exit")
        print("\nPlease select an option: ")
        return input()

    def connecting_screen(self) -> str:
        """接続画面の表示"""
        self.display_header("Data Collection Settings")
        print("This tool will collect:")
        print("- Video statistics")
        print("- Public video information")
        print("- Basic creator information")
        print("\nData will be:")
        print("- Stored locally")
        print("- Encrypted using AES-256")
        print("- Automatically deleted after 30 days")
        print("\nOptions:")
        print("1. Proceed with connection")
        print("2. Go back")
        print("3. Exit")
        print("\nPlease select an option: ")
        return input()

    def auth_screen(self):
        """認証画面の表示（TikTok標準画面の模擬）"""
        self.display_header("TikTok Authorization")
        print("Connecting to TikTok...")
        print("\nYou will be redirected to TikTok's login page.")
        print("Please authorize the application.")
        print("\nPress Enter to continue...")
        input()

    def results_screen(self, data_summary: Dict) -> str:
        """結果画面の表示"""
        self.display_header("Analysis Results")
        print("Successfully connected to TikTok!")
        print(f"\nRetrieved data for {data_summary.get('video_count', 0)} videos")
        print("\nOptions:")
        print("1. Export to CSV")
        print("2. View Data Summary")
        print("3. Delete Data")
        print("4. Exit")
        print("\nPlease select an option: ")
        return input() 