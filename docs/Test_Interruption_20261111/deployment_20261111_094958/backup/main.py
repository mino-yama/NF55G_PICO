# Picoの/main.pyへ配置する通常起動の入口。src.mainの初期化と常駐ループを呼び出す。

"""Deployment entry point. Copy with the src/ package after HIL entry checks."""

from src.main import main

main()
