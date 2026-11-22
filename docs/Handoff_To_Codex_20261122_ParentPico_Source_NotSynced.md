# Codex引継ぎ 2026-11-22

## 現在の停止点

親Picoの実機ソース取得とworkspace側候補修正の照合まで完了した。親Pico実機はworkspace候補修正を含まないことをdiffで確認した。作業はここで停止し、繰返し調査をしない。

## 確認済み

- 親Pico COM6は通信対応USB CDCとして再認識。
- unique_idは `69f7d45962cfdfad`。
- 親Pico実ファイル: `src/external_instrument_link.py`
- 親Pico実サイズ: 9848 byte。
- workspace候補: 10012 byte。
- 親Picoとworkspaceはバイト一致しない。
- 差分は主にworkspace側の `take_reply()` に以下の修正候補が追加された部分。

```python
if result['status'] == 'LINK_NOT_READY' and not ambiguous:
    self.session = None
    self.host_info = None
    self.fault = False
```

親Pico実ファイルにはこの差分がない。親Picoは修正前ソースのまま。

## 未完了

- 親Picoへの修正ソース配置は未実施。
- Host `meter-host-relay-20261121.1` UF2の実機配置は未実施。
- 親Pico候補実機ソースの統合試験は未実施。
- 7355 idle切断、処理中切断、再接続、旧応答排除、親Cache INVALID連携は未実施。
- 長期反復・複合負荷・ATE/NF55G/SD共存受入は未実施。

## 次のCodex開始手順

1. 親Picoの実機ソースが修正前であることを最初に確認する。
2. `src/external_instrument_link.py`の候補修正を親Picoの配置パッケージへ含める。
3. 親Picoの対象個体・現行Flashを退避し、配置用ソースhashを照合する。
4. 親Picoを配置・再起動し、COM6からunique_idと修正後ソースを照合する。
5. Host `meter-host-relay-20261121.1` UF2を別工程で配置し、同じ対象Hostを再起動する。
6. その後にidle切断/再接続の統合試験を1回だけ実施する。
7. 成功確認前に追加の切断・測定・設定変更を送らない。

## 現在の候補実装

- Host candidate: `meter-host-relay-20261121.1`
- Host candidate UF2: `firmware/usb_submcu_external_meter_host/build/usb_submcu_external_meter_relay.uf2`
- Host candidate UF2 SHA-256: `2C7314B9ED42F00ACD6EAF32684854FF13EEBE4101B4F8E6ACB3506C6F4E014B`
- 親Pico unique_id: `69f7d45962cfdfad`
- 親Pico実機source: `9848 byte`、workspace候補: `10012 byte`
- 親Pico実機Host/Mock修正反映: 未確認、実比較では修正差分あり

## 停止理由

親PicoとHostの候補修正が統合されていない状態で切断試験を繰り返すと、実機原因とソース未反映を区別できないため停止する。
