from pathlib import Path
root = Path(__file__).resolve().parents[1]
path = root / 'docs/ATE_Command_List_for_Test_Program_Rev4_20261126.md'
text = path.read_text(encoding='utf-8')
text = text.replace('ATE要求・応答終端はCRLF。', 'ATE要求はCRLFで送る。応答終端はATE_RESPONSE_TERMINATORに従い、現行ソース既定はCR。CR／LF／CRLFから設定するためATEの受信設定を配置FWに合わせる。')
text = text.replace('要求・応答はCRLFとする。', '要求はCRLF、応答は配置FWの設定に従う（現行ソース既定CR）。')
text = text.replace('全ての要求・応答末尾にCRLFを付加する。', '要求末尾にCRLFを付加し、応答は配置FWの終端設定で受信する（現行ソース既定CR）。')
text = text.replace('要求・応答にはCRLFを付加する。', '要求にはCRLFを付加し、応答は配置FWの終端設定で受信する。')
text = text.replace('| CRLF | 要求・応答の行終端。CR=0x0D、LF=0x0A。 |', '| CRLF | CR=0x0D、LF=0x0A。要求例はCRLF。応答は設定依存で現行ソース既定CR。 |')
text = text.replace('直近の記録ではHost Unit Test / Mock NF55G Test全557件成功', '本改訂の直接指定AD追加後、Host Unit Test / Mock NF55G Test全567件成功。実機未配置。既存の直近記録では全557件成功')
path.write_text(text, encoding='utf-8')
path = root / 'README.md'
text = path.read_text(encoding='utf-8')
lines = text.splitlines()
for i, line in enumerate(lines):
    if line.startswith('最新版は2026-11-26の **Rev.3**'):
        lines[i] = line.replace('Rev.3', 'Rev.4').replace('Rev3_20261126', 'Rev4_20261126').replace(
            '7355 ADC設定、回路名での', '人が測定器を読んだ値をATEから直接指定するAD方式、7355 ADC設定、回路名での').replace(
            '今回は資料更新のみで、実機デバッグ・FW配置は行わない。Rev.2以前は履歴として保持する。',
            '直接指定ADを既存サンプル診断条件で実装し、Host／Mock全567件成功。実機デバッグ・FW配置は未実施。Rev.3以前は履歴として保持する。')
path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
# Markdown表の列数と、新入口・正式でない製品側条件を確認する。
text = (root / 'docs/ATE_Command_List_for_Test_Program_Rev4_20261126.md').read_text(encoding='utf-8')
expected = None
tables = 0
for line in text.splitlines():
    if line.startswith('|'):
        count = len(line.strip('|').split('|'))
        if expected is None:
            expected = count
            tables += 1
        assert count == expected, line
    else:
        expected = None
assert '第10.6／14.18節' in text
assert '方式採用確定。サンプル診断条件あり' in text
print('PASS: Rev.4 table columns and direct AD entry; tables=', tables)
