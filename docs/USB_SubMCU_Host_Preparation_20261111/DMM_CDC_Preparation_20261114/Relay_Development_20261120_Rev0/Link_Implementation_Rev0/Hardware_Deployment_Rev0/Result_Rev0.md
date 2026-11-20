# 中継実機配置前確認 Rev.0

2026-11-20 親配置完了: COM6/unique_id 69f7d45962cfdfadの既存26ファイルを退避・SHA照合後、配置対象30ファイルを実機SHA照合（追加/更新8）。実機RAM検証と配置後import成功。通常起動せずREPL停止、PIO4/5はinactive。Host/親の配置は完了したが、配線と実機中継受入は未実施。[親配置結果](Parent_Deployment_01/Result_Rev0.md)。以下の親未配置記述は配置前の状態として保持。

2026-11-20 後続配置: Host BFCF2EDB84B0B37Fへmeter-host-relay-20261120.1を書込み、Flash verifyと書込み後版照合に成功。旧.5全Flash退避・照合済み。BOOTSELのままrebootせず、親Picoは未配置・実機中継未試験。[Host配置結果](Host_Deployment_01/Result_Rev0.md)。以下のHost未配置記述は配置前の状態として保持。

2026-11-20 JST。実機配置に向けて読取り確認を実施。

- 配置用31ファイルのSHA-256はmanifestと全て一致。
- 現在の接続中ポートはUSB-SERIAL CH341 COM22（状態OK）。列挙一覧に親Pico/HostのVID_2E8A機器は現れなかった。
- 対象serial BFCF2EDB84B0B37Fを指定したpicotool infoは、アクセス可能なBOOTSEL機器なし（exit 1）。
- USB列挙結果だけで無給電/物理切離し済みとは判断しない。Flash操作・親ファイル変更・reset・計測器送信は行っていない。

次はユーザー側でHostの外部5V・7355 USB・診断UARTを外し、Host開発USB-CだけでPCへ接続してBOOTSELに入れる。対象認識後に現Flash退避・照合から進める。親Picoはこの段階ではまだ接続しない。

[確認記録](Preflight_01.json)／[全体受入手順](../Acceptance_Procedure_Rev0.md)
