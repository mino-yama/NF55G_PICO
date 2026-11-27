# NF55G 校正書込み許可範囲の初期設定（2026-11-27 / Rev.0）
# PicoのMicroPythonからimportして使用するための定数ファイル。
# Pico起動時に読み込み、ADの送信直前に全6点の設定と候補値を検証する。
#
# 修正する箇所：各回路・A/B点のLOWER（下限）とUPPER（上限）の数値。
# 初期値は基準値の±20%。今後は下限・上限を個別に変更できる。
# 判定：LOWER以上、UPPER以下の値だけ書込みを許可する。
# 単位：電流はA、電圧はV。DMM原文ではなく単位換算後の書込み値へ適用。
# 範囲外の値を範囲内へ丸めたり、目標値で置き換えたりしない。
# 値を変更したらSETTINGS_REVも更新し、ファイル配置後にPicoを再起動する。

SETTINGS_REV = "20261127-Rev0"

# ① バッテリ放電電流 DISCHG_I（動作条件：バッテリ充電）
# A点：44 A付近 → 初期範囲35.2～52.8 A
DISCHG_I_A_LOWER = 35.2       # 下限 [A]
DISCHG_I_A_UPPER = 52.8       # 上限 [A]

# B点：0.3 A付近 → 初期範囲0.24～0.36 A
DISCHG_I_B_LOWER = 0.24       # 下限 [A]
DISCHG_I_B_UPPER = 0.36       # 上限 [A]

# ② バッテリ充電電流 BATT_CHG（動作条件：バッテリ放電）
# A点：1.85 A付近 → 初期範囲1.48～2.22 A
BATT_CHG_A_LOWER = 1.48       # 下限 [A]
BATT_CHG_A_UPPER = 2.22       # 上限 [A]

# B点：0.5 A付近 → 初期範囲0.4～0.6 A
BATT_CHG_B_LOWER = 0.4        # 下限 [A]
BATT_CHG_B_UPPER = 0.6        # 上限 [A]

# ③ バッテリ電圧 BATT_V（動作条件：充電時）
# A点：8 V付近 → 初期範囲6.4～9.6 V
BATT_V_A_LOWER = 6.4          # 下限 [V]
BATT_V_A_UPPER = 9.6          # 上限 [V]

# B点：5 V付近 → 初期範囲4～6 V
BATT_V_B_LOWER = 4.0          # 下限 [V]
BATT_V_B_UPPER = 6.0          # 上限 [V]
